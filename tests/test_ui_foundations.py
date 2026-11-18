"""Verificações da estrutura HTML e dos estilos da interface."""
from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'static/index.html').read_text(encoding='utf-8')
JS = (ROOT / 'static/app.js').read_text(encoding='utf-8')
CSS = (ROOT / 'static/styles.css').read_text(encoding='utf-8')
ATLAS_CSS = (ROOT / 'static/atlas.css').read_text(encoding='utf-8')
ADMIN_HTML = (ROOT / 'static/admin.html').read_text(encoding='utf-8')
ADMIN_JS = (ROOT / 'static/admin.js').read_text(encoding='utf-8')

class IdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
    def handle_starttag(self, tag, attrs):
        for key,value in attrs:
            if key == 'id': self.ids.append(value)

def test_required_dom_elements_exist():
    parser = IdParser()
    parser.feed(HTML)
    assert len(parser.ids) == len(set(parser.ids)), 'IDs duplicados no frontend'
    used = set(re.findall(r"\$\('([^']+)'\)", JS))
    missing = used - set(parser.ids)
    assert not missing, f'IDs usados em app.js não existem: {missing}'

def test_essential_public_and_admin_sections():
    for element_id in ('inicio','medicoes','historico','impacto','seguranca', 'history-city-search', 'compare-city-search', 'history-start','history-end','history-chart','history-download','history-insight','sensor-empty','weather-retry','history-retry'):
        assert f'id="{element_id}"' in HTML
    for element_id in ('login-form','audit-button','admin-section','logout','remediation-button'):
        assert f'id="{element_id}"' in ADMIN_HTML
    assert 'id="login-form"' not in HTML

def test_accessibility_and_mobile_layout():
    assert 'class="skip-link"' in HTML
    assert 'aria-live="polite"' in HTML
    assert '@media(max-width:660px)' in CSS
    assert '@media(prefers-reduced-motion:reduce)' in CSS
    assert ':focus-visible' in CSS

def test_asset_versions_match():
    assert 'public-bundle.css?v=20261118.1' in HTML
    bundle = (ROOT/'static/public-bundle.css').read_text(encoding='utf-8')
    assert bundle.index('=== styles.css ===') < bundle.index('=== atlas.css ===')
    assert 'app.js?v=20261117.4' in HTML
    assert '=== atlas.css ===' in bundle
    assert 'navigation.js?v=20261117.1' in HTML
    assert 'admin.js?v=20261117.7' in ADMIN_HTML


def test_atlas_identity_and_source_attribution():
    assert 'id="menu-toggle"' in HTML
    assert 'visaooeste.com.br' in HTML and 'ae a' not in HTML
    assert 'Letícia Juliana Pazian' in HTML and 'Marina Vasarini Lopes' in HTML
    assert 'Parque_Ecol' in HTML
    assert 'agenciamural.org.br/calcadao' in HTML
    assert 'history-insight' in JS
    assert '.nav-open .sidebar nav' in ATLAS_CSS
    assert '.history-insight' in ATLAS_CSS
