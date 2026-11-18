"""Interface adotada do esboço conjunto, sem mudanças nos contratos da API."""
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = (ROOT/'static/index.html').read_text(encoding='utf-8')
ADMIN = (ROOT/'static/admin.html').read_text(encoding='utf-8')
ADMIN_JS = (ROOT/'static/admin.js').read_text(encoding='utf-8')


def test_hero_unificado_com_titulo_e_acao_em_imagem():
    dom = BeautifulSoup(PUBLIC, 'html.parser')
    figure = dom.select_one('#inicio figure.sv-hero-unified')
    assert figure is not None
    assert figure.select_one('img.hero-documentary-photo')
    assert figure.select_one('#hero-title').get_text(' ', strip=True).endswith('sombra.')
    assert figure.select_one('.sv-action-primary[href="#historico"]')
    assert figure.select_one('figcaption') and 'CONCEITUAL' in figure.select_one('figcaption').get_text()
    assert 'sv-cover-ink' not in PUBLIC


def test_tarefas_antes_do_texto_editorial_e_sem_dados_inventados():
    dom=BeautifulSoup(PUBLIC,'html.parser')
    main=dom.select_one('main')
    classes=[el.get('class') or [] for el in main.find_all(recursive=False)]
    hero=next(i for i,cls in enumerate(classes) if 'sv-editorial-hero' in cls)
    route=next(i for i,cls in enumerate(classes) if 'reading-route' in cls)
    statement=next(i for i,cls in enumerate(classes) if 'sv-editorial-statement' in cls)
    assert hero < route < statement
    assert 'SIMULAÇÃO' in PUBLIC and 'ERA5' in PUBLIC


def test_resultado_climatico_prioriza_grafico_e_preserva_filtros():
    dom=BeautifulSoup(PUBLIC,'html.parser')
    section=dom.select_one('#historico')
    assert section.select_one('#history-filters details') or section.select_one('details#history-filters')
    assert section.select_one('#history-city-charts')
    assert section.select_one('#history-observations')
    assert PUBLIC.index('id="history-city-charts"') < PUBLIC.index('id="history-observations"')
    assert section.select_one('#history-download')


def test_soc_abre_no_arquivo_sem_perder_visao_geral():
    dom=BeautifulSoup(ADMIN,'html.parser')
    assert dom.select_one('#tab-alerts[aria-selected="true"]')
    assert dom.select_one('#pane-alerts:not(.hidden)')
    assert dom.select_one('#pane-overview.hidden')
    assert "let currentTab = 'alerts';" in ADMIN_JS
    assert "switchTab('alerts', false);await refreshAll();" in ADMIN_JS
    for section in ('pane-events','pane-devices','pane-lab'):
        assert dom.select_one('#'+section)
    assert dom.select_one('#soc-seed') and dom.select_one('#soc-demo')


def test_estilos_compilados_sem_mudar_apis():
    public = (ROOT/'static/public-bundle.css').read_text(encoding='utf-8')
    admin = (ROOT/'static/admin-bundle.css').read_text(encoding='utf-8')
    assert '.sv-hero-content' in public and '.sv-hero-unified' in public
    assert '.admin-body.admin-authenticated .admin-hero{display:none' in admin
    assert '.sv-casework' in admin and '.sv-case-index' in admin
    assert '/api/v1/admin/security/alerts' in ADMIN_JS
