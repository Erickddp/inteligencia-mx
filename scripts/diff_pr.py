#!/usr/bin/env python3
"""Diferencias de un PR contra main, en Markdown, para el comentario automático.

  python scripts/diff_pr.py --anterior DIR_BASE_DE_MAIN --nuevo base > diff.md

Usa compara() de release.py. Los VALORES CAMBIADOS son las firmas que se caen en Timbra.
"""
import argparse
import importlib.util
import sys
from pathlib import Path

MARCA = "<!-- timbra-reglas-diff -->"
AQUI = Path(__file__).resolve().parent


def carga_release():
    spec = importlib.util.spec_from_file_location("release", AQUI / "release.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def markdown(dif: dict) -> str:
    def bloque(titulo, items, alerta=False):
        if not items:
            return f"- {titulo}: ninguno\n"
        cab = f"- **{titulo}: {len(items)}**" if alerta else f"- {titulo}: {len(items)}"
        return cab + "\n" + "".join(f"  - `{i}`\n" for i in items)

    hay = any(dif[k] for k in dif)
    out = [MARCA, "## Diferencias contra `main`\n"]
    if not hay:
        out.append("Sin cambios en la base (parámetros, vigencias, estados ni reglas).\n")
        return "\n".join(out)
    if dif["valor_cambiado"]:
        out.append("> **Atención:** hay valores publicados que cambian. Cada uno es una **firma que se cae** en Timbra.\n")
    out.append(bloque("Valores cambiados (= firmas que se caen)", dif["valor_cambiado"], alerta=True))
    out.append(bloque("Vigencias cambiadas", dif["vigencia_cambiada"]))
    out.append(bloque("Estados cambiados", dif["estado_cambiado"]))
    out.append(bloque("Tramos nuevos", dif["tramos_nuevos"]))
    out.append(bloque("Parámetros nuevos", dif["param_nuevos"]))
    out.append(bloque("Parámetros quitados", dif["param_quitados"], alerta=True))
    out.append(bloque("Reglas nuevas", dif["reglas_nuevas"]))
    out.append(bloque("Reglas quitadas", dif["reglas_quitadas"], alerta=True))
    out.append(bloque("Reglas que cambiaron de estado", dif["regla_estado"]))
    out.append("\n_Un valor publicado no se edita: se agrega un tramo. Si ves «valores cambiados», revisa que sea corrección y no cambio de ley._")
    return "\n".join(out)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--anterior", required=True)
    a.add_argument("--nuevo", default=str(AQUI.parent / "base"))
    x = a.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    print(markdown(carga_release().compara(Path(x.anterior), Path(x.nuevo))))


if __name__ == "__main__":
    main()
