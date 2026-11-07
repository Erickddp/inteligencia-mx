#!/usr/bin/env python3
"""Prueba el paquete plano de un release SOLO, sin el repositorio al lado.

  python scripts/probar_paquete.py DIR_DEL_PAQUETE

DIR_DEL_PAQUETE es la carpeta que arma release.py (parametros.yaml, reglas.yaml, motor.py, FASES.md, series/, SHA256SUMS).
Copia a una carpeta vacía exactamente los archivos que lista SHA256SUMS (verificando cada huella) y corre ahí
`python -I motor.py probar`. Así falla si al paquete le falta algo, por ejemplo una serie que el motor necesita.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

OBLIGATORIOS = ("parametros.yaml", "reglas.yaml", "motor.py", "FASES.md")


def prueba(paquete: Path) -> tuple[int, str]:
    sumas = (paquete / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    listados = {}
    for linea in sumas:
        if linea.strip():
            huella, nombre = linea.split(None, 1)
            listados[nombre.strip().lstrip("*")] = huella
    faltan = [n for n in OBLIGATORIOS if n not in listados]
    if faltan:
        return 1, f"SHA256SUMS no lista: {', '.join(faltan)}"
    with tempfile.TemporaryDirectory() as tmp:
        solo = Path(tmp) / "solo"
        for nombre, huella in listados.items():
            origen = paquete / nombre
            if not origen.is_file():
                return 1, f"{nombre} está en SHA256SUMS pero no en el paquete"
            if hashlib.sha256(origen.read_bytes()).hexdigest() != huella:
                return 1, f"{nombre}: la huella no coincide con SHA256SUMS"
            (solo / nombre).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(origen, solo / nombre)
        r = subprocess.run([sys.executable, "-I", "motor.py", "probar"], cwd=solo, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env={**os.environ, "PYTHONUTF8": "1"})
        ultima = (r.stdout.strip().splitlines() or ["sin salida"])[-1]
        if r.returncode != 0:
            return 1, f"motor.py probar falló desde el paquete solo: {ultima}\n{r.stdout[-1500:]}\n{r.stderr[-1500:]}"
        return 0, ultima


if __name__ == "__main__":
    codigo, mensaje = prueba(Path(sys.argv[1]))
    print(("PAQUETE PLANO OK: " if codigo == 0 else "PAQUETE PLANO FALLA: ") + mensaje)
    sys.exit(codigo)
