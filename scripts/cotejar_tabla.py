#!/usr/bin/env python3
"""Coteja una tabla de la base contra texto copiado del PDF oficial.

  python scripts/cotejar_tabla.py [--base base] --param ISR_TARIFA_QUINCENAL --desde 2026-01-01 --texto tabla.txt [--mes 02]

tabla.txt: un renglón por línea, como sale del PDF: "3,537.16 6,216.15 207.75 10.88" ("En adelante" se acepta).
"""
import argparse, sys
from decimal import Decimal as D
from pathlib import Path
import yaml

a = argparse.ArgumentParser()
a.add_argument("--base", default=str(Path(__file__).resolve().parent.parent / "base")); a.add_argument("--param", required=True)
a.add_argument("--desde", required=True); a.add_argument("--texto", required=True); a.add_argument("--mes")
x = a.parse_args()
P = yaml.safe_load((Path(x.base) / "parametros.yaml").read_text(encoding="utf-8"))["parametros"][x.param]
tramo = next(v for v in P["valores"] if v["desde"] == x.desde)
filas = tramo["valor"][x.mes] if x.mes else tramo["valor"]
conv = lambda r: [None if c in (None, "None") else D(str(c)) for c in r]
base = [conv(f) for f in filas]
of = [conv(l.replace(",", "").replace("En adelante", "None").split()) for l in Path(x.texto).read_text().splitlines() if l.strip()]
dif = [(i + 1, o, b) for i, (o, b) in enumerate(zip(of, base)) if o != b]
if len(of) != len(base):
    dif.append(("renglones", len(of), len(base)))
print("IGUAL AL PDF" if not dif else "\n".join(f"renglón {i}: PDF {o} | base {b}" for i, o, b in dif))
sys.exit(1 if dif else 0)
