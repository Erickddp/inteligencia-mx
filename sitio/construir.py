"""Arma el sitio público de Inteligencia MX a partir de datos_abiertos/.

Uso:
    python sitio/construir.py            # escribe _site/index.html
    python sitio/construir.py --out DIR  # en otra carpeta

No toca la base: solo lee datos_abiertos/*.csv y catalogo.json, que el CI ya
comprueba que estén al día con base/. El workflow pages.yml lo corre en cada
push a main y publica el resultado en GitHub Pages.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos_abiertos"
PLANTILLA = Path(__file__).resolve().parent / "plantilla.html"


def leer(nombre: str) -> list[dict[str, str]]:
    with open(DATOS / nombre, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def armar() -> tuple[dict, str]:
    leyes = [
        {
            "c": r["clave"], "n": r["nombre"], "a": r["ambito"], "e": r["entidad"],
            "m": r["materia"], "u": r["url"], "r": r["ultima_reforma"],
            "t": r["articulos"], "h": r["cotejo_humano"],
        }
        for r in leer("leyes.csv")
    ]
    par = [
        {
            "i": r["id"], "n": r["nombre"],
            "v": r["valor_ultimo"] or r["formula"],
            "u": "%" if r["tipo"] == "porcentaje" and r["valor_ultimo"] else "",
            "s": r["estado_ultimo"], "d": r["desde_ultimo"], "f": r["fuente_ultimo"],
        }
        for r in leer("parametros.csv")
    ]
    reglas_csv = leer("reglas.csv")
    reg = [
        {"i": r["id"], "n": r["nombre"], "s": r["estado"], "c": r["calculadora"], "k": r["casos"] or "0"}
        for r in reglas_csv
    ]
    casos = sum(int(r["casos"] or 0) for r in reglas_csv)
    version = json.loads((DATOS / "catalogo.json").read_text(encoding="utf-8"))["version_base"]
    return {"leyes": leyes, "par": par, "reg": reg, "casos": casos}, version


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(RAIZ / "_site"))
    args = ap.parse_args()

    datos, version = armar()
    # </ dentro de un <script> cerraría la etiqueta: se escapa
    js = json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = (
        PLANTILLA.read_text(encoding="utf-8")
        .replace("__DATOS__", js)
        .replace("__VERSION__", version)
        .replace("__FECHA__", dt.date.today().isoformat())
        .replace("__NLEYES__", str(len(datos["leyes"])))
        .replace("__NPAR__", str(len(datos["par"])))
        .replace("__NREG__", str(len(datos["reg"])))
    )
    salida = Path(args.out)
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "index.html").write_text(html, encoding="utf-8")
    (salida / ".nojekyll").write_text("", encoding="utf-8")
    cname = Path(__file__).resolve().parent / "CNAME"
    if cname.exists():
        (salida / "CNAME").write_text(cname.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Sitio armado en {salida}: {len(datos['leyes'])} leyes, {len(datos['par'])} cifras, "
          f"{len(datos['reg'])} reglas, {datos['casos']} casos, base v{version}")


if __name__ == "__main__":
    main()
