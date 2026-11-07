"""meta_cambiada: cambios de `citas`, `que_dice` y `correcto_si` viajan en integracion_vX.json."""
import importlib.util
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


def test_sin_cambios_no_hay_meta(tmp_path):
    assert integ.integracion(copia(tmp_path, "a"), BASE, "0.4.2")["meta_cambiada"] == []


def test_cambios_de_citas_que_dice_y_correcto_si(tmp_path):
    ant, nue = copia(tmp_path, "a"), copia(tmp_path, "b")

    def regla(r):
        x = next(i for i in r["reglas"] if i["id"] == "R-150")
        x["que_dice"] = "otro texto"
        x["citas"] = [{"ley": "CFF", "articulo": "28"}]
        x.pop("correcto_si")

    def param(p):
        p["parametros"]["UMA_DIARIA"]["que_dice"] = "La UMA diaria es la base de topes y multas."

    edita(nue, "reglas.yaml", regla)
    edita(nue, "parametros.yaml", param)
    d = integ.integracion(ant, nue, "0.5.0")
    cambios = {(m["id"], m["campo"]) for m in d["meta_cambiada"]}
    assert cambios == {("R-150", "que_dice"), ("R-150", "citas"), ("R-150", "correcto_si"), ("UMA_DIARIA", "que_dice")}
    assert {"R-150", "UMA_DIARIA"} <= set(d["ids_afectados"])
    assert d["firmas_que_se_caen"] == []        # texto de apoyo: no es un valor, no tira firmas
