"""Regressions for territory map and temperature interpretation (visual layer only)."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_territorial_atlas_is_not_presented_as_sensor_map(client):
    res=client.get('/')
    assert res.status_code==200
    html=res.text
    assert 'id="mapa"' in html
    assert 'id="territory-map-frame"' in html
    assert 'data-map-location="calcadao"' in html
    assert 'data-map-location="parque"' in html
    assert 'não medições nesses locais' in html
    assert '/static/territory-map.js?v=20261119.1' in html
    assert 'id="history-observations"' in html


def test_map_assets_and_csp(client):
    js=client.get('/static/territory-map.js').text
    assert 'www.openstreetmap.org/export/embed.html' in js
    assert 'new URLSearchParams' in js
    assert 'lat: -23.5333671' in js
    assert 'lat: -23.5163255' in js
    csp=client.get('/').headers.get('content-security-policy','')
    assert "frame-src https://www.openstreetmap.org" in csp


def test_daily_extremes_use_only_api_readings(client):
    script=client.get('/static/app.js').text
    assert 'renderHistoryObservations(pairs);' in script
    assert "Number.isFinite(row.temperature_max_c)" in script
    assert 'não define uma onda de calor' in script
    assert 'temperature_min_c' in script
