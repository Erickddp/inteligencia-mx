#!/usr/bin/env python3
"""Biblioteca de leyes: baja el PDF oficial de una ley, extrae el texto y lo guarda UN ARTÍCULO POR ARCHIVO.

  python scripts/extraer_ley.py LISR                     # baja de diputados.gob.mx
  python scripts/extraer_ley.py LISR --pdf ruta.pdf      # usa un PDF ya bajado
  python scripts/extraer_ley.py --todas                  # las leyes del catálogo

Sale en fuentes/leyes/<CLAVE>/:
  manifiesto.json    url, última reforma (la que dice el PDF), fecha de descarga, SHA256 del PDF y del texto
  indice.json        artículo -> SHA256 de su texto y ubicación (título, capítulo, sección)
  articulos/art-0106.md, art-0004-a.md, ...
  transitorios.md    el transitorio de la ley y los de los decretos de reforma

El PDF NO se guarda en el repo (solo su huella y su URL). Un artículo por archivo hace que un cambio de ley se vea
en git como el artículo que cambió, y permite que una regla cite «LISR art. 106 fr. II» y se pueda abrir.
Requiere pdftotext (poppler-utils). El texto es el de la Cámara de Diputados: orientación hasta cotejarlo con el DOF.
"""
import argparse, datetime as dt, hashlib, json, re, subprocess, sys, tempfile, urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BASE_URL = "https://www.diputados.gob.mx/LeyesBiblio/pdf/{archivo}.pdf"
# clave del repo -> (archivo en diputados, nombre oficial)
LEYES = {
    "LISR": ("LISR", "Ley del Impuesto sobre la Renta"),
    "LIVA": ("LIVA", "Ley del Impuesto al Valor Agregado"),
    "LFPIORPI": ("LFPIORPI", "Ley Federal para la Prevención e Identificación de Operaciones con Recursos de Procedencia Ilícita"),
    "LSS": ("LSS", "Ley del Seguro Social"),
    "LINFONAVIT": ("LIFNVT", "Ley del Instituto del Fondo Nacional de la Vivienda para los Trabajadores"),
}

SUFIJO = r"(?:Bis|Ter|Qu[áa]ter|Quinquies|Sexies|Septies|Octies|Nonies|Decies|Quintus|Sextus|Septimus)"
INICIO = re.compile(r"^ {0,6}Art[íi]culo\s+(?=\d)")
SUF_RE = [re.compile(r"\s*\.?\s*-\s*([A-Z])\b"),                                  # -A
          re.compile(rf"\s*\.?\s*-?\s*({SUFIJO})\b", re.I),                        # Bis, -Quáter, BIS
          re.compile(r"\s+([A-Z])\b(?=\s*[.\-])"),                                   # «5 A.»
          re.compile(r"\s+(\d{1,2})\b(?=\s*[.\-])")]                                # «18 Bis 1.»


def encabezado(linea: str) -> str | None:
    """Devuelve el id normalizado si la línea es el encabezado de un artículo («Artículo 1o.-A.- ...», «82-Quáter. ...»)."""
    if not INICIO.match(linea):
        return None
    s = linea[INICIO.match(linea).end():]
    m = re.match(r"(\d+)(?:[º°]|o(?=[.\-\s]))?", s)
    if not m:
        return None
    partes, resto = [m.group(1)], s[m.end():]
    while True:
        m2 = next((m for r in SUF_RE if (m := r.match(resto))), None)
        if not m2:
            break
        partes.append(m2.group(1))
        resto = resto[m2.end():]
    if not re.match(r"\s*[.\-]", resto):
        return None
    return "-".join(p.lower().replace("á", "a") for p in partes)


ENCABEZADO = re.compile(r"^\s{30,}(LEY|C[ÓO]DIGO) [A-ZÁÉÍÓÚÑ ,]+\s*$|^\s*(C[ÁA]MARA DE DIPUTADOS DEL H\. CONGRESO DE LA UNI[ÓO]N|Secretar[íi]a General|Secretar[íi]a de Servicios Parlamentarios|\d+ de \d+)\s*$|[ÚU]ltima [Rr]eforma",)
ESTRUCTURA = re.compile(r"^\s*(LIBRO|T[ÍI]TULO|CAP[ÍI]TULO|SECCI[ÓO]N)\s+([IVXLCDM]+|PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|S[ÉE]PTIMO|OCTAVO|NOVENO|D[ÉE]CIMO|[ÚU]NICO|\d+)(\s+(?:Bis|BIS|[A-Z]))?\s*$", re.I)
TRANSITORIOS = re.compile(r"^\s*(ART[ÍI]CULOS\s+)?TRANSITORIOS\s*$")
NIVEL = {"LIBRO": 0, "TITULO": 1, "TÍTULO": 1, "CAPITULO": 2, "CAPÍTULO": 2, "SECCION": 3, "SECCIÓN": 3}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def nombre_archivo(aid: str) -> str:
    n, *resto = aid.split("-")
    return "art-" + "-".join([n.zfill(4)] + resto) + ".md"


def limpia_pagina(lineas: list[str]) -> list[str]:
    return [l for l in lineas if not ENCABEZADO.search(l)]


def reflow(lineas: list[str]) -> str:
    """Une líneas cortadas por el PDF. Párrafo nuevo = línea con sangría; nota de reforma = sangría enorme."""
    out, actual = [], ""
    for l in lineas:
        if not l.strip():
            if actual:
                out.append(actual); actual = ""
            continue
        sangria = len(l) - len(l.lstrip())
        t = re.sub(r"\s+", " ", l.strip())
        if sangria > 40:  # «Artículo reformado DOF ...», alineado a la derecha
            if actual:
                out.append(actual); actual = ""
            out.append(f"_{t}_")
        elif sangria >= 2 or not actual:
            if actual:
                out.append(actual)
            actual = t
        else:
            actual = (actual[:-1] + t) if actual.endswith("-") and t[:1].islower() else f"{actual} {t}"
    if actual:
        out.append(actual)
    # las notas en cursiva que quedaron partidas en varias líneas se juntan
    texto = "\n\n".join(out)
    return re.sub(r"_\n\n_", " ", texto)


def extrae(texto: str):
    lineas = limpia_pagina(texto.splitlines())
    fin = next((i for i, l in enumerate(lineas) if TRANSITORIOS.match(l)), len(lineas))
    cuerpo, trans = lineas[:fin], lineas[fin:]
    arts, orden = {}, []
    ubic = {}
    actual = None
    i = 0
    while i < len(cuerpo):
        l = cuerpo[i]
        m = ESTRUCTURA.match(l)
        if m and not encabezado(l):
            tipo = m.group(1).upper().replace("Í", "I").replace("Ó", "O")
            nivel = {"LIBRO": 0, "TITULO": 1, "CAPITULO": 2, "SECCION": 3}[tipo]
            titulo = ""
            j = i + 1
            while j < len(cuerpo) and not cuerpo[j].strip():
                j += 1
            partes_t = []
            while j < len(cuerpo) and cuerpo[j].strip() and not encabezado(cuerpo[j]) and len(partes_t) < 4 and not ESTRUCTURA.match(cuerpo[j]):
                partes_t.append(" ".join(cuerpo[j].split()))
                j += 1
            titulo = " ".join(partes_t) if sum(len(x) for x in partes_t) < 260 else ""
            for k in [k for k in ubic if k >= nivel]:
                del ubic[k]
            ubic[nivel] = " ".join(f"{m.group(1).capitalize()} {m.group(2)}{m.group(3) or ''}".split()) + (f" · {titulo}" if titulo else "")
            i += 1
            continue
        aid = encabezado(l)
        if aid:
            if aid not in arts:  # si ya existe, es una cita al inicio de línea dentro de otro artículo: no es encabezado

                actual = aid
                orden.append(aid)
                arts[aid] = {"lineas": [l], "ubicacion": " / ".join(ubic[k] for k in sorted(ubic))}
                i += 1
                continue
        if actual:
            arts[actual]["lineas"].append(l)
        i += 1
    return arts, orden, trans


def ultima_reforma(texto: str) -> str | None:
    m = re.search(r"[ÚU]ltima [Rr]eforma(?: publicada)?\s+DOF\s+(\d{2})-(\d{2})-(\d{4})", texto)
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def procesa(clave: str, pdf: Path, url: str, out_raiz: Path) -> dict:
    archivo, nombre = LEYES[clave]
    with tempfile.TemporaryDirectory() as td:
        txt = Path(td) / "ley.txt"
        subprocess.run(["pdftotext", "-layout", str(pdf), str(txt)], check=True)
        texto = txt.read_text(encoding="utf-8", errors="replace")
    arts, orden, trans = extrae(texto)
    if len(orden) < 20:
        sys.exit(f"{clave}: solo encontré {len(orden)} artículos; el formato del PDF cambió, revisa el extractor")
    dest = out_raiz / clave
    (dest / "articulos").mkdir(parents=True, exist_ok=True)
    for viejo in (dest / "articulos").glob("art-*.md"):
        viejo.unlink()
    reforma = ultima_reforma(texto)
    indice = {}
    for aid in orden:
        a = arts[aid]
        cuerpo = reflow(a["lineas"])
        cab = f"# {clave} · Artículo {aid.upper() if '-' in aid else aid}\n\n"
        if a["ubicacion"]:
            cab += f"Ubicación: {a['ubicacion']}\n\n"
        md = cab + cuerpo.rstrip() + "\n"
        f = dest / "articulos" / nombre_archivo(aid)
        f.write_text(md, encoding="utf-8", newline="\n")
        indice[aid] = {"archivo": f"articulos/{f.name}", "sha256": sha(cuerpo.encode()), "ubicacion": a["ubicacion"],
                       "derogado": bool(re.search(r"\bSe deroga\b", cuerpo[:400]))}
    (dest / "transitorios.md").write_text(f"# {clave} · Transitorios\n\n" + reflow(trans).rstrip() + "\n", encoding="utf-8", newline="\n")
    (dest / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    man = {"clave": clave, "nombre": nombre, "url": url, "fuente": "Cámara de Diputados (texto vigente); cotejar contra el DOF",
           "ultima_reforma_segun_pdf": reforma, "descargado": dt.date.today().isoformat(),
           "sha256_pdf": sha(pdf.read_bytes()), "sha256_texto": sha("".join(indice[a]["sha256"] for a in orden).encode()),
           "articulos": len(orden), "derogados": sum(1 for a in indice.values() if a["derogado"])}
    (dest / "manifiesto.json").write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return man


def baja(url: str, destino: Path):
    req = urllib.request.Request(url, headers={"User-Agent": "timbra-reglas/0.1 (biblioteca de leyes)"})
    with urllib.request.urlopen(req, timeout=180) as r:
        destino.write_bytes(r.read())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clave", nargs="?", choices=sorted(LEYES))
    ap.add_argument("--pdf", type=Path)
    ap.add_argument("--todas", action="store_true")
    ap.add_argument("--out", type=Path, default=RAIZ / "fuentes" / "leyes")
    a = ap.parse_args()
    claves = sorted(LEYES) if a.todas else [a.clave] if a.clave else ap.error("indica una clave o --todas")
    for c in claves:
        url = BASE_URL.format(archivo=LEYES[c][0])
        with tempfile.TemporaryDirectory() as td:
            pdf = a.pdf if (a.pdf and not a.todas) else Path(td) / f"{c}.pdf"
            if not (a.pdf and not a.todas):
                baja(url, pdf)
            m = procesa(c, pdf, url, a.out)
        print(f"{c}: {m['articulos']} artículos ({m['derogados']} derogados), última reforma según el PDF: {m['ultima_reforma_segun_pdf']}")


if __name__ == "__main__":
    main()
