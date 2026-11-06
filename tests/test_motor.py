"""Pruebas propias del motor: lo que protege la integridad de la base, no sus cifras."""
from decimal import Decimal as D

import pytest

from conftest import BASE
from timbra_reglas.motor import Base, SinValor

TARIFAS_PERIODO = [("ISR_TARIFA_SEMANAL", 7), ("ISR_TARIFA_DECENAL", 10), ("ISR_TARIFA_QUINCENAL", 15)]


def primer_tramo(datos, pid):
    return datos["parametros"][pid]["valores"][0]


def test_la_base_real_carga(base):
    assert len(base.p) > 100 and len(base.r) > 80


def test_estado_desconocido_frena_la_carga(copia):
    carpeta, edita = copia
    edita("parametros.yaml", lambda d: primer_tramo(d, "UMA_DIARIA").update(estado="aprobado_x"))
    with pytest.raises(ValueError, match="estado desconocido 'aprobado_x'"):
        Base(base_dir=carpeta)


def test_tramo_sin_fuente_frena_la_carga(copia):
    carpeta, edita = copia
    edita("parametros.yaml", lambda d: primer_tramo(d, "UMA_DIARIA").pop("fuente"))
    with pytest.raises(ValueError, match="valor sin fuente"):
        Base(base_dir=carpeta)


def test_vigencias_encimadas_frenan_la_carga(copia):
    carpeta, edita = copia
    edita("parametros.yaml", lambda d: primer_tramo(d, "UMA_DIARIA").update(hasta=None))
    with pytest.raises(ValueError, match="vigencias encimadas"):
        Base(base_dir=carpeta)


def test_tramo_pendiente_de_dof_no_se_aplica(base):
    # RESICO PF: el tope de 5 M está aprobado por el Congreso, sin DOF: sigue valiendo 3.5 M
    d = base.detalle("RESICO_PF_TOPE_ANUAL", "2027-01-15")
    assert D(str(d["valor"])) == D("3500000")
    assert d["reforma_pendiente"]["estado"] == "aprobado_congreso_pendiente_dof"
    # solo entra al simular
    assert Base(base_dir=BASE, propuestas=True).valor("RESICO_PF_TOPE_ANUAL", "2027-01-15") == D("5000000")


def test_solo_pendiente_da_sin_valor_y_avisa(base):
    # ISR_RET_INTERESES: solo hay tramo 2027 pendiente; no se aplica
    with pytest.raises(SinValor, match="no se aplica sin DOF"):
        base.valor("ISR_RET_INTERESES", "2027-06-30")


def test_estados_de_los_tramos_son_validos(base):
    validos = {"vigente", "por_confirmar", "propuesta", "aprobado_congreso_pendiente_dof"}
    estados = {v.get("estado", "vigente") for p in base.p.values() for v in p.get("valores", [])}
    assert estados <= validos


@pytest.mark.parametrize("tabla,dias", TARIFAS_PERIODO)
def test_tarifa_periodica_es_diaria_por_dias(base, tabla, dias):
    diaria, otra = base.valor("ISR_TARIFA_DIARIA", "2026-06-30"), base.valor(tabla, "2026-06-30")
    assert len(diaria) == len(otra)
    n = D(dias)
    cent = D("0.01")
    for (_, ls, c, p), (_, ls2, c2, p2) in zip(diaria, otra):
        assert p == p2
        assert (c * n).quantize(cent) == c2
        assert (ls is None and ls2 is None) or (ls * n).quantize(cent) == ls2


def test_renglones_de_tarifa_contiguos_en_la_base_real(base):
    for pid, p in base.p.items():
        if p.get("tipo") == "tabla" and p.get("columnas", [])[:2] == ["limite_inferior", "limite_superior"]:
            for v in p["valores"]:
                for f1, f2 in zip(v["valor"], v["valor"][1:]):
                    assert D(f1[1]) + D("0.01") == D(f2[0]), f"{pid} {v['desde']}"


def test_renglon_no_contiguo_frena_la_carga(copia):
    carpeta, edita = copia

    def rompe(d):
        d["parametros"]["ISR_TARIFA_MENSUAL"]["valores"][-1]["valor"][1][0] = "999.99"

    edita("parametros.yaml", rompe)
    with pytest.raises(ValueError, match="renglones no contiguos"):
        Base(base_dir=carpeta)


def test_ids_de_regla_unicos(base):
    ids = [r["id"] for r in base.r]
    assert len(ids) == len(set(ids))


def test_id_de_regla_repetido_frena_la_carga(copia):
    carpeta, edita = copia
    edita("reglas.yaml", lambda d: d["reglas"].append(dict(d["reglas"][0])))
    with pytest.raises(ValueError, match="repetida"):
        Base(base_dir=carpeta)


def test_numeros_como_texto_nunca_float(base):
    def sin_float(x, donde):
        assert not isinstance(x, float), donde
        if isinstance(x, list):
            for i in x:
                sin_float(i, donde)
        elif isinstance(x, dict):
            for i in x.values():
                sin_float(i, donde)

    for pid, p in base.p.items():
        for v in p.get("valores", []):
            sin_float(v.get("valor"), f"{pid} {v['desde']}")
