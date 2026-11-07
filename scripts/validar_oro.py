#!/usr/bin/env python3
"""Reglas de oro de la base: lo que el CI exige en cada PR.

  python scripts/validar_oro.py [--base base] [--deuda scripts/deuda_oro.json] [--actualizar-deuda]

Revisa (además de lo que ya frena la carga del motor: estados válidos, vigencias, renglones contiguos, IDs de regla únicos):
  R2  IDs de parámetro sin año ni mes
  R5  ley sin plazo: hasta null lleva confirmado_hasta
  R6  regla con calculadora lleva al menos 2 casos (uno normal y uno en el límite)
  R7  números como texto, nunca float (en valores y en casos)
  R1  toda la base trae fuente (cada tramo y cada fórmula)
  R8  sin RFC reales (solo genéricos), sin secretos ni tokens en el repo

Deuda: lo que la base ya traía al nacer el CI vive en scripts/deuda_oro.json. Un PR NO puede agregar
violaciones nuevas. Lo que se arregla debe salir de la deuda (el CI lo exige), así la lista solo baja.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
RFC_GENERICOS = {"XAXX010101000", "XEXX010101000", "AAA010101AAA", "AAAA010101AAA",
                 # RFC genéricos para residentes en el extranjero, definidos por la propia RMF 2026 (reglas 2.4.3, 3.17.8 y 12.2.9)
                 "EXT990101NI1", "EXTF900101NI1", "EXT990101NI4", "EXT990101NI9"}
RE_RFC = re.compile(r"\b[A-ZÑ&]{3,4}\d{6}[A-Z0-9]{3}\b")
RE_ANIO_MES = re.compile(r"(?:^|_)(?:(?:19|20)\d\d|ENE|FEB|MAR|ABR|MAY|JUN|JUL|AGO|SEP|OCT|NOV|DIC|"
                         r"ENERO|FEBRERO|MARZO|ABRIL|MAYO|JUNIO|JULIO|AGOSTO|SEPTIEMBRE|OCTUBRE|NOVIEMBRE|DICIEMBRE)(?:_|$)")
SECRETOS = [re.compile(p) for p in (
    r"gh[pousr]_[A-Za-z0-9]{30,}", r"github_pat_[A-Za-z0-9_]{30,}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"AKIA[0-9A-Z]{16}", r"xox[baprs]-[A-Za-z0-9-]{10,}", r"(?i)\b(?:api[_-]?key|token|secret|password)\b\s*[:=]\s*['\"]?[A-Za-z0-9/+_-]{16,}")]
EXT_TEXTO = {".py", ".yaml", ".yml", ".md", ".txt", ".json", ".toml", ".cfg", ".ini", ".sh", ".js"}


def hay_float(x):
    if isinstance(x, float):
        return True
    if isinstance(x, list):
        return any(hay_float(i) for i in x)
    if isinstance(x, dict):
        return any(hay_float(i) for i in x.values())
    return False


def valida(P: dict, R: list) -> set:
    """Violaciones de la base como llaves estables 'Rn:objeto:detalle'."""
    v = set()
    for pid, p in P.items():
        if RE_ANIO_MES.search(pid):
            v.add(f"R2:{pid}:año o mes en el ID")
        if "formula" in p and not p.get("fuente"):
            v.add(f"R1:{pid}:fórmula sin fuente")
        for t in p.get("valores", []):
            d = t.get("desde")
            if not t.get("fuente"):
                v.add(f"R1:{pid}@{d}:tramo sin fuente")
            if hay_float(t.get("valor")):
                v.add(f"R7:{pid}@{d}:número float en el valor")
            if t.get("hasta") is None and not t.get("confirmado_hasta") and t.get("estado", "vigente") in ("vigente", "por_confirmar"):
                v.add(f"R5:{pid}@{d}:hasta null sin confirmado_hasta")
    for r in R:
        if r.get("calculadora") and len(r.get("casos", [])) < 2:
            v.add(f"R6:{r['id']}:calculadora con menos de 2 casos")
        for c in r.get("casos", []):
            if hay_float(c.get("entradas")) or hay_float(c.get("esperado")):
                v.add(f"R7:{r['id']}:{c.get('nombre')}:float en el caso")
    return v


def valida_texto(nombre: str, texto: str) -> set:
    v = set()
    for rfc in sorted(set(RE_RFC.findall(texto)) - RFC_GENERICOS):
        v.add(f"R8:{nombre}:RFC no genérico {rfc}")
    for pat in SECRETOS:
        if pat.search(texto):
            v.add(f"R8:{nombre}:posible secreto ({pat.pattern[:24]}…)")
    return v


def archivos_texto():
    sal = subprocess.run(["git", "ls-files"], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
    nombres = sal.stdout.splitlines() if sal.returncode == 0 else [str(p.relative_to(RAIZ)) for p in RAIZ.rglob("*") if p.is_file()]
    for n in nombres:
        p = RAIZ / n
        if p.suffix in EXT_TEXTO and p.is_file() and n not in ("scripts/validar_oro.py", "scripts/deuda_oro.json") and not n.startswith("tests/"):
            yield n, p.read_text(encoding="utf-8", errors="ignore")


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--base", default=str(RAIZ / "base"))
    a.add_argument("--deuda", default=str(RAIZ / "scripts" / "deuda_oro.json"))
    a.add_argument("--actualizar-deuda", action="store_true")
    x = a.parse_args()
    base = Path(x.base)
    P = yaml.safe_load((base / "parametros.yaml").read_text(encoding="utf-8"))["parametros"]
    R = yaml.safe_load((base / "reglas.yaml").read_text(encoding="utf-8"))["reglas"]
    viol = valida(P, R)
    for n, t in archivos_texto():
        viol |= valida_texto(n, t)
    deuda_path = Path(x.deuda)
    if x.actualizar_deuda:
        deuda_path.write_text(json.dumps(sorted(viol), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"Deuda actualizada: {len(viol)} violaciones en {deuda_path}")
        return 0
    deuda = set(json.loads(deuda_path.read_text(encoding="utf-8"))) if deuda_path.exists() else set()
    nuevas, saldadas = sorted(viol - deuda), sorted(deuda - viol)
    print(f"Reglas de oro: {len(viol)} violaciones, {len(viol & deuda)} en la lista de deuda, {len(nuevas)} nuevas.")
    if nuevas:
        print("\nNUEVAS (arréglalas; un PR no puede agregarlas):\n  " + "\n  ".join(nuevas))
    if saldadas:
        print("\nSALDADAS (ya no son violación; quítalas de scripts/deuda_oro.json con --actualizar-deuda):\n  " + "\n  ".join(saldadas))
    return 1 if nuevas or saldadas else 0


if __name__ == "__main__":
    sys.exit(main())
