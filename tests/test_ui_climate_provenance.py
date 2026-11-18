"""Guarda os contratos de UX, proveniência e segurança do plano unificado.

Não substitui verificação WCAG em navegador nem teste da instalação MySQL.
"""
from pathlib import Path
from bs4 import BeautifulSoup

PUBLIC = (Path(__file__).resolve().parents[1] / 'static/index.html').read_text(encoding='utf-8')
ADMIN = (Path(__file__).resolve().parents[1] / 'static/admin.html').read_text(encoding='utf-8')
JS = (Path(__file__).resolve().parents[1] / 'static/app.js').read_text(encoding='utf-8')
ADMIN_JS = (Path(__file__).resolve().parents[1] / 'static/admin.js').read_text(encoding='utf-8')
CSS = (Path(__file__).resolve().parents[1] / 'static/editorial-natureza.css').read_text(encoding='utf-8')


def test_climate_automatic_results_with_collapsed_advanced_filters():
    doc = BeautifulSoup(PUBLIC, 'html.parser')
    filters = doc.find('details', id='history-filters')
    assert filters and not filters.has_attr('open')
    assert filters.select_one('#history-form') is not None
    assert filters.select_one('#comparison-disclosure') is not None
    assert doc.select_one('#history-results') is not None
    assert "chooseHistoryDates('30');" in JS and 'queryHistory();' in JS


def test_provenance_labels_are_semantic_and_explicit():
    doc = BeautifulSoup(PUBLIC, 'html.parser')
    for kind in ('source-regional', 'source-simulation', 'source-hypothesis'):
        assert doc.select('.' + kind), kind
    assert doc.select_one('#history-source-chip[aria-live="polite"]')
    assert doc.select_one('#weather-origin-chip[aria-live="polite"]')
    assert 'SIMULAÇÃO DIDÁTICA' in doc.select_one('#mapa-calor').get_text(' ', strip=True)
    assert 'não é um mapa térmico medido' in doc.select_one('#mapa-calor').get_text(' ', strip=True)


def test_history_source_changes_only_after_data_validation():
    assert JS.index('historySeriesMatchesPeriod(results[0]') < JS.index('markHistorySource(isDemo);', JS.index('async function queryHistory'))
    assert 'source-simulation' in JS and 'source-unavailable' in JS
    assert 'aria-busy' in JS and 'history-source-freshness' in JS
    assert 'SINTETICO_DEMO' in JS


def test_weather_has_distinct_external_demo_and_failure_states():
    assert "'DADO REGIONAL · OPEN-METEO'" in JS
    assert "'SIMULAÇÃO · SEM DADO REAL'" in JS
    assert "'FONTE INDISPONÍVEL'" in JS
    assert 'weather-retry' in PUBLIC


def test_sensor_cards_have_identity_and_last_reading_instead_of_false_placement():
    assert 'station-provenance' in JS
    assert 'station.code' in JS and 'station.latest?.measured_at' in JS
    assert 'SIMULAÇÃO · NÃO INSTALADO' in JS
    assert 'posição não verificada' in JS


def test_methodology_page_gives_source_and_limits():
    doc = BeautifulSoup(PUBLIC, 'html.parser')
    sources = doc.select_one('#fontes')
    assert sources is not None
    for phrase in ('Open-Meteo', 'reais', 'Hipótese', 'fotografias do Calçadão'):
        assert phrase.lower() in sources.get_text(' ',strip=True).lower()
    assert doc.select_one('a[href="#fontes"]')
    assert doc.select_one('#history-chart-text-summary')


def test_admin_initial_landing_is_operational_not_misleading():
    assert "switchTab('alerts', false);await refreshAll();" in ADMIN_JS
    assert "textContent='Erro'" in ADMIN_JS
    assert 'Nenhum indicador foi confirmado' in ADMIN_JS
    assert 'HIPÓTESE ASSISTIDA PELA OPENAI' in ADMIN_JS
    assert 'COMPROMETIMENTO NÃO CONFIRMADO' in ADMIN_JS
    assert 'OPENAI_API_KEY' not in ADMIN_JS
    doc = BeautifulSoup(ADMIN, 'html.parser')
    assert doc.select_one('#admin-status[aria-live="polite"]')


def test_styles_keep_usable_mobile_controls_and_visible_focus():
    assert 'min-height:44px' in CSS
    assert '.sources-register' in CSS
    assert 'focus-visible' in CSS
    assert '.source-type' in CSS
