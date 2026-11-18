"""Testes determinísticos da integração externa, sem depender de internet."""
from datetime import date, timedelta
from urllib.parse import parse_qs
import httpx
import pytest
from app import weather_history as wh


def mock_external(monkeypatch, handler):
    original = httpx.AsyncClient
    def build_client(*args, **kwargs):
        kwargs['transport'] = httpx.MockTransport(handler)
        return original(*args, **kwargs)
    monkeypatch.setattr(wh.httpx, 'AsyncClient', build_client)


def test_search_other_cities(client, monkeypatch):
    def handler(request):
        assert request.url.host == 'geocoding-api.open-meteo.com'
        assert request.url.params['name'] == 'Barueri'
        return httpx.Response(200, json={'results': [
            {'id': 3457898, 'name':'Barueri','admin1':'São Paulo','country':'Brasil',
             'country_code':'BR','latitude':-23.51,'longitude':-46.87},
        ]})
    mock_external(monkeypatch, handler)
    result=client.get('/api/v1/weather/places',params={'search':'Barueri'})
    assert result.status_code==200
    cities=result.json()['locations']
    assert len(cities)==1 and cities[0]['name']=='Barueri'
    assert cities[0]['longitude']==-46.87


def test_geocoding_length_validation(client):
    assert client.get('/api/v1/weather/places',params={'search':'a'}).status_code==422


def test_historical_other_city_real_provider_mock(client,monkeypatch):
    def handler(request):
        assert request.url.host == 'archive-api.open-meteo.com'
        assert request.url.params['latitude'] == '-23.51'
        assert request.url.params['longitude'] == '-46.87'
        assert request.url.params['models'] == 'era5'
        assert request.url.params['daily'] == 'temperature_2m_mean,temperature_2m_max,temperature_2m_min'
        assert request.url.params['timezone'] == 'auto'
        return httpx.Response(200,json={
            'timezone':'America/Sao_Paulo',
            'daily':{'time':['2025-01-01','2025-01-02'],
                     'temperature_2m_mean':[23.0,25.0],
                     'temperature_2m_max':[31.0,32.0],
                     'temperature_2m_min':[18.0,19.0]}
        })
    mock_external(monkeypatch,handler)
    result=client.get('/api/v1/weather/history', params={
        'latitude':-23.51,'longitude':-46.87,
        'start_date':'2025-01-01','end_date':'2025-01-02'})
    assert result.status_code==200, result.text
    body=result.json()
    assert body['summary']['mean_temperature_c']==24.0
    assert body['summary']['highest_temperature_c']==32.0
    assert body['summary']['lowest_temperature_c']==18.0
    assert body['days'][0]['temperature_min_c']==18.0
    assert body['model']=='era5'
    assert body['location']['longitude']==-46.87


def test_osasco_legacy_route_uses_common_archive(client, monkeypatch):
    def handler(request):
        assert request.url.params['latitude']=='-23.5329'
        return httpx.Response(200,json={'timezone':'America/Sao_Paulo','daily':{
            'time':['2024-02-02'],'temperature_2m_mean':[24.0],
            'temperature_2m_max':[30.0],'temperature_2m_min':[17.0]}})
    mock_external(monkeypatch,handler)
    result=client.get('/api/v1/weather/history/osasco',params={'start_date':'2024-02-02','end_date':'2024-02-02'})
    assert result.status_code==200
    assert result.json()['days'][0]['temperature_mean_c']==24.0


def test_reject_periods_and_out_of_bounds(client,monkeypatch):
    def forbidden(_request):
        raise AssertionError('Não deve chamar API externa para consultas inválidas')
    mock_external(monkeypatch,forbidden)
    endpoint='/api/v1/weather/history'
    base={'latitude':-23.53,'longitude':-46.79}
    scenarios=[
        {'start_date':'2025-04-01','end_date':'2025-03-01'},
        {'start_date':'2023-01-01','end_date':'2025-01-01'},
        {'start_date':(date.today()-timedelta(days=1)).isoformat(), 'end_date':(date.today()-timedelta(days=1)).isoformat()},
        {'start_date':'1939-01-01','end_date':'1939-01-02'},
    ]
    for scenario in scenarios:
        response=client.get(endpoint,params={**base,**scenario})
        assert response.status_code==422, response.text
    assert client.get(endpoint,params={**base,'longitude':200,'start_date':'2025-01-01','end_date':'2025-01-02'}).status_code==422


def test_provider_unavailable_returns_503(client,monkeypatch):
    mock_external(monkeypatch,lambda _request:httpx.Response(502,json={'error':True}))
    result=client.get('/api/v1/weather/history',params={'latitude':-23,'longitude':-46,'start_date':'2024-01-01','end_date':'2024-01-02'})
    assert result.status_code==503
    city=client.get('/api/v1/weather/places',params={'search':'São Paulo'})
    assert city.status_code==503


def test_archive_missing_values_are_not_fabricated(client,monkeypatch):
    mock_external(monkeypatch,lambda _:httpx.Response(200,json={'daily':{
        'time':['2024-01-01','2024-01-02'],'temperature_2m_mean':[22.0,None],
        'temperature_2m_min':[16.0,None],'temperature_2m_max':[30.0,None],
    }}))
    r=client.get('/api/v1/weather/history',params={'latitude':-23,'longitude':-46,'start_date':'2024-01-01','end_date':'2024-01-02'})
    assert r.status_code==200
    assert r.json()['days'][1]['temperature_mean_c'] is None
    assert r.json()['summary']['days_with_data']==1
