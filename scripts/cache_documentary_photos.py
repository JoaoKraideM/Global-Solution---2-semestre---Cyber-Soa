"""Cache opcional de fotografias com licença de reutilização conhecida.

Uso na raiz do projeto, quando houver acesso à internet:
    python scripts/cache_documentary_photos.py

Não baixa automaticamente fotografias jornalísticas ou imagens do concurso:
essas imagens estão na página via URL, com seus créditos e fontes, e
podem exigir autorização de reprodução antes de publicação.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "static" / "assets"
HTML = ROOT / "static" / "index.html"

PARK_REMOTE = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/"
    "Parque_Ecol%C3%B3gico_Jardim_Piratininga_-_panoramio.jpg/"
    "1024px-Parque_Ecol%C3%B3gico_Jardim_Piratininga_-_panoramio.jpg"
)
PARK_LOCAL = "/static/assets/parque-piratininga-2010.jpg"


def main() -> int:
    target = ASSETS / "parque-piratininga-2010.jpg"
    if not target.is_file():
        # Só HTTPS: impede que uma URL trocada por engano leia arquivos locais (file://).
        if urlparse(PARK_REMOTE).scheme != "https":
            raise ValueError("A fotografia só pode ser baixada por HTTPS")
        request = Request(PARK_REMOTE, headers={"User-Agent": "SombraViva/1.0 (academic study)"})
        try:
            # URL fixa e esquema https conferido acima (Bandit B310 revisado).
            with urlopen(request, timeout=25) as response:  # nosec B310
                if response.headers.get_content_type() != "image/jpeg":
                    raise ValueError("Resposta não é um JPEG")
                data = response.read(8 * 1024 * 1024 + 1)
            if not (10000 <= len(data) <= 8 * 1024 * 1024 and data.startswith(b"\xff\xd8\xff")):
                raise ValueError("JPEG inválido ou acima do limite")
            ASSETS.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        except (OSError, ValueError) as exc:
            print(f"Não foi possível armazenar a fotografia licenciada: {exc}")
            print("A página continuará usando a imagem externa e o fallback informativo.")
            return 1
    html = HTML.read_text(encoding="utf-8")
    HTML.write_text(html.replace(PARK_REMOTE, PARK_LOCAL), encoding="utf-8")
    print("Foto de BêS (2010, CC BY-SA 3.0) salva localmente com crédito mantido no HTML.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
