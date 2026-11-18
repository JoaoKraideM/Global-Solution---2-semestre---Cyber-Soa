"""Cross-layer regressions without internet, Docker or deployed sensors."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_connection_controls_and_semantic_disclaimer(client):
    page = client.get('/')
    assert page.status_code == 200
    html = page.text
    for key in (
        'atlas-connection', 'atlas-selected-place', 'atlas-sensor-value',
        'atlas-era5-value', 'atlas-open-history', 'atlas-sensor-context',
        'map-availability', 'map-retry', 'atlas-orientation-map',
    ):
        assert f'id="{key}"' in html or (key == 'atlas-connection' and f'class="{key}"' in html) or (key == 'atlas-orientation-map' and 'class="atlas-orientation-map"' in html)
    assert 'não há medição comprovada neste endereço' in (ROOT/'static/territory-map.js').read_text('utf-8').lower() or 'não há medição comprovada' in html.lower()
    assert 'não demonstra' in html
    assert 'estação exibida é apenas um cenário' in html.lower()
    assert client.get('/static/assets/osasco-orientation.svg').status_code == 200


def test_iot_and_era5_events_update_atlas_without_new_backend_schema(client):
    js = client.get('/static/app.js').text
    territory = client.get('/static/territory-map.js').text
    assert "publishAtlas('stations'" in js
    assert "publishAtlas('history'" in js
    assert "new CustomEvent('sombraviva:select-place'" in js
    assert "window.addEventListener('sombraviva:choose-osasco'" in js
    assert "window.addEventListener('sombraviva:history'" in territory
    assert "window.addEventListener('sombraviva:stations'" in territory
    assert "stationCode: 'centro-demo'" in territory
    assert "stationCode: 'verde-demo'" in territory
    assert 'st.simulated' in territory
    assert 'isOsasco(historyData.main)' in territory
    assert 'historySeriesMatchesPeriod' in js
    assert 'sombravivaAtlasLatest' in js
    assert 'sombravivaAtlasLatest' in territory


def test_map_external_link_and_failure_recovery(client):
    page=client.get('/')
    assert "frame-src https://www.openstreetmap.org" in page.headers['content-security-policy']
    js=client.get('/static/territory-map.js').text
    assert 'window.setTimeout' in js
    assert "frame.addEventListener('error'" in js
    assert "retry?.addEventListener('click', showMap)" in js
    assert 'www.openstreetmap.org/export/embed.html' in js
