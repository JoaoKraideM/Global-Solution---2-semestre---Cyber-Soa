"""Contrato do redesenho 2026.3 (painel público + central de segurança com Apache ECharts).

Os testes verificam integrações e garantias, não pixels: cada elemento usado pelo JavaScript
existe no HTML, os gráficos vêm de uma cópia local do ECharts, a CSP continua rígida e a
origem dos dados (simulado, ERA5, hipotético) aparece para o usuário.
"""
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / 'static'
PUBLIC = (STATIC / 'index.html').read_text(encoding='utf-8')
ADMIN = (STATIC / 'admin.html').read_text(encoding='utf-8')
DASH = (STATIC / 'dashboard.js').read_text(encoding='utf-8')
ADMIN_JS = (STATIC / 'admin.js').read_text(encoding='utf-8')
ADMIN_CHARTS = (STATIC / 'admin-charts.js').read_text(encoding='utf-8')
BASE_CSS = (STATIC / 'sv-base.css').read_text(encoding='utf-8')
VERSION = '20261118.3'


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.hrefs, self.scripts, self.inline_scripts, self.style_attrs, self.labels = [], [], [], 0, 0, []
        self._in_script = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'):
            self.ids.append(a['id'])
        if tag == 'a' and a.get('href'):
            self.hrefs.append(a['href'])
        if 'style' in a:
            self.style_attrs += 1
        if tag == 'script':
            if a.get('src'):
                self.scripts.append(a['src'])
            else:
                self._in_script = True
        if tag == 'label' and a.get('for'):
            self.labels.append(a['for'])

    def handle_data(self, data):
        if self._in_script and data.strip():
            self.inline_scripts += 1

    def handle_endtag(self, tag):
        if tag == 'script':
            self._in_script = False


def parse(html):
    page = Page()
    page.feed(html)
    return page


def js_ids(source):
    return set(re.findall(r"\$\('([a-z0-9-]+)'\)", source)) | set(re.findall(r"getElementById\('([a-z0-9-]+)'\)", source))


def test_ids_are_unique_and_every_id_used_by_the_scripts_exists():
    for html, scripts in ((PUBLIC, [DASH]), (ADMIN, [ADMIN_JS, ADMIN_CHARTS])):
        page = parse(html)
        assert len(page.ids) == len(set(page.ids))
        missing = set().union(*(js_ids(s) for s in scripts)) - set(page.ids)
        assert not missing, f'IDs usados no JS e ausentes no HTML: {sorted(missing)}'
        assert set(page.labels) <= set(page.ids)


def test_internal_navigation_points_to_existing_sections():
    page = parse(PUBLIC)
    anchors = [h[1:] for h in page.hrefs if h.startswith('#') and len(h) > 1]
    assert anchors and set(anchors) <= set(page.ids)
    for section in ('inicio', 'esp32', 'mapa-calor', 'historico', 'fontes'):
        assert section in page.ids


def test_echarts_is_vendored_locally_and_loaded_before_the_charts():
    lib = STATIC / 'vendor' / 'echarts.min.js'
    assert lib.is_file() and lib.stat().st_size > 500_000
    assert (STATIC / 'vendor' / 'ECHARTS-LICENSE.txt').is_file()
    for html, own in ((PUBLIC, '/static/dashboard.js'), (ADMIN, '/static/admin-charts.js')):
        scripts = parse(html).scripts
        lib_pos = next(i for i, s in enumerate(scripts) if s.startswith('/static/vendor/echarts.min.js'))
        own_pos = next(i for i, s in enumerate(scripts) if s.startswith(own))
        assert lib_pos < own_pos
        assert not any(s.startswith('http') for s in scripts), 'nenhum script de CDN'


def test_no_inline_scripts_or_style_attributes_so_the_csp_stays_strict(client):
    for html in (PUBLIC, ADMIN):
        page = parse(html)
        assert page.inline_scripts == 0 and page.style_attrs == 0
    csp = client.get('/').headers['content-security-policy']
    assert "script-src 'self'" in csp and "style-src 'self'" in csp and 'unsafe-inline' not in csp
    # Tooltips do ECharts usam classes, não style="" (bloqueado pela CSP).
    assert 'style=' not in DASH and 'style=' not in ADMIN_CHARTS
    assert '.sv-tip' in BASE_CSS


def test_pages_and_assets_are_served_with_versions(client):
    for route, bundle in (('/', 'public-bundle.css'), ('/admin', 'admin-bundle.css')):
        html = client.get(route).text
        assert f'/static/{bundle}?v={VERSION}' in html
    for path in ('/static/dashboard.js', '/static/admin-charts.js', '/static/admin.js', '/static/navigation.js',
                 '/static/vendor/echarts.min.js', '/static/public-bundle.css', '/static/admin-bundle.css'):
        assert client.get(path).status_code == 200


def test_public_dashboard_uses_real_endpoints_with_labeled_fallbacks():
    for endpoint in ('/api/v1/summary', '/api/v1/stations/', '/api/v1/medicoes?limit=', '/api/v1/weather/osasco',
                     '/api/v1/weather/history?', '/api/v1/weather/places?search=', '/api/v1/heatmap/demo'):
        assert endpoint in DASH
    for fallback in ('/api/v1/demo/summary', '/api/v1/demo/weather', '/api/v1/demo/history?', '/api/v1/demo/places?search='):
        assert fallback in DASH
    for chart in ('chart-compare', 'chart-gauge', 'chart-island', 'chart-heatmap', 'chart-history'):
        assert f'id="{chart}"' in PUBLIC and f"'{chart}'" in DASH


def test_risk_thresholds_match_the_esp32_firmware():
    # Mesmas faixas NOAA do sketch.ino: 27 / 32 / 41 °C e ilha de calor a partir de 3 °C.
    assert "hi >= 41 ? 'perigo' : hi >= 32 ? 'alerta' : hi >= 27 ? 'atencao' : 'normal'" in DASH
    assert 'yAxis: 3' in DASH and 'delta >= 3' in DASH
    for text in ('abaixo de 27 °C', '27 a 31,9 °C', '32 a 40,9 °C', '41 °C ou mais'):
        assert text in PUBLIC


def test_history_respects_era5_delay_and_csv_is_protected():
    assert 'end.getDate() - 8' in DASH  # a API exige data final de pelo menos 7 dias atrás
    assert "/^[=+\\-@]/.test(t)" in DASH  # neutraliza fórmulas (CSV injection)
    assert 'SERIE FICTICIA' in DASH


def test_admin_keeps_every_operational_area_and_adds_charts():
    page = parse(ADMIN)
    for name in ('login-form', 'admin-section', 'pane-overview', 'pane-alerts', 'pane-events', 'pane-devices', 'pane-lab',
                 'soc-alert-list', 'soc-dossier', 'didactic-risk', 'chart-risk', 'chart-events', 'chart-findings'):
        assert name in page.ids
    assert ADMIN.count('role="tab"') == 5 and ADMIN.count('role="tabpanel"') == 5
    assert "dispatchEvent(new CustomEvent('sombraviva:admin-overview'" in ADMIN_JS
    assert "'sombraviva:admin-overview'" in ADMIN_CHARTS
    code = re.sub(r'/\*.*?\*/', '', ADMIN_CHARTS, flags=re.S)  # ignora o comentário de cabeçalho
    for forbidden in ('localStorage', 'sessionStorage', 'Authorization', 'fetch('):
        assert forbidden not in code  # os gráficos só reaproveitam dados já carregados


def test_accessibility_basics():
    for html in (PUBLIC, ADMIN):
        assert 'class="skip-link" href="#conteudo"' in html and 'id="conteudo"' in html
        assert html.count('role="img"') >= 3  # cada gráfico tem descrição textual
    assert ':focus-visible' in BASE_CSS and 'prefers-reduced-motion' in BASE_CSS
    assert 'min-height: 44px' in BASE_CSS  # alvos de toque confortáveis
