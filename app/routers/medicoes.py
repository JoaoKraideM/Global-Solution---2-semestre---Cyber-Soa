"""Endpoints REST da telemetria IoT (ESP32 + DHT22 + LDR no Wokwi)."""
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import MedicaoIn, MedicaoOut, ResumoIlhaCalor, Zona
from app.services import medicoes as service

router = APIRouter(prefix="/api/v1/medicoes", tags=["iot"])


def _bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, value = authorization.partition(" ")
    return value.strip() if scheme.lower() == "bearer" and value.strip() else None


@router.post("", response_model=MedicaoOut, status_code=status.HTTP_201_CREATED,
             summary="Recebe uma medição do ESP32",
             responses={401: {"description": "Token do dispositivo ausente ou inválido"},
                        403: {"description": "device_id não corresponde ao token"}})
def criar_medicao(medicao: MedicaoIn, db: Session = Depends(get_db),
                  authorization: str | None = Header(default=None, description="Bearer <token do dispositivo>"),
                  x_device_id: str | None = Header(default=None, description="Identificador do ESP32")):
    try:
        device = service.autenticar(db, _bearer(authorization))
    except service.DispositivoNaoAutorizado:
        service.registrar_evento(db, "medium", "blocked", "Medição IoT recusada: token de dispositivo inválido")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credencial de dispositivo inválida")
    try:
        reading = service.registrar_medicao(db, device, medicao, x_device_id)
    except service.DispositivoDivergente:
        service.registrar_evento(db, "high", "blocked", f"device_id divergente do token ({device.device_id})")
        raise HTTPException(status.HTTP_403_FORBIDDEN, "device_id não corresponde ao token")
    except LookupError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    return service.para_saida(reading, service.ZONA_PARA_ESTACAO[medicao.zona])


@router.get("", response_model=list[MedicaoOut], summary="Lista as últimas medições do ESP32")
def listar_medicoes(zona: Zona | None = Query(None), limit: int = Query(50, ge=1, le=500),
                    db: Session = Depends(get_db)):
    return service.listar(db, zona, limit)


@router.get("/resumo", response_model=ResumoIlhaCalor,
            summary="Resumo da ilha de calor: Calçadão x zona arborizada")
def resumo_ilha_calor(db: Session = Depends(get_db)):
    return service.resumo(db)
