from datetime import date, timedelta
import os

def test_health_and_stations(client):
    assert client.get('/api/v1/health').json()['status']=='ok'
    response=client.get('/api/v1/stations')
    assert response.status_code==200
    assert len(response.json())==2
    assert all(s['simulated'] for s in response.json())

def test_device_auth_and_reading(client):
    url='/api/v1/stations/centro-demo/readings'
    payload={'temperature_c':32.1,'humidity_pct':55.0}
    no_key=client.post(url,json=payload)
    assert no_key.status_code==401
    bad_key=client.post(url,json=payload,headers={'X-Device-Key':'wrong'})
    assert bad_key.status_code==401
    good=client.post(url,json=payload,headers={'X-Device-Key':os.environ['SENSOR_A_KEY']})
    assert good.status_code==201
    assert good.json()['simulated'] is True
    readings=client.get(url).json()
    assert len(readings)==1 and readings[0]['temperature_c']==32.1

def test_reject_invalid_sensor_reading(client):
    r=client.post('/api/v1/stations/centro-demo/readings',json={'temperature_c':500,'humidity_pct':20},headers={'X-Device-Key':os.environ['SENSOR_A_KEY']})
    assert r.status_code==422

def test_admin_protection_and_login_events(client,token):
    assert client.get('/api/v1/admin/overview').status_code==401
    assert client.get('/api/v1/admin/overview',headers={'Authorization':'Bearer invalid'}).status_code==401
    r=client.get('/api/v1/admin/overview',headers={'Authorization':f'Bearer {token}'})
    assert r.status_code==200
    assert r.json()['counts']['events']>=1

def test_audit_redacts_sensitive_content(client,token):
    headers={'Authorization':f'Bearer {token}'}
    text='CPF: 000.000.000-00; email: exemplo@example.invalid; senha: palavra_fake'
    r=client.post('/api/v1/admin/audit',json={'sample_text':text,'sink':'log_bruto','source':'formulario'},headers=headers)
    assert r.status_code==200
    data=r.json()
    assert data['blocked'] is True
    assert set(data['pii_types']) >= {'cpf','email','senha'}
    assert '000.000.000-00' not in data['redacted_preview']
    overview=client.get('/api/v1/admin/overview',headers=headers).json()
    assert overview['counts']['findings'] >= 3
    assert 'palavra_fake' not in str(overview)
    assert '000.000.000-00' not in str(overview)

def test_taint_sanitized_sink_not_blocked(client,token):
    r=client.post('/api/v1/admin/audit',json={'sample_text':'teste@example.invalid','sink':'log_redigido','source':'formulario'},headers={'Authorization':f'Bearer {token}'})
    assert r.status_code==200
    assert r.json()['blocked'] is False

def test_remediation_without_llm_is_not_called_ai(client,token):
    headers={'Authorization':f'Bearer {token}'}
    client.post('/api/v1/admin/audit',json={'sample_text':'teste@example.invalid','sink':'resposta_publica'},headers=headers)
    r=client.post('/api/v1/admin/remediation',headers=headers)
    assert r.status_code==200
    assert r.json()['ai_used'] is False
    assert r.json()['mode']=='regras'


def test_historical_validation_without_external_call(client):
    r=client.get('/api/v1/weather/history/osasco', params={'start_date':'2025-05-30','end_date':'2025-01-01'})
    assert r.status_code==422
    r=client.get('/api/v1/weather/history/osasco', params={'start_date':(date.today()-timedelta(days=1)).isoformat(),'end_date':(date.today()-timedelta(days=1)).isoformat()})
    assert r.status_code==422


def test_database_health_check(client):
    response = client.get('/api/v1/health/db')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'
