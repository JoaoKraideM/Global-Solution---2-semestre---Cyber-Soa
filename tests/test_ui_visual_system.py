"""Sistema visual (sv-base.css + CSS das páginas): cores com contraste legível, fonte local,
classes usadas no HTML que existem no CSS e as faixas de risco com cor própria.

Substitui test_ui_colors, test_ui_foundations, test_ui_accessibility e
test_architectural_frontend, escritos para o tema anterior.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / 'static'
BASE = (STATIC / 'sv-base.css').read_text(encoding='utf-8')
PUBLIC_CSS = (STATIC / 'public-bundle.css').read_text(encoding='utf-8')
ADMIN_CSS = (STATIC / 'admin-bundle.css').read_text(encoding='utf-8')


def token(name):
    match = re.search(rf'--{name}:\s*(#[0-9A-Fa-f]{{6}})', BASE)
    assert match, f'token --{name} ausente'
    return match.group(1)


def luminance(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def classes_in(html):
    found = set()
    for attr in re.findall(r'class="([^"]+)"', html):
        found.update(attr.split())
    return found


def test_palette_tokens_are_declared_once_in_the_base():
    for name in ('green', 'brick', 'wine', 'amber', 'violet', 'page', 'paper', 'card', 'ink', 'ink-2', 'ink-3'):
        token(name)


def test_body_text_contrast_meets_wcag_aa():
    for fg, bg in (('ink', 'page'), ('ink-2', 'page'), ('ink-3', 'card'), ('ink-3', 'page'), ('green', 'page')):
        assert contrast(token(fg), token(bg)) >= 4.5, (fg, bg)


def test_text_on_dark_and_colored_surfaces_meets_wcag_aa():
    pairs = ((token('on-green'), token('green')), ('#FFFFFF', token('green')), ('#FFFFFF', token('brick')),
             ('#FFFFFF', token('wine')), ('#FFFFFF', token('green-2')))
    for fg, bg in pairs:
        assert contrast(fg, bg) >= 4.5, (fg, bg)


def test_secondary_text_on_green_is_at_least_large_text_contrast():
    assert contrast(token('on-green-2'), token('green')) >= 4.5


def test_risk_levels_have_distinct_text_and_pill_colors():
    for level in ('normal', 'atencao', 'alerta', 'perigo'):
        assert f'.risk-{level} {{ color:' in BASE
        assert f'.sv-pill.risk-{level} {{ background:' in BASE


def test_risk_scale_markers_use_the_same_four_colors_as_the_gauge():
    for level in ('normal', 'atencao', 'alerta', 'perigo'):
        assert f'.sv-scale .r-{level}::before' in PUBLIC_CSS


def test_public_sans_is_served_locally_with_its_license(client):
    faces = re.findall(r'url\("(/static/vendor/fonts/[^"]+)"\)', BASE)
    assert len(faces) == 4
    for face in faces:
        assert (ROOT / face.lstrip('/')).is_file()
        assert client.get(face).status_code == 200
    assert (STATIC / 'vendor' / 'fonts' / 'PUBLIC-SANS-LICENSE.txt').is_file()
    assert 'font-display: swap' in BASE


def test_styles_load_nothing_from_other_domains():
    for css in (PUBLIC_CSS, ADMIN_CSS):
        assert 'http://' not in css and 'https://' not in css and '@import' not in css
    for page in ('index.html', 'admin.html'):
        assert 'fonts.googleapis' not in (STATIC / page).read_text(encoding='utf-8')


def test_every_class_in_the_public_page_has_a_style():
    html = (STATIC / 'index.html').read_text(encoding='utf-8')
    # Classes que só servem de gancho para estados ou para o JavaScript.
    hooks = {'skip-link', 'menu-toggle', 'documentary-media'}  # documentary-media: gancho do media.js
    missing = sorted(c for c in classes_in(html) - hooks if f'.{c}' not in PUBLIC_CSS)
    assert not missing, f'classes sem estilo no painel público: {missing}'


def test_every_class_in_the_admin_page_has_a_style():
    html = (STATIC / 'admin.html').read_text(encoding='utf-8')
    hooks = {'skip-link', 'admin-page', 'documentary-media'}
    missing = sorted(c for c in classes_in(html) - hooks if f'.{c}' not in ADMIN_CSS)
    assert not missing, f'classes sem estilo na central: {missing}'


def test_classes_created_by_admin_js_have_a_style():
    js = (STATIC / 'admin.js').read_text(encoding='utf-8')
    created = set()
    for value in re.findall(r"add\('[a-z0-9]+','([a-z][a-z0-9 -]*)'", js):
        created.update(value.split())
    hooks = {'resolve', 'is-wide'}
    missing = sorted(c for c in created - hooks if f'.{c}' not in ADMIN_CSS)
    assert not missing, f'classes criadas pelo admin.js sem estilo: {missing}'


def test_focus_skip_link_and_touch_targets():
    assert ':focus-visible { outline: 3px solid' in BASE
    assert '.skip-link:focus' in BASE
    assert BASE.count('min-height: 48px') >= 2 and 'min-height: 44px' in BASE


def test_motion_is_disabled_for_users_who_ask_for_it():
    block = BASE.split('@media (prefers-reduced-motion: reduce)')[1].split('\n')[0]
    assert 'scroll-behavior: auto' in block and 'animation: none' in block and 'transition: none' in block


def test_layout_adapts_to_small_screens():
    assert '@media (max-width: 960px)' in BASE and 'body.nav-open .sv-nav { display: flex; }' in BASE
    assert '@media (max-width: 720px)' in PUBLIC_CSS
    assert '.mobile-admin-nav { display: flex; }' in ADMIN_CSS


def test_chart_tooltips_have_a_color_key_for_every_series():
    for key in ('c-shade', 'c-sun', 'c-max', 'c-mean', 'c-min', 'c-cmp', 'c-heat'):
        assert f'.sv-tip .{key}' in BASE


def test_dashboard_chart_colors_match_the_palette():
    dash = (STATIC / 'dashboard.js').read_text(encoding='utf-8')
    for name, hex_color in (('canopy', token('green')), ('brick', token('brick')), ('leaf', token('green-2'))):
        assert f"{name}:'{hex_color}'" in dash
    assert '"Public Sans"' in dash
