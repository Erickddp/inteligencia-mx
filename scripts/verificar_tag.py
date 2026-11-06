#!/usr/bin/env python3
"""El tag vX.Y.Z debe coincidir con version_base (los dos YAML) y con VERSION_MOTOR.

  python scripts/verificar_tag.py v0.5.0
"""
import re
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent


def versiones(raiz: Path = RAIZ) -> dict:
    v = {f: yaml.safe_load((raiz / "base" / f).read_text(encoding="utf-8"))["version_base"] for f in ("parametros.yaml", "reglas.yaml")}
    m = re.search(r'^VERSION_MOTOR = "(.*)"$', (raiz / "timbra_reglas" / "motor.py").read_text(encoding="utf-8"), re.M)
    v["motor.py"] = m.group(1) if m else None
    return v


def verifica(tag: str, raiz: Path = RAIZ) -> list:
    """Lista de errores; vacía si el tag coincide en los tres lugares."""
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        return [f"El tag '{tag}' no tiene la forma vX.Y.Z"]
    quiere = tag[1:]
    errores = [f"{arch}: dice {ver!r} y el tag pide {quiere!r}" for arch, ver in versiones(raiz).items() if ver != quiere]
    cl = raiz / "CHANGELOG.md"
    if cl.exists() and f"## [{tag}]" not in cl.read_text(encoding="utf-8"):
        errores.append(f"CHANGELOG.md no tiene la entrada «## [{tag}]» (python scripts/release.py --changelog ...)")
    return errores


def main():
    errores = verifica(sys.argv[1])
    if errores:
        print("EL TAG NO COINCIDE CON LA BASE:\n  " + "\n  ".join(errores))
        return 1
    print(f"Tag {sys.argv[1]} coincide con version_base y VERSION_MOTOR.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
