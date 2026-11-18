"""Dados fictícios para prévia sem MySQL: nunca representam medições em Osasco."""
from datetime import date, datetime, timedelta, timezone
from math import sin, cos
from statistics import mean
from unicodedata import normalize

def snapshot() -> dict:
    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    setups = (("centro-demo", "Área exposta · DEMONSTRAÇÃO", "Cenário didático de pouca sombra"),
              ("verde-demo", "Área arborizada · DEMONSTRAÇÃO", "Cenário didático de vegetação"))
    rows = {}
    stations = []
    for n,(code,name,setting) in enumerate(setups):
        series = []
        for i in range(24):
            temp = 29.2 + 3.4*sin(i*.31) + .4*sin(i*.12) - (1.7 if n else 0)
            series.append({"temperature_c": round(temp,1), "humidity_pct": 65.0 if n else 58.0,
                           "measured_at": (end-timedelta(hours=23-i)).isoformat(), "simulated": True})
        rows[code] = list(reversed(series))
        stations.append({"code":code,"name":name,"setting":setting,
                         "simulated":True,"latest":series[-1]})
    return {"demo": True, "simulated": True, "source": "synthetic_demo",
            "notice":"Dados gerados em memória para demonstração. Não foram registrados no MySQL nem medidos em Osasco.",
            "station_count":2, "readings_total":0, "stations":stations,
            "pairwise_difference_c": round(stations[0]["latest"]["temperature_c"] - stations[1]["latest"]["temperature_c"],1),
            "readings": rows}


def weather_snapshot() -> dict:
    """Weather example only, not a fallback *measurement*."""
    return {"source":"synthetic_demo", "simulated":True,"time":"não observado",
            "temperature_c":26.7,"humidity_pct":61.0,"apparent_temperature_c":27.9,
            "notice":"EXEMPLO FICTÍCIO. Não representa o clima atual em Osasco."}


def history_snapshot(latitude:float,longitude:float,start_date:date,end_date:date) -> dict:
    from app.weather_history import validate_period
    validate_period(start_date,end_date)
    points=[]
    span=(end_date-start_date).days+1
    location_factor=cos(latitude*.08)*1.2+sin(longitude*.04)*1.5
    for i in range(span):
        day=start_date+timedelta(days=i)
        base=22.5+2.8*sin(i*.18)+0.9*cos(i*.46)+location_factor
        low=round(base-4.2-.7*cos(i*.12),1)
        high=round(base+5.3+.8*sin(i*.28),1)
        points.append({"date":day.isoformat(),"temperature_mean_c":round(base,1),
                       "temperature_max_c":high,"temperature_min_c":low})
    return {"source":"synthetic_demo","kind":"serie_historica_ficticia", "simulated":True,
            "location":{"latitude":latitude,"longitude":longitude},
            "period":[start_date.isoformat(),end_date.isoformat()],"days":points,
            "summary":{"days_with_data":len(points),
                       "mean_temperature_c":round(mean(p['temperature_mean_c'] for p in points),2),
                       "highest_temperature_c":max(p['temperature_max_c'] for p in points),
                       "lowest_temperature_c":min(p['temperature_min_c'] for p in points),
                       "days_mean_above_30c":sum(p['temperature_mean_c']>=30 for p in points)},
            "notice":"SÉRIE FICTÍCIA, sem relação com temperaturas observadas ou ERA5. Usar apenas para testar gráficos e filtros."}


DEMO_CITIES = (
    ("Osasco", "São Paulo", "Brasil", -23.5329, -46.7917),
    ("Barueri", "São Paulo", "Brasil", -23.5114, -46.8765),
    ("São Paulo", "São Paulo", "Brasil", -23.5505, -46.6333),
    ("Franca", "São Paulo", "Brasil", -20.5386, -47.4008),
    ("Paris", "Île-de-France", "França", 48.8566, 2.3522),
)

def search_snapshot(query: str) -> dict:
    """Catálogo mínimo OFFLINE com coordenadas aproximadas de cidades reais.
    Não é uma API oficial de geocodificação nem uma fonte de dados climáticos.
    """
    def fold(text):
        return ''.join(c for c in normalize('NFKD',text.casefold()) if not 0x300 <= ord(c) <= 0x36f)
    q=fold(query.strip())
    locations=[{"id":f"demo-{i}","name":name,"state":state,"country":country,
               "latitude":latitude,"longitude":longitude,"approximate_coordinates":True}
               for i,(name,state,country,latitude,longitude) in enumerate(DEMO_CITIES)
               if q and q in fold(name)]
    return {"source":"fallback_offline_approximate_city_centers", "demo":True,
            "notice":"Coordenadas aproximadas para pesquisa de demonstração offline, não de geocodificação oficial.",
            "locations":locations}
