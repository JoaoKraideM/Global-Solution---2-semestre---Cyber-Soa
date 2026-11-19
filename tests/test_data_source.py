"""Fonte das leituras do painel público: estações cadastradas (original) ou ESP32 (Wokwi),
trocada pela central de segurança e lida pelo dashboard."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / 'static'
ESP = {'Authorization': f"Bearer {os.environ['SENSOR_A_KEY']}", 'X-Device-Id': 'esp32-osasco-calcadao-01'}


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def esp_reading(client, zona, temperatura):
    body = {'device_id': 'esp32-osasco-calcadao-01', 'zona': zona, 'temperatura': temperatura, 'umidade': 55,
            'indice_calor': temperatura + 1, 'luminosidade': 900, 'nivel_risco': 'alerta'}
    response = client.post('/api/v1/medicoes', json=body, headers=ESP)
    assert response.status_code == 201, response.text


def station_reading(client, code, key, temperatura):
    response = client.post(f'/api/v1/stations/{code}/readings', json={'temperature_c': temperatura, 'humidity_pct': 60},
                           headers={'X-Device-Key': os.environ[key]})
    assert response.status_code == 201, response.text


def test_default_source_is_the_original_stations(client):
    data = client.get('/api/v1/data-source').json()
    assert data['source'] == 'estacoes' and data['label'] == 'Estações cadastradas'
    assert [o['source'] for o in data['options']] == ['estacoes', 'esp32']
    assert data['updated_at'] is None


def test_only_admins_can_read_stats_or_change_the_source(client):
    assert client.get('/api/v1/admin/data-source').status_code == 401
    assert client.put('/api/v1/admin/data-source', json={'source': 'esp32'}).status_code == 401
    assert client.get('/api/v1/data-source').json()['source'] == 'estacoes'


def test_admin_switches_the_source_and_it_persists(client, token):
    changed = client.put('/api/v1/admin/data-source', json={'source': 'esp32'}, headers=auth(token))
    assert changed.status_code == 200
    assert changed.json()['source'] == 'esp32' and changed.json()['updated_by'] == 'admin@sombraviva.local'
    public = client.get('/api/v1/data-source').json()
    assert public['source'] == 'esp32' and public['label'] == 'ESP32 (Wokwi)' and public['updated_at']
    back = client.put('/api/v1/admin/data-source', json={'source': 'estacoes'}, headers=auth(token)).json()
    assert back['source'] == 'estacoes'


def test_unknown_sources_are_rejected(client, token):
    assert client.put('/api/v1/admin/data-source', json={'source': 'openweather'}, headers=auth(token)).status_code == 422
    assert client.get('/api/v1/stations/centro-demo/readings?source=planilha').status_code == 422


def test_readings_are_separated_by_source(client):
    station_reading(client, 'centro-demo', 'SENSOR_A_KEY', 30.0)
    esp_reading(client, 'sem_vegetacao', 34.5)
    esp_only = client.get('/api/v1/stations/centro-demo/readings?source=esp32').json()
    stations_only = client.get('/api/v1/stations/centro-demo/readings?source=estacoes').json()
    everything = client.get('/api/v1/stations/centro-demo/readings').json()
    assert [r['temperature_c'] for r in esp_only] == [34.5]
    assert [r['temperature_c'] for r in stations_only] == [30.0]
    assert len(everything) == 2


def test_admin_stats_count_each_source(client, token):
    station_reading(client, 'verde-demo', 'SENSOR_B_KEY', 25.0)
    esp_reading(client, 'arborizada', 26.0)
    esp_reading(client, 'sem_vegetacao', 33.0)
    stats = client.get('/api/v1/admin/data-source', headers=auth(token)).json()['stats']
    assert stats['estacoes']['readings'] == 1 and stats['esp32']['readings'] == 2
    assert stats['esp32']['last_reading_at']


def test_dashboard_reads_the_chosen_source():
    dash = (STATIC / 'dashboard.js').read_text(encoding='utf-8')
    assert "get('/api/v1/data-source')" in dash
    assert 'readings?limit=24&source=${panelSource.source}' in dash
    assert "panelSource.source === 'esp32' && rows.length > 0" in dash  # gauge e ilha seguem a fonte
    assert "$('live-source')" in dash and 'id="live-source"' in (STATIC / 'index.html').read_text(encoding='utf-8')


def test_central_offers_both_sources_and_saves_with_put():
    html = (STATIC / 'admin.html').read_text(encoding='utf-8')
    js = (STATIC / 'admin.js').read_text(encoding='utf-8')
    assert 'value="estacoes"' in html and 'value="esp32"' in html and 'id="source-save"' in html
    assert "request('/api/v1/admin/data-source',{method:'PUT'" in js
    assert 'void loadDataSource();' in js
