"""Código agrupador del SAT: el catálogo es consistente y todo concepto de las pólizas tipo apunta a un código que existe."""
import re

import yaml

from conftest import BASE
from timbra_reglas.motor import Base

PARAMS = yaml.safe_load((BASE / "parametros.yaml").read_text(encoding="utf-8"))["parametros"]
REGLAS = {r["id"]: r for r in yaml.safe_load((BASE / "reglas.yaml").read_text(encoding="utf-8"))["reglas"]}
CATALOGO_2014 = PARAMS["CONTA_CODIGO_AGRUPADOR"]["valores"][0]["valor"]
CATALOGO = PARAMS["CONTA_CODIGO_AGRUPADOR"]["valores"][-1]["valor"]   # el vigente: Anexo 24 de la RMF 2026
MAPA = PARAMS["CONTA_CONCEPTO_AGRUPADOR"]["valores"][0]["valor"]
POLIZAS = ["R-150", "R-151", "R-152", "R-153", "R-154", "R-155", "R-156", "R-157", "R-171"]


def test_catalogo_completo_y_unico():
    codigos = [c for c, _, _ in CATALOGO]
    assert len(codigos) == len(set(codigos)) == 1080
    assert {nv for _, _, nv in CATALOGO} == {"", "1", "2"}
    assert sum(1 for _, _, nv in CATALOGO if nv == "") == 13          # 12 rubros + 000 (sector financiero, nivel n*)
    assert sum(1 for _, _, nv in CATALOGO if nv == "1") == 139        # cuentas
    assert sum(1 for _, _, nv in CATALOGO if nv == "2") == 928        # subcuentas (924 de 2014 + 4 de zona fronteriza norte)


def test_diferencias_2014_contra_anexo_24_de_2026():
    a = {c: n for c, n, _ in CATALOGO_2014}
    b = {c: n for c, n, _ in CATALOGO}
    assert set(b) - set(a) == {"000", "401.39", "401.40", "401.41", "402.05"} and not set(a) - set(b)
    # sólo cambia la escritura: «diesel» → «diésel» (111, 111.01) e «infonavit» → «INFONAVIT»
    assert {c for c in a if c in b and a[c] != b[c]} == {'111.01', '602.27', '601.27', '605.29', '211.03', '604.27', '603.27', '111'}
    assert all(a[c].lower().replace("diesel", "diésel") == b[c].lower() for c in a if c in b)


def test_estructura_de_los_codigos():
    for codigo, nombre, nivel in CATALOGO:
        assert nombre.strip() and re.fullmatch(r"\d{3}(\.\d{2})?", codigo), codigo
        if nivel == "1":
            assert re.fullmatch(r"\d{3}", codigo), codigo
        if nivel == "2":
            assert re.fullmatch(r"\d{3}\.\d{2}", codigo), codigo
    cuentas = {c for c, _, nv in CATALOGO if nv == "1"}
    assert all(c.split(".")[0] in cuentas for c, _, nv in CATALOGO if nv == "2")      # toda subcuenta cuelga de una cuenta


def test_el_catalogo_2014_queda_por_confirmar_y_el_de_2026_es_vigente():
    viejo, nuevo = PARAMS["CONTA_CODIGO_AGRUPADOR"]["valores"][0], PARAMS["CONTA_CODIGO_AGRUPADOR"]["valores"][-1]
    assert viejo["estado"] == "por_confirmar" and "2014" in viejo["fuente"] and viejo["hasta"] == "2025-12-31"
    assert nuevo.get("estado", "vigente") == "vigente" and "5778160" in nuevo["fuente"]
    b = Base(base_dir=BASE)
    assert b.detalle("CONTA_CODIGO_AGRUPADOR", "2025-06-30")["estado"] == "arrastrado"
    assert b.detalle("CONTA_CODIGO_AGRUPADOR", "2026-06-30")["estado"] == "vigente"


def test_cada_codigo_del_mapa_existe_en_el_catalogo():
    existentes = {c for c, _, _ in CATALOGO}
    for concepto, contexto, codigo, _ in MAPA:
        assert codigo in existentes, f"{concepto}/{contexto}: {codigo} no existe en el catálogo del SAT"


def test_todo_concepto_de_las_polizas_tiene_agrupador():
    usados = set()
    for rid in POLIZAS:
        for caso in REGLAS[rid].get("casos", []):
            if isinstance(caso.get("esperado"), str):
                usados |= set(re.findall(r"(?:^|; )[DH] ([a-z_0-9]+) ", caso["esperado"]))
    assert len(usados) >= 25
    mapeados = {c for c, ctx, _, _ in MAPA if ctx == ""}
    assert usados <= mapeados, f"conceptos sin código agrupador: {sorted(usados - mapeados)}"
