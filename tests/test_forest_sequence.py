"""Regressões de apresentação do SombraViva: visual verde e leitura sequencial."""
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
HTML=BeautifulSoup((ROOT/'static/index.html').read_text(encoding='utf8'),'html.parser')
CSS=(ROOT/'static/forest-sequence.css').read_text(encoding='utf8')


def test_hero_has_editorial_title_left_and_full_width_photo_below():
    assert HTML.select_one('#inicio.arch-home .arch-intro-grid')
    assert HTML.select_one('#inicio.arch-home .arch-photographic-cover .hero-documentary-photo')
    assert '#inicio.arch-home{\n  display:block;' in CSS
    assert 'body:not(.admin-body) #inicio .arch-photographic-cover' in CSS
    assert 'grid-column:2;grid-row:1 / span 2' in CSS
    assert HTML.select_one('#inicio .arch-intro-aside > span').get_text(strip=True) == '01 — OSASCO, SÃO PAULO'
    assert '01 — OSASCO' not in HTML.select_one('#inicio .arch-intro-index').get_text()
    assert '@media(max-width:740px)' in CSS


def test_source_order_and_alternation():
    assert HTML.select_one('#projeto-referencia .arch-case-feature .arch-competition-side')
    assert HTML.select_one('#projeto-referencia .arch-case-feature .arch-competition-figure')
    assert HTML.select_one('#impacto .territory-visual')
    assert HTML.select_one('#impacto .impact-intro')
    assert '.arch-case-feature .arch-competition-side{\n  order:1' in CSS
    assert '#impacto .territory-visual{grid-column:1;grid-row:1' in CSS


def test_theme_only_targets_public_and_keeps_source_disclosures():
    assert 'body:not(.admin-body)' in CSS
    assert '#0D261A' in CSS and '#FFFFFF' in CSS
    assert 'public-bundle.css?v=20261118.1&amp;layout=forest-sage' in str(HTML)
    assert HTML.select_one('img.documentary-media[data-credit-id]')
    assert HTML.select_one('#history-form')
    assert HTML.select_one('#temperature-chart')
    assert HTML.select_one('#territory-map-frame')
