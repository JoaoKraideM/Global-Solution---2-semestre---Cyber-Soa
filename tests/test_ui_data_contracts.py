"""Contratos entre a API e as telas: cada campo que dashboard.js e admin.js leem existe na
resposta, inclusive nos modos de demonstração, e a origem dos dados é sempre declarada.

Substitui test_ui_climate_provenance, test_history_frontend, test_city_comparison_charts,
test_territory_data_connections e test_ui_home_and_assets do frontend anterior.
"""
import json
import os
import shutil
import subprocess
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DASH = (ROOT / 'static' / 'dashboard.js').read_text(encoding='utf-8')
PUBLIC = (ROOT / 'static' / 'index.html').read_text(encoding='utf-8')


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def test_public_page_is_served_with_a_strict_csp(client):
    page = client.get('/')
    assert page.status_code == 200 and 'text/html' in page.headers['content-type']
    csp = page.headers['content-security-policy']
    assert "frame-src https://www.openstreetmap.org" in csp and "frame-ancestors 'none'" in csp


def test_demo_summary_has_both_stations_read_by_the_dashboard(client):
    data = client.get('/api/v1/demo/summary').json()
    for code in ('verde-demo', 'centro-demo'):
        readings = data['readings'][code]
        assert readings
        assert {'temperature_c', 'humidity_pct', 'measured_at'} <= set(readings[-1])


def test_station_readings_have_the_fields_of_the_comparison_chart(client):
    summary = client.get('/api/v1/summary').json()
    assert {'stations', 'readings_total'} <= set(summary)
    assert {s['code'] for s in summary['stations']} >= {'verde-demo', 'centro-demo'}
    client.post('/api/v1/stations/centro-demo/readings', json={'temperature_c': 33.1, 'humidity_pct': 50},
                headers={'X-Device-Key': os.environ['SENSOR_A_KEY']})
    rows = client.get('/api/v1/stations/centro-demo/readings?limit=24').json()
    assert rows and {'temperature_c', 'humidity_pct', 'measured_at', 'simulated'} <= set(rows[-1])


def test_demo_weather_has_the_fields_of_the_weather_card(client):
    data = client.get('/api/v1/demo/weather').json()
    assert {'temperature_c', 'apparent_temperature_c', 'humidity_pct'} <= set(data)
    assert 'Exemplo fictício' in DASH


@pytest.mark.parametrize('period', ['tarde', 'noite'])
def test_heatmap_periods_return_a_grid_for_both_buttons(client, period):
    data = client.get(f'/api/v1/heatmap/demo?period={period}').json()
    points = data['grid']['points']
    assert points and {'latitude', 'longitude', 'temperature_c'} <= set(points[0])
    assert data.get('notice')


def test_heatmap_rejects_periods_without_a_button(client):
    assert client.get('/api/v1/heatmap/demo?period=madrugada').status_code == 422


def test_demo_city_search_returns_what_the_result_buttons_show(client):
    data = client.get('/api/v1/demo/places?search=Bar').json()
    assert data['locations']
    assert {'name', 'latitude', 'longitude'} <= set(data['locations'][0])


def test_demo_history_has_the_series_and_summary_of_the_history_chart(client):
    end = date.today() - timedelta(days=8)
    start = end - timedelta(days=29)
    data = client.get(f'/api/v1/demo/history?latitude=-23.53&longitude=-46.79&start_date={start}&end_date={end}').json()
    assert len(data['days']) == 30
    assert {'date', 'temperature_mean_c', 'temperature_min_c', 'temperature_max_c'} <= set(data['days'][0])
    assert {'mean_temperature_c', 'highest_temperature_c', 'lowest_temperature_c', 'days_mean_above_30c'} <= set(data['summary'])


def test_every_source_shown_to_the_user_is_labelled():
    for label in ('reanálise ERA5', 'hipotética', 'Open-Meteo', 'NOAA', 'EPA', 'simuladas'):
        assert label in PUBLIC
    for label in ('Valores fictícios', 'série fictícia', 'SERIE FICTICIA', 'Busca offline'):
        assert label in DASH


def test_esp32_listing_has_the_fields_of_the_table(client):
    assert client.get('/api/v1/medicoes?limit=60').status_code == 200
    for field in ('medido_em', 'zona', 'temperatura', 'umidade', 'indice_calor', 'luminosidade', 'nivel_risco'):
        assert f'r.{field}' in DASH or f'rows[0].{field}' in DASH


def test_audit_response_feeds_the_result_card_for_unsafe_and_control_sinks(client, token):
    for sink, blocked in (('log_bruto', True), ('banco_parametrizado', False)):
        result = client.post('/api/v1/admin/audit', headers=auth(token),
                             json={'sample_text': 'CPF: 000.000.000-00; email: exemplo@example.invalid', 'source': 'formulario', 'sink': sink}).json()
        assert result['blocked'] is blocked and result['sink'] == sink
        assert {'pii_types', 'severity', 'redacted_preview', 'remediation'} <= set(result)
        assert '000.000.000-00' not in result['redacted_preview'] and 'exemplo@example.invalid' not in result['redacted_preview']


def test_operations_feed_the_station_cards_and_counters(client, token):
    data = client.get('/api/v1/admin/operations', headers=auth(token)).json()
    assert {'failed_logins_24h', 'rejected_devices_24h', 'stale_real_stations', 'demo_events', 'demo_findings', 'stations', 'simulated_stations'} <= set(data['counts'])
    station = data['stations'][0]
    assert {'name', 'code', 'setting', 'simulated', 'status', 'latest', 'last_seen_at'} <= set(station)


def test_alerts_have_every_field_shown_in_the_dossier(client, token):
    assert client.post('/api/v1/admin/security/demo-scenario', headers=auth(token)).status_code in (200, 201)
    alerts = client.get('/api/v1/admin/security/alerts?hours=168&status=all&include_demo=true', headers=auth(token)).json()['alerts']
    assert alerts
    needed = {'id', 'title', 'severity', 'status', 'category', 'created_at', 'observed', 'summary', 'hypothetical_impact',
              'affected_asset', 'affected_status', 'next_steps', 'evidence_gaps', 'related_event_count', 'is_demo'}
    assert needed <= set(alerts[0])


def heat_index_js(t, rh):
    source = DASH.split('function heatIndex(t, rh) {')[1].split('\nconst riskOf')[0]
    script = ('const num = v => Number.isFinite(Number(v)) ? Number(v) : null;\n'
              'function heatIndex(t, rh) {' + source + f'\nconsole.log(JSON.stringify(heatIndex({t}, {rh})));')
    return json.loads(subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True).stdout)


def heat_index_py(t, rh):
    T = t * 9 / 5 + 32
    hi = 0.5 * (T + 61 + (T - 68) * 1.2 + rh * 0.094)
    if (hi + T) / 2 >= 80:
        hi = (-42.379 + 2.04901523 * T + 10.14333127 * rh - .22475541 * T * rh - .00683783 * T * T
              - .05481717 * rh * rh + .00122874 * T * T * rh + .00085282 * T * rh * rh - .00000199 * T * T * rh * rh)
    return (hi - 32) * 5 / 9


@pytest.mark.skipif(shutil.which('node') is None, reason='Node.js não instalado')
def test_dashboard_heat_index_matches_the_noaa_formula():
    for t, rh in ((25.0, 60), (33.9, 48), (36.0, 40)):
        assert abs(heat_index_js(t, rh) - heat_index_py(t, rh)) < 0.05
