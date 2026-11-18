"""Verificações de regressão para o comparativo e os gráficos por cidade."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'static'
HTML=(ROOT/'index.html').read_text(encoding='utf-8')
JS=(ROOT/'app.js').read_text(encoding='utf-8')
CSS=(ROOT/'styles.css').read_text(encoding='utf-8')


def test_combined_and_individual_chart_containers():
    assert 'id="history-chart"' in HTML
    assert 'id="history-city-charts"' in HTML
    assert 'Temperaturas por dia' in HTML
    assert 'renderCityCharts(pairs);' in JS
    assert 'drawIndividualCityCharts();' in JS
    assert 'city-chart-canvas' in CSS


def test_selected_city_auto_refreshes_and_obsolete_results_are_ignored():
    code=JS.split('function applyHistoryCity(field) {',1)[1].split('function historyDatesValid()',1)[0]
    assert 'queryHistory();' in code
    code=JS.split("$('remove-compare').addEventListener",1)[1].split("$('history-form').addEventListener",1)[0]
    assert 'queryHistory();' in code
    assert 'requestId !== historyRequestId' in JS


def test_distinct_chart_per_city_with_complete_daily_values():
    assert 'canvas.id=`history-city-chart-${i}`' in JS
    for key in ('temperature_min_c','temperature_mean_c','temperature_max_c'):
        assert key in JS
    for field in ('minima_cidade_2_c','maxima_cidade_2_c'):
        assert field in JS
    assert '@media(max-width:1100px)' in CSS
