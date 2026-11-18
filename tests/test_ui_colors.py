"""Contrato visual do Atlas Claro: legibilidade, origem de dados e proteção de APIs."""
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = (ROOT / 'static' / 'index.html').read_text(encoding='utf-8')
ADMIN = (ROOT / 'static' / 'admin.html').read_text(encoding='utf-8')
THEME = (ROOT / 'static' / 'atlas-claro.css').read_text(encoding='utf-8')
CHART = (ROOT / 'static' / 'app.js').read_text(encoding='utf-8')


def luminance(hexcolor):
    values = [int(hexcolor[i:i+2], 16) / 255 for i in (1, 3, 5)]
    channels = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055)**2.4 for v in values]
    return .2126 * channels[0] + .7152 * channels[1] + .0722 * channels[2]


def ratio(a, b):
    u, v = sorted((luminance(a), luminance(b)))
    return (v + .05) / (u + .05)


def test_atlas_claro_available_on_public_and_admin():
    client = TestClient(app)
    for route in ('/', '/admin'):
        html = client.get(route).text
        css = 'admin-bundle.css' if route == '/admin' else 'public-bundle.css'
        version = '20261117.3' if route == '/admin' else '20261118.1'
        assert f'/static/{css}?v={version}' in html
        bundle = client.get('/static/' + ('admin-bundle.css' if route == '/admin' else 'public-bundle.css'))
        assert '=== atlas-claro.css ===' in bundle.text
        assert '<meta name="color-scheme" content="light"' in html
    response = client.get('/static/atlas-claro.css')
    assert response.status_code == 200
    assert 'background:#FFFFFF' in response.text


def test_theme_contrast_for_operational_copy_and_action():
    for foreground, background in (
        ('#132D29', '#FFFFFF'),
        ('#526A61', '#FFFFFF'),
        ('#62766E', '#FFFFFF'),
        ('#225847', '#FFFFFF'),
        ('#BA543C', '#FFFFFF'),
        ('#28718A', '#FFFFFF'),
        ('#FFFFFF', '#225847'),
    ):
        assert ratio(foreground, background) >= 4.5, (foreground, background)


def test_frontend_retains_data_provenance_and_chart_controls():
    assert 'cenários sintéticos' in PUBLIC.lower()
    assert 'SIMULAÇÃO ATIVA' in PUBLIC
    assert 'role="status"' in PUBLIC
    assert 'history-city-search' in PUBLIC
    assert 'history-download' in PUBLIC
    assert 'history-city-charts' in PUBLIC
    assert "#BA543C" in CHART and "#28718A" in CHART


def test_security_ui_remains_separate_from_climate_public_page():
    assert 'href="/admin"' in PUBLIC
    assert 'id="admin-section"' in ADMIN
    assert 'id="login-form"' in ADMIN
    assert 'id="soc-alert-list"' in ADMIN
    assert 'id="soc-dossier"' in ADMIN
    assert 'id="audit-sink"' in ADMIN
    assert 'role="tablist"' in ADMIN


def test_key_focus_and_mobile_states():
    assert ':focus-visible' in THEME
    assert '@media(max-width:700px)' in THEME
    assert 'prefers-reduced-motion' in THEME
    assert 'body.admin-body' in THEME
