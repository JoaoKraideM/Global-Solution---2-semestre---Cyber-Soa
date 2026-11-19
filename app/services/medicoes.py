"""Regras de domínio da telemetria IoT: autenticação do dispositivo, mapeamento
zona -> estação e cálculo do resumo de ilha de calor."""
from datetime import datetime, timezone
import hmac
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.auth import hash_device_key
from app.models import IotDevice, Reading, Station, SecurityEvent
from app.schemas import MedicaoIn, Zona, NivelRisco

# Cada zona monitorada pelo ESP32 alimenta uma estação já exibida no portal.
ZONA_PARA_ESTACAO = {Zona.sem_vegetacao: "centro-demo", Zona.arborizada: "verde-demo"}
LIMIAR_ILHA_CALOR_C = 3.0


class DispositivoNaoAutorizado(Exception):
    """Token ausente, desconhecido ou de dispositivo desativado."""


class DispositivoDivergente(Exception):
    """O device_id do corpo/cabeçalho não corresponde ao token apresentado."""


def registrar_evento(db: Session, severity: str, outcome: str, summary: str) -> None:
    # Nunca grava o token, IP ou corpo da requisição.
    db.add(SecurityEvent(category="iot_auth", severity=severity, outcome=outcome, summary=summary[:300]))
    db.commit()


def autenticar(db: Session, token: str | None) -> IotDevice:
    if not token:
        raise DispositivoNaoAutorizado("Token ausente")
    digest = hash_device_key(token)
    for device in db.scalars(select(IotDevice).where(IotDevice.active.is_(True))).all():
        if hmac.compare_digest(device.token_hash, digest):
            return device
    raise DispositivoNaoAutorizado("Token inválido")


def registrar_medicao(db: Session, device: IotDevice, medicao: MedicaoIn, header_device_id: str | None) -> Reading:
    if medicao.device_id != device.device_id or (header_device_id and header_device_id != device.device_id):
        raise DispositivoDivergente(device.device_id)
    station = db.scalar(select(Station).where(Station.code == ZONA_PARA_ESTACAO[medicao.zona]))
    if station is None:
        raise LookupError("Estação da zona não cadastrada; execute python -m app.seed")
    medido_em = medicao.timestamp or datetime.now(timezone.utc)
    if medido_em.tzinfo is None:
        medido_em = medido_em.replace(tzinfo=timezone.utc)
    reading = Reading(
        station_id=station.id, temperature_c=medicao.temperatura, humidity_pct=medicao.umidade,
        measured_at=medido_em.astimezone(timezone.utc), is_simulated=True, source="esp32-wokwi",
        device_id=device.device_id, zone=medicao.zona.value, heat_index_c=medicao.indice_calor,
        luminosity_lux=medicao.luminosidade, risk_level=medicao.nivel_risco.value,
        heat_island_delta_c=medicao.delta_ilha_calor, official_temp_c=medicao.temperatura_oficial)
    device.last_seen_at = datetime.now(timezone.utc)
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def para_saida(reading: Reading, station_code: str) -> dict:
    dt = reading.measured_at
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return {"id": reading.id, "device_id": reading.device_id, "estacao": station_code,
            "zona": reading.zone, "temperatura": reading.temperature_c, "umidade": reading.humidity_pct,
            "indice_calor": reading.heat_index_c, "luminosidade": reading.luminosity_lux,
            "nivel_risco": reading.risk_level, "delta_ilha_calor": reading.heat_island_delta_c,
            "temperatura_oficial": reading.official_temp_c, "medido_em": dt,
            "origem": reading.source, "simulado": reading.is_simulated}


def listar(db: Session, zona: Zona | None, limit: int) -> list[dict]:
    stmt = (select(Reading, Station.code).join(Station, Reading.station_id == Station.id)
            .where(Reading.source == "esp32-wokwi"))
    if zona is not None:
        stmt = stmt.where(Reading.zone == zona.value)
    rows = db.execute(stmt.order_by(Reading.measured_at.desc(), Reading.id.desc()).limit(limit)).all()
    return [para_saida(r, code) for r, code in rows]


def resumo(db: Session) -> dict:
    zonas, ultimas = [], {}
    for zona, code in ZONA_PARA_ESTACAO.items():
        base = select(Reading).where(Reading.source == "esp32-wokwi", Reading.zone == zona.value)
        total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
        last = db.scalars(base.order_by(Reading.measured_at.desc(), Reading.id.desc()).limit(1)).first()
        ultimas[zona] = last
        zonas.append({"zona": zona, "estacao": code, "total_medicoes": total,
                      "ultima": para_saida(last, code) if last else None})
    delta = None
    a, b = ultimas[Zona.sem_vegetacao], ultimas[Zona.arborizada]
    if a and b:
        delta = round(a.temperature_c - b.temperature_c, 1)
    ordem = ["normal", "atencao", "alerta", "perigo"]
    niveis = [r.risk_level for r in (a, b) if r and r.risk_level in ordem]
    atual = max(niveis, key=ordem.index) if niveis else None
    return {"zonas": zonas, "delta_ilha_calor_c": delta,
            "ilha_de_calor": delta is not None and delta >= LIMIAR_ILHA_CALOR_C,
            "nivel_risco_atual": NivelRisco(atual) if atual else None,
            "aviso": "Leituras do ESP32 simulado no Wokwi; não são medições físicas no Calçadão."}
