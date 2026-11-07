#!/usr/bin/env python3
"""INPC índice general (Banxico SIE, serie SP1; base 2a. quincena de julio 2018 = 100), para cruzar contra el INPC que publica el DOF.
  BANXICO_TOKEN=... python bajar.py [desde] [hasta]     (por omisión 2015-01-01 .. hoy)
Escribe sp1.json (respuesta cruda), inpc.csv (mes, índice) y SHA256SUMS."""
import csv, hashlib, json, os, sys, urllib.request
from datetime import date
from pathlib import Path
AQUI = Path(__file__).resolve().parent
desde = sys.argv[1] if len(sys.argv) > 1 else "2015-01-01"
hasta = sys.argv[2] if len(sys.argv) > 2 else date.today().isoformat()
req = urllib.request.Request(f"https://www.banxico.org.mx/SieAPIRest/service/v1/series/SP1/datos/{desde}/{hasta}",
                             headers={"Bmx-Token": os.environ.get("BANXICO_TOKEN", "proxy-injected"), "Accept": "application/json"})
crudo = urllib.request.urlopen(req, timeout=60).read()
(AQUI / "sp1.json").write_bytes(crudo)
with open(AQUI / "inpc.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["mes", "inpc_general"])
    for x in json.loads(crudo)["bmx"]["series"][0]["datos"]:
        d, m, a = x["fecha"].split("/")
        w.writerow([f"{a}-{m}", x["dato"].rstrip("0").rstrip(".")])
(AQUI / "SHA256SUMS").write_text("".join(f"{hashlib.sha256((AQUI / n).read_bytes()).hexdigest()}  {n}\n" for n in ("sp1.json", "inpc.csv")))
print(open(AQUI / "inpc.csv").read().splitlines()[-1])
