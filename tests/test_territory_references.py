"""Regressions for the SombraViva territorial editorial experience.

Uses only local files and API HTML responses; no MySQL or external weather service.
"""
from pathlib import Path
import re
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
CSS = (ROOT / 'static/identidade-territorial.css').read_text(encoding='utf-8')
PUBLIC = (ROOT / 'static/index.html').read_text(encoding='utf-8')
ADMIN = (ROOT / 'static/admin.html').read_text(encoding='utf-8')


def test_new_layer_is_last_for_both_surfaces(client):
    for endpoint in ['/', '/admin']:
        html = client.get(endpoint).text
        bundle_url = '/static/admin-bundle.css' if endpoint == '/admin' else '/static/public-bundle.css'
        assert bundle_url + '?v=20261117.2' in html
        css = client.get(bundle_url).text
        assert css.index('=== refinement.css ===') < css.index('=== identidade-territorial.css ===')
    response = client.get('/static/identidade-territorial.css')
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/css')


def test_sources_have_truthful_labels_and_case_notes():
    assert 'não é fotografia de Osasco' in PUBLIC
    assert 'não representa o parque' in PUBLIC
    assert 'DADOS 100% SINTÉTICOS' in PUBLIC
    assert 'Open-Meteo' in PUBLIC
    assert 'O QUE JÁ ESTÁ DOCUMENTADO' in PUBLIC
    assert 'O QUE AINDA PRECISA SER MEDIDO' in PUBLIC
    assert 'não possui uma série antes/depois' in PUBLIC
    assert 'agenciamural.org.br' in PUBLIC
    assert 'commons.wikimedia.org' in PUBLIC


def test_preserved_public_and_admin_ids():
    for element in ('temp-a','temp-b','temp-diff','readings-count','temperature-chart',
                    'history-city-search','history-comparison','history-city-charts',
                    'heatmap-canvas','territory-map-frame'):
        assert f'id="{element}"' in PUBLIC
    for element in ('login-form','admin-section','soc-dossier','soc-alert-list',
                    'audit-button','admin-refresh'):
        assert f'id="{element}"' in ADMIN


def test_responsive_modes_and_accessibility():
    for token in ('--sv-canvas','--sv-paper','--sv-lime','--sv-sensor',
                  '--sv-heat','--sv-climate'):
        assert token in CSS
    assert '@media(max-width:760px)' in CSS
    assert '@media(max-width:440px)' in CSS
    assert '@media(prefers-reduced-motion:reduce)' in CSS
    assert ':focus-visible' in CSS
    assert '.admin-body.admin-authenticated .admin-hero{display:none}' in CSS


def luminance(hex_value):
    values = [int(hex_value[i:i+2],16) / 255 for i in (1,3,5)]
    values = [v / 12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in values]
    return .2126*values[0]+.7152*values[1]+.0722*values[2]


def test_critical_text_paper_contrast():
    # WCAG contrast for principal foreground/background pairs; decoration excluded.
    pairs = [('#F4F1E7','#071A1C'),('#D1E2D9','#102E2D'),
             ('#102E2D','#F4F1E7'),('#96AEA3','#071A1C'),
             ('#D6FF4B','#071A1C')]
    for fg,bg in pairs:
        a,b=sorted([luminance(fg),luminance(bg)],reverse=True)
        assert (a+.05)/(b+.05) >= 4.5, (fg,bg)
