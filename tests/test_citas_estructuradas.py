"""Citas estructuradas (`citas`), `que_dice` y `correcto_si`: lo que el círculo de fundamento de las apps lee.

Una cita es una de estas formas (con la misma clave de ley y de artículo que el índice de fuentes/leyes/):
  {ley: LISR, articulo: "106", fraccion: null, parrafo: null}
  {ley: RMF, anio: "2026", articulo: "2.8.1.6"}
  {nif: "C-3"}
"""
import json

import pytest
import yaml

from conftest import BASE, RAIZ

LLAVES = {"ley", "articulo", "fraccion", "parrafo", "anio", "nif"}
NIF = {n["id"]: n for n in yaml.safe_load((RAIZ / "fuentes" / "nif" / "indice.yaml").read_text(encoding="utf-8"))["nif"]}
REGLAS = yaml.safe_load((BASE / "reglas.yaml").read_text(encoding="utf-8"))["reglas"]
PARAMS = yaml.safe_load((BASE / "parametros.yaml").read_text(encoding="utf-8"))["parametros"]
CON_CITAS = [(r["id"], r) for r in REGLAS if r.get("citas")] + [(i, p) for i, p in PARAMS.items() if p.get("citas")]


def indice_de(ley, anio=None):
    if ley == "RMF":
        return json.loads((RAIZ / "fuentes" / "rmf" / str(anio) / f"RMF{anio}" / "indice.json").read_text(encoding="utf-8"))
    return json.loads((RAIZ / "fuentes" / "leyes" / ley / "indice.json").read_text(encoding="utf-8"))


def test_indice_de_nif():
    ids = [n["id"] for n in NIF.values()]
    assert len(ids) == len(set(ids)) and len(NIF) >= 40
    for n in NIF.values():
        assert n["titulo"] and n["tema"] and n["cotejado"] is False


def test_hay_reglas_con_citas_estructuradas():
    assert len(CON_CITAS) >= 6


@pytest.mark.parametrize("id_,obj", CON_CITAS, ids=[i for i, _ in CON_CITAS])
def test_citas_resuelven(id_, obj):
    for c in obj["citas"]:
        assert set(c) <= LLAVES, f"{id_}: llaves desconocidas en {c}"
        if "nif" in c:
            assert c["nif"] in NIF, f"{id_}: la NIF {c['nif']} no está en fuentes/nif/indice.yaml"
        else:
            assert c.get("ley") and c.get("articulo"), f"{id_}: la cita {c} necesita ley y articulo"
            assert str(c["articulo"]) in indice_de(c["ley"], c.get("anio")), f"{id_}: {c} no existe en la biblioteca"


@pytest.mark.parametrize("id_,obj", CON_CITAS, ids=[i for i, _ in CON_CITAS])
def test_con_citas_dice_que_dice_y_cuando_es_correcto(id_, obj):
    assert obj.get("que_dice") and obj.get("correcto_si"), f"{id_}: con `citas` también van `que_dice` y `correcto_si`"
