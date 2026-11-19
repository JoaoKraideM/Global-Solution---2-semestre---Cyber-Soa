"""Central de segurança (static/admin.html + admin.js): login, abas, laboratório PII e segurança do DOM.

Recupera a cobertura dos testes antigos da interface administrativa (test_soc_ui,
test_admin_frontend_operational, test_admin_page_route) para a central redesenhada.
"""
import re
import typing
from html.parser import HTMLParser
from pathlib import Path

from app.pii import PATTERNS
from app.schemas import AuditIn

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / 'static'
HTML = (STATIC / 'admin.html').read_text(encoding='utf-8')
JS = (STATIC / 'admin.js').read_text(encoding='utf-8')
TABS = ['overview', 'alerts', 'events', 'devices', 'lab']


class Tree(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    handle_startendtag = handle_starttag

    def find(self, tag=None, **attrs):
        return [a for t, a in self.tags if (tag is None or t == tag) and all(a.get(k) == v for k, v in attrs.items())]


PAGE = Tree()
PAGE.feed(HTML)
IDS = [a['id'] for _, a in PAGE.tags if a.get('id')]


def schema_sinks():
    return list(typing.get_args(AuditIn.model_fields['sink'].annotation))


def test_admin_route_serves_the_page_without_indexing(client):
    page = client.get('/admin')
    assert page.status_code == 200 and 'text/html' in page.headers['content-type']
    assert 'name="robots" content="noindex"' in page.text
    assert client.get('/api/v1/admin/overview').status_code == 401


def test_login_fields_use_the_right_types_and_autocomplete():
    email = PAGE.find('input', id='admin-email')[0]
    password = PAGE.find('input', id='admin-pass')[0]
    assert email['type'] == 'email' and email['autocomplete'] == 'username' and 'required' in email
    assert password['type'] == 'password' and password['autocomplete'] == 'current-password' and 'required' in password
    assert PAGE.find('button', type='submit')


def test_login_explains_the_lockout_rule_shown_by_the_api():
    assert '5 tentativas erradas em um minuto' in HTML and '60 segundos' in HTML


def test_operational_area_starts_hidden_until_login():
    assert PAGE.find('div', id='admin-section')[0]['class'] == 'hidden'
    assert "$('admin-section').classList.remove('hidden')" in JS
    assert "document.body.classList.add('admin-authenticated')" in JS


def test_each_tab_controls_its_own_panel():
    tabs = PAGE.find('button', role='tab')
    assert [t['data-tab'] for t in tabs] == TABS
    for tab in tabs:
        panel = PAGE.find('section', id=tab['aria-controls'])
        assert panel and panel[0]['role'] == 'tabpanel', tab
        assert tab['id'] == f"tab-{tab['data-tab']}"
    assert sum(t['aria-selected'] == 'true' for t in tabs) == 1


def test_mobile_select_offers_the_same_areas_as_the_tabs():
    select = HTML.split('id="admin-section-select"')[1].split('</select>')[0]
    assert re.findall(r'value="([a-z]+)"', select) == TABS


def test_shortcuts_only_point_to_existing_tabs():
    targets = {a['data-go'] for _, a in PAGE.tags if 'data-go' in a}
    assert targets and targets <= set(TABS)
    assert "document.querySelectorAll('[data-go]')" in JS


def test_keyboard_navigation_between_tabs():
    for key in ('ArrowRight', 'ArrowLeft', 'Home', 'End'):
        assert key in JS


def test_tab_counters_are_filled_after_loading_operations():
    for counter in ('tab-count-alerts', 'tab-count-devices'):
        assert counter in IDS and f"$('{counter}')" in JS


def test_session_email_is_shown_and_cleared_on_logout():
    assert "$('session-email').textContent=$('admin-email').value" in JS
    assert "$('session-email').textContent='admin'" in JS


def test_logout_clears_data_and_restores_the_lab_placeholder():
    logout = JS.split('function logout(')[1].split('\nfunction ')[0]
    for cleared in ('event-list', 'soc-dossier', 'finding-list', 'device-list', 'attention-list'):
        assert cleared in logout
    assert 'auditPlaceholder();' in logout and "$('admin-pass').value = ''" in logout


def test_lab_offers_exactly_the_sinks_accepted_by_the_api():
    radios = PAGE.find('input', type='radio', name='audit-sink')
    assert [r['value'] for r in radios] == schema_sinks()
    assert sum('checked' in r for r in radios) == 1
    assert "document.querySelector('input[name=\"audit-sink\"]:checked')" in JS


def test_lab_labels_unsafe_and_control_sinks():
    fieldset = HTML.split('class="ops-sinks"')[1].split('</fieldset>')[0]
    assert fieldset.count('Inseguro') == 3 and fieldset.count('Controle') == 2


def test_result_card_names_every_pii_type_the_detector_finds():
    names = dict(re.findall(r"(\w+):'([^']+)'", JS.split('const PII_NAMES={')[1].split('};')[0]))
    assert set(PATTERNS) <= set(names)


def test_result_card_names_every_sink():
    names = dict(re.findall(r"(\w+):'([^']+)'", JS.split('const SINKS={')[1].split('};')[0]))
    assert list(names) == schema_sinks()


def test_result_card_shows_flow_severity_action_preview_and_fix():
    render = JS.split('function renderAudit(result){')[1].split('\n}\n')[0]
    for part in ("'Entrada'", "'Proteção'", "'Destino'", "'Dados detectados'", "'Gravidade'", "'Ação'",
                 "'Prévia guardada no servidor'", "'O que fazer'", 'result.redacted_preview', 'result.remediation'):
        assert part in render, part
    assert "'O texto original nunca é guardado.'" in render


def test_dynamic_content_never_uses_innerhtml():
    for source in (JS, (STATIC / 'dashboard.js').read_text(encoding='utf-8')):
        assert 'innerHTML' not in source and 'insertAdjacentHTML' not in source and 'document.write' not in source


def test_token_lives_only_in_memory():
    assert 'localStorage' not in JS and 'sessionStorage' not in JS and 'document.cookie' not in JS
    assert 'let token = null;' in JS


def test_badges_use_sentence_case_instead_of_all_caps():
    for old in ('EXEMPLO FICTÍCIO', 'CENÁRIO FICTÍCIO', 'COMPROMETIMENTO NÃO CONFIRMADO', 'SIMULAÇÃO'):
        assert old not in JS
    assert "badge('Fictício','demo')" in JS


def test_resolving_an_event_requires_a_justification():
    assert "note.length < 8" in JS and 'pelo menos oito caracteres' in JS


def test_device_flow_diagram_documents_the_iot_limits():
    figure = HTML.split('O caminho de uma leitura')[1].split('</svg>')[0]
    for text in ('401 recusado', '429 bloqueado', 'Após 10 erros em 1 min', '201 · Leitura gravada'):
        assert text in figure


def test_admin_footer_has_the_lab_warning_and_area_links():
    footer = HTML.split('<footer')[1]
    assert 'Use só dados inventados no laboratório de privacidade.' in footer
    assert footer.count('data-go=') == 5
