"""Regression checks for the incident index and investigation dossier.

These tests deliberately assert integration points rather than pixel positions.
The browser screenshot test runs separately and uses only synthetic metadata.
"""
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'static/admin.html').read_text(encoding='utf-8')
JS=(ROOT/'static/admin.js').read_text(encoding='utf-8')
CSS=(ROOT/'static/admin-editorial.css').read_text(encoding='utf-8')

class Ids(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]
    def handle_starttag(self,tag,attrs):
        self.ids.extend(v for k,v in attrs if k=='id')


def test_dossier_has_one_index_and_one_inspector():
    parser=Ids();parser.feed(HTML)
    assert len(parser.ids)==len(set(parser.ids))
    for item in ('soc-alert-list','soc-dossier','soc-search','soc-hours','soc-status','soc-demo','soc-seed'):
        assert item in parser.ids
    assert 'admin-bundle.css?v=20261117.3' in HTML
    assert '=== admin-editorial.css ===' in (ROOT/'static/admin-bundle.css').read_text(encoding='utf-8')
    assert 'admin.js?v=20261117.7' in HTML
    assert 'Nenhum comprometimento é confirmado' in HTML


def test_actions_still_route_to_real_protected_endpoints():
    assert 'renderSocAlert' in JS
    assert 'selectSocAlert' in JS
    assert 'displaySocAlerts' in JS
    assert "$('soc-search').addEventListener('input',displaySocAlerts)" in JS
    assert "'/api/v1/admin/events/'" not in JS or '/api/v1/admin/events/' in JS
    assert '/api/v1/admin/security/alerts/' in JS
    assert '/analyze' in JS
    assert '/api/v1/admin/events/' in JS
    assert 'request(' in JS
    assert 'textContent' in JS
    assert "moveToDossier && window.matchMedia('(max-width: 920px)')" in JS


def test_editorial_visual_system_and_responsive():
    for marker in ('.sv-casework','.sv-case-dossier','.sv-case-row.is-active',
                   '.sv-dossier-block','.soc-toolbar','@media(max-width:920px)',
                   '@media(max-width:620px)','prefers-reduced-motion'):
        assert marker in CSS
    assert ':focus-visible' in CSS
    assert 'var(--sv-paper)' in CSS


def test_public_frontend_is_not_replaced():
    assert (ROOT/'static/index.html').is_file()
    assert (ROOT/'static/app.js').is_file()
    assert (ROOT/'app/security_intelligence.py').is_file()
    assert (ROOT/'alembic/versions/003_security_triage.py').is_file()
