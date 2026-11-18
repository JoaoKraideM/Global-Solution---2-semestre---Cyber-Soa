"""Grade de temperatura totalmente SINTÉTICA para demonstração de cartografia.

Coordenadas geográficas delimitam apenas um recorte retangular de Osasco.
Nenhum valor é medição, previsão, interpolação física ou evidência de ilha de calor.
"""
from math import exp, sin, cos

BOUND = {"north": -23.503, "south": -23.555, "west": -46.824, "east": -46.747}
PLACES = (
    {"code": "calcadao", "name": "Calçadão da Antônio Agú", "latitude": -23.5333671, "longitude": -46.7790848},
    {"code": "parque", "name": "Parque Ana Luiza Moura Freitas", "latitude": -23.5163255, "longitude": -46.7852783},
)

def build_heatmap(period: str = "tarde") -> dict:
    rows, cols = 17, 23
    points = []
    for i in range(rows):
        lat = BOUND["north"] + (BOUND["south"] - BOUND["north"]) * i / (rows - 1)
        for j in range(cols):
            lon = BOUND["west"] + (BOUND["east"] - BOUND["west"]) * j / (cols - 1)
            urban = exp(-(((lat+23.5334)/0.014)**2 + ((lon+46.7791)/0.024)**2)*1.7)
            green = exp(-(((lat+23.5163)/0.012)**2 + ((lon+46.7853)/0.013)**2)*1.5)
            # Ondulações criadas apenas para produzir uma figura didática convincente.
            base = (29.1 if period == "tarde" else 23.2)
            val = base + 4.5*urban - 2.3*green + 0.35*sin(i*.65)*cos(j*.38)
            points.append({"latitude": round(lat, 6), "longitude": round(lon, 6), "temperature_c": round(val, 1)})
    vals = [p["temperature_c"] for p in points]
    return {
        "source": "synthetic_demo", "simulated": True,
        "model": "função matemática didática sem calibração ou validação",
        "title": "Mapa de calor HIPOTÉTICO — Osasco",
        "notice": "SIMULAÇÃO DIDÁTICA: temperaturas inventadas, sem sensores ou base observacional. NÃO representa calor real, efeito térmico de árvores, mapa municipal ou previsão meteorológica.",
        "period": period, "unit": "°C", "bounds": BOUND,
        "grid": {"rows": rows, "columns": cols, "points": points},
        "places": PLACES, "range": {"minimum": min(vals), "maximum": max(vals)}
    }
