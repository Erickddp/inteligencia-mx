import shutil
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parent.parent
BASE = RAIZ / "base"


@pytest.fixture(scope="session")
def base():
    from timbra_reglas.motor import Base
    return Base(base_dir=BASE)


@pytest.fixture
def copia(tmp_path):
    """Copia editable de base/: devuelve (carpeta, edita) para romper la base a propósito."""
    for f in ("parametros.yaml", "reglas.yaml"):
        shutil.copy(BASE / f, tmp_path / f)

    def edita(archivo, fn):
        p = tmp_path / archivo
        datos = yaml.safe_load(p.read_text(encoding="utf-8"))
        fn(datos)
        p.write_text(yaml.safe_dump(datos, allow_unicode=True, sort_keys=False), encoding="utf-8")

    return tmp_path, edita
