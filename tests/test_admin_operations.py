"""Testes de operação e triagem de eventos: separação produção/demonstração e proteção."""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool
from app.models import SecurityEvent, Station, Reading, AuditFinding, SecurityTriageAction
from app.database import get_db
from app.main import app


def test_admin_routes_require_token(client):
    assert client.get('/api/v1/admin/operations').status_code == 401
    assert client.get('/api/v1/admin/events').status_code == 401
    assert client.get('/api/v1/admin/findings').status_code == 401
    assert client.patch('/api/v1/admin/events/10/triage',json={'status':'resolved','note':'Validado no teste'}).status_code == 401


def test_dashboard_operational_counts_and_demo_filter(client,token):
    headers={'Authorization':f'Bearer {token}'}
    base=client.get('/api/v1/admin/operations',headers=headers)
    assert base.status_code == 200
    assert base.json()['counts']['simulated_stations'] == 2
    assert base.json()['counts']['stale_real_stations'] == 0
    assert all(s['status']=='demo' for s in base.json()['stations'])
    # A própria autenticação legítima gera um evento, mas não deve elevar a fila.
    assert base.json()['counts']['open_alerts'] == 0
    assert client.get('/api/v1/admin/events?category=login&include_demo=false',headers=headers).status_code==200
    # Tentativa de autenticação IoT inválida deve ser real, diferente do seed.
    response=client.post('/api/v1/stations/centro-demo/readings',json={'temperature_c':30,'humidity_pct':60})
    assert response.status_code==401
    counts=client.get('/api/v1/admin/operations',headers=headers).json()['counts']
    assert counts['rejected_devices_24h'] == 1
    assert counts['open_alerts'] == 1
    filtered=client.get('/api/v1/admin/events?category=iot_auth&severity=medium',headers=headers).json()
    assert filtered['total'] == 1 and filtered['events'][0]['is_demo'] is False
    assert filtered['events'][0]['triage_status']=='new'


def test_triage_requires_justification_and_maintains_history(client, token):
    headers={'Authorization':f'Bearer {token}'}
    client.post('/api/v1/stations/centro-demo/readings',json={'temperature_c':30,'humidity_pct':61})
    event=client.get('/api/v1/admin/events?category=iot_auth',headers=headers).json()['events'][0]
    event_id=event['id']
    url=f'/api/v1/admin/events/{event_id}/triage'
    assert client.patch(url,headers=headers,json={'status':'resolved','note':'curto'}).status_code==422
    assert client.patch(url,headers=headers,json={'status':'wrong','note':'Nope'}).status_code==422
    investigating=client.patch(url,headers=headers,json={'status':'investigating','note':'Verificando origem da tentativa'}).json()
    assert investigating['triage_status']=='investigating'
    resolved=client.patch(url,headers=headers,json={'status':'resolved','note':'Autenticação inválida examinada; bloqueio confirmado'}).json()
    assert resolved['triage_status']=='resolved'
    assert client.get('/api/v1/admin/operations',headers=headers).json()['counts']['open_alerts'] == 0
    history=client.get(f'/api/v1/admin/events/{event_id}/history',headers=headers).json()
    assert len(history)==2 and history[0]['next_status']=='resolved'
    assert history[1]['previous_status']=='new'
    assert client.get('/api/v1/admin/events?status=resolved',headers=headers).json()['total']==1
    # Não repetir a mesma transição.
    client.patch(url,headers=headers,json={'status':'resolved','note':'Autenticação inválida examinada; bloqueio confirmado'})
    assert len(client.get(f'/api/v1/admin/events/{event_id}/history',headers=headers).json())==2


def test_notes_are_redacted_before_storage(client, token):
    headers={'Authorization':f'Bearer {token}'}
    client.post('/api/v1/stations/centro-demo/readings',json={'temperature_c':29,'humidity_pct':61})
    event_id=client.get('/api/v1/admin/events?category=iot_auth',headers=headers).json()['events'][0]['id']
    note='Teste com CPF: 123.456.789-09; senha: topsecret123'
    r=client.patch(f'/api/v1/admin/events/{event_id}/triage',headers=headers,json={'status':'investigating','note':note})
    assert r.status_code==200
    assert '123.456.789-09' not in str(r.json()) and 'topsecret123' not in str(r.json())
    history=client.get(f'/api/v1/admin/events/{event_id}/history',headers=headers)
    assert '123.456.789-09' not in history.text and 'topsecret123' not in history.text


def test_filters_paginate_and_validate(client,token):
    headers={'Authorization':f'Bearer {token}'}
    for _ in range(3):client.post('/api/v1/stations/centro-demo/readings',json={'temperature_c':28,'humidity_pct':61})
    a=client.get('/api/v1/admin/events?category=iot_auth&offset=0&limit=2',headers=headers).json()
    assert a['total']==3 and len(a['events'])==2
    b=client.get('/api/v1/admin/events?category=iot_auth&offset=2&limit=2',headers=headers).json()
    assert len(b['events'])==1
    assert client.get('/api/v1/admin/events?limit=999',headers=headers).status_code==422
    assert client.get('/api/v1/admin/events?category=hack',headers=headers).status_code==422
    assert client.get('/api/v1/admin/events/99999/history',headers=headers).status_code==404
    assert client.patch('/api/v1/admin/events/99999/triage',headers=headers,json={'status':'resolved','note':'evento inexistente'}).status_code==404


def test_findings_separate_demo_and_real(client,token):
    headers={'Authorization':f'Bearer {token}'}
    r=client.get('/api/v1/admin/findings',headers=headers)
    assert r.status_code==200 and r.json()==[]
    assert client.post('/api/v1/admin/audit',json={'sample_text':'teste@example.invalid','sink':'log_bruto'},headers=headers).status_code==200
    rows=client.get('/api/v1/admin/findings',headers=headers).json()
    assert rows and all(not f['is_demo'] for f in rows)
    assert 'teste@example.invalid' not in str(rows)
