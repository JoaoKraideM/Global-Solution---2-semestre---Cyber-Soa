"""Direção visual: projeto urbano e fotografia documental, sem alterar a API."""
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DOC = BeautifulSoup((ROOT/'static/index.html').read_text(encoding='utf-8'), 'html.parser')


def test_portfolio_sections_preserve_operational_modules():
    assert DOC.select_one('#inicio .arch-intro-grid')
    assert DOC.select_one('#projeto-referencia .arch-competition-figure')
    assert DOC.select_one('.arch-reality-grid .arch-reality-before')
    assert DOC.select_one('.arch-reality-grid .arch-reality-after')
    for ident in ('history-form','temperature-chart','history-download','heatmap-canvas',
                  'territory-map-frame','temp-a','temp-b','readings-count'):
        assert DOC.select_one('#'+ident), ident
    links = {a.get('href') for a in DOC.select('#site-navigation a')}
    assert '#projeto-referencia' in links and '#medicoes' in links and '#historico' in links


def test_photos_are_not_claimed_as_thermal_evidence():
    text = DOC.get_text(' ', strip=True)
    for phrase in ('Letícia Juliana Pazian','Marina Vasarini Lopes',
                   'não um levantamento térmico','propostas do concurso',
                   'não constituem um experimento térmico controlado'):
        assert phrase.lower() in text.lower()
    for img in DOC.select('img.documentary-media'):
        assert img.get('alt') and img.get('data-credit-id')
        assert img.get('src').startswith('https://')
        assert img.find_parent('figure').select_one('figcaption')


def test_styling_responsive_and_public_only(client):
    css=client.get('/static/public-bundle.css').text
    assert '=== architectural-direction.css ===' in css
    assert css.index('=== editorial-natureza.css ===') < css.index('=== architectural-direction.css ===')
    assert '@media(max-width:700px)' in css and ':focus-visible' in css
    assert '=== architectural-direction.css ===' not in client.get('/static/admin-bundle.css').text


def test_external_images_allowlisted_under_csp(client):
    response=client.get('/')
    csp=response.headers['content-security-policy']
    assert "script-src 'self'" in csp
    for domain in ('https://www.aeaosasco.org.br','https://www.visaooeste.com.br',
                   'https://www.oanhanguera.com.br','https://agenciamural.org.br',
                   'https://upload.wikimedia.org'):
        assert domain in csp
    assert "connect-src 'self'" in csp
