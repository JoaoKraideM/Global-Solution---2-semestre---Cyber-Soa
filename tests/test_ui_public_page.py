"""Painel público (static/index.html): estrutura, navegação, acessibilidade e ligação com o dashboard.js.

Substitui os testes do frontend antigo (atlas, sequência da floresta, navegação da home) pela
mesma cobertura aplicada ao redesenho: cada seção existe, cada número exibido tem um elemento
com id que o JavaScript preenche e cada imagem e link externo segue as regras de acessibilidade.
"""
import re
from html.parser import HTMLParser
from urllib.parse import urlparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / 'static'
HTML = (STATIC / 'index.html').read_text(encoding='utf-8')
DASH = (STATIC / 'dashboard.js').read_text(encoding='utf-8')


class Tree(HTMLParser):
    """Guarda cada tag de abertura com seus atributos, na ordem do documento."""

    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    handle_startendtag = handle_starttag

    def find(self, tag=None, **attrs):
        return [a for t, a in self.tags if (tag is None or t == tag) and all(a.get(k) == v for k, v in attrs.items())]

    def ids(self):
        return [a['id'] for _, a in self.tags if a.get('id')]


PAGE = Tree()
PAGE.feed(HTML)
IDS = PAGE.ids()


def section_order():
    wanted = ('inicio', 'problema', 'como', 'esp32', 'mapa-calor', 'historico')
    return [i for i in IDS if i in wanted]


def test_sections_follow_the_reading_order_of_the_design():
    assert section_order() == ['inicio', 'problema', 'como', 'esp32', 'mapa-calor', 'historico']


def test_every_section_is_labelled_by_an_existing_heading():
    sections = PAGE.find('section')
    assert len(sections) >= 7
    for attrs in sections:
        label = attrs.get('aria-labelledby')
        assert label, f'seção sem aria-labelledby: {attrs}'
        assert label in IDS


def test_page_has_a_single_h1_and_named_h2s():
    assert HTML.count('<h1') == 1
    assert len(re.findall(r'<h2[ >]', HTML)) >= 7


def test_document_metadata_for_portuguese_and_mobile():
    assert '<html lang="pt-BR">' in HTML
    assert 'name="viewport" content="width=device-width, initial-scale=1"' in HTML
    assert 'name="description"' in HTML and 'Osasco' in HTML
    assert 'name="theme-color" content="#0F3D3A"' in HTML


def test_header_and_footer_navigation_point_to_existing_sections():
    hrefs = [a['href'] for a in PAGE.find('a') if a.get('href', '').startswith('#')]
    assert len(hrefs) >= 12
    for href in hrefs:
        assert href[1:] in IDS, href


def test_header_links_to_the_security_center_and_swagger_is_in_the_footer():
    links = [a['href'] for a in PAGE.find('a')]
    assert '/admin' in links and '/docs' in links


def test_mobile_menu_button_controls_the_navigation():
    button = PAGE.find('button', id='menu-toggle')[0]
    assert button['aria-controls'] == 'site-navigation' and button['aria-expanded'] == 'false'
    assert 'site-navigation' in IDS


def test_live_strip_values_are_filled_by_the_dashboard():
    for element in ('live-shade', 'live-sun', 'live-delta', 'live-risk', 'live-updated'):
        assert element in IDS
        assert f"$('{element}')" in DASH


def test_headline_and_problem_numbers_come_from_the_readings():
    for element in ('hero-delta', 'hero-updated', 'prob-shade', 'prob-sun', 'prob-over', 'temp-delta', 'delta-verdict'):
        assert element in IDS and f"$('{element}')" in DASH
    # A contagem de leituras acima do limite usa o mesmo limiar de ilha de calor do firmware.
    assert 'temperature_c >= 3) over++' in DASH


def test_four_steps_explain_the_pipeline_with_described_illustrations():
    block = HTML.split('class="sv-steps"')[1].split('</ol>')[0]
    assert block.count('<li>') == 4
    assert block.count('role="img"') == 4 and block.count('aria-label="') == 4
    for step in ('Etapa 1', 'Etapa 2', 'Etapa 3', 'Etapa 4'):
        assert step in block


def test_how_to_read_ruler_is_updated_with_the_real_values():
    for element in ('howto-svg', 'howto-shade', 'howto-sun', 'howto-limit', 'howto-over', 'howto-under', 'howto-bracket', 'howto-verdict'):
        assert element in IDS
    assert 'function drawHowto(shade, sun)' in DASH
    assert 'drawHowto(ls?.temperature_c, lu?.temperature_c)' in DASH
    assert "x(sh + 3)" in DASH  # o limite fica 3 °C acima da sombra


def test_status_cards_have_values_and_explanations():
    for value, meta in (('weather-temp', 'weather-meta'), ('risk-now', 'risk-now-meta'), ('readings-total', 'readings-meta'), ('esp-total', 'esp-last')):
        assert value in IDS and meta in IDS
        assert f"$('{value}')" in DASH and f"$('{meta}')" in DASH


def test_esp32_table_has_seven_columns_and_an_empty_state():
    head = HTML.split('<thead>')[1].split('</thead>')[0]
    assert head.count('scope="col"') == 7
    assert 'colspan="7"' in HTML and 'Nenhuma medição do ESP32 ainda' in HTML
    assert 'id="esp-table-caption"' in HTML and 'aria-describedby="esp-table-caption"' in HTML


def test_risk_scale_lists_the_four_noaa_bands_in_order():
    scale = HTML.split('class="sv-scale"')[1].split('</ul>')[0]
    assert re.findall(r'class="r-([a-z]+)"', scale) == ['normal', 'atencao', 'alerta', 'perigo']


def test_heatmap_period_buttons_are_toggle_buttons():
    buttons = PAGE.find('button', **{'class': 'sv-chip'})
    assert [b['data-period'] for b in buttons] == ['tarde', 'noite']
    assert [b['aria-pressed'] for b in buttons] == ['true', 'false']
    assert "b.setAttribute('aria-pressed', String(b === btn))" in DASH


def test_history_form_fields_are_labelled_and_dates_required():
    for field in ('city-main', 'city-compare', 'date-start', 'date-end'):
        assert PAGE.find('label', **{'for': field}), field
    assert 'required' in PAGE.find('input', id='date-start')[0]
    assert 'required' in PAGE.find('input', id='date-end')[0]
    assert 'disabled' in PAGE.find('button', id='export-csv')[0]


def test_city_results_list_announces_changes():
    assert PAGE.find('ul', id='city-results')[0]['aria-live'] == 'polite'
    assert [b['data-search'] for b in PAGE.find('button') if 'data-search' in b] == ['main', 'compare']


def test_sdg_goals_appear_in_the_purpose_section_and_in_the_footer():
    for goal in ('ODS 3', 'ODS 11', 'ODS 13'):
        assert goal in HTML
    assert HTML.count('class="ods-3"') == 2


def test_external_links_open_safely_in_a_new_tab():
    external = [a for a in PAGE.find('a') if a.get('href', '').startswith('http')]
    assert len(external) >= 4
    for link in external:
        assert link.get('target') == '_blank'
        assert 'noopener' in link.get('rel', '') and 'noreferrer' in link.get('rel', '')


def test_map_iframe_is_titled_and_does_not_leak_the_referrer():
    frame = PAGE.find('iframe')[0]
    assert frame['title'] and frame['loading'] == 'lazy' and frame['referrerpolicy'] == 'no-referrer'
    assert frame['src'].startswith('https://www.openstreetmap.org/')


def test_every_image_has_alt_text_and_reserved_size():
    images = PAGE.find('img')
    assert len(images) == 6
    for img in images:
        assert img.get('alt'), img
        assert img.get('width') and img.get('height'), img


DOCUMENTARY = [img for img in PAGE.find('img') if 'documentary-media' in img.get('class', '')]


def test_the_five_documentary_photos_are_back():
    hosts = sorted(urlparse(img['src']).hostname for img in DOCUMENTARY)
    assert hosts == ['jornalcomarcapaulista.com.br', 'upload.wikimedia.org', 'www.aeaosasco.org.br',
                     'www.oanhanguera.com.br', 'www.visaooeste.com.br']


def test_wikimedia_thumbnail_uses_a_standard_width():
    # Desde 2026 a Wikimedia recusa miniaturas fora dos tamanhos padrão quando chamadas por outro site.
    standard = {20, 40, 60, 120, 250, 330, 500, 960, 1280, 1920, 3840}
    for img in DOCUMENTARY:
        match = re.search(r'/(\d+)px-', img['src'])
        if 'upload.wikimedia.org' in img['src']:
            assert match and int(match.group(1)) in standard, img['src']


def test_how_to_read_labels_point_away_from_each_other():
    draw = DASH.split('function drawHowto(shade, sun) {')[1].split('\n}\n')[0]
    assert "'text-anchor': shadeLeft ? 'end' : 'start'" in draw
    assert 'hi - lo < 14' in draw  # escala mínima de 14 °C


def test_motion_respects_reduced_motion_and_works_without_javascript():
    motion = (STATIC / 'motion.js').read_text(encoding='utf-8')
    assert "matchMedia('(prefers-reduced-motion: reduce)')" in motion and 'if (reduce.matches' in motion
    assert "root.classList.add('js-motion')" in motion  # conteúdo só fica oculto quando o script roda
    css = (STATIC / 'public-bundle.css').read_text(encoding='utf-8')
    assert '.js-motion .sv-reveal {' in css and '.js-motion .sv-reveal.is-visible' in css
    assert '/static/motion.js' in HTML


def test_documentary_photos_are_allowed_by_the_csp(client):
    csp = client.get('/').headers['content-security-policy']
    img_src = csp.split('img-src')[1].split(';')[0].split()
    for img in DOCUMENTARY:
        assert f"https://{urlparse(img['src']).hostname}" in img_src, img['src']
        assert img.get('referrerpolicy') == 'no-referrer'


def test_every_documentary_photo_has_a_credit_link_and_a_fallback_note():
    for img in DOCUMENTARY:
        note = img['data-credit-id']
        assert PAGE.find('p', id=note)[0].get('role') == 'status'
        assert f'id="{note}" hidden' in HTML
        figure = HTML.split(img['src'])[1].split('</figure>')[0]
        caption = figure.split('<figcaption class="sv-credit">')[1]
        assert 'href="https://' in caption and 'target="_blank"' in caption


def test_media_script_shows_the_note_instead_of_a_synthetic_image():
    media = (STATIC / 'media.js').read_text(encoding='utf-8')
    assert "querySelectorAll('img.documentary-media')" in media and "addEventListener('error'" in media
    assert 'note.hidden = false' in media and 'image.hidden = true' in media
    assert '/static/media.js' in HTML


def test_local_images_come_from_the_repository_assets(client):
    local = [img['src'] for img in PAGE.find('img') if img['src'].startswith('/')]
    assert local == ['/static/assets/osasco-orientation.svg']
    for src in local:
        assert (ROOT / src.lstrip('/')).is_file() and client.get(src).status_code == 200


def test_footer_states_that_the_readings_are_simulated():
    footer = HTML.split('<footer')[1]
    assert 'simuladas' in footer and 'Global Solution FIAP 2026.2' in footer
    assert 'id="fontes"' in footer


def test_skyline_illustration_is_decorative():
    skyline = HTML.split('class="sv-skyline')[1].split('</svg>')[0]
    assert 'aria-hidden="true"' in skyline
