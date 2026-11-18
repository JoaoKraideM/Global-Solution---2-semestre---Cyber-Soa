"""Contrato ESP32 (Wokwi) -> API: POST /api/v1/medicoes com Bearer + X-Device-Id."""
import os

DEVICE = "esp32-osasco-calcadao-01"


def payload(zona="sem_vegetacao", temp=34.6, **extra):
    body = {"device_id": DEVICE, "zona": zona, "temperatura": temp, "umidade": 48.0,
            "indice_calor": 36.9, "luminosidade": 52000, "nivel_risco": "alerta",
            "delta_ilha_calor": 4.1, "temperatura_oficial": 31.2, "timestamp": "2026-11-17T14:30:00-03:00"}
    body.update(extra)
    return body


def headers(token=None, device=DEVICE):
    return {"Authorization": f"Bearer {token or os.environ['SENSOR_A_KEY']}", "X-Device-Id": device}


def test_esp32_cria_medicao(client):
    r = client.post("/api/v1/medicoes", json=payload(), headers=headers())
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["estacao"] == "centro-demo" and body["zona"] == "sem_vegetacao"
    assert body["nivel_risco"] == "alerta" and body["origem"] == "esp32-wokwi" and body["simulado"] is True


def test_medicao_aparece_na_estacao_do_portal(client):
    client.post("/api/v1/medicoes", json=payload("arborizada", 30.1), headers=headers())
    readings = client.get("/api/v1/stations/verde-demo/readings").json()
    assert readings[-1]["temperature_c"] == 30.1


def test_token_invalido_retorna_401_e_audita(client, token):
    r = client.post("/api/v1/medicoes", json=payload(), headers=headers(token="token-falso-qualquer"))
    assert r.status_code == 401
    events = client.get("/api/v1/admin/events", headers={"Authorization": f"Bearer {token}"}).json()
    texto = str(events)
    assert "token de dispositivo inválido" in texto and "token-falso-qualquer" not in texto


def test_sem_token_retorna_401(client):
    assert client.post("/api/v1/medicoes", json=payload()).status_code == 401


def test_device_id_divergente_retorna_403(client):
    r = client.post("/api/v1/medicoes", json=payload(device_id="esp32-intruso"), headers=headers())
    assert r.status_code == 403
    r = client.post("/api/v1/medicoes", json=payload(), headers=headers(device="esp32-intruso"))
    assert r.status_code == 403


def test_validacao_de_faixa(client):
    r = client.post("/api/v1/medicoes", json=payload(temp=120), headers=headers())
    assert r.status_code == 422


def test_listagem_e_resumo_ilha_de_calor(client):
    client.post("/api/v1/medicoes", json=payload("arborizada", 30.0, nivel_risco="atencao"), headers=headers())
    client.post("/api/v1/medicoes", json=payload("sem_vegetacao", 34.5), headers=headers())
    lista = client.get("/api/v1/medicoes?zona=arborizada").json()
    assert len(lista) == 1 and lista[0]["temperatura"] == 30.0
    resumo = client.get("/api/v1/medicoes/resumo").json()
    assert resumo["delta_ilha_calor_c"] == 4.5
    assert resumo["ilha_de_calor"] is True
    assert resumo["nivel_risco_atual"] == "alerta"


def test_swagger_documenta_contrato_esp32(client):
    spec = client.get("/openapi.json").json()
    assert "/api/v1/medicoes" in spec["paths"]
    assert "MedicaoIn" in spec["components"]["schemas"] and "MedicaoOut" in spec["components"]["schemas"]


def test_health_raiz_para_monitor_da_vm(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["banco"] == "ok"
