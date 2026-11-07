"""Series (INPC): sin huecos, sin saltos raros, y cada cifra del DOF cuadra con Banxico."""
import csv
from decimal import Decimal

import yaml

from conftest import RAIZ

SERIE = yaml.safe_load((RAIZ / "series" / "inpc.yaml").read_text(encoding="utf-8"))
BANXICO = {r["mes"]: Decimal(r["inpc_general"]) for r in csv.DictReader(open(RAIZ / "fuentes" / "evidencia" / "inpc_banxico" / "inpc.csv", encoding="utf-8"))}
V = SERIE["valores"]


def siguiente(m):
    a, mes = map(int, m.split("-"))
    return f"{a + (mes == 12)}-{(mes % 12) + 1:02d}"


def test_sin_huecos_ni_duplicados():
    meses = list(V)
    assert len(meses) == len(set(meses))
    assert meses[0] == SERIE["cobertura"]["desde"] and meses[-1] == SERIE["cobertura"]["hasta"]
    for a, b in zip(meses, meses[1:]):
        assert siguiente(a) == b, f"hueco entre {a} y {b}"


def test_cifras_son_texto_con_decimales_y_sin_saltos_mayores_a_5_por_ciento():
    previo = None
    for mes, d in V.items():
        assert isinstance(d["valor"], str), mes
        x = Decimal(d["valor"])
        if previo:
            assert abs(x / previo - 1) < Decimal("0.05"), f"salto raro en {mes}"
        previo = x


def test_cada_mes_cuadra_con_banxico():
    for mes, d in V.items():
        assert Decimal(d["valor"]) == BANXICO[mes], mes


def test_cada_cifra_del_dof_trae_su_nota_y_la_de_banxico_no_se_hace_pasar_por_dof():
    for mes, d in V.items():
        if d["fuente"] == "dof":
            assert d["dof"].startswith("https://dof.gob.mx/nota_detalle.php?codigo="), mes
            assert d["via"] in {"mes_publicado", "anexo_conceptos", "mes_anterior_citado"}
        else:
            assert d["fuente"] == "banxico_sp1" and d["cotejado_dof"] is False, mes
            assert "dof" not in d


def test_base_del_indice_es_2018():
    assert "2018" in SERIE["base"] and SERIE["unidad"] == "puntos"
