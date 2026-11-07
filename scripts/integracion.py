#!/usr/bin/env python3
"""integracion_vX.json: lo que una app necesita saber de una versión para tomarla sola.

  python scripts/integracion.py --anterior DIR_BASE_ANTERIOR --nuevo base --version 0.5.0 [--commit SHA] > integracion.json

Lo genera release.py en cada release. Contrato (schema 1), todo en JSON:
  version, commit, tag, generado, anterior (version_base anterior o null), huellas {ruta en el paquete: sha256},
  assets {ruta en el paquete: nombre del asset en el release}, pruebas,
  parametros_nuevos, parametros_quitados, tramos_nuevos, valores_cambiados (antes y después, con las huellas
  del valor), formulas_cambiadas, vigencias_cambiadas, estados_cambiados, reglas_nuevas, reglas_quitadas,
  reglas_estado, calculadoras_nuevas, meta_cambiada (citas, que_dice, correcto_si), firmas_que_se_caen y ids_afectados (todos los IDs tocados).

hash_valor usa la misma fórmula que las firmas de Timbra (parámetro + desde + valor), para que la app
sepa EXACTAMENTE qué firma se cae.
"""
import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

SCHEMA = 1
META = ("citas", "que_dice", "correcto_si")  # lo que el círculo de fundamento de las apps lee de cada ID


def carga(d: Path):
    P = yaml.safe_load((d / "parametros.yaml").read_text(encoding="utf-8"))
    R = yaml.safe_load((d / "reglas.yaml").read_text(encoding="utf-8"))
    return P["parametros"], {r["id"]: r for r in R["reglas"]}, P.get("version_base")


def hash_valor(pid: str, desde: str, valor) -> str:
    """Misma huella que las firmas de Timbra: param + desde + valor, sin hasta, fuente ni estado."""
    s = json.dumps({"param": pid, "desde": str(desde), "valor": valor}, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def integracion(ant: Path | None, nue: Path, version: str, commit: str = "", huellas: dict | None = None,
                pruebas: str = "", generado: str | None = None, assets: dict | None = None) -> dict:
    Pn, Rn, _ = carga(nue)
    Pa, Ra, vant = carga(ant) if ant else ({}, {}, None)
    out = {"schema": SCHEMA, "version": version, "tag": f"v{version}", "commit": commit,
           "generado": generado or dt.date.today().isoformat(), "anterior": vant, "huellas": huellas or {}, "assets": assets or {}, "pruebas": pruebas,
           "parametros_nuevos": [{"id": i, "nombre": Pn[i].get("nombre"), "tipo": Pn[i].get("tipo"), "formula": Pn[i].get("formula")}
                                 for i in sorted(set(Pn) - set(Pa))] if ant else [],
           "parametros_quitados": sorted(set(Pa) - set(Pn)),
           "tramos_nuevos": [], "valores_cambiados": [], "formulas_cambiadas": [], "vigencias_cambiadas": [],
           "estados_cambiados": [], "reglas_nuevas": [], "reglas_quitadas": sorted(set(Ra) - set(Rn)), "reglas_estado": [],
           "calculadoras_nuevas": [], "meta_cambiada": [], "firmas_que_se_caen": [], "ids_afectados": []}
    if not ant:
        return out
    for pid in sorted(set(Pa) & set(Pn)):
        ta = {v["desde"]: v for v in Pa[pid].get("valores", [])}
        tn = {v["desde"]: v for v in Pn[pid].get("valores", [])}
        for d in sorted(set(tn) - set(ta)):
            t = tn[d]
            out["tramos_nuevos"].append({"id": pid, "desde": d, "hasta": t.get("hasta"), "confirmado_hasta": t.get("confirmado_hasta"),
                                         "estado": t.get("estado", "vigente"), "fuente": t.get("fuente")})
        for d in sorted(set(ta) & set(tn)):
            a, n = ta[d], tn[d]
            if a.get("valor") != n.get("valor"):
                out["valores_cambiados"].append({"id": pid, "desde": d, "antes": a.get("valor"), "despues": n.get("valor"),
                                                 "hash_antes": hash_valor(pid, d, a.get("valor")), "hash_despues": hash_valor(pid, d, n.get("valor"))})
                out["firmas_que_se_caen"].append({"id": pid, "desde": d, "hash_antes": hash_valor(pid, d, a.get("valor"))})
            va = {"hasta": a.get("hasta"), "confirmado_hasta": a.get("confirmado_hasta")}
            vn = {"hasta": n.get("hasta"), "confirmado_hasta": n.get("confirmado_hasta")}
            if va != vn:
                out["vigencias_cambiadas"].append({"id": pid, "desde": d, "antes": va, "despues": vn})
            ea, en = a.get("estado", "vigente"), n.get("estado", "vigente")
            if ea != en:
                out["estados_cambiados"].append({"id": pid, "desde": d, "antes": ea, "despues": en})
        if Pa[pid].get("formula") != Pn[pid].get("formula"):
            out["formulas_cambiadas"].append({"id": pid, "antes": Pa[pid].get("formula"), "despues": Pn[pid].get("formula")})
            out["firmas_que_se_caen"].append({"id": pid, "desde": None, "hash_antes": None})
    for i in sorted((set(Pa) & set(Pn)) | (set(Ra) & set(Rn))):
        a, n = (Pa[i], Pn[i]) if i in Pn else (Ra[i], Rn[i])
        for campo in META:
            if a.get(campo) != n.get(campo):
                out["meta_cambiada"].append({"id": i, "campo": campo, "antes": a.get(campo), "despues": n.get(campo)})
    for rid in sorted(set(Rn) - set(Ra)):
        r = Rn[rid]
        out["reglas_nuevas"].append({"id": rid, "nombre": r.get("nombre"), "estado": r.get("estado"), "calculadora": r.get("calculadora"),
                                     "parametros": r.get("parametros", []), "casos": len(r.get("casos", []))})
    for rid in sorted(set(Ra) & set(Rn)):
        if Ra[rid].get("estado") != Rn[rid].get("estado"):
            out["reglas_estado"].append({"id": rid, "antes": Ra[rid].get("estado"), "despues": Rn[rid].get("estado")})
    out["calculadoras_nuevas"] = sorted({r.get("calculadora") for r in Rn.values() if r.get("calculadora")}
                                        - {r.get("calculadora") for r in Ra.values() if r.get("calculadora")})
    ids = set(out["parametros_quitados"]) | {x["id"] for k in ("parametros_nuevos", "tramos_nuevos", "valores_cambiados", "formulas_cambiadas",
                                                                  "vigencias_cambiadas", "estados_cambiados", "meta_cambiada") for x in out[k]}
    ids |= set(out["reglas_quitadas"]) | {x["id"] for k in ("reglas_nuevas", "reglas_estado") for x in out[k]}
    out["ids_afectados"] = sorted(ids)
    return out


def commit_actual() -> str:
    r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=Path(__file__).resolve().parent.parent)
    return r.stdout.strip() if r.returncode == 0 else ""


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--anterior")
    a.add_argument("--nuevo", default=str(Path(__file__).resolve().parent.parent / "base"))
    a.add_argument("--version", required=True)
    a.add_argument("--commit", default="")
    x = a.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(integracion(Path(x.anterior) if x.anterior else None, Path(x.nuevo), x.version, x.commit or commit_actual()),
                     ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
