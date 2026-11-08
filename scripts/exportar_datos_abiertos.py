#!/usr/bin/env python3
"""Datos abiertos de inteligencia-mx: la base, las leyes y lo que falta verificar, en CSV y JSON para que cualquiera los use.

  python scripts/exportar_datos_abiertos.py                      # regenera datos_abiertos/
  python scripts/exportar_datos_abiertos.py --comprobar          # falla si datos_abiertos/ no está al día (lo corre el CI)
  python scripts/exportar_datos_abiertos.py --corpus corpus.jsonl  # además, el texto de cada artículo y regla, un JSON por línea

Salida (datos_abiertos/, licencia CC BY 4.0):
  parametros.csv       cada parámetro de ley: tramos, estado, vigencia y fuente del último tramo
  reglas.csv           cada regla: estado, calculadora, casos, citas
  leyes.csv            cada ley de la biblioteca: ámbito, entidad, materia, reforma, huella, si tiene cotejo humano
  citas.csv            qué artículo cita cada regla o parámetro (citas estructuradas) y si existe en la biblioteca
  cotejo_pendiente.csv los artículos que la base cita y nadie ha cotejado con el DOF, ordenados por cuántas cosas dependen de ellos
  catalogo.json        qué trae cada archivo, columnas, filas y huella SHA256

Es DETERMINISTA (sin fechas ni orden aleatorio): si la base cambia y no se regenera, `--comprobar` lo avisa.
El corpus (--corpus) NO se versiona: pesa decenas de MB; se genera cuando se necesita o se publica como asset de un release.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import citas_fuentes as cf  # noqa: E402  (reutiliza el analizador de citas del repo)

ESCALARES = {"importe", "porcentaje", "numero", "texto"}
DESCRIPCIONES = {
    "parametros.csv": "Cada parámetro de ley con sus tramos, estado y vigencia (valor solo si es un dato simple).",
    "reglas.csv": "Cada regla R-xx con su estado, calculadora, número de casos y citas.",
    "leyes.csv": "Cada ley, código o reglamento de la biblioteca con su ámbito, materia, huella y si tiene cotejo humano.",
    "citas.csv": "Citas estructuradas de reglas y parámetros a artículos de la biblioteca.",
    "cotejo_pendiente.csv": "Artículos citados por la base que nadie ha cotejado con el diario oficial, por prioridad.",
}


def carga(raiz: Path):
    P = yaml.safe_load((raiz / "base" / "parametros.yaml").read_text(encoding="utf-8"))
    R = yaml.safe_load((raiz / "base" / "reglas.yaml").read_text(encoding="utf-8"))
    return P, R["reglas"]


def leyes(raiz: Path) -> dict:
    out = {}
    for d in sorted(p for p in (raiz / "fuentes" / "leyes").iterdir() if p.is_dir()):
        m = json.loads((d / "manifiesto.json").read_text(encoding="utf-8"))
        out[d.name] = (m, json.loads((d / "indice.json").read_text(encoding="utf-8")))
    return out


def reglas_rmf_idx(raiz: Path) -> dict:
    out = {}
    for ix in sorted((raiz / "fuentes" / "rmf").glob("*/*/indice.json")):
        out[ix.parent.parent.name] = json.loads(ix.read_text(encoding="utf-8"))
    return out


def csv_texto(columnas: list, filas: list) -> str:
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\n")
    w.writerow(columnas)
    w.writerows(filas)
    return b.getvalue()


def resumen_valor(p: dict, tramo: dict) -> str:
    if "formula" in p:
        return ""
    v = tramo.get("valor")
    if p.get("tipo") in ESCALARES and not isinstance(v, (list, dict)):
        return str(v)
    if isinstance(v, dict):
        return f"{p.get('tipo')}: {len(v)} grupos"
    return f"{p.get('tipo')}: {len(v)} renglones" if isinstance(v, list) else ""


def tabla_parametros(P: dict) -> str:
    filas = []
    for pid in sorted(P["parametros"]):
        p = P["parametros"][pid]
        tr = sorted(p.get("valores", []), key=lambda t: str(t["desde"]))
        estados = {}
        for t in tr:
            estados[t.get("estado", "vigente")] = estados.get(t.get("estado", "vigente"), 0) + 1
        u = tr[-1] if tr else {}
        filas.append([pid, p.get("nombre", ""), p.get("tipo", ""), p.get("unidad", ""), len(tr),
                      "; ".join(f"{k}:{v}" for k, v in sorted(estados.items())), u.get("desde", ""), u.get("hasta") or "",
                      u.get("confirmado_hasta") or "", u.get("estado", "vigente") if tr else "", resumen_valor(p, u) if tr else "",
                      p.get("formula", ""), (u.get("fuente") or p.get("fuente") or "")])
    return csv_texto(["id", "nombre", "tipo", "unidad", "tramos", "estados", "desde_ultimo", "hasta_ultimo", "confirmado_hasta_ultimo",
                      "estado_ultimo", "valor_ultimo", "formula", "fuente_ultimo"], filas)


def tabla_reglas(reglas: list) -> str:
    filas = [[r["id"], r.get("nombre", ""), r.get("estado", ""), r.get("fase", ""), r.get("calculadora", ""), len(r.get("casos", [])),
              ";".join(r.get("parametros", [])), len(r.get("citas", [])), "si" if r.get("que_dice") else "no", r.get("fuente", "")]
             for r in sorted(reglas, key=lambda r: r["id"])]
    return csv_texto(["id", "nombre", "estado", "fase", "calculadora", "casos", "parametros", "citas", "tiene_que_dice", "fuente"], filas)


def cotejado(m: dict, articulo: str) -> bool:
    c = m.get("cotejado_dof", {}) or {}
    return bool(c.get("ley_completa")) or articulo in (c.get("articulos") or {})


def tabla_leyes(L: dict) -> str:
    filas = []
    for clave, (m, ix) in L.items():
        c = m.get("cotejado_dof", {}) or {}
        filas.append([clave, m.get("nombre", ""), m.get("ambito", "federal"), m.get("entidad", ""), m.get("materia", ""), m.get("emisor", ""),
                      m.get("url", ""), m.get("ultima_reforma_segun_pdf") or "", m.get("articulos", len(ix)), m.get("derogados", 0),
                      "si" if (c.get("ley_completa") or c.get("articulos")) else "no", m.get("sha256_pdf", "")])
    return csv_texto(["clave", "nombre", "ambito", "entidad", "materia", "emisor", "url", "ultima_reforma", "articulos", "derogados",
                      "cotejo_humano", "sha256_pdf"], filas)


def citas_estructuradas(P: dict, reglas: list):
    for r in reglas:
        for c in r.get("citas", []) or []:
            yield "regla", r["id"], c
    for pid, p in P["parametros"].items():
        for c in p.get("citas", []) or []:
            yield "parametro", pid, c


def tabla_citas(P: dict, reglas: list, L: dict, RMF: dict) -> str:
    filas = []
    for tipo, origen, c in citas_estructuradas(P, reglas):
        if "nif" in c:
            filas.append([tipo, origen, f"NIF-{c['nif']}", "", "", "referencia"])
            continue
        ley, art, anio = c["ley"], str(c["articulo"]), c.get("anio", "")
        existe = art in (RMF.get(str(anio), {}) if ley == "RMF" else (L[ley][1] if ley in L else {}))
        filas.append([tipo, origen, ley, anio, art, "si" if existe else "no"])
    return csv_texto(["origen_tipo", "origen_id", "ley", "anio", "articulo", "existe_en_biblioteca"], sorted(filas))


def origenes_por_articulo(P: dict, reglas: list, L: dict) -> dict:
    """{(ley, articulo): {origenes}} con las citas estructuradas y las que están escritas en los textos de fuente."""
    o = {}

    def agrega(ley, art, origen):
        if ley in L and art in L[ley][1]:
            o.setdefault((ley, art), set()).add(origen)

    for tipo, origen, c in citas_estructuradas(P, reglas):
        if "ley" in c and c["ley"] != "RMF":
            agrega(c["ley"], str(c["articulo"]), f"{origen}")
    textos = [(r["id"], r.get("fuente", "")) for r in reglas]
    for pid, p in P["parametros"].items():
        textos.append((pid, p.get("fuente", "")))
        textos += [(pid, t.get("fuente", "")) for t in p.get("valores", [])]
    for origen, texto in textos:
        for m in cf.CITA.finditer(texto or ""):
            for i in cf.ids(m.group(2)):
                agrega(cf.ALIAS[m.group(1)], i, origen)
    return o


def tabla_cotejo(P: dict, reglas: list, L: dict) -> str:
    filas = []
    for (ley, art), orig in origenes_por_articulo(P, reglas, L).items():
        m = L[ley][0]
        if not cotejado(m, art):
            filas.append([ley, art, m.get("ambito", "federal"), len(orig), ";".join(sorted(orig)), "no"])
    filas.sort(key=lambda f: (-f[3], f[0], f[1]))
    return csv_texto(["ley", "articulo", "ambito", "citado_por", "origenes", "cotejado"], filas)


def contar(texto: str) -> int:
    return max(0, len(list(csv.reader(io.StringIO(texto)))) - 1)


def exportar(raiz: Path = RAIZ, destino: Path | None = None) -> dict:
    destino = Path(destino or raiz / "datos_abiertos")
    destino.mkdir(parents=True, exist_ok=True)
    P, reglas = carga(raiz)
    L, RMF = leyes(raiz), reglas_rmf_idx(raiz)
    archivos = {"parametros.csv": tabla_parametros(P), "reglas.csv": tabla_reglas(reglas), "leyes.csv": tabla_leyes(L),
                "citas.csv": tabla_citas(P, reglas, L, RMF), "cotejo_pendiente.csv": tabla_cotejo(P, reglas, L)}
    catalogo = {"nombre": "Datos abiertos de inteligencia-mx", "licencia": "CC BY 4.0", "version_base": P.get("version_base"),
                "archivos": {}}
    for nombre, texto in archivos.items():
        (destino / nombre).write_text(texto, encoding="utf-8", newline="\n")
        catalogo["archivos"][nombre] = {"descripcion": DESCRIPCIONES[nombre], "columnas": next(csv.reader(io.StringIO(texto))),
                                        "filas": contar(texto), "sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest()}
    (destino / "catalogo.json").write_text(json.dumps(catalogo, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return catalogo


def cuerpo(texto: str) -> str:
    lineas = texto.split("\n")
    i = next((k for k, l in enumerate(lineas) if l.startswith("Cotejado con")), None)
    return "\n".join(lineas[i + 2:]).strip() if i is not None else texto.strip()


def corpus(raiz: Path, salida: Path) -> int:
    """El texto de cada artículo y de cada regla de la RMF, un JSON por línea, ordenado: es la entrada de cualquier búsqueda."""
    n = 0
    with open(salida, "w", encoding="utf-8", newline="\n") as f:
        for clave, (m, ix) in leyes(raiz).items():
            for art in sorted(ix):
                t = (raiz / "fuentes" / "leyes" / clave / ix[art]["archivo"]).read_text(encoding="utf-8")
                f.write(json.dumps({"id": f"{clave}:{art}", "tipo": "articulo", "ley": clave, "nombre_ley": m.get("nombre"), "numero": art,
                                    "ubicacion": ix[art].get("ubicacion", ""), "derogado": ix[art].get("derogado", False),
                                    "ambito": m.get("ambito", "federal"), "entidad": m.get("entidad", ""), "materia": m.get("materia", ""),
                                    "url": m.get("url", ""), "cotejado": cotejado(m, art), "sha256": ix[art]["sha256"], "texto": cuerpo(t)},
                                   ensure_ascii=False) + "\n")
                n += 1
        for anio, ix in reglas_rmf_idx(raiz).items():
            for regla in sorted(ix):
                t = (raiz / "fuentes" / "rmf" / anio / f"RMF{anio}" / ix[regla]["archivo"]).read_text(encoding="utf-8")
                f.write(json.dumps({"id": f"RMF{anio}:{regla}", "tipo": "regla_rmf", "ley": f"RMF{anio}", "nombre_ley": f"Resolución Miscelánea Fiscal {anio}",
                                    "numero": regla, "ubicacion": ix[regla].get("ubicacion", ""), "derogado": ix[regla].get("derogada", False),
                                    "ambito": "federal", "entidad": "", "materia": "fiscal", "url": "", "cotejado": False,
                                    "sha256": ix[regla]["sha256"], "texto": cuerpo(t)}, ensure_ascii=False) + "\n")
                n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=RAIZ / "datos_abiertos")
    ap.add_argument("--comprobar", action="store_true", help="no escribe: falla si datos_abiertos/ no está al día")
    ap.add_argument("--corpus", type=Path, help="escribe también el texto de cada artículo en este archivo JSONL")
    a = ap.parse_args()
    if a.comprobar:
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            exportar(RAIZ, Path(td))
            malos = [f.name for f in Path(td).iterdir() if not (a.out / f.name).is_file() or (a.out / f.name).read_bytes() != f.read_bytes()]
        if malos:
            print(f"datos_abiertos/ NO está al día ({', '.join(sorted(malos))}). Regenera con: python scripts/exportar_datos_abiertos.py")
            return 1
        print("datos_abiertos/ está al día.")
        return 0
    cat = exportar(RAIZ, a.out)
    print("datos_abiertos/:", ", ".join(f"{k} ({v['filas']} filas)" for k, v in cat["archivos"].items()))
    if a.corpus:
        print(f"corpus: {corpus(RAIZ, a.corpus)} textos en {a.corpus}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
