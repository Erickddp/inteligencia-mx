"""Pruebas de los scripts del CI: reglas de oro, diferencias del PR y verificación del tag."""
import copy
import importlib.util
import json
import shutil

import pytest
import yaml

from conftest import BASE, RAIZ


def carga(nombre):
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / "scripts" / f"{nombre}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


oro, dif_pr, tag = carga("validar_oro"), carga("diff_pr"), carga("verificar_tag")


@pytest.fixture(scope="module")
def datos():
    P = yaml.safe_load((BASE / "parametros.yaml").read_text(encoding="utf-8"))["parametros"]
    R = yaml.safe_load((BASE / "reglas.yaml").read_text(encoding="utf-8"))["reglas"]
    return P, R


def deuda():
    return set(json.loads((RAIZ / "scripts" / "deuda_oro.json").read_text(encoding="utf-8")))


def test_la_base_actual_no_trae_violaciones_fuera_de_la_deuda(datos):
    assert oro.valida(*datos) <= deuda()


def test_la_deuda_no_tiene_entradas_viejas(datos):
    vivas = oro.valida(*datos)
    for nombre, texto in oro.archivos_texto():
        vivas |= oro.valida_texto(nombre, texto)
    assert deuda() - vivas == set()


def test_id_con_anio_se_detecta(datos):
    P, R = copy.deepcopy(datos[0]), datos[1]
    P["UMA_2027"] = P["UMA_DIARIA"]
    P["TOPE_ENE"] = P["UMA_DIARIA"]
    nuevas = oro.valida(P, R) - deuda()
    assert any("UMA_2027" in n for n in nuevas) and any("TOPE_ENE" in n for n in nuevas)


@pytest.mark.parametrize("sano", ["IVA_TASA_GENERAL", "UMA_DIARIA", "ISR_TARIFA_ACUMULADA_106", "RECARGOS_PARCIALIDADES_12"])
def test_ids_sanos_no_se_marcan(sano):
    assert not oro.RE_ANIO_MES.search(sano)


def test_float_sin_fuente_y_sin_confirmado_se_detectan(datos):
    P, R = copy.deepcopy(datos[0]), copy.deepcopy(datos[1])
    P["NUEVO_PARAM"] = {"nombre": "x", "tipo": "importe", "valores": [{"valor": 1.5, "desde": "2027-01-01", "hasta": None}]}
    nuevas = oro.valida(P, R) - deuda()
    assert {"R1:NUEVO_PARAM@2027-01-01:tramo sin fuente", "R7:NUEVO_PARAM@2027-01-01:número float en el valor",
            "R5:NUEVO_PARAM@2027-01-01:hasta null sin confirmado_hasta"} <= nuevas


def test_regla_con_numero_sin_dos_casos(datos):
    P, R = datos[0], copy.deepcopy(datos[1])
    R.append({"id": "R-999", "nombre": "x", "calculadora": "parametro", "casos": [{"nombre": "uno", "fecha": "2026-01-01", "entradas": {"id": "UMA_DIARIA"}, "esperado": "1"}]})
    assert "R6:R-999:calculadora con menos de 2 casos" in oro.valida(P, R)


def test_rfc_real_y_secretos_se_detectan_pero_no_los_genericos():
    assert not oro.valida_texto("a.yaml", "rfc: XAXX010101000 y AAA010101AAA")
    assert any("RFC no genérico" in v for v in oro.valida_texto("a.yaml", "rfc: GOMA850317H23"))
    assert any("secreto" in v for v in oro.valida_texto("a.md", "token: ghp_" + "a" * 36))
    assert any("secreto" in v for v in oro.valida_texto("a.md", "-----BEGIN PRIVATE KEY-----"))


def test_el_repo_no_trae_secretos_ni_rfc_nuevos():
    violaciones = set()
    for nombre, texto in oro.archivos_texto():
        violaciones |= oro.valida_texto(nombre, texto)
    assert violaciones - deuda() == set()


def copia_base(tmp_path, nombre):
    d = tmp_path / nombre
    d.mkdir()
    for f in ("parametros.yaml", "reglas.yaml"):
        shutil.copy(BASE / f, d / f)
    return d


def test_diff_sin_cambios(tmp_path):
    dif = dif_pr.carga_release().compara(copia_base(tmp_path, "a"), BASE)
    md = dif_pr.markdown(dif)
    assert dif_pr.MARCA in md and "Sin cambios" in md


def test_diff_detecta_valor_tramo_estado_y_regla(tmp_path):
    ant = copia_base(tmp_path, "a")
    nue = copia_base(tmp_path, "b")
    p = yaml.safe_load((nue / "parametros.yaml").read_text(encoding="utf-8"))
    uma = p["parametros"]["UMA_DIARIA"]["valores"]
    uma[0]["valor"] = "999.99"                                          # valor publicado editado = firma que se cae
    uma.append({"valor": "120.00", "desde": "2099-01-01", "hasta": None, "fuente": "x", "estado": "propuesta"})
    p["parametros"]["IVA_TASA_GENERAL"]["valores"][0]["estado"] = "por_confirmar"
    (nue / "parametros.yaml").write_text(yaml.safe_dump(p, allow_unicode=True, sort_keys=False), encoding="utf-8")
    r = yaml.safe_load((nue / "reglas.yaml").read_text(encoding="utf-8"))
    r["reglas"].append({"id": "R-998", "nombre": "nueva", "estado": "NUEVA", "fase": 1})
    (nue / "reglas.yaml").write_text(yaml.safe_dump(r, allow_unicode=True, sort_keys=False), encoding="utf-8")
    md = dif_pr.markdown(dif_pr.carga_release().compara(ant, nue))
    assert "UMA_DIARIA desde" in md and "firmas que se caen" in md
    assert "UMA_DIARIA desde 2099-01-01 (propuesta)" in md
    assert "IVA_TASA_GENERAL" in md and "vigente -> por_confirmar" in md
    assert "R-998" in md


def test_tag_coincide_con_la_base():
    v = tag.versiones()
    assert len(set(v.values())) == 1
    version = next(iter(v.values()))
    assert tag.verifica(f"v{version}") == []


@pytest.mark.parametrize("malo", ["0.4.1", "v0.4", "v0.4.1-rc1", "vX.Y.Z", "v9.9.9"])
def test_tag_que_no_coincide_falla(malo):
    assert tag.verifica(malo)


def test_release_publica_los_cuatro_archivos_con_nombre_plano_ademas_del_sufijo(tmp_path):
    """Timbra baja los 4 archivos del release por su nombre (sin sufijo) y compara huellas; el workflow usa los de sufijo para las diferencias."""
    import hashlib
    import shutil
    import subprocess
    import sys
    raiz = tmp_path / "raiz"
    shutil.copytree(BASE, raiz / "base")
    (raiz / "timbra_reglas").mkdir()
    for f in (RAIZ / "timbra_reglas").glob("*.py"):
        shutil.copy(f, raiz / "timbra_reglas" / f.name)
    shutil.copytree(RAIZ / "scripts", raiz / "scripts")
    shutil.copytree(RAIZ / "series", raiz / "series")
    out = tmp_path / "out"
    r = subprocess.run([sys.executable, str(raiz / "scripts" / "release.py"), "--raiz", str(raiz), "--version", "9.9.9", "--out", str(out)],
                       capture_output=True, text=True, env={**__import__("os").environ, "PYTHONPATH": str(raiz)})
    assert r.returncode == 0, r.stdout + r.stderr
    for nombre in ("parametros.yaml", "reglas.yaml", "motor.py", "FASES.md"):
        stem, suf = nombre.rsplit(".", 1)
        plano, con_sufijo = out / nombre, out / f"{stem}_v9.9.9.{suf}"
        assert plano.read_bytes() == con_sufijo.read_bytes()
    sumas = dict(l.split("  ")[::-1] for l in (out / "SHA256SUMS").read_text(encoding="utf-8").splitlines())
    # contrato: 4 archivos + series/*.yaml (la serie con su ruta; el asset plano del release se llama series_<id>.yaml)
    series = {f"series/{p.name}" for p in (RAIZ / "series").glob("*.yaml")}
    assert set(sumas) == {"parametros.yaml", "reglas.yaml", "motor.py", "FASES.md"} | series and "series/dias_inhabiles.yaml" in series
    for nombre, h in sumas.items():
        assert hashlib.sha256((out / nombre).read_bytes()).hexdigest() == h
