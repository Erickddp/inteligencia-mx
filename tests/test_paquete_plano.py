"""El paquete plano de un release debe funcionar SOLO: 4 archivos + series/*.yaml, sin el repositorio al lado."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import zipfile

import pytest

from conftest import BASE, RAIZ

spec = importlib.util.spec_from_file_location("probar_paquete", RAIZ / "scripts" / "probar_paquete.py")
pp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pp)


@pytest.fixture(scope="module")
def paquete(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("rel")
    raiz = tmp / "raiz"
    shutil.copytree(BASE, raiz / "base")
    (raiz / "timbra_reglas").mkdir()
    for f in (RAIZ / "timbra_reglas").glob("*.py"):
        shutil.copy(f, raiz / "timbra_reglas" / f.name)
    shutil.copytree(RAIZ / "scripts", raiz / "scripts")
    shutil.copytree(RAIZ / "series", raiz / "series")
    out = tmp / "out"
    r = subprocess.run([sys.executable, str(raiz / "scripts" / "release.py"), "--raiz", str(raiz), "--version", "9.9.9", "--out", str(out)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "PYTHONPATH": str(raiz), "PYTHONUTF8": "1"})
    assert r.returncode == 0, r.stdout + r.stderr
    return out


def test_las_series_van_en_sha256sums_zip_y_assets(paquete):
    sumas = (paquete / "SHA256SUMS").read_text(encoding="utf-8")
    assert "series/inpc.yaml" in sumas and "\r" not in sumas
    assert (paquete / "series" / "inpc.yaml").read_bytes() == (RAIZ / "series" / "inpc.yaml").read_bytes()
    assert (paquete / "series_inpc.yaml").read_bytes() == (RAIZ / "series" / "inpc.yaml").read_bytes()   # asset plano del release
    assert "series/inpc.yaml" in zipfile.ZipFile(paquete / "timbra-reglas-v9.9.9.zip").namelist()


def test_integracion_trae_huellas_y_assets_de_las_series(paquete):
    d = json.loads((paquete / "integracion_v9.9.9.json").read_text(encoding="utf-8"))
    assert "series/inpc.yaml" in d["huellas"] and len(d["huellas"]) == 5
    assert d["assets"]["series/inpc.yaml"] == "series_inpc.yaml" and d["assets"]["motor.py"] == "motor.py"


def test_el_paquete_plano_pasa_probar_solo(paquete):
    codigo, mensaje = pp.prueba(paquete)
    assert codigo == 0, mensaje
    assert "0 fallan" in mensaje


def test_sin_la_serie_el_paquete_falla(paquete, tmp_path):
    """El error que tuvo v0.4.2: un paquete sin series/inpc.yaml no debe pasar."""
    roto = tmp_path / "roto"
    shutil.copytree(paquete, roto)
    (roto / "series" / "inpc.yaml").unlink()
    sumas = [l for l in (roto / "SHA256SUMS").read_text(encoding="utf-8").splitlines() if "series/" not in l]
    (roto / "SHA256SUMS").write_text("\n".join(sumas) + "\n", encoding="utf-8")
    codigo, mensaje = pp.prueba(roto)
    assert codigo == 1 and "falló" in mensaje


def test_una_huella_alterada_falla(paquete, tmp_path):
    roto = tmp_path / "alterado"
    shutil.copytree(paquete, roto)
    with open(roto / "motor.py", "ab") as f:
        f.write(b"\n# editado a mano\n")
    codigo, mensaje = pp.prueba(roto)
    assert codigo == 1 and "huella" in mensaje
