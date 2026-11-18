"""Regressões da camada editorial, sem alterar as integrações SOA/Cybersecurity."""
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'static/index.html').read_text(encoding='utf-8')
CSS = (ROOT / 'static/editorial-natureza.css').read_text(encoding='utf-8')


class Ids(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
    def handle_starttag(self, name, attrs):
        attributes = dict(attrs)
        if attributes.get('id'):
            self.ids.append(attributes['id'])


def test_editorial_homepage_uses_real_existing_backend_controls(client):
    response = client.get('/')
    assert response.status_code == 200
    assert '/static/public-bundle.css?v=20261118.1' in response.text
    assert '=== editorial-natureza.css ===' in client.get('/static/public-bundle.css').text
    assert 'a cidade <span>precisa de</span>' in HTML
    assert 'href="#historico"' in HTML
    assert 'href="#impacto"' in HTML
    assert 'sv-editorial-statement' in HTML
    assert 'menos<br>verde.<br><em>mais calor?</em>' in HTML
    for item in ['history-form', 'history-city-search', 'history-city-charts',
                 'temperature-chart', 'heatmap-canvas', 'territory-map-frame',
                 'history-download']:
        assert f'id="{item}"' in HTML
    parser = Ids(); parser.feed(HTML)
    assert len(parser.ids) == len(set(parser.ids)), 'IDs duplicados no HTML'


def test_real_reference_photos_and_provenance_are_clear(client):
    html = client.get('/').text
    assert 'paisagem-conceitual.webp' not in html
    assert 'cidade-conceitual.webp' not in html
    assert 'verde-ilustrativo.webp' not in html
    assert 'Fotografia documental' in html
    assert 'IMAGEM DE PROJETO, NÃO FOTO DA OBRA' in html
    assert 'Letícia Juliana Pazian' in html
    assert 'Marina Vasarini Lopes' in html
    assert 'medições locais' in html
    assert 'hero-documentary-photo documentary-media' in html
    assert 'data-fallback=""' in html


def test_visual_layer_is_scoped_and_responsive(client):
    response = client.get('/static/editorial-natureza.css')
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/css')
    assert 'body:not(.admin-body)' in CSS
    assert '@media(max-width:750px)' in CSS
    assert '@media(prefers-reduced-motion:reduce)' in CSS
    assert ':focus-visible' in CSS
    assert '/static/editorial-natureza.css' not in (ROOT / 'static/admin.html').read_text(encoding='utf-8')


def test_auth_and_api_are_untouched(client):
    assert client.get('/api/v1/health').json()['status'] == 'ok'
    assert client.get('/api/v1/admin/events').status_code in (401, 403)
    assert client.get('/admin').status_code == 200
    assert 'id="soc-alert-list"' in client.get('/admin').text
