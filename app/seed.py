"""Bootstrap idempotente de usuários e cenários acadêmicos estritamente fictícios.

Não dispara ataques, não chama provedores de IA e não altera eventos reais.
O uso de demos é controlado por SEED_DEMO_DATA, desativado em produção.
"""
import os
from datetime import datetime, timedelta, timezone
from math import sin
from sqlalchemy import select

from app import config
from app.auth import hash_password, hash_device_key
from app.database import SessionLocal
from app.models import User, Station, Reading, SecurityEvent, AuditFinding, IotDevice
from app.taint import audit_flow


SOC_SCENARIOS = (
    ("login", "high", "blocked", "[DEMO-SOC] Sequência hipotética de logins recusados no painel administrativo"),
    ("iot_auth", "medium", "blocked", "[DEMO-SOC] Chave não autorizada simulada para estação IoT"),
    ("taint", "high", "blocked", "[DEMO-SOC] Redação de credencial em log fictício (bloqueio preventivo)"),
)

# Apenas valores artificiais; os textos originais NÃO são persistidos no banco.
PII_SCENARIOS = (
    ("CPF: 000.000.000-00", "formulario", "log_bruto"),
    ("CID-10: J45; diagnóstico: registro fictício", "formulario", "resposta_publica"),
    ("senha: EXEMPLO_NAO_REAL_123", "iot", "servico_externo"),
)


def demo_seed_enabled() -> bool:
    environment = os.getenv("APP_ENV", "development").strip().lower()
    if environment in {"production", "prod"}:
        return False  # proibido inserir incidentes didáticos em produção
    value = os.getenv("SEED_DEMO_DATA", "false").strip().lower()
    if value not in {"true", "false", "1", "0", "yes", "no", "on", "off"}:
        raise RuntimeError("SEED_DEMO_DATA deve ser true ou false")
    return value in {"true", "1", "yes", "on"}


def ensure_soc_scenarios(db) -> int:
    """Cria os três casos de SOC do curso sem duplicar ou modificar a triagem."""
    added = 0
    for category, severity, outcome, summary in SOC_SCENARIOS:
        present = db.scalar(select(SecurityEvent.id).where(
            SecurityEvent.is_demo.is_(True), SecurityEvent.summary == summary).limit(1))
        if present is None:
            db.add(SecurityEvent(category=category, severity=severity, outcome=outcome,
                                 summary=summary, is_demo=True))
            added += 1
    db.flush()
    return added


def seed_demo(db) -> dict:
    """Não regrava leituras que já existem, nem altera dispositivos reais."""
    counters = {"stations": 0, "readings": 0, "events": 0, "findings": 0}
    stations = (
        ("centro-demo", "Centro — área exposta (SIMULAÇÃO)", "Hipótese: pouca sombra", config.SENSOR_A_KEY),
        ("verde-demo", "Área arborizada (SIMULAÇÃO)", "Hipótese: vegetação urbana", config.SENSOR_B_KEY),
    )
    for code, name, setting, key in stations:
        station = db.scalar(select(Station).where(Station.code == code))
        if station is None:
            db.add(Station(code=code, name=name, setting=setting, simulated=True,
                           api_key_hash=hash_device_key(key)))
            counters["stations"] += 1
        # Não fazemos rotação silenciosa de chaves existentes no restart.
    db.flush()
    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    for code, base_hum, offset in (("centro-demo", 57.0, 0.0), ("verde-demo", 64.0, 1.8)):
        station = db.scalar(select(Station).where(Station.code == code))
        if not station or not station.simulated:
            continue
        if db.scalar(select(Reading.id).where(Reading.station_id == station.id).limit(1)) is not None:
            continue
        for i in range(24):
            dt = end - timedelta(hours=23-i)
            demo_temp = 28.4 + 4.5 * sin(i * 0.32) + i * 0.035 - offset
            db.add(Reading(station_id=station.id, temperature_c=round(demo_temp, 1),
                           humidity_pct=base_hum, measured_at=dt, is_simulated=True))
            counters["readings"] += 1

    # Compatibilidade com os dados antigos (preserva a apresentação existente).
    legacy_events = (
        ("iot_auth", "medium", "blocked", "[DEMO] Chave IoT inválida — evento fictício"),
        ("login", "low", "failed", "[DEMO] Tentativa de login inválida — evento fictício"),
        ("taint", "high", "blocked", "[DEMO] Fluxo de senha para log bruto bloqueado — exemplo"),
    )
    for category, severity, outcome, summary in legacy_events:
        if db.scalar(select(SecurityEvent.id).where(SecurityEvent.is_demo.is_(True),
                      SecurityEvent.summary == summary).limit(1)) is None:
            db.add(SecurityEvent(category=category, severity=severity, outcome=outcome,
                                 summary=summary, is_demo=True))
            counters["events"] += 1
    counters["events"] += ensure_soc_scenarios(db)

    # A prova da triagem PII/taint é criada pelo próprio módulo do sistema.
    for sample, source, sink in PII_SCENARIOS:
        result = audit_flow(sample, source, sink)
        for kind in result["pii_types"]:
            category = "PII/taint:" + kind
            found = db.scalar(select(AuditFinding.id).where(
                AuditFinding.is_demo.is_(True), AuditFinding.category == category,
                AuditFinding.source == source, AuditFinding.sink == sink).limit(1))
            if found is None:
                db.add(AuditFinding(category=category, severity=result["severity"],
                    source=source, sink=sink, field=kind, action=result["action"],
                    evidence_redacted="[AMOSTRA_FICTICIA_REDACTED]",
                    remediation=result["remediation"], is_demo=True))
                counters["findings"] += 1
    db.flush()
    return counters


def ensure_iot(db) -> None:
    """Estações das duas zonas do ESP32 e o próprio dispositivo (sempre, inclusive em produção).
    Não grava leituras: elas só chegam pelo POST /api/v1/medicoes."""
    for code, name, setting, key in (
        ("centro-demo", "Centro — área exposta (SIMULAÇÃO)", "Hipótese: pouca sombra", config.SENSOR_A_KEY),
        ("verde-demo", "Área arborizada (SIMULAÇÃO)", "Hipótese: vegetação urbana", config.SENSOR_B_KEY),
    ):
        station = db.scalar(select(Station).where(Station.code == code))
        if station is None:
            db.add(Station(code=code, name=name, setting=setting, simulated=True, api_key_hash=hash_device_key(key)))
        elif station.api_key_hash != hash_device_key(key):
            # A chave mudou no .env: a estação passa a aceitar só a chave nova.
            station.api_key_hash = hash_device_key(key)
            print(f"Chave da estação atualizada a partir do .env: {code}")
    device = db.scalar(select(IotDevice).where(IotDevice.device_id == config.ESP32_DEVICE_ID))
    if device is None:
        db.add(IotDevice(device_id=config.ESP32_DEVICE_ID,
                         name="ESP32 Wokwi — Calçadão x zona arborizada (SIMULADOR)",
                         token_hash=hash_device_key(config.ESP32_DEVICE_TOKEN)))
        print(f"Dispositivo IoT cadastrado: {config.ESP32_DEVICE_ID}")
    elif device.token_hash != hash_device_key(config.ESP32_DEVICE_TOKEN):
        # Token trocado no .env: o ESP32 precisa usar o mesmo valor no sketch.ino.
        device.token_hash = hash_device_key(config.ESP32_DEVICE_TOKEN)
        print(f"Token do dispositivo IoT atualizado a partir do .env: {config.ESP32_DEVICE_ID}")
    db.flush()


def main():
    config.require_secrets()
    with SessionLocal() as db:
        with db.begin():
            user = db.scalar(select(User).where(User.email == config.ADMIN_EMAIL))
            if user is None:
                db.add(User(email=config.ADMIN_EMAIL, password_hash=hash_password(config.ADMIN_PASSWORD), role="admin"))
                print("Administrador inicial cadastrado usando credenciais do .env")
            ensure_iot(db)
            if demo_seed_enabled():
                counts = seed_demo(db)
                print("Dados sintéticos habilitados — novos registros:", counts)
            else:
                print("Seed demonstrativo desativado. Nenhum caso fictício criado.")
    print("Bootstrap idempotente concluído; sem sobrescrever eventos/leituras reais.")


if __name__ == "__main__":
    main()
