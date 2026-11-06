#!/usr/bin/env python3
"""R-52 / R-138: ¿la regla «dof_anterior» de Timbra da el tipo de cambio del CFF art. 20 (el publicado en el DOF el día anterior)?

Baja de Banxico SIE las dos series del dólar FIX:
  SF43718 = FIX por fecha de DETERMINACIÓN (la que Timbra guarda en la tabla tipo_cambio).
  SF60653 = FIX por fecha de LIQUIDACIÓN: para cada día dice el tipo de cambio aplicable a ese día (el publicado en el DOF la víspera).
Aplica a SF43718 la misma regla que `app/services/tipo_cambio.valor(..., "dof_anterior")` (copiada abajo, sin cambios de lógica) y compara,
día por día de calendario, contra SF60653. Escribe:
  sf43718.json, sf60653.json   respuesta cruda de Banxico (evidencia)
  comparacion.csv              fecha, valor Timbra, fecha del FIX usado, SF60653, coincide

  BANXICO_TOKEN=... python comparar.py [desde] [hasta]     (por omisión 2025-01-01 .. hoy)
Sale con 1 si hay una diferencia.
"""
import csv, json, os, sys, urllib.request
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

AQUI = Path(__file__).resolve().parent
URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/{s}/datos/{d}/{h}"
VIGENCIA = 7  # igual que tipo_cambio.VIGENCIA


def bajar(serie, desde, hasta):
    req = urllib.request.Request(URL.format(s=serie, d=desde, h=hasta),
                                 headers={"Bmx-Token": os.environ.get("BANXICO_TOKEN", "proxy-injected"), "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        crudo = json.loads(r.read())
    (AQUI / f"{serie.lower()}.json").write_text(json.dumps(crudo, ensure_ascii=False, indent=1), encoding="utf-8")
    out = {}
    for x in crudo["bmx"]["series"][0]["datos"]:
        if x["dato"] not in ("N/E", ""):
            d, m, a = x["fecha"].split("/")
            out[date(int(a), int(m), int(d))] = Decimal(x["dato"].replace(",", ""))
    return out


def dof_anterior(fix: dict, dia: date):
    """Copia de tipo_cambio.valor, regla dof_anterior: de los dos últimos FIX determinados ANTES del día, el más viejo."""
    previos = sorted((f for f in fix if f < dia), reverse=True)[:2]
    if len(previos) < 2 or (dia - previos[0]).days > VIGENCIA:
        return None
    return fix[previos[1]], previos[1]


def main(argv):
    desde = date.fromisoformat(argv[0]) if argv else date(2025, 1, 1)
    hasta = date.fromisoformat(argv[1]) if len(argv) > 1 else date.today()
    fix = bajar("SF43718", desde - timedelta(days=20), hasta)
    pub = bajar("SF60653", desde, hasta)
    filas, malas = [], 0
    d = desde
    while d <= hasta:
        if d in pub:
            r = dof_anterior(fix, d)
            v, f = r if r else (None, None)
            ok = v == pub[d]
            malas += not ok
            filas.append([d.isoformat(), v, f.isoformat() if f else "", pub[d], "sí" if ok else "NO"])
        d += timedelta(days=1)
    with open(AQUI / "comparacion.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["fecha_operacion", "timbra_dof_anterior", "fix_determinado_el", "banxico_SF60653", "coincide"])
        w.writerows(filas)
    print(f"{desde}..{hasta}: días comparados {len(filas)}, diferencias {malas}")
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
