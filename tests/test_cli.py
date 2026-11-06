import json
import os
import subprocess
import sys

from conftest import RAIZ


def corre(*args):
    # PYTHONIOENCODING=cp1252 reproduce la consola de Windows, donde «→» truena si el motor no fuerza UTF-8
    env = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
    return subprocess.run([sys.executable, "-m", "timbra_reglas", *args], cwd=RAIZ, capture_output=True,
                          text=True, encoding="utf-8", env=env)


def test_probar_pasa_aun_con_consola_cp1252():
    r = corre("probar")
    assert r.returncode == 0, r.stderr[-500:]
    assert "0 fallan" in r.stdout


def test_valor_y_exportar():
    v = json.loads(corre("valor", "UMA_DIARIA", "2026-03-15").stdout)
    assert v["valor"] == "117.31" and v["estado"] == "vigente"
    e = json.loads(corre("exportar", "2026-03").stdout)
    assert "2026-03" in e["meses"]


def test_impacto_vigencias_simular():
    assert "R-" in corre("impacto", "IVA_TASA_GENERAL").stdout
    assert "VENCEN" in corre("vigencias", "2027-01-01").stdout
    assert "IVA_TASA_GENERAL" in corre("simular", "IVA_TASA_GENERAL=10", "2027-01-01").stdout
