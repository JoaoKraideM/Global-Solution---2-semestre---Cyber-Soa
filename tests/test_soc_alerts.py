"""SOC: sinais observados, cenários controlados, IA opt-in e privacidade."""
import json
from datetime import datetime, timezone
from app import config
from app.models import SecurityEvent
from app.security_intelligence import local_report, RULES
from app.main import AI_SOC_LIMITS


def headers(token):
    return {"Authorization": "Bearer " + token}


def test_alert_routes_protected_and_input_validation(client):
    assert client.get('/api/v1/admin/security/alerts').status_code == 401
    assert client.post('/api/v1/admin/security/demo-scenario').status_code == 401
    assert client.post('/api/v1/admin/security/alerts/1/analyze').status_code == 401


def test_alerts_from_real_signals_and_not_success(client, token):
    auth = headers(token)
    result=client.get('/api/v1/admin/security/alerts',headers=auth)
    assert result.status_code==200
    assert result.json()['alerts']==[]  # login bem-sucedido não cria alerta
    client.post('/api/v1/stations/centro-demo/readings',json={'temperature_c':32,'humidity_pct':61})
    a=client.get('/api/v1/admin/security/alerts',headers=auth).json()
    assert a['total']==1
    item=a['alerts'][0]
    assert item['affected_asset']=='Ingestão IoT e identidade dos sensores'
    assert item['confirmed_compromise'] is False
    assert 'não confirmado' in item['affected_status'].lower() or 'sem comprovação' in item['affected_status'].lower()
    assert item['observed']=='Controle bloqueou a operação'
    assert len(item['next_steps']) >= 2
    client.patch(f'/api/v1/admin/events/{item["id"]}/triage',headers=auth,
                 json={'status':'resolved','note':'Bloqueio inspecionado e credencial rejeitada'})
    assert client.get('/api/v1/admin/security/alerts',headers=auth).json()['total']==0
    assert client.get('/api/v1/admin/security/alerts?status=resolved',headers=auth).json()['total']==1
    assert client.get('/api/v1/admin/security/alerts?hours=200',headers=auth).status_code==422


def test_demo_scenario_explicit_idempotent_and_isolated(client, token):
    auth=headers(token)
    one=client.post('/api/v1/admin/security/demo-scenario',headers=auth)
    assert one.status_code==200 and one.json()['created']==3
    two=client.post('/api/v1/admin/security/demo-scenario',headers=auth)
    assert two.status_code==200 and two.json()['created']==0
    assert client.get('/api/v1/admin/security/alerts',headers=auth).json()['total']==0
    demonstration=client.get('/api/v1/admin/security/alerts?include_demo=true',headers=auth).json()
    assert demonstration['total']==3
    assert all(x['is_demo'] and x['confirmed_compromise'] is False for x in demonstration['alerts'])
    assert demonstration['alerts'][0]['severity']=='high'


def test_local_analysis_no_secret_never_claims_damage(client, token, monkeypatch):
    monkeypatch.setattr(config, 'OPENAI_API_KEY', '')
    auth=headers(token)
    client.post('/api/v1/admin/security/demo-scenario',headers=auth)
    item=client.get('/api/v1/admin/security/alerts?include_demo=true',headers=auth).json()['alerts'][0]
    r=client.post(f'/api/v1/admin/security/alerts/{item["id"]}/analyze',headers=auth)
    assert r.status_code==200,r.text
    data=r.json()
    assert data['mode']=='regras_locais' and data['ai_used'] is False
    assert data['verdict']=='Comprometimento não confirmado'
    assert 'danificad' not in data['verdict']
    assert client.post('/api/v1/admin/security/alerts/9999/analyze',headers=auth).status_code==404
    assert client.post('/api/v1/admin/security/alerts/1/analyze',headers=auth).status_code==404  # evento de login bem sucedido


def test_ai_only_sends_safe_metadata(client, token, monkeypatch):
    from app import security_intelligence
    monkeypatch.setattr(config, 'OPENAI_API_KEY', 'dummy-key-never-really-used')
    AI_SOC_LIMITS.clear()
    sent=[]
    class FakeResponse:
        def raise_for_status(self): return None
        def json(self):
            report={'summary':'Sinal preventivo observado.', 'possible_impact':'Possível risco se o controle falhar.',
                    'next_steps':['Rever credenciais','Inspecionar logs'],
                    'evidence_gaps':['Sem logs de host']}
            return {'output':[{'content':[{'type':'output_text','text':json.dumps(report)}]}]}
    class FakeClient:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *exc): pass
        async def post(self,url,**kwargs):
            sent.append({'url':url,**kwargs});return FakeResponse()
    monkeypatch.setattr(security_intelligence.httpx, 'AsyncClient', FakeClient)
    auth=headers(token)
    client.post('/api/v1/admin/security/demo-scenario',headers=auth)
    item=client.get('/api/v1/admin/security/alerts?include_demo=true',headers=auth).json()['alerts'][0]
    response=client.post(f'/api/v1/admin/security/alerts/{item["id"]}/analyze',headers=auth)
    assert response.status_code==200 and response.json()['ai_used'] is True
    assert response.json()['verdict']=='Comprometimento não confirmado'
    assert len(sent)==1 and sent[0]['json']['store'] is False
    assert 'summary' not in json.loads(sent[0]['json']['input'])
    assert sent[0]['json']['text']['format']['type']=='json_schema'
    assert sent[0]['url']=='https://api.openai.com/v1/responses'
    for _ in range(5):
        assert client.post(f'/api/v1/admin/security/alerts/{item["id"]}/analyze',headers=auth).status_code==200
    assert client.post(f'/api/v1/admin/security/alerts/{item["id"]}/analyze',headers=auth).status_code==429
    AI_SOC_LIMITS.clear()


def test_soc_frontend_markup_and_safety():
    from pathlib import Path
    html=Path('static/admin.html').read_text()
    js=Path('static/admin.js').read_text()
    for marker in ('id="pane-alerts"','id="soc-alert-list"','id="soc-seed"','id="soc-demo"',
                   'Comprometimento', 'id="pane-events"'):
        assert marker.lower() in html.lower()
    for marker in ('/api/v1/admin/security/alerts','/analyze','/demo-scenario',
                   'createElement','textContent','renderSocAlert'):
        assert marker in js


def test_direct_event_detail_is_protected_and_preserves_id(client,token):
    auth=headers(token)
    client.post('/api/v1/stations/centro-demo/readings',json={'temperature_c':30,'humidity_pct':60})
    event_id=client.get('/api/v1/admin/security/alerts',headers=auth).json()['alerts'][0]['id']
    assert client.get(f'/api/v1/admin/events/{event_id}').status_code==401
    found=client.get(f'/api/v1/admin/events/{event_id}',headers=auth)
    assert found.status_code==200 and found.json()['id']==event_id
    assert client.get('/api/v1/admin/events/999999',headers=auth).status_code==404


def test_informational_login_is_not_actionable_in_frontend():
    from pathlib import Path
    js=Path('static/admin.js').read_text()
    assert "item.outcome==='failed'||item.outcome==='blocked'" in js
    assert 'Registro informativo: autenticação autorizada' in js
    assert 'switchTab(\'alerts\', false);await refreshAll();' in js
