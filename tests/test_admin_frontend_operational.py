"""Regressão visual/estrutura: administrador age sobre eventos sem mapa climático."""
from pathlib import Path
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'static/admin.html').read_text(encoding='utf-8')
JS=(ROOT/'static/admin.js').read_text(encoding='utf-8')
CSS=(ROOT/'static/admin-ops.css').read_text(encoding='utf-8')

class ExtractIds(HTMLParser):
    def __init__(self):super().__init__();self.ids=[]
    def handle_starttag(self,tag,attrs):
        self.ids.extend(v for k,v in attrs if k=='id')


def test_admin_has_four_operational_areas_and_no_heatmap():
    ids=ExtractIds();ids.feed(HTML)
    assert len(ids.ids)==len(set(ids.ids))
    for name in ('pane-overview','pane-events','pane-devices','pane-lab','open-alerts',
                 'attention-list','event-list','device-list','finding-list','didactic-risk'):
        assert name in ids.ids
    assert 'id="admin-heatmap-canvas"' not in HTML
    assert '/#mapa-calor' in HTML


def test_admin_has_real_filters_triage_and_demo_provenance():
    for marker in ('/api/v1/admin/operations','/api/v1/admin/events','/api/v1/admin/findings',
                   'triage','Ver histórico','include-demo','risk_citizen_demo','EXEMPLO FICTÍCIO'):
        assert marker in JS or marker in HTML
    assert '/static/admin-bundle.css?v=20261117.2' in HTML
    assert (ROOT/'static/admin-bundle.css').read_text(encoding='utf-8').index('=== admin-ops.css ===') < (ROOT/'static/admin-bundle.css').read_text(encoding='utf-8').index('=== admin-editorial.css ===')
    assert '@media(max-width:750px)' in CSS
    assert '.ops-tabs{display:grid' in CSS
    assert 'aria-live="polite"' in HTML
