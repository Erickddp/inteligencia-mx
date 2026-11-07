"""integracion_vX.json: el contrato que las apps leen para tomar una versión nueva sin revisar a mano."""
import importlib.util
import json
import shutil

import yaml

from conftest import BASE, RAIZ

spec = importlib.util.spec_from_file_location("integracion", RAIZ / "scripts" / "integracion.py")
integ = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integ)


def copia(tmp_path, nombre):
    d = tmp_path / nombre
    d.mkdir()
    for f in ("parametros.yaml", "reglas.yaml"):
        shutil.copy(BASE / f, d / f)
    return d


def edita(d, archivo, fn):
    p = d / archivo
    datos = yaml.safe_load(p.read_text(encoding="utf-8"))
    fn(datos)
    p.write_text(yaml.safe_dump(datos, allow_unicode=True, sort_keys=False), encoding="utf-8")


def test_hash_valor_es_el_de_las_firmas_de_timbra():
    h = integ.hash_valor("UMA_DIARIA", "2026-02-01", "117.31")
    assert h.startswith("ae87431e") and h.endswith("6a8b07")


def test_sin_cambios_no_afecta_ningun_id(tmp_path):
    d = integ.integracion(copia(tmp_path, "a"), BASE, "0.4.2", "abc", {"motor.py": "x"}, "90 pasan")
    assert d["schema"] == 1 and d["tag"] == "v0.4.2" and d["commit"] == "abc" and d["huellas"] == {"motor.py": "x"}
    assert d["ids_afectados"] == [] and d["firmas_que_se_caen"] == [] and d["valores_cambiados"] == []


def test_detecta_todo_y_las_firmas_que_se_caen(tmp_path):
    ant, nue = copia(tmp_path, "a"), copia(tmp_path, "b")

    def cambia(p):
        uma = p["parametros"]["UMA_DIARIA"]["valores"]
        uma[0]["valor"] = "999.99"                                              # valor publicado editado
        uma.append({"valor": "120.00", "desde": "2099-01-01", "hasta": None, "fuente": "x", "estado": "propuesta"})
        p["parametros"]["IVA_TASA_GENERAL"]["valores"][0]["estado"] = "por_confirmar"
        p["parametros"]["IVA_TASA_GENERAL"]["valores"][0]["confirmado_hasta"] = "2030-12-31"
        p["parametros"]["PARAM_NUEVO"] = {"nombre": "Nuevo", "tipo": "importe", "valores": [{"valor": "1", "desde": "2027-01-01", "hasta": None, "fuente": "x"}]}

    def regla(r):
        r["reglas"][0]["estado"] = "CORREGIR"
        r["reglas"].append({"id": "R-998", "nombre": "nueva", "estado": "NUEVA", "fase": 1, "calculadora": "calc_nueva_x", "parametros": ["PARAM_NUEVO"]})

    edita(nue, "parametros.yaml", cambia)
    edita(nue, "reglas.yaml", regla)
    d = integ.integracion(ant, nue, "0.5.0", "c0ffee")
    v = d["valores_cambiados"][0]
    assert v["id"] == "UMA_DIARIA" and v["despues"] == "999.99" and v["antes"] != v["despues"]
    assert v["hash_antes"] != v["hash_despues"]
    assert d["firmas_que_se_caen"][0] == {"id": "UMA_DIARIA", "desde": v["desde"], "hash_antes": v["hash_antes"]}
    assert {"id": "UMA_DIARIA", "desde": "2099-01-01", "hasta": None, "confirmado_hasta": None, "estado": "propuesta", "fuente": "x"} in d["tramos_nuevos"]
    assert any(e["id"] == "IVA_TASA_GENERAL" and e["despues"] == "por_confirmar" for e in d["estados_cambiados"])
    assert any(e["id"] == "IVA_TASA_GENERAL" for e in d["vigencias_cambiadas"])
    assert [p["id"] for p in d["parametros_nuevos"]] == ["PARAM_NUEVO"]
    assert d["reglas_nuevas"][0]["id"] == "R-998" and d["reglas_estado"][0]["despues"] == "CORREGIR"
    assert "calc_nueva_x" in d["calculadoras_nuevas"]
    assert {"UMA_DIARIA", "IVA_TASA_GENERAL", "PARAM_NUEVO", "R-998"} <= set(d["ids_afectados"])
    json.dumps(d, default=str)                                                 # serializable


def test_formula_cambiada_cae_la_firma(tmp_path):
    ant, nue = copia(tmp_path, "a"), copia(tmp_path, "b")
    edita(nue, "parametros.yaml", lambda p: p["parametros"]["UMA_MENSUAL"].update(formula="UMA_DIARIA * 30"))
    d = integ.integracion(ant, nue, "0.5.0")
    assert d["formulas_cambiadas"][0]["id"] == "UMA_MENSUAL" and "UMA_MENSUAL" in d["ids_afectados"]
    assert d["firmas_que_se_caen"] == [{"id": "UMA_MENSUAL", "desde": None, "hash_antes": None}]


def test_primera_version_sin_anterior(tmp_path):
    d = integ.integracion(None, BASE, "0.4.1")
    assert d["anterior"] is None and d["ids_afectados"] == [] and d["parametros_nuevos"] == []
