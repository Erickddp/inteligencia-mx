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
NIF_YAML = yaml.safe_load((RAIZ / "fuentes" / "nif" / "indice.yaml").read_text(encoding="utf-8"))
NIF = {n["id"]: n for n in NIF_YAML["nif"]}
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
    fuentes = NIF_YAML["fuentes_cotejo"]
    for n in NIF.values():
        assert n["titulo"] and n["tema"] and isinstance(n["cotejado"], bool)
        # cotejado sólo con la fuente del CINIF donde se leyó; sin cotejo, sin fuente
        assert (n.get("cotejo") in fuentes) if n["cotejado"] else ("cotejo" not in n), n["id"]


def test_nif_derogadas_no_se_citan():
    """El Marco Conceptual (A-1, 2023) sustituyó a las A-1 a A-8 viejas; la A-2 de hoy es negocio en marcha."""
    assert NIF["A-1"]["titulo"].startswith("Marco Conceptual") and NIF["A-2"]["titulo"] == "Incertidumbres sobre negocio en marcha"
    assert {"A-3", "A-8"}.isdisjoint(NIF) and len(NIF_YAML["derogadas"]) == 8
    for id_, obj in CON_CITAS:
        for c in obj["citas"]:
            assert c.get("nif") != "A-2" or id_ not in {"R-152"}, f"{id_}: la devengación está en la A-1, no en la A-2"


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


def test_indice_niif_apunta_a_nif_que_existen_y_no_se_hace_pasar_por_cotejado():
    """El índice de NIIF es referencia: ninguna NIIF está cotejada y todo equivalente en NIF existe en el índice de NIF."""
    niif = yaml.safe_load((RAIZ / "fuentes" / "niif" / "indice.yaml").read_text(encoding="utf-8"))
    ids = [n["id"] for n in niif["niif"]]
    assert len(ids) == len(set(ids)) >= 35 and {"IAS 1", "IFRS 9", "IFRS 15", "IFRS 16", "IFRS 18"} <= set(ids)
    assert all(n["cotejado"] is False for n in niif["niif"]), "la IFRS Foundation no se ha abierto: nada se marca cotejado"
    for n in niif["niif"]:
        assert n["titulo"] and n["tema"] and n["diferencia"] and n["estado"] in {"vigente", "vigente_hasta_2026", "por_confirmar"}, n["id"]
        for nif in [x.strip() for x in n["nif"].split(",") if x.strip()]:
            assert nif in NIF, f"{n['id']}: la NIF {nif} no existe en fuentes/nif/indice.yaml"
    # lo único cotejado: quién está obligado a NIIF en México (DOF, CNBV)
    cotejados = [o for o in niif["obligados"] if o["cotejado"]]
    assert any("2012-01-01" == str(o.get("desde")) and "5078507" in o["url"] for o in cotejados)
