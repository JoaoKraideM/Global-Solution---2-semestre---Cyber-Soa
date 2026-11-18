"""API REST SombraViva. Execute migrações e seed antes de iniciar."""
from collections import defaultdict, deque
from datetime import datetime, timezone, date, timedelta
from pathlib import Path
import time
import httpx
from fastapi import FastAPI, Depends, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware
from sqlalchemy import select, func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.database import get_db
from app import config
from app.models import User, Station, Reading, SecurityEvent, AuditFinding, SecurityTriageAction
from app.auth import authenticate_device, create_token, require_admin, verify_password
from app.schemas import LoginIn, SensorReadingIn, AuditIn, EventTriageIn
from app.taint import audit_flow
from app.pii import classify
from app.llm import explain_findings
from app.security_intelligence import build_alerts, is_security_signal, ai_report
from app.seed import ensure_soc_scenarios
from app.demo import snapshot, weather_snapshot, history_snapshot, search_snapshot
from app.heatmap import build_heatmap
from app.weather_history import archive_for_location, search_cities
from app.routers import medicoes as medicoes_router

app = FastAPI(title="SombraViva CitizenTech API", version="0.1.0", description="Monitoramento climático urbano: IoT + SOA + Cybersecurity. Dados de demonstração identificados como simulados.")
app.add_middleware(GZipMiddleware, minimum_size=1400)  # bundle CSS/JS e respostas grandes
ROOT = Path(__file__).resolve().parent.parent
app.include_router(medicoes_router.router)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
failed_logins: dict[str, deque] = defaultdict(deque)
failed_iot_keys: dict[str, deque] = defaultdict(deque)  # limite local de demonstração, não distribuído
WEATHER_CACHE = {"expires": 0.0, "data": None}
AI_SOC_LIMITS: dict[int, deque] = defaultdict(deque)  # limite por processo; Redis em produção multi-instância


def iso_utc(dt: datetime | None):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def event(db: Session, category: str, severity: str, outcome: str, summary: str):
    # Sem IP, senha, token, corpo HTTP ou CPF.
    db.add(SecurityEvent(category=category, severity=severity, outcome=outcome, summary=summary))
    db.commit()


def station_output(db: Session, station: Station):
    latest = db.scalars(select(Reading).where(Reading.station_id == station.id).order_by(Reading.measured_at.desc(), Reading.id.desc()).limit(1)).first()
    return {"code": station.code, "name": station.name, "setting": station.setting,
            "simulated": station.simulated, "latest": None if not latest else {
              "temperature_c": latest.temperature_c, "humidity_pct": latest.humidity_pct,
              "measured_at": iso_utc(latest.measured_at), "simulated": latest.is_simulated}}

@app.middleware("http")
async def protective_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.url.path in ("/", "/admin", "/api/v1/auth/login") or request.url.path.startswith("/api/v1/admin"):
        # Autenticação e dados administrativos nunca são cacheados.
        response.headers["Cache-Control"] = "no-store"
    elif request.url.path.startswith("/static/"):
        # Revalidação por ETag: permite 304, sem manter versões desatualizadas.
        response.headers["Cache-Control"] = "public, max-age=0, must-revalidate"
    if not request.url.path.startswith(("/docs", "/redoc")):
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: https://commons.wikimedia.org https://upload.wikimedia.org https://www.visaooeste.com.br https://www.aeaosasco.org.br https://www.oanhanguera.com.br https://agenciamural.org.br; connect-src 'self'; frame-src https://www.openstreetmap.org; frame-ancestors 'none'"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response

@app.get("/", include_in_schema=False)
def homepage():
    return FileResponse(ROOT / "static" / "index.html")

@app.get("/admin", include_in_schema=False)
def admin_page():
    return FileResponse(ROOT / "static" / "admin.html")

@app.get("/api/v1/health", tags=["infra"])
def health():
    return {"status": "ok", "service": "sombraviva", "version": "0.1.0"}

@app.get("/health", tags=["infra"], summary="Health check usado pelo monitor e pelo Nginx da VM")
def health_root(db: Session = Depends(get_db)):
    """Responde 200 com o MySQL acessível e 503 quando o banco cai (usado no teste de falha da VM)."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível")
    return {"status": "ok", "service": "sombraviva", "banco": "ok", "horario": datetime.now(timezone.utc).isoformat()}


@app.get("/api/v1/health/db", tags=["infra"])
def database_health(db: Session = Depends(get_db)):
    """Verifica efetivamente a conexão com o banco MySQL."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível")
    return {"status": "ok", "database": "mysql" if config.DATABASE_URL.get_backend_name() == "mysql" else "test"}


@app.get("/api/v1/stations", tags=["clima"])
def get_stations(db: Session = Depends(get_db)):
    stations = db.scalars(select(Station).order_by(Station.id)).all()
    return [station_output(db, station) for station in stations]

@app.get("/api/v1/stations/{code}/readings", tags=["clima"])
def get_readings(code: str, limit: int = Query(24, ge=1, le=200), db: Session = Depends(get_db)):
    station = db.scalar(select(Station).where(Station.code == code))
    if station is None:
        raise HTTPException(404, "Sensor não encontrado")
    rows = db.scalars(select(Reading).where(Reading.station_id == station.id).order_by(Reading.measured_at.desc(), Reading.id.desc()).limit(limit)).all()
    return [{"temperature_c": r.temperature_c, "humidity_pct": r.humidity_pct,
             "measured_at": iso_utc(r.measured_at), "simulated": r.is_simulated} for r in reversed(rows)]

@app.post("/api/v1/stations/{code}/readings", status_code=201, tags=["iot"])
def ingest_reading(code: str, reading: SensorReadingIn, request: Request, x_device_key: str | None = Header(default=None), db: Session = Depends(get_db)):
    station = db.scalar(select(Station).where(Station.code == code))
    if not station:
        raise HTTPException(404, "Sensor não encontrado")
    # Proteção contra inundação de logs por chaves inválidas: 10 falhas/minuto por
    # origem e estação. A implementação é por processo, não substitui gateway/Redis.
    origin = request.client.host if request.client else "unknown"
    bucket = failed_iot_keys[f"{origin}:{station.code}"]
    now = time.monotonic()
    while bucket and bucket[0] < now - 60:
        bucket.popleft()
    valid_key = bool(x_device_key and len(x_device_key) <= 256 and
                     authenticate_device(x_device_key, station.api_key_hash))
    if not valid_key:
        if len(bucket) >= 10:
            # Rejeite sem adicionar novos registros ao banco: evita log flooding.
            # Uma chave legítima continua apta a enviar leituras nessa origem.
            raise HTTPException(429, "Muitas tentativas de autenticação IoT. Tente novamente em 60 segundos.")
        bucket.append(now)
        event(db, "iot_auth", "medium", "blocked", f"Falha de autenticação de dispositivo: {station.code}")
        raise HTTPException(401, "Credencial de dispositivo inválida")
    bucket.clear()
    new = Reading(station_id=station.id, temperature_c=reading.temperature_c,
                  humidity_pct=reading.humidity_pct, measured_at=datetime.now(timezone.utc), is_simulated=station.simulated)
    db.add(new)
    db.commit()
    db.refresh(new)
    return {"id": new.id, "station": code, "measured_at": iso_utc(new.measured_at), "simulated": new.is_simulated}

@app.get("/api/v1/demo/summary", tags=["demonstração"])
def demonstration_summary():
    """Cenário fictício em memória, independente de MySQL; nunca é uma medição real."""
    return snapshot()

@app.get("/api/v1/heatmap/demo", tags=["demonstração"])
def demonstration_heatmap(period: str = Query("tarde", pattern="^(tarde|noite)$")):
    """Mapa térmico de DEMONSTRAÇÃO, não observacional nem microclimático."""
    return build_heatmap(period)

@app.get("/api/v1/demo/places", tags=["demonstração"])
def demonstration_places(search: str = Query(..., min_length=2, max_length=80)):
    """Busca de cidades de referência, com coordenadas aproximadas, para modo offline."""
    return search_snapshot(search)

@app.get("/api/v1/demo/weather", tags=["demonstração"])
def demonstration_weather():
    """Valor artificial, identificado e sem qualquer observação meteorológica."""
    return weather_snapshot()

@app.get("/api/v1/demo/history", tags=["demonstração"])
def demonstration_history(latitude: float = Query(...,ge=-90,le=90),
                          longitude: float = Query(...,ge=-180,le=180),
                          start_date: date = Query(...), end_date: date = Query(...)):
    """Série artificial usada SOMENTE em prévias sem a fonte Open-Meteo."""
    return history_snapshot(latitude,longitude,start_date,end_date)

@app.get("/api/v1/summary", tags=["clima"])
def summary(db: Session = Depends(get_db)):
    stations = [station_output(db, s) for s in db.scalars(select(Station).order_by(Station.id)).all()]
    current = [s for s in stations if s["latest"]]
    diff = None
    if len(current) >= 2:
        a, b = current[0]["latest"], current[1]["latest"]
        t1, t2 = datetime.fromisoformat(a["measured_at"]), datetime.fromisoformat(b["measured_at"])
        if abs((t1 - t2).total_seconds()) <= 600:
            diff = round(a["temperature_c"] - b["temperature_c"], 1)
    return {"station_count": len(stations), "readings_total": db.scalar(select(func.count(Reading.id))) or 0,
            "stations": stations, "pairwise_difference_c": diff,
            "notice": "Diferença apenas descritiva entre sensores; não demonstra causalidade nem representa toda a cidade."}

@app.get("/api/v1/weather/osasco", tags=["clima"])
async def osasco_weather():
    now = time.monotonic()
    if WEATHER_CACHE["data"] is not None and now < WEATHER_CACHE["expires"]:
        return WEATHER_CACHE["data"]
    params = {"latitude": -23.5329, "longitude": -46.7917, "current": "temperature_2m,relative_humidity_2m,apparent_temperature",
              "timezone": "America/Sao_Paulo"}
    try:
        async with httpx.AsyncClient(timeout=7.0) as client:
            response = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
            response.raise_for_status()
            raw = response.json()
        current = raw["current"]
        data = {"source": "Open-Meteo", "type": "modelo_meteorologico_regional", "time": current["time"],
                "temperature_c": current["temperature_2m"], "humidity_pct": current["relative_humidity_2m"],
                "apparent_temperature_c": current["apparent_temperature"],
                "attribution": "https://open-meteo.com/", "note": "Estimativa modelada regional, não medição específica do Calçadão."}
        WEATHER_CACHE.update({"data": data, "expires": now + 900})
        return data
    except (httpx.HTTPError, KeyError, ValueError):
        raise HTTPException(503, "Fonte meteorológica temporariamente indisponível")

@app.get("/api/v1/weather/places", tags=["clima"])
async def weather_places(search: str = Query(..., min_length=2, max_length=80, description="Nome da cidade, por exemplo Osasco ou São Paulo")):
    """Busca cidades pelo nome e devolve coordenadas para a consulta histórica."""
    if not search.strip() or len(search.strip()) < 2:
        raise HTTPException(422, "Informe pelo menos dois caracteres no nome da cidade")
    return await search_cities(search)


@app.get("/api/v1/weather/history", tags=["clima"])
async def weather_history(latitude: float = Query(..., ge=-90, le=90),
                          longitude: float = Query(..., ge=-180, le=180),
                          start_date: date = Query(..., description="AAAA-MM-DD"),
                          end_date: date = Query(..., description="AAAA-MM-DD")):
    """Série diária real, histórica e REGIONAL para coordenadas de uma cidade."""
    return await archive_for_location(latitude, longitude, start_date, end_date)


@app.get("/api/v1/weather/history/osasco", tags=["clima"])
async def osasco_historical_weather(start_date: date = Query(..., description="AAAA-MM-DD"),
                                    end_date: date = Query(..., description="AAAA-MM-DD")):
    """Compatibilidade com clientes antigos: mesmo histórico, fixado em Osasco."""
    return await archive_for_location(-23.5329, -46.7917, start_date, end_date)

@app.post("/api/v1/auth/login", tags=["autenticação"])
def login(payload: LoginIn, request: Request, db: Session = Depends(get_db)):
    # Limite simples por origem para DEMO; em produção usar rate limiting compartilhado.
    origin = request.client.host if request.client else "unknown"
    attempts = failed_logins[origin]
    now = time.monotonic()
    while attempts and attempts[0] < now - 60:
        attempts.popleft()
    if len(attempts) >= 5:
        event(db, "login", "high", "blocked", "Excesso de tentativas de login")
        raise HTTPException(429, "Muitas tentativas. Tente novamente em 60 segundos.")
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        attempts.append(now)
        event(db, "login", "low", "failed", "Tentativa de autenticação recusada")
        raise HTTPException(401, "Credenciais inválidas")
    attempts.clear()
    event(db, "login", "info", "success", "Autenticação administrativa bem-sucedida")
    return {"access_token": create_token(user), "token_type": "bearer", "expires_in": 7200}

@app.get("/api/v1/admin/overview", tags=["cybersecurity"])
def admin_overview(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    events = db.scalars(select(SecurityEvent).order_by(SecurityEvent.id.desc()).limit(40)).all()
    findings = db.scalars(select(AuditFinding).order_by(AuditFinding.id.desc()).limit(40)).all()
    blocked = db.scalar(select(func.count(SecurityEvent.id)).where(SecurityEvent.outcome == "blocked")) or 0
    failed = db.scalar(select(func.count(SecurityEvent.id)).where(SecurityEvent.outcome == "failed")) or 0
    high = db.scalar(select(func.count(AuditFinding.id)).where(AuditFinding.severity == "high")) or 0
    medium = db.scalar(select(func.count(AuditFinding.id)).where(AuditFinding.severity == "medium")) or 0
    # Pontuação HEURÍSTICA de demonstração; não é modelo calibrado de risco real.
    risk = min(100, high * 20 + medium * 9 + blocked * 6 + failed * 2)
    return {"risk_citizen_demo": risk, "risk_method": "heurística demonstrativa: 20/achado alto + 9/médio + 6/bloqueio + 2/login falho; máximo 100",
            "counts": {"demo_events": db.scalar(select(func.count(SecurityEvent.id)).where(SecurityEvent.is_demo.is_(True))) or 0, "demo_findings": db.scalar(select(func.count(AuditFinding.id)).where(AuditFinding.is_demo.is_(True))) or 0, "events": db.scalar(select(func.count(SecurityEvent.id))) or 0, "blocked": blocked,
                       "failed_logins": failed, "findings": db.scalar(select(func.count(AuditFinding.id))) or 0},
            "events": [{"id": e.id, "category": e.category, "severity": e.severity, "outcome": e.outcome,
                        "summary": e.summary, "is_demo": e.is_demo, "created_at": iso_utc(e.created_at)} for e in events],
            "findings": [{"id": f.id, "category": f.category, "severity": f.severity, "source": f.source,
                          "sink": f.sink, "field": f.field, "action": f.action, "remediation": f.remediation,
                          "evidence_redacted": f.evidence_redacted, "is_demo": f.is_demo, "created_at": iso_utc(f.created_at)} for f in findings]}

@app.post("/api/v1/admin/audit", tags=["cybersecurity"])
def audit_sample(payload: AuditIn, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    result = audit_flow(payload.sample_text, payload.source, payload.sink)
    for kind in result["pii_types"]:
        db.add(AuditFinding(category="PII/taint:" + kind, severity=result["severity"],
                            source=payload.source, sink=payload.sink, field=kind,
                            action=result["action"], evidence_redacted="[DADO_SENSIVEL_REDACTED]",
                            remediation=result["remediation"]))
    db.commit()
    if result["blocked"]:
        event(db, "taint", result["severity"], "blocked", "Fluxo inseguro identificado e bloqueado")
    return result

@app.post("/api/v1/admin/remediation", tags=["cybersecurity"])
async def remediation(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    findings = db.scalars(select(AuditFinding).order_by(AuditFinding.id.desc()).limit(5)).all()
    # Somente categorias e metadados, NUNCA conteúdo PII, são enviados ao provedor LLM.
    abstract = [{"type": f.category, "source": f.source, "sink": f.sink, "severity": f.severity} for f in findings]
    return await explain_findings(abstract)


# Central operacional: somente eventos observados; exemplos fictícios ficam em trilha própria.
def _event_view(e: SecurityEvent):
    return {"id":e.id,"category":e.category,"severity":e.severity,"outcome":e.outcome,
            "summary":e.summary,"is_demo":e.is_demo,"created_at":iso_utc(e.created_at),
            "triage_status":e.triage_status,"triage_note":e.triage_note,
            "triaged_at":iso_utc(e.triaged_at)}

@app.get("/api/v1/admin/operations", tags=["cybersecurity"])
def admin_operations(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Indicadores operacionais, com janela fixa de 24 horas e cenário fictício separado."""
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    observed = SecurityEvent.is_demo.is_(False)
    recent = SecurityEvent.created_at >= since
    active = db.scalar(select(func.count(SecurityEvent.id)).where(
        observed, SecurityEvent.triage_status != "resolved",
        SecurityEvent.severity.in_(["high","medium"]),
        SecurityEvent.outcome.in_(["failed","blocked"]))) or 0
    failed = db.scalar(select(func.count(SecurityEvent.id)).where(
        observed, recent, SecurityEvent.category == "login", SecurityEvent.outcome == "failed")) or 0
    rejected = db.scalar(select(func.count(SecurityEvent.id)).where(
        observed, recent, SecurityEvent.category == "iot_auth", SecurityEvent.outcome == "blocked")) or 0
    demo_events = db.scalar(select(func.count(SecurityEvent.id)).where(SecurityEvent.is_demo.is_(True))) or 0
    demo_findings = db.scalar(select(func.count(AuditFinding.id)).where(AuditFinding.is_demo.is_(True))) or 0
    real_findings = db.scalar(select(func.count(AuditFinding.id)).where(AuditFinding.is_demo.is_(False))) or 0
    stations = []
    stale_real = 0
    now = datetime.now(timezone.utc)
    for station in db.scalars(select(Station).order_by(Station.id)).all():
        newest = db.scalars(select(Reading).where(Reading.station_id == station.id).order_by(Reading.measured_at.desc(), Reading.id.desc()).limit(1)).first()
        measured = newest.measured_at if newest else None
        if measured and measured.tzinfo is None:
            measured = measured.replace(tzinfo=timezone.utc)
        stale = measured is None or (now - measured).total_seconds() > 15 * 60
        if not station.simulated and stale:
            stale_real += 1
        stations.append({"code":station.code,"name":station.name,"setting":station.setting,
                         "simulated":station.simulated,"status": "demo" if station.simulated else ("stale" if stale else "recent"),
                         "last_seen_at":iso_utc(measured),
                         "latest": None if newest is None else {"temperature_c":newest.temperature_c,
                           "humidity_pct":newest.humidity_pct,"simulated":newest.is_simulated}})
    attention = db.scalars(select(SecurityEvent).where(
        observed, SecurityEvent.triage_status != "resolved",
        SecurityEvent.severity.in_(["high", "medium"]),
        SecurityEvent.outcome.in_(["failed", "blocked"]))
        .order_by(SecurityEvent.created_at.desc(), SecurityEvent.id.desc()).limit(5)).all()
    return {"window_hours":24, "refresh_mode":"manual",
            "attention_events": [_event_view(e) for e in attention],
            "counts":{"open_alerts":active,"failed_logins_24h":failed,"rejected_devices_24h":rejected,
                      "stale_real_stations":stale_real,"demo_events":demo_events,
                      "demo_findings":demo_findings,"real_findings":real_findings,
                      "stations":len(stations),"simulated_stations":sum(s["simulated"] for s in stations)},
            "stations":stations,
            "methodology":"Alertas: eventos reais não resolvidos de gravidade média/alta com resultado failed/blocked. Falhas e rejeições: últimas 24 horas. Estação real sem leitura recente: mais de 15 minutos; simulações não são avaliadas como equipamento físico."}

@app.get("/api/v1/admin/events", tags=["cybersecurity"])
def admin_events(_: User = Depends(require_admin), db: Session = Depends(get_db),
                 include_demo: bool = Query(False),
                 category: str = Query("all", pattern="^(all|login|iot_auth|taint)$"),
                 severity: str = Query("all", pattern="^(all|info|low|medium|high)$"),
                 status: str = Query("all", pattern="^(all|new|investigating|resolved)$"),
                 offset: int = Query(0, ge=0), limit: int = Query(30, ge=1, le=100)):
    """Filtra, pagina e separa evidência real de demonstrações."""
    conditions = []
    if not include_demo: conditions.append(SecurityEvent.is_demo.is_(False))
    if category != "all": conditions.append(SecurityEvent.category == category)
    if severity != "all": conditions.append(SecurityEvent.severity == severity)
    if status != "all": conditions.append(SecurityEvent.triage_status == status)
    total = db.scalar(select(func.count(SecurityEvent.id)).where(*conditions)) or 0
    events = db.scalars(select(SecurityEvent).where(*conditions).order_by(SecurityEvent.created_at.desc(),SecurityEvent.id.desc()).offset(offset).limit(limit)).all()
    return {"total":total,"limit":limit,"offset":offset,"events":[_event_view(e) for e in events]}

@app.get("/api/v1/admin/events/{event_id}", tags=["cybersecurity"])
def admin_event_detail(event_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Acesso ao registro específico preserva a rastreabilidade sem depender de paginação."""
    item = db.get(SecurityEvent, event_id)
    if item is None:
        raise HTTPException(404, "Evento não encontrado")
    return _event_view(item)

@app.patch("/api/v1/admin/events/{event_id}/triage", tags=["cybersecurity"])
def update_triage(event_id: int, payload: EventTriageIn, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Registra a investigação e uma trilha imutável de ações, sem conteúdo sensível."""
    item = db.get(SecurityEvent, event_id)
    if item is None:
        raise HTTPException(404, "Evento não encontrado")
    note = classify(payload.note.strip())["redacted"]
    if payload.status == "resolved" and len(note) < 8:
        raise HTTPException(422, "Para resolver, registre uma justificativa com pelo menos oito caracteres")
    if item.triage_status == payload.status and item.triage_note == note:
        return _event_view(item)
    db.add(SecurityTriageAction(event_id=item.id, actor_id=admin.id,
         previous_status=item.triage_status, next_status=payload.status, note=note))
    item.triage_status = payload.status
    item.triage_note = note
    item.triaged_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)
    return _event_view(item)

@app.get("/api/v1/admin/events/{event_id}/history", tags=["cybersecurity"])
def triage_history(event_id: int, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    if db.get(SecurityEvent, event_id) is None:
        raise HTTPException(404, "Evento não encontrado")
    actions = db.scalars(select(SecurityTriageAction).where(SecurityTriageAction.event_id == event_id).order_by(SecurityTriageAction.id.desc())).all()
    return [{"previous_status":a.previous_status,"next_status":a.next_status,
             "note":a.note,"actor_id":a.actor_id,"created_at":iso_utc(a.created_at)} for a in actions]

@app.get("/api/v1/admin/findings", tags=["cybersecurity"])
def admin_findings(_: User = Depends(require_admin), db: Session = Depends(get_db),
                   include_demo: bool = Query(False), limit: int = Query(30, ge=1, le=100)):
    constraints = [] if include_demo else [AuditFinding.is_demo.is_(False)]
    rows = db.scalars(select(AuditFinding).where(*constraints).order_by(AuditFinding.created_at.desc(),AuditFinding.id.desc()).limit(limit)).all()
    return [{"id":f.id,"category":f.category,"severity":f.severity,"source":f.source,
             "sink":f.sink,"action":f.action,"remediation":f.remediation,
             "is_demo":f.is_demo,"created_at":iso_utc(f.created_at)} for f in rows]


# Análise SOC acadêmica: alertas derivados de observações, sem confirmar invasão.
@app.get("/api/v1/admin/security/alerts", tags=["cybersecurity"])
def security_alerts(_: User = Depends(require_admin), db: Session = Depends(get_db),
                    include_demo: bool = Query(False), hours: int = Query(24, ge=1, le=168),
                    status: str = Query("open", pattern="^(open|resolved|all)$"),
                    limit: int = Query(100, ge=1, le=100)):
    return build_alerts(db, include_demo=include_demo, hours=hours, status=status, limit=limit)


@app.post("/api/v1/admin/security/alerts/{event_id}/analyze", tags=["cybersecurity"])
async def analyze_security_alert(event_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Solicitação explícita de IA. Análise de metadados mínimos, nunca logs ou dados pessoais."""
    found = db.get(SecurityEvent, event_id)
    if found is None or not is_security_signal(found):
        raise HTTPException(404, "Alerta de segurança não encontrado")
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    similar = db.scalar(select(func.count(SecurityEvent.id)).where(
        SecurityEvent.category == found.category, SecurityEvent.is_demo == found.is_demo,
        SecurityEvent.outcome.in_(["blocked", "failed"]), SecurityEvent.created_at >= since)) or 1
    if config.OPENAI_API_KEY and config.OPENAI_API_KEY.lower() not in ("xxxxx", "test", "sua_chave"):
        attempts = AI_SOC_LIMITS[admin.id]
        now = time.monotonic()
        while attempts and attempts[0] < now - 3600:
            attempts.popleft()
        if len(attempts) >= 6:
            raise HTTPException(429, "Limite de seis análises assistidas por hora. Use o relatório por regras locais.")
        attempts.append(now)
    return await ai_report(found, similar)


@app.post("/api/v1/admin/security/demo-scenario", tags=["demonstração"])
def create_soc_demo(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Cria os três casos de apresentação individualmente, sem tocar logs reais."""
    if not __import__("os").getenv("APP_ENV", "development").lower() in {"development", "dev", "test"}:
        raise HTTPException(403, "Casos fictícios só podem ser criados em desenvolvimento.")
    with db.begin_nested():
        created = ensure_soc_scenarios(db)
    db.commit()
    return {"created": created,
            "simulated": True,
            "notice": "Cenários estritamente fictícios; nenhuma invasão ocorreu. Ative 'Incluir cenários fictícios' para consultar."}
