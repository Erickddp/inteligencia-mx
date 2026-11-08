"""Datos abiertos: al día con la base, completos, con huellas correctas, y un corpus que sirve de entrada a una búsqueda."""
import csv
import hashlib
import importlib.util
import json

import pytest
import yaml

from conftest import BASE, RAIZ

spec = importlib.util.spec_from_file_location("exportar", RAIZ / "scripts" / "exportar_datos_abiertos.py")
ex = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ex)

DESTINO = RAIZ / "datos_abiertos"
ARCHIVOS = ["parametros.csv", "reglas.csv", "leyes.csv", "citas.csv", "cotejo_pendiente.csv", "catalogo.json"]


def filas(nombre):
    with open(DESTINO / nombre, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_los_datos_abiertos_estan_al_dia(tmp_path):
    ex.exportar(RAIZ, tmp_path)
    malos = [n for n in ARCHIVOS if (tmp_path / n).read_bytes() != (DESTINO / n).read_bytes()]
    assert not malos, f"datos_abiertos/ no está al día ({malos}). Regenera con: python scripts/exportar_datos_abiertos.py"


def test_son_deterministas(tmp_path):
    ex.exportar(RAIZ, tmp_path / "a")
    ex.exportar(RAIZ, tmp_path / "b")
    assert all((tmp_path / "a" / n).read_bytes() == (tmp_path / "b" / n).read_bytes() for n in ARCHIVOS)


def test_traen_todo_lo_que_hay_en_la_base():
    P = yaml.safe_load((BASE / "parametros.yaml").read_text(encoding="utf-8"))["parametros"]
    R = yaml.safe_load((BASE / "reglas.yaml").read_text(encoding="utf-8"))["reglas"]
    assert len(filas("parametros.csv")) == len(P)
    assert len(filas("reglas.csv")) == len(R)
    assert len(filas("leyes.csv")) == len([d for d in (RAIZ / "fuentes" / "leyes").iterdir() if d.is_dir()])
    assert {f["id"] for f in filas("reglas.csv")} == {r["id"] for r in R}


def test_el_catalogo_describe_cada_archivo_con_su_huella():
    cat = json.loads((DESTINO / "catalogo.json").read_text(encoding="utf-8"))
    assert cat["licencia"] == "CC BY 4.0"
    for nombre, info in cat["archivos"].items():
        assert hashlib.sha256((DESTINO / nombre).read_bytes()).hexdigest() == info["sha256"], nombre
        assert info["filas"] == len(filas(nombre)) and info["columnas"] == list(filas(nombre)[0]), nombre


def test_todas_las_citas_estructuradas_existen_en_la_biblioteca():
    citas = [c for c in filas("citas.csv") if c["existe_en_biblioteca"] != "referencia"]
    assert len(citas) >= 100
    assert all(c["existe_en_biblioteca"] == "si" for c in citas)


def test_cotejo_pendiente_esta_ordenado_por_prioridad():
    f = filas("cotejo_pendiente.csv")
    assert f and all(x["cotejado"] == "no" for x in f)
    citado = [int(x["citado_por"]) for x in f]
    assert citado == sorted(citado, reverse=True)
    top = {(x["ley"], x["articulo"]) for x in f[:5]}
    assert ("CFF", "28") in top                                              # el artículo del que más cosas dependen
    assert len(f) < 200 < sum(int(x["articulos"]) for x in filas("leyes.csv"))   # cotejar lo que se cita, no todo


def test_el_corpus_es_entrada_de_una_busqueda(tmp_path):
    salida = tmp_path / "corpus.jsonl"
    n = ex.corpus(RAIZ, salida)
    registros = [json.loads(l) for l in salida.read_text(encoding="utf-8").splitlines()]
    esperado = sum(int(x["articulos"]) for x in filas("leyes.csv")) + len(
        json.loads((RAIZ / "fuentes" / "rmf" / "2026" / "RMF2026" / "indice.json").read_text(encoding="utf-8")))
    assert n == len(registros) == esperado
    ids = [r["id"] for r in registros]
    assert len(ids) == len(set(ids))
    por_id = {r["id"]: r for r in registros}
    assert "trimestrales" in por_id["LISR:116"]["texto"] and por_id["LISR:116"]["cotejado"] is False
    assert "24 horas" in por_id["RMF2026:2.7.1.21"]["texto"] and por_id["RMF2026:2.7.1.21"]["tipo"] == "regla_rmf"
    assert por_id["CMX-CP:276-quater"]["ambito"] == "estatal" and por_id["CMX-CP:276-quater"]["entidad"] == "CMX"
    vacios = sum(1 for r in registros if not r["texto"].strip())
    assert vacios / len(registros) < 0.01


@pytest.mark.parametrize("campo", ["id", "tipo", "ley", "numero", "ambito", "materia", "cotejado", "derogado", "sha256", "texto"])
def test_cada_registro_del_corpus_trae_sus_campos(tmp_path, campo):
    salida = tmp_path / "c.jsonl"
    ex.corpus(RAIZ, salida)
    with open(salida, encoding="utf-8") as f:
        assert all(campo in json.loads(next(f)) for _ in range(3))
