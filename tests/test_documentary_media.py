"""Regressions: documentary photos should never leave an empty, uncredited frame."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_photographic_sources_and_offline_fallback(client):
    html = client.get('/').text
    assert html.count('class="documentary-media"') == 1
    assert 'hero-documentary-photo documentary-media' in html
    assert 'sv-hero-unified' in html and 'id="hero-title"' in html
    assert '/static/assets/verde-ilustrativo.webp' in html
    assert 'não representa o parque' in html
    assert 'Ver fotografia documental de Osasco' in html
    for image in ['cidade-ilustrativa.webp', 'verde-ilustrativo.webp']:
        r = client.get(f'/static/assets/{image}')
        assert r.status_code == 200 and r.headers['content-type'].startswith('image/webp')
    assert html.count('data-fallback=') == 2
    assert '/static/media.js?v=20261119.1' in html
    for name in ['centro-cartografia-fallback.svg','parque-cartografia-fallback.svg']:
        response=client.get(f'/static/assets/{name}')
        assert response.status_code == 200
        assert b'<svg' in response.content
    js = client.get('/static/media.js').text
    assert "addEventListener('error'" in js
    assert 'image.src = fallback;' in js


def test_official_sources_do_not_point_to_broken_visao360(client):
    html=client.get('/').text
    assert 'visao360.osasco.sp.gov.br' not in html
    assert 'osasco.sp.gov.br/obras-de-cobertura-do-calcadao-seguem-em-ritmo-acelerado' in html
    assert 'ae a' not in html
    assert 'aeaosasco.org.br/concurso-revitalizacao' in html
    assert 'agenciamural.org.br/calcadao-de-osasco-perde' in html
