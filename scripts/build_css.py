"""Combine CSS sources in existing cascade order; no CSS minification or selector changes.

Usage:
    python scripts/build_css.py           # update committed bundles
    python scripts/build_css.py --check   # fail CI if outdated
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / "static"
BUNDLES = {
    "public-bundle.css": ["styles.css", "atlas.css", "refinement.css", "identidade-territorial.css", "atlas-claro.css", "editorial-natureza.css"],
    "admin-bundle.css": ["styles.css", "atlas.css", "admin-ops.css", "admin-editorial.css", "refinement.css", "identidade-territorial.css", "atlas-claro.css"],
}


def bundle(files):
    # Keep ordering and all media queries exactly; source comments make future refactoring traceable.
    return "/* SombraViva: generated CSS. Edit source files and run scripts/build_css.py. */\n" + "\n".join(
        f"/* === {name} === */\n" + (CSS / name).read_text(encoding="utf-8") for name in files
    ) + "\n"


def main():
    check = "--check" in sys.argv
    stale = []
    for filename, sources in BUNDLES.items():
        target = CSS / filename
        expected = bundle(sources)
        if not target.exists() or target.read_text(encoding="utf-8") != expected:
            stale.append(filename)
            if not check:
                target.write_text(expected, encoding="utf-8")
    if check and stale:
        print("CSS bundles out of date: " + ", ".join(stale))
        return 1
    print("CSS OK: " + ", ".join(BUNDLES))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
