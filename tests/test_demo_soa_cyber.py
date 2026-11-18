"""Novos cenários FIAP SOA + Cyber, usando SQLite de memória sem afetar o MySQL."""
from app.demo import snapshot
from app.heatmap import build_heatmap
from app.pii import classify
from app.taint import audit_flow
from sqlalchemy import inspect
from app.models import SecurityEvent, AuditFinding


def test_demo_summary_does_not_pretend_to_be_a_real_observation(client):
    before = client.get('/api/v1/summary').json()['readings_total']
    response = client.get('/api/v1/demo/summary')
    assert response.status_code == 200
    data=response.json()
    assert data['demo'] is True and data['simulated'] is True
    assert data['readings_total'] == 0
    assert len(data['readings']['centro-demo'])==24
    assert all(point['simulated'] for point in data['readings']['verde-demo'])
    assert client.get('/api/v1/summary').json()['readings_total'] == before


def test_heatmap_is_an_explicitly_synthetic_georeferenced_grid(client):
    for period in ('tarde', 'noite'):
        r = client.get('/api/v1/heatmap/demo', params={'period':period})
        assert r.status_code==200
        result = r.json()
        assert result['simulated'] and result['source'] == 'synthetic_demo'
        assert 'NÃO representa calor real' in result['notice']
        grid=result['grid']
        assert len(grid['points']) == grid['rows']*grid['columns']
        assert all(result['bounds']['south'] <= p['latitude'] <= result['bounds']['north'] for p in grid['points'])
        assert all(result['bounds']['west'] <= p['longitude'] <= result['bounds']['east'] for p in grid['points'])
    assert client.get('/api/v1/heatmap/demo?period=amanha').status_code==422


def test_privacy_rules_cover_health_data_and_sensitive_sink():
    sensitive=classify('CID-10: J45; diagnóstico: exemplo de teste')
    assert 'saude' in sensitive['pii_types']
    assert 'J45' not in sensitive['redacted']
    flow=audit_flow('CID-10: J45', 'formulario','log_bruto')
    assert flow['blocked'] and flow['severity'] == 'high'
    allowed=audit_flow('CID-10: J45','formulario','log_redigido')
    assert allowed['blocked'] is False


def test_demo_provenance_schema_and_credential_protection(client,token):
    assert 'is_demo' in SecurityEvent.__table__.columns
    assert 'is_demo' in AuditFinding.__table__.columns
    assert client.get('/api/v1/admin/overview').status_code==401
    overview=client.get('/api/v1/admin/overview',headers={'Authorization':'Bearer '+token}).json()
    assert 'demo_events' in overview['counts']
    assert 'demo_findings' in overview['counts']
    assert all('is_demo' in e for e in overview['events'])


def test_demo_weather_and_historical_series_never_masquerade_as_open_meteo(client):
    r=client.get('/api/v1/demo/weather')
    assert r.status_code==200 and r.json()['simulated'] is True
    from datetime import date,timedelta
    end=date.today()-timedelta(days=12)
    start=end-timedelta(days=29)
    query={'latitude':-23.5329,'longitude':-46.7917,'start_date':start.isoformat(),'end_date':end.isoformat()}
    history=client.get('/api/v1/demo/history',params=query)
    assert history.status_code==200
    body=history.json()
    assert body['source']=='synthetic_demo' and body['simulated'] is True
    assert len(body['days'])==30 and body['days'][0]['date']==start.isoformat()
    assert body['days'][-1]['date']==end.isoformat()


def test_demo_offline_city_search(client):
    r=client.get('/api/v1/demo/places?search=Barueri')
    assert r.status_code==200 and r.json()['demo'] is True
    assert r.json()['locations'][0]['name']=='Barueri'
    r=client.get('/api/v1/demo/places?search=Franca')
    assert r.json()['locations'][0]['name']=='Franca'
