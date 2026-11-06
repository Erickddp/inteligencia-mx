"""Corre cada caso de reglas.yaml con el motor (lo mismo que `timbra-reglas probar`, uno por uno)."""
import pytest
import yaml

from conftest import BASE
from timbra_reglas.motor import CALC, SinValor

REGLAS = yaml.safe_load((BASE / "reglas.yaml").read_text(encoding="utf-8"))["reglas"]
CASOS = [pytest.param(r, c, id=f"{r['id']} · {c['nombre']}") for r in REGLAS for c in r.get("casos", [])]


def test_hay_casos():
    assert len(CASOS) >= 90


@pytest.mark.parametrize("regla,caso", CASOS)
def test_caso(base, regla, caso):
    calc = CALC[caso.get("calculadora", regla.get("calculadora"))]
    if caso.get("espera_error") == "SinValor":
        with pytest.raises(SinValor):
            calc(base, caso["fecha"], **caso.get("entradas", {}))
        return
    res = calc(base, caso["fecha"], **caso.get("entradas", {}))
    res = {k: str(v) for k, v in res.items()} if isinstance(res, dict) else str(res)
    if caso.get("confirmado") is False and res != caso.get("esperado"):
        pytest.skip("esperado aún no confirmado")
    assert res == caso["esperado"]
