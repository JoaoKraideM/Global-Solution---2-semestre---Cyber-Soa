"""Fonte das leituras sombra x sol mostradas no painel público, escolhida na central.

- "estacoes": fonte original do projeto. Leituras enviadas pelas estações cadastradas
  (POST /api/v1/stations/{code}/readings, seed e scripts/simulate_iot.py).
- "esp32": telemetria do ESP32 no Wokwi (POST /api/v1/medicoes), gravada com source="esp32-wokwi".
As duas fontes ficam guardadas no banco; a escolha só muda o que o painel exibe.
"""
from datetime import datetime, timezone
import os

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from app.models import AppSetting, Reading

SETTING_KEY = "panel_data_source"
ESP32_SOURCE = "esp32-wokwi"
SOURCES = {
    "estacoes": {
        "label": "Estações cadastradas",
        "description": "Fonte original do projeto: leituras enviadas pelas estações da zona arborizada e do Calçadão (simulador e seed).",
    },
    "esp32": {
        "label": "ESP32 (Wokwi)",
        "description": "Telemetria do circuito ESP32 no Wokwi, com DHT22 na sombra e no sol, enviada para POST /api/v1/medicoes.",
    },
}


def default_source() -> str:
    value = os.getenv("PANEL_DATA_SOURCE", "estacoes").strip().lower()
    return value if value in SOURCES else "estacoes"


def reading_filter(source: str) -> ColumnElement[bool] | None:
    """Condição SQL que separa as leituras de cada fonte; None = todas."""
    if source == "esp32":
        return Reading.source == ESP32_SOURCE
    if source == "estacoes":
        return Reading.source != ESP32_SOURCE
    return None


def current(db: Session) -> dict:
    row = db.get(AppSetting, SETTING_KEY)
    source = row.value if row is not None and row.value in SOURCES else default_source()
    updated = row.updated_at if row is not None else None
    if updated is not None and updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return {"source": source, **SOURCES[source],
            "updated_at": updated.isoformat() if updated else None,
            "updated_by": row.updated_by if row is not None else None,
            "options": [{"source": key, **meta} for key, meta in SOURCES.items()]}


def save(db: Session, source: str, who: str) -> dict:
    row = db.get(AppSetting, SETTING_KEY)
    now = datetime.now(timezone.utc)
    if row is None:
        db.add(AppSetting(key=SETTING_KEY, value=source, updated_at=now, updated_by=who))
    else:
        row.value, row.updated_at, row.updated_by = source, now, who
    db.commit()
    return current(db)


def stats(db: Session) -> dict:
    """Quantidade e horário da última leitura de cada fonte, para a decisão na central."""
    out = {}
    for key in SOURCES:
        cond = reading_filter(key)
        total = db.scalar(select(func.count(Reading.id)).where(cond)) or 0
        last = db.scalar(select(func.max(Reading.measured_at)).where(cond))
        if last is not None and last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        out[key] = {"readings": total, "last_reading_at": last.isoformat() if last else None}
    return out
