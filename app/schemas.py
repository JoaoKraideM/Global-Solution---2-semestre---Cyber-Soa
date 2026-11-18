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
