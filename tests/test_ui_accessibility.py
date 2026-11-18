"""Teste de contrato UI do redesenho integral; não depende de dados externos."""
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=(ROOT/'static/index.html').read_text(encoding='utf-8')
ADMIN=(ROOT/'static/admin.html').read_text(encoding='utf-8')
JS=(ROOT/'static/app.js').read_text(encoding='utf-8')
ADMIN_JS=(ROOT/'static/admin.js').read_text(encoding='utf-8')
CSS=(ROOT/'static/refinement.css').read_text(encoding='utf-8')

class Extract(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=[];self.labels=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get('id'): self.ids.append(a['id'])
        if tag=='label' and a.get('for'):self.labels.append(a['for'])

def test_public_paths_and_sources_cannot_be_confused():
    for fragment in ('class="reading-route"','class="provenance-line"','Clima regional',
                     'Cenários sintéticos','Simulação didática','href="#historico"','href="#medicoes"','href="#mapa"'):
        assert fragment in PUBLIC
    for element in ('sensor-empty','history-source-chip','history-demo-banner','history-demo-source-note','heatmap-status'):
        assert f'id="{element}"' in PUBLIC

def test_single_city_no_redundant_comparison_graph():
    assert 'id="history-comparison" class="history-comparison hidden"' in PUBLIC
    assert "$('history-comparison').classList.toggle('hidden',pairs.length !== 2)" in JS
    assert 'comparison-disclosure' in PUBLIC
    assert '<details class="history-summary-details">' in PUBLIC
    assert 'class="technical-help"' in PUBLIC

def test_admin_keyboard_navigation_and_tab_panels():
    assert 'role="tablist"' in ADMIN
    assert 'id="admin-section-select"' in ADMIN
    assert "$('admin-section-select')?.addEventListener('change'" in ADMIN_JS
    for name in ['overview','alerts','events','devices','lab']:
        assert f'id="tab-{name}"' in ADMIN
        assert f'id="pane-{name}"' in ADMIN
    assert "event.key==='Home'" in ADMIN_JS
    assert "button.setAttribute('aria-selected',String(active))" in ADMIN_JS
    assert 'Central de<br><em>investigação.</em>' in ADMIN

def test_unique_dom_ids_and_existing_api_controls():
    for page in [PUBLIC,ADMIN]:
        parser=Extract();parser.feed(page)
        assert len(parser.ids)==len(set(parser.ids))
    for id_ in ('login-form','soc-alert-list','soc-dossier','audit-button','admin-refresh','logout'):
        assert f'id="{id_}"' in ADMIN
    for id_ in ('history-form','history-download','temperature-chart','history-city-charts','territory-map-frame'):
        assert f'id="{id_}"' in PUBLIC

def test_responsive_reduced_motion_and_focus():
    assert '@media(max-width:700px)' in CSS
    assert '@media(prefers-reduced-motion:reduce)' in CSS
    assert ':focus-visible' in CSS
    assert 'max-width' in CSS

def test_css_served(client):
    for page in ('/','/admin'):
        r=client.get(page);assert r.status_code==200
        css = 'public-bundle.css' if page == '/' else 'admin-bundle.css'
        version = '20261118.1' if page == '/' else '20261117.3'
        assert f'/static/{css}?v={version}' in r.text
        assert '=== refinement.css ===' in client.get('/static/' + ('public-bundle.css' if page == '/' else 'admin-bundle.css')).text
    r=client.get('/static/refinement.css');assert r.status_code==200
