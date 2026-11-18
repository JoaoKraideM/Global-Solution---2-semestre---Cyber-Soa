"""Fotos e perspectivas arquitetônicas identificadas com fonte rastreável."""
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


def test_photographic_sources_have_credentials_and_no_fake_substitutes(client):
    html = client.get('/').text
    doc = BeautifulSoup(html, 'html.parser')
    images = doc.select('img.documentary-media')
    assert len(images) >= 5
    assert doc.select_one('figure.sv-hero-unified img.hero-documentary-photo')
    for image in images:
        assert image.get('src', '').startswith('https://')
        assert image.get('alt')
        note = doc.select_one('#' + image['data-credit-id'])
        assert note and note.has_attr('hidden')
        assert image.find_parent('figure').select_one('figcaption')
    assert 'IMAGEM DE PROJETO, NÃO FOTO DA OBRA' in html
    assert 'Fotografia documental' in html
    assert 'paisagem-conceitual.webp' not in html
    assert 'verde-ilustrativo.webp' not in html
    assert 'cidade-conceitual.webp' not in html
    assert html.count('data-fallback=""') == len(images)
    assert '/static/media.js?v=20261119.1' in html
    js = client.get('/static/media.js').text
    assert "addEventListener('error'" in js
    assert 'image.hidden = true;' in js
    assert "classList.add('media-fallback-visible')" in js


def test_original_sources_are_accessible_as_links(client):
    doc = BeautifulSoup(client.get('/').text, 'html.parser')
    assert doc.select_one('a[href="https://www.aeaosasco.org.br/concurso-revitalizacao/"]')
    assert doc.select_one('a[href*="concurso_revitalizacao_osasco.pdf"]')
    assert doc.select_one('a[href*="visaooeste.com.br"]')
    assert doc.select_one('a[href*="agenciamural.org.br"]')
    assert doc.select_one('a[href*="commons.wikimedia.org"]')
    assert 'visao360.osasco.sp.gov.br' not in str(doc)
