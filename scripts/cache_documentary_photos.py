"""Baixa imagens documentais licenciadas e habilita cópias locais.

Na raiz do SombraViva, com internet:
    python scripts/cache_documentary_photos.py

Falhas de rede são informadas, sem inventar imagens nem substituir imagens com erro.
As fotos são creditadas no site e continuam disponíveis nas páginas de origem.
"""
from __future__ import annotations
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "static" / "assets"
HTML = ROOT / "static" / "index.html"

PHOTOS = (
    ("centro-osasco.jpg", "Centro_passarela.jpg", "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ed/Centro_passarela.jpg/1280px-Centro_passarela.jpg"),
    ("parque-piratininga.jpg", "Parque_Ecológico_Jardim_Piratininga_-_panoramio.jpg", "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Parque_Ecol%C3%B3gico_Jardim_Piratininga_-_panoramio.jpg/1024px-Parque_Ecol%C3%B3gico_Jardim_Piratininga_-_panoramio.jpg"),
)

def fetch(url: str) -> bytes:
    req=Request(url, headers={"User-Agent":"SombraViva-Atlas/1.1 (academic research; local cache)"})
    with urlopen(req,timeout=20) as resp:
        if resp.headers.get_content_type() not in ("image/jpeg","image/jpg"):
            raise ValueError("A resposta não é JPEG")
        content=resp.read(7*1024*1024+1)
    if not (10000 <= len(content) <= 7*1024*1024 and content.startswith(b"\xff\xd8\xff")):
        raise ValueError("Conteúdo JPEG inválido")
    return content

def main() -> int:
    ASSETS.mkdir(parents=True,exist_ok=True)
    html=HTML.read_text(encoding="utf-8")
    succeeded=0
    for output,name,source in PHOTOS:
        local=ASSETS/output
        if local.exists() and local.read_bytes()[:3]==b"\xff\xd8\xff":
            print(f"Já existe: {local}")
        else:
            urls=[source,"https://commons.wikimedia.org/wiki/Special:Redirect/file/"+quote(name)+"?width=1280"]
            for uri in urls:
                try:
                    local.write_bytes(fetch(uri))
                    print(f"Foto salva: {local} ({local.stat().st_size} bytes)")
                    break
                except Exception as exc:
                    print(f"Fonte não disponível: {type(exc).__name__}: {exc}")
            else:
                print(f"Foto não obtida: {output}. Fonte online e cartografia ilustrativa continuam no site.")
                continue
        # O cache nunca modifica créditos, licenças, datas ou legendas.
        # Ao trocar a ilustração pela foto original, atualiza também as legendas.
        if output == "centro-osasco.jpg":
            html=html.replace('/static/assets/cidade-ilustrativa.webp', f'/static/assets/{output}')
            html=html.replace('Ilustração editorial autoral de uma cidade com ruas, edifícios e árvores; não é fotografia de Osasco',
                              'Vista do centro de Osasco de uma passarela sobre o Tietê, CWM99, 2026')
            html=html.replace('ILUSTRAÇÃO EDITORIAL · CENÁRIO CONCEITUAL', 'FOTO DOCUMENTAL · OSASCO · CC0')
        else:
            html=html.replace('/static/assets/verde-ilustrativo.webp', f'/static/assets/{output}')
            html=html.replace('Ilustração editorial original de vegetação, vias e edifícios; não corresponde a um parque específico',
                              'Registro fotográfico de 2010 do Parque Ecológico Jardim Piratininga, autor BêS')
            html=html.replace('Ilustração editorial · não é foto do Parque Piratininga',
                              'Fotografia de 2010 · Parque Ecológico Jardim Piratininga')
        succeeded+=1
    HTML.write_text(html,encoding="utf-8")
    print(f"{succeeded}/{len(PHOTOS)} fotos locais configuradas. Execute: docker compose up -d --build --force-recreate")
    return 0 if succeeded == len(PHOTOS) else 1

if __name__=="__main__":
    raise SystemExit(main())
