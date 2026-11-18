"""Regressões de interface: o histórico precisa carregar com assets atualizados."""


def test_static_files_are_not_cached(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.headers.get('cache-control') == 'no-store'
    for path in ('/static/app.js?v=20261117.4', '/static/public-bundle.css?v=20261117.2'):
        response = client.get(path)
        assert response.status_code == 200
        assert response.headers.get('cache-control') == 'public, max-age=0, must-revalidate'


def test_html_references_versioned_assets(client):
    html = client.get('/').text
    assert '/static/app.js?v=20261117.4' in html
    assert '/static/public-bundle.css?v=20261117.2' in html
    assert 'history-results' in html


def test_historical_chart_render_after_panel_is_visible(client):
    js = client.get('/static/app.js?v=20261117.4').text
    assert "$('history-results').classList.remove('hidden');" in js
    assert "renderHistoricalData();" in js
    assert "chooseHistoryDates('30');" in js
    assert 'queryHistory();' in js
