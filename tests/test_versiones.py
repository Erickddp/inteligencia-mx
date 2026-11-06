"""La versión es una sola: version_base de los dos YAML = VERSION_MOTOR = versión del paquete."""
import re
import tomllib

import yaml

from conftest import BASE, RAIZ
from timbra_reglas import motor


def test_versiones_iguales():
    vp = yaml.safe_load((BASE / "parametros.yaml").read_text(encoding="utf-8"))["version_base"]
    vr = yaml.safe_load((BASE / "reglas.yaml").read_text(encoding="utf-8"))["version_base"]
    assert vp == vr == motor.VERSION_MOTOR


def test_pyproject_toma_la_version_del_motor():
    cfg = tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))
    assert "version" in cfg["project"]["dynamic"]
    assert cfg["tool"]["setuptools"]["dynamic"]["version"]["attr"] == "timbra_reglas.motor.VERSION_MOTOR"
    assert re.fullmatch(r"\d+\.\d+\.\d+", motor.VERSION_MOTOR)
