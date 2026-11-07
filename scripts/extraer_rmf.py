#!/usr/bin/env python3
"""Biblioteca de la RMF: baja del DOF el archivo Word de una resolución y la guarda UNA REGLA POR ARCHIVO.

  python scripts/extraer_rmf.py RMF2026                      # baja el Word del DOF y lo extrae
  python scripts/extraer_rmf.py RMF2026 --doc ruta.doc       # usa un .doc ya bajado

Sale en fuentes/rmf/<año>/<CLAVE>/ con el mismo formato que fuentes/leyes/:
  manifiesto.json   DOF (fecha y nota), URL del Word, SHA256 del Word y del texto, `origen` y `cotejado_dof`
  indice.json       regla -> archivo, SHA256, ubicación (título, capítulo, sección), título de la regla, fundamento (CFF 18, 29-A…), derogada
  reglas/regla-2-1-1.md
  preambulo.md      considerandos
  transitorios.md   transitorios de la resolución

Las modificaciones (primera, segunda…) entran cada una en su carpeta (RMF2026-M1…), con solo las reglas que tocan.
El Word NO se guarda en el repo: solo su URL y su huella. Requiere LibreOffice (soffice) para leer el .doc.
El texto sale del DOF mismo, pero NINGUNA persona lo ha revisado: `cotejado_dof` queda vacío hasta que alguien coteje.
"""
import argparse, datetime as dt, hashlib, json, re, shutil, subprocess, sys, tempfile, urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
# clave -> (año, código de nota del DOF, fecha DOF, nombre)
RESOLUCIONES = {
    "RMF2026": ("2026", "5777217", "2025-12-28", "Resolución Miscelánea Fiscal para 2026"),
}
DOF_DOC = "https://dof.gob.mx/nota_to_doc.php?codnota={codigo}"
DOF_NOTA = "https://dof.gob.mx/nota_detalle.php?codigo={codigo}&fecha={d}/{m}/{a}"

REGLA = re.compile(r"^\s*(\d{1,2}(?:\.\d{1,3}){1,4})\.\t")
ESTRUCTURA = re.compile(r"^\s*(T[ií]tulo|Cap[ií]tulo|Subsecci[oó]n|Secci[oó]n)\s+(\d+(?:\.\d+){0,3})\.?\s*(?:\t|\s)(.*)$")
TRANSITORIOS = re.compile(r"^\s*(Transitorios|TRANSITORIOS)\s*$")
INICIO_FUND = re.compile(r"^(?:CFF|RCFF|LISR|RLISR|LIVA|RLIVA|LIEPS|LIF|LFT|LSS|LFD|LCF|LGSM|LMV|LSH|LGTAIP|LFPIORPI|LISSSTE|CPEUM|RMF|RISAT|NOM|"
                         r"Ley|Reglamento|Decreto|Código|Disposiciones|Resolución|Lineamientos|Convenio|Acuerdo|Criterio|Anexo|Tratado|Estatuto|Convención|Convenios?|Decretos)\b")
ORACION = re.compile(r"\b(podrán|podrá|deberán|deberá|serán|será|estarán|efectuar|presentar|contribuyentes|autoridad|quienes|cuando)\b")


def es_fundamento(l: str) -> bool:
    """Línea final de una regla con su fundamento («CFF 18, 29-A, RMF 2.1.3.», «LIF Vigésimo Cuarto Transitorio»): empieza con una sigla o el
    nombre de una ley, no termina en «:» y no trae verbos de oración. Se aplica solo a la última línea de la regla."""
    l = l.strip()
    return bool(l) and len(l) < 900 and not l.endswith(":") and bool(INICIO_FUND.match(l) or re.match(r"^[A-Z]{2,}[A-Z\- ]*\b", l) or l.startswith("Decretos")) and not ORACION.search(l) and bool(re.search(r"\d|transitori[oa]s?|DOF|LFD", l, re.I))


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def a_texto(doc: Path) -> str:
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["soffice", "--headless", "--convert-to", "txt:Text (encoded):UTF8", "--outdir", td, str(doc)],
                       check=True, capture_output=True, timeout=600)
        return next(Path(td).glob("*.txt")).read_text(encoding="utf-8").lstrip("﻿")


def extrae(texto: str):
    L = texto.splitlines()
    fin = next((i for i, l in enumerate(L) if TRANSITORIOS.match(l) and i > len(L) // 2), len(L))
    cuerpo, trans = L[:fin], L[fin:]
    H = [i for i, l in enumerate(cuerpo) if REGLA.match(l)]
    if len(H) < 500:
        sys.exit(f"solo encontré {len(H)} reglas; el formato del documento cambió, revisa el extractor")
    preambulo = [l for l in cuerpo[:H[0]]]
    ubic, reglas, orden = {}, {}, []

    def aplica_estructura(lineas):
        for l in lineas:
            m = ESTRUCTURA.match(l)
            if m:
                nivel = 3 if m.group(1).lower().startswith("sub") else {"t": 0, "c": 1, "s": 2}[m.group(1)[0].lower()]
                for k in [k for k in ubic if k >= nivel]:
                    del ubic[k]
                ubic[nivel] = f"{m.group(1).capitalize()} {m.group(2)} · {m.group(3).strip()}".rstrip(" ·")

    # la cabecera de la primera regla (títulos/capítulos antes de ella) fija la ubicación inicial
    aplica_estructura(preambulo)
    titulos_regla = {}
    for k, i in enumerate(H):
        j = H[k + 1] if k + 1 < len(H) else len(cuerpo)
        span = cuerpo[i:j]
        # al final del span viven: [base legal] / [Título/Capítulo/Sección ...] / título de la regla siguiente
        cola = []
        if k + 1 < len(H):
            fin_s = len(span)
            while fin_s and not span[fin_s - 1].strip():
                fin_s -= 1
            if fin_s:
                fin_s -= 1  # título de la regla siguiente
                titulos_regla[k + 1] = " ".join(span[fin_s].split())
                while fin_s and (not span[fin_s - 1].strip() or ESTRUCTURA.match(span[fin_s - 1])):
                    fin_s -= 1
                cola = span[fin_s:len(span) - 1]
                span = span[:fin_s]
        rid = REGLA.match(span[0]).group(1)
        ubicacion = " / ".join(ubic[x] for x in sorted(ubic))
        reglas[rid] = {"span": span, "ubicacion": ubicacion, "k": k}
        orden.append(rid)
        aplica_estructura(cola)
    for rid in orden:
        reglas[rid]["titulo"] = titulos_regla.get(reglas[rid]["k"], "")
    return reglas, orden, preambulo, trans


def md_regla(rid, r, clave, nombre, nota, fundamento):
    cuerpo = [re.sub(r"[ \t]+", " ", re.sub(r"^\s*([IVXLC]+|[a-z]|\d+)\.\t", r"\1. ", l)).strip() for l in r["span"]]
    cuerpo[0] = re.sub(r"^\s*" + re.escape(rid) + r"\.\s*", f"{rid}. ", cuerpo[0])
    texto = "\n\n".join(l for l in cuerpo if l)
    meta = [f"Resolución: {nombre} ({clave})", f"Fuente: DOF, {nota}"]
    if r["ubicacion"]:
        meta.insert(1, f"Ubicación: {r['ubicacion']}")
    if fundamento:
        meta.append(f"Fundamento: {fundamento}")
    meta.append("Cotejado con el DOF: NO (el texto sale del archivo del DOF, sin revisión de una persona)")
    cab = f"# {clave} · Regla {rid}" + (f" · {r['titulo']}" if r["titulo"] else "") + "\n\n" + "\n".join(meta) + "\n\n"
    return cab + texto + "\n"


def procesa(clave: str, doc: Path, out_raiz: Path) -> dict:
    año, codigo, fecha, nombre = RESOLUCIONES[clave]
    a, m, d = fecha.split("-")
    nota = DOF_NOTA.format(codigo=codigo, a=a, m=m, d=d)
    reglas, orden, preambulo, trans = extrae(a_texto(doc))
    dest = out_raiz / año / clave
    (dest / "reglas").mkdir(parents=True, exist_ok=True)
    for viejo in (dest / "reglas").glob("regla-*.md"):
        viejo.unlink()
    previo = {}
    if (dest / "manifiesto.json").exists():
        previo = json.loads((dest / "manifiesto.json").read_text(encoding="utf-8")).get("cotejado_dof", {})
    cotejo = {"ley_completa": previo.get("ley_completa"), "articulos": previo.get("articulos", {})}
    indice = {}
    for rid in orden:
        r = reglas[rid]
        ult = next((l.strip() for l in reversed(r["span"]) if l.strip()), "")
        fundamento = ult if es_fundamento(ult) and len(r["span"]) > 1 else ""
        if fundamento:
            r["span"] = r["span"][:max(1, len(r["span"]) - 1 - next(i for i, l in enumerate(reversed(r["span"])) if l.strip() == fundamento))]
        md = md_regla(rid, r, clave, nombre, nota, fundamento)
        cuerpo_txt = md.split("\n\n", 2)[-1]
        f = dest / "reglas" / ("regla-" + rid.replace(".", "-") + ".md")
        f.write_text(md, encoding="utf-8", newline="\n")
        indice[rid] = {"archivo": f"reglas/{f.name}", "sha256": sha(cuerpo_txt.encode()), "ubicacion": r["ubicacion"],
                       "titulo": r["titulo"], "fundamento": fundamento,
                       "derogada": bool(re.search(r"\bSe deroga\b", " ".join(r["span"])[:300]))}
    (dest / "preambulo.md").write_text(f"# {clave} · Preámbulo y considerandos\n\n" + "\n\n".join(l.strip() for l in preambulo if l.strip()) + "\n", encoding="utf-8", newline="\n")
    (dest / "transitorios.md").write_text(f"# {clave} · Transitorios\n\n" + "\n\n".join(re.sub(r"[ \t]+", " ", l).strip() for l in trans if l.strip()) + "\n", encoding="utf-8", newline="\n")
    (dest / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    man = {"clave": clave, "nombre": nombre, "tipo": "resolucion", "dof": {"fecha": fecha, "nota": codigo, "url": nota},
           "url_documento": DOF_DOC.format(codigo=codigo), "origen": "DOF (archivo Word de la nota; texto sin revisión humana)",
           "descargado": dt.date.today().isoformat(), "sha256_documento": sha(doc.read_bytes()),
           "sha256_texto": sha("".join(indice[x]["sha256"] for x in orden).encode()), "cotejado_dof": cotejo,
           "reglas": len(orden), "derogadas": sum(1 for v in indice.values() if v["derogada"])}
    (dest / "manifiesto.json").write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return man


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clave", choices=sorted(RESOLUCIONES))
    ap.add_argument("--doc", type=Path)
    ap.add_argument("--out", type=Path, default=RAIZ / "fuentes" / "rmf")
    a = ap.parse_args()
    if not shutil.which("soffice"):
        sys.exit("hace falta LibreOffice (soffice) para leer el .doc")
    with tempfile.TemporaryDirectory() as td:
        doc = a.doc
        if not doc:
            doc = Path(td) / f"{a.clave}.doc"
            req = urllib.request.Request(DOF_DOC.format(codigo=RESOLUCIONES[a.clave][1]), headers={"User-Agent": "timbra-reglas/0.1 (biblioteca RMF)"})
            doc.write_bytes(urllib.request.urlopen(req, timeout=300).read())
        m = procesa(a.clave, doc, a.out)
    print(f"{a.clave}: {m['reglas']} reglas ({m['derogadas']} derogadas), DOF {m['dof']['fecha']}")


if __name__ == "__main__":
    main()
