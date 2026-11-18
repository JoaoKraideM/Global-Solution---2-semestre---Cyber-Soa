"""Consultas históricas regionais (Open-Meteo ERA5) e busca geográfica.

Não converte reanálise meteorológica em medição local de sensor IoT.
"""
from datetime import date, timedelta
from statistics import mean
import httpx
from fastapi import HTTPException

ARCHIVE_ENDPOINT = 'https://archive-api.open-meteo.com/v1/archive'
GEOCODING_ENDPOINT = 'https://geocoding-api.open-meteo.com/v1/search'
EARLIEST_DAY = date(1940, 1, 1)
MAX_DAYS = 366
# Disponibilidade ERA5 costuma ter atraso; margem conservadora de 7 dias.
LAG_DAYS = 7


def last_available_day() -> date:
    return date.today() - timedelta(days=LAG_DAYS)


def validate_period(start_date: date, end_date: date) -> None:
    if start_date < EARLIEST_DAY or start_date > end_date:
        raise HTTPException(422, 'Período inválido: a data inicial deve ser a partir de 1940-01-01 e anterior à final.')
    if (end_date - start_date).days >= MAX_DAYS:
        raise HTTPException(422, 'Período muito longo: selecione no máximo 366 dias por consulta.')
    if end_date > last_available_day():
        raise HTTPException(422, 'O histórico ERA5 é disponibilizado com atraso; selecione data final de pelo menos 7 dias atrás.')


async def search_cities(search: str) -> dict:
    """Retorna cidades reais da geocodificação, nunca faz requisições a URLs arbitrárias."""
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.get(GEOCODING_ENDPOINT, params={'name': search.strip(), 'count': 8, 'language': 'pt', 'format': 'json'})
            resp.raise_for_status()
            raw = resp.json()
        locations = []
        for item in raw.get('results', []):
            lat, lon = item.get('latitude'), item.get('longitude')
            if not isinstance(lat, (float, int)) or not isinstance(lon, (float, int)):
                continue
            locations.append({
                'id': item.get('id'), 'name': item.get('name', ''),
                'state': item.get('admin1') or '', 'country': item.get('country') or '',
                'country_code': item.get('country_code') or '', 'latitude': lat,
                'longitude': lon,
            })
        return {'source': 'Open-Meteo Geocoding / GeoNames', 'locations': locations}
    except (httpx.HTTPError, ValueError, TypeError, KeyError):
        raise HTTPException(503, 'Serviço de busca de cidades temporariamente indisponível')


async def archive_for_location(latitude: float, longitude: float, start_date: date, end_date: date) -> dict:
    """Carrega a mesma série ERA5 para todas as cidades, permitindo comparação coerente."""
    validate_period(start_date, end_date)
    params = {
        'latitude': latitude, 'longitude': longitude,
        'start_date': start_date.isoformat(), 'end_date': end_date.isoformat(),
        'daily': 'temperature_2m_mean,temperature_2m_max,temperature_2m_min',
        'timezone': 'auto', 'models': 'era5',
    }
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            resp = await client.get(ARCHIVE_ENDPOINT, params=params)
            resp.raise_for_status()
            raw = resp.json()
        daily = raw['daily']
        days = daily['time']
        avgs = daily['temperature_2m_mean']
        highs = daily['temperature_2m_max']
        lows = daily['temperature_2m_min']
        if not days or not (len(days) == len(avgs) == len(highs) == len(lows)):
            raise ValueError('Série inválida ou vazia')
        series = [
            {'date': day, 'temperature_mean_c': avg, 'temperature_max_c': high,
             'temperature_min_c': low}
            for day, avg, high, low in zip(days, avgs, highs, lows)
        ]
        valid_avg = [v for v in avgs if isinstance(v, (int, float))]
        valid_high = [v for v in highs if isinstance(v, (int, float))]
        valid_low = [v for v in lows if isinstance(v, (int, float))]
        return {
            'source': 'Open-Meteo ERA5', 'kind': 'reanálise meteorológica regional',
            'model': 'era5',
            'location': {'latitude': latitude, 'longitude': longitude,
                         'timezone': raw.get('timezone', 'auto')},
            'period': [start_date.isoformat(), end_date.isoformat()],
            'days': series,
            'summary': {
                'days_with_data': len(valid_avg),
                'mean_temperature_c': round(mean(valid_avg), 2) if valid_avg else None,
                'highest_temperature_c': round(max(valid_high), 2) if valid_high else None,
                'lowest_temperature_c': round(min(valid_low), 2) if valid_low else None,
                'days_mean_above_30c': sum(v >= 30 for v in valid_avg),
            },
            'attribution': 'https://open-meteo.com/',
            'note': 'ERA5 é uma reanálise regional com resolução de cerca de 25 km. Não mede diferenças de temperatura entre ruas, árvores ou toldos de Osasco; medições IoT são separadas.',
        }
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        raise HTTPException(503, 'Dados meteorológicos históricos temporariamente indisponíveis')
