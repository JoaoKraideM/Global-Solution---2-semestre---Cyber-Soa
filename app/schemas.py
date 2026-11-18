from pydantic import BaseModel, Field
from typing import Literal

class LoginIn(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=1, max_length=300)

class SensorReadingIn(BaseModel):
    temperature_c: float = Field(ge=-50, le=65)
    humidity_pct: float = Field(ge=0, le=100)

class AuditIn(BaseModel):
    sample_text: str = Field(min_length=1, max_length=3000)
    source: Literal["formulario", "iot", "api_externa"] = "formulario"
    sink: Literal["log_bruto", "resposta_publica", "servico_externo", "log_redigido", "banco_parametrizado"] = "log_bruto"


class EventTriageIn(BaseModel):
    status: Literal["new", "investigating", "resolved"]
    note: str = Field(default="", max_length=300)


# ---------------------------------------------------------------------------
# Telemetria IoT (ESP32 no Wokwi) — contrato idêntico ao JSON do sketch.ino
# ---------------------------------------------------------------------------
from datetime import datetime
from enum import Enum
from pydantic import ConfigDict


class Zona(str, Enum):
    arborizada = "arborizada"
    sem_vegetacao = "sem_vegetacao"


class NivelRisco(str, Enum):
    normal = "normal"
    atencao = "atencao"
    alerta = "alerta"
    perigo = "perigo"


class MedicaoIn(BaseModel):
    """Medição enviada pelo ESP32 a cada 30 s (uma por zona)."""
    device_id: str = Field(max_length=64, examples=["esp32-osasco-calcadao-01"])
    zona: Zona
    temperatura: float = Field(ge=-40, le=80, description="Temperatura do DHT22, em °C")
    umidade: float = Field(ge=0, le=100, description="Umidade relativa, em %")
    indice_calor: float = Field(ge=-40, le=90, description="Índice de calor (NOAA), em °C")
    luminosidade: float = Field(ge=0, le=200000, description="Luminosidade estimada pelo LDR, em lux")
    nivel_risco: NivelRisco
    delta_ilha_calor: float | None = Field(None, ge=-30, le=30, description="Calçadão menos zona arborizada, em °C")
    temperatura_oficial: float | None = Field(None, ge=-40, le=80, description="Temperatura da Open-Meteo para Osasco, em °C")
    timestamp: datetime | None = Field(None, description="ISO 8601; se ausente, vale a hora do servidor")

    model_config = ConfigDict(json_schema_extra={"example": {
        "device_id": "esp32-osasco-calcadao-01", "zona": "sem_vegetacao", "temperatura": 34.6,
        "umidade": 48.0, "indice_calor": 36.9, "luminosidade": 52000, "nivel_risco": "alerta",
        "delta_ilha_calor": 4.1, "temperatura_oficial": 31.2, "timestamp": "2026-11-17T14:30:00-03:00"}})


class MedicaoOut(BaseModel):
    id: int
    device_id: str | None
    estacao: str
    zona: Zona | None
    temperatura: float
    umidade: float
    indice_calor: float | None
    luminosidade: float | None
    nivel_risco: NivelRisco | None
    delta_ilha_calor: float | None
    temperatura_oficial: float | None
    medido_em: datetime
    origem: str
    simulado: bool


class ResumoZona(BaseModel):
    zona: Zona
    estacao: str
    total_medicoes: int
    ultima: MedicaoOut | None


class ResumoIlhaCalor(BaseModel):
    zonas: list[ResumoZona]
    delta_ilha_calor_c: float | None = Field(description="Última temperatura do Calçadão menos a da zona arborizada")
    ilha_de_calor: bool = Field(description="Verdadeiro quando o delta é de 3 °C ou mais")
    nivel_risco_atual: NivelRisco | None
    aviso: str
