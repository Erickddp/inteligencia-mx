#!/usr/bin/env python3
"""Cruza las citas de ley de la base («LISR art. 106», «LIVA arts. 1o.-A y 5-D») contra la biblioteca fuentes/leyes/.

  python scripts/citas_fuentes.py            # resumen
  python scripts/citas_fuentes.py --detalle  # lista cada cita sin resolver
  python scripts/citas_fuentes.py --estricto # sale con error si una cita de una ley YA incluida no existe

Una cita se resuelve si el artículo existe en fuentes/leyes/<LEY>/indice.json. Las leyes que aún no están en la
biblioteca (CFF, LFT, RMF...) se cuentan aparte: son la lista de trabajo para ampliarla.
"""
import argparse, collections, json, re, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LEYES_DIR = RAIZ / "fuentes" / "leyes"
ALIAS = {"LISR": "LISR", "LIVA": "LIVA", "LSS": "LSS", "LFPIORPI": "LFPIORPI", "LINFONAVIT": "LINFONAVIT",
         "Ley del Infonavit": "LINFONAVIT", "LFT": "LFT", "CFF": "CFF", "RLISR": "RLISR", "RLIVA": "RLIVA",
         "LIEPS": "LIEPS", "RMF": "RMF", "LIF": "LIF"}
CITA = re.compile(r"\b(" + "|".join(sorted(map(re.escape, ALIAS), key=len, reverse=True)) + r")\s+(?:arts?\.|artículos?)\s*([^;\"\)\n]+)")
NUM = re.compile(r"(\d+)\s*[º°]?o?\.?\s*(?:-\s*([A-Z])\b|\s+(Bis|Ter|Qu[áa]ter))?", re.I)


RMF_CITA = re.compile(r"\bRMF(?:\s+(\d{4}))?\s+reglas?\s+(\d{1,2}(?:\.\d{1,3}){1,4})(?![\d.]*x)")


def reglas_rmf() -> dict:
    """Reglas de la RMF en la biblioteca, por año: {'2026': {'2.7.1.21', ...}}."""
    out = {}
    for ix in (RAIZ / "fuentes" / "rmf").glob("*/*/indice.json"):
        out.setdefault(ix.parent.parent.name, set()).update(json.loads(ix.read_text(encoding="utf-8")))
    return out


def ids(texto: str) -> list[str]:
    out = []
    for m in NUM.finditer(re.split(r"\(|\b(?:fr|frs|fracc|fracción|fracciones|párr|párrafo|inciso|reforma|reformada|DOF|decreto|transitorios?|con)\b\.?", texto)[0]):
        partes = [m.group(1)] + [x.lower().replace("á", "a") for x in (m.group(2), m.group(3)) if x]
        out.append("-".join(partes))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detalle", action="store_true")
    ap.add_argument("--estricto", action="store_true")
    a = ap.parse_args()
    indices = {d.name: set(json.loads((d / "indice.json").read_text(encoding="utf-8"))) for d in LEYES_DIR.glob("*/") if (d / "indice.json").exists()}
    texto = "\n".join((RAIZ / "base" / f).read_text(encoding="utf-8") for f in ("parametros.yaml", "reglas.yaml"))
    cotejo = {}
    for d in LEYES_DIR.glob("*/"):
        if (d / "manifiesto.json").exists():
            c = json.loads((d / "manifiesto.json").read_text(encoding="utf-8")).get("cotejado_dof", {})
            cotejo[d.name] = (bool(c.get("ley_completa")), set(c.get("articulos", {})))
    ok, mal, fuera = collections.Counter(), collections.defaultdict(set), collections.Counter()
    sin_cotejar = collections.defaultdict(set)
    for m in CITA.finditer(texto):
        ley = ALIAS[m.group(1)]
        for i in ids(m.group(2)):
            if ley not in indices:
                fuera[ley] += 1
            elif i in indices[ley]:
                ok[ley] += 1
                if not (cotejo[ley][0] or i in cotejo[ley][1]):
                    sin_cotejar[ley].add(i)
            else:
                mal[ley].add(i)
    rmf = reglas_rmf()
    for m in RMF_CITA.finditer(texto):
        año = m.group(1) or "2026"
        if año not in rmf:
            fuera["RMF " + año] += 1
        elif m.group(2) in rmf[año]:
            ok["RMF"] += 1
        else:
            mal["RMF"].add(m.group(2))
    print("Citas que resuelven a un artículo de la biblioteca:", dict(ok) or "ninguna")
    print("Citas de leyes que aún NO están en la biblioteca (trabajo pendiente):", dict(fuera) or "ninguna")
    print("Citas sin artículo en la biblioteca:", {k: sorted(v) for k, v in mal.items()} if a.detalle else {k: len(v) for k, v in mal.items()} or "ninguna")
    print("Artículos citados que NO están cotejados con el DOF (sus parámetros no se firman):", {k: sorted(v) for k, v in sin_cotejar.items()} if a.detalle else {k: len(v) for k, v in sin_cotejar.items()})
    if a.estricto and mal:
        sys.exit(1)


if __name__ == "__main__":
    main()
