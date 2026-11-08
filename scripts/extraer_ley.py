#!/usr/bin/env python3
"""Biblioteca de leyes: baja el PDF oficial de una ley, extrae el texto y lo guarda UN ARTÍCULO POR ARCHIVO.

  python scripts/extraer_ley.py LISR                     # baja de diputados.gob.mx
  python scripts/extraer_ley.py LISR --pdf ruta.pdf      # usa un PDF ya bajado
  python scripts/extraer_ley.py --todas                  # las leyes del catálogo

Una ley FUERA del catálogo federal (estatal o municipal) se registra con su clave <ENTIDAD>-<SIGLAS>, su URL oficial y sus datos:

  python scripts/extraer_ley.py QUE-XXXX --url https://sitio.oficial.gob.mx/ley.pdf --nombre "Nombre oficial de la ley" \
      --ambito estatal --entidad QUE --materia fiscal --emisor "Congreso del Estado" --diario "Periódico Oficial"

La URL debe ser de un dominio oficial (fuentes/dominios_oficiales.yaml) y la entidad una clave de fuentes/entidades.yaml.
Estándar completo: docs/ESTANDAR_APORTACION.md.

Sale en fuentes/leyes/<CLAVE>/:
  manifiesto.json    url, última reforma (la que dice el PDF), fecha de descarga, SHA256 del PDF y del texto, `advertencias` y `cotejado_dof`
                     (quién cotejó contra el DOF y cuándo; lo llena una persona y regenerar no lo borra)
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
sys.path.insert(0, str(Path(__file__).resolve().parent))
import validar_aportacion as va  # noqa: E402  (dominios oficiales y entidades)
BASE_URL = "https://www.diputados.gob.mx/LeyesBiblio/{ruta}"
# clave del repo -> (archivo en diputados, nombre oficial)
LEYES = {
    "LISR": ("pdf/LISR.pdf", "Ley del Impuesto sobre la Renta"),
    "LIVA": ("pdf/LIVA.pdf", "Ley del Impuesto al Valor Agregado"),
    "LFPIORPI": ("pdf/LFPIORPI.pdf", "Ley Federal para la Prevención e Identificación de Operaciones con Recursos de Procedencia Ilícita"),
    "LSS": ("pdf/LSS.pdf", "Ley del Seguro Social"),
    "LINFONAVIT": ("pdf/LIFNVT.pdf", "Ley del Instituto del Fondo Nacional de la Vivienda para los Trabajadores"),
    "LFT": ("pdf/LFT.pdf", "Ley Federal del Trabajo"),
    "CFF": ("pdf/CFF.pdf", "Código Fiscal de la Federación"),
    "RLISR": ("regley/Reg_LISR_060516.pdf", "Reglamento de la Ley del Impuesto sobre la Renta"),
    "RLIVA": ("regley/Reg_LIVA_250914.pdf", "Reglamento de la Ley del Impuesto al Valor Agregado"),
    "LIEPS": ("pdf/LIEPS.pdf", "Ley del Impuesto Especial sobre Producción y Servicios"),
    "RLIEPS": ("regley/Reg_LIEPS.pdf", "Reglamento de la Ley del Impuesto Especial sobre Producción y Servicios"),
    "RCFF": ("regley/Reg_CFF.pdf", "Reglamento del Código Fiscal de la Federación"),
    "RLFPIORPI": ("regley/Reg_LFPIORPI.pdf", "Reglamento de la Ley Federal para la Prevención e Identificación de Operaciones con Recursos de Procedencia Ilícita"),
    "LIF2026": ("pdf/LIF_2026.pdf", "Ley de Ingresos de la Federación para el Ejercicio Fiscal de 2026"),
    "LA": ("pdf/LAdua.pdf", "Ley Aduanera"),
    "LFD": ("pdf/LFD.pdf", "Ley Federal de Derechos"),
    "LISH": ("pdf/LIH.pdf", "Ley de Ingresos sobre Hidrocarburos"),
    "LFISAN": ("pdf/LFISAN.pdf", "Ley Federal del Impuesto sobre Automóviles Nuevos"),
    "LCF": ("pdf/LCF.pdf", "Ley de Coordinación Fiscal"),
    "LMV": ("pdf/LMV.pdf", "Ley del Mercado de Valores"),
}

SUFIJO = (r"(?:Bis|Ter|Qu[áa]ter|Quinquies|Sexies|Septies|Octies|Nonies|Decies|Quintus|Sextus|S[ée]ptimus|Octavus|Nonus|D[ée]cimus"
          r"|Undecies|Duodecies|Terdecies|Quaterdecies|Cuarter|Cuater"
          r"|Quitus|Quintos)")  # Quitus y Quintos son erratas del texto oficial del Código Civil de la CDMX (art. 135 y 469): el id sigue al texto
INICIO = re.compile(r"^ {0,6}(?:Art[íi]culo|ART[ÍI]CULO)\s+(?=\d)")  # la Ley Aduanera lo escribe en mayúsculas
SUF_RE = [re.compile(r"\s*\(SIC\)\s*-?\s*([A-ZÑ])\b(?=\s*[.\-:])"),                       # «2448 (SIC) E.-»
          re.compile(r"\s*\.?\s*-([A-ZÑ])\b(?!\s+[a-záéíóú])"),                                  # -A
          re.compile(rf"\s*\.?\s*-?\s*({SUFIJO})\b", re.I),                        # Bis, -Quáter, BIS
          re.compile(r"\s+([A-ZÑ])\b(?=\s*(?:[.\-:]|\(|$))"),                                   # «5 A.»
          re.compile(r"\s+(\d{1,2})\b(?=\s*(?:[.\-:]|\(|$))")]                                # «18 Bis 1.»


NO_ENCABEZADO = re.compile(r"^\s*ART[ÍI]CULOS?\s+\d+\S*?(?:\s+DE\s+LAS?\s+DISPOSICIONES\s+TRANSITORIAS|,\s+SE\s+RECOMIENDA\s+CONSULTAR)", re.I)


def encabezado(linea: str) -> str | None:
    """Devuelve el id normalizado si la línea es el encabezado de un artículo («Artículo 1o.-A.- ...», «82-Quáter. ...»)."""
    if NO_ENCABEZADO.match(linea) or not INICIO.match(linea):
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
    if not re.match(r"\s*[.\-:]", resto) and not re.fullmatch(r"\s*(\(.*)?", resto):
        return None
    return "-".join(p.lower().replace("á", "a") for p in partes)


ENCABEZADO = re.compile(r"^\s{30,}(LEY|C[ÓO]DIGO|REGLAMENTO) [A-ZÁÉÍÓÚÑ0-9 ,]+\s*$"
                        r"|^\s*C[ÁA]MARA DE DIPUTADOS DEL H\. CONGRESO DE LA UNI[ÓO]N\b.*$"   # a veces trae «Nuevo Reglamento DOF …» en la misma línea
                        r"|^\s*(Secretar[íi]a General|Secretar[íi]a de Servicios Parlamentarios|\d+ de \d+)\s*$|[ÚU]ltima [Rr]eforma",)
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


MESES = {m: f"{i:02d}" for i, m in enumerate("enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(), 1)}


def ultima_reforma(texto: str):
    """(fecha, origen). Primero la línea «Última reforma DOF» del encabezado; si no hay, la fecha más reciente de una reforma, adición o
    derogación citada en el texto (no cuenta una fecha de acuerdo o de cuotas)."""
    m = re.search(r"[ÚU]ltima [Rr]eforma(?: publicada)?\s+DOF\s+(\d{2})-(\d{2})-(\d{4})", texto)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}", "encabezado del PDF"
    m = re.search(r"[ÚU]ltima reforma publicada en la\s+G\.?\s*O\.?\s*(?:C\.?\s*D\.?\s*M\.?\s*X\.?)?\s+el\s+(\d{1,2})\s+de\s+([a-záéíóú]+)\s+de\s+(\d{4})", texto[:3000], re.I)
    if m and m.group(2).lower() in MESES:
        return f"{m.group(3)}-{MESES[m.group(2).lower()]}-{int(m.group(1)):02d}", "encabezado del PDF (Gaceta Oficial)"
    fechas = []
    for linea in texto.splitlines():
        if re.search(r"reformad|adicionad|derogad|Reforma DOF|Fe de erratas", linea, re.I) and not re.search(r"Acuerdo", linea):
            fechas += [f"{y}-{mo}-{d}" for d, mo, y in re.findall(r"DOF\s+(\d{2})-(\d{2})-(\d{4})", linea)]
    return (max(fechas), "fecha más reciente citada en el texto (el PDF no trae encabezado de última reforma)") if fechas else (None, "sin dato")


def procesa(clave: str, pdf: Path, url: str, out_raiz: Path, nombre: str | None = None, datos: dict | None = None) -> dict:
    # `datos` (ámbito, entidad, materia, emisor, diario) no se llama meta: dentro del ciclo de artículos `meta` es el encabezado de cada uno
    datos = datos or {}
    nombre = nombre or LEYES[clave][1]
    emisor, diario = datos.get("emisor", "Cámara de Diputados"), datos.get("diario", "DOF")
    art = "el " if diario == "DOF" else ""
    with tempfile.TemporaryDirectory() as td:
        txt = Path(td) / "ley.txt"
        subprocess.run(["pdftotext", "-enc", "UTF-8", "-layout", str(pdf), str(txt)], check=True)
        texto = txt.read_text(encoding="utf-8", errors="replace")
    arts, orden, trans = extrae(texto)
    if len(orden) < 10:
        sys.exit(f"{clave}: solo encontré {len(orden)} artículos; el formato del PDF cambió, revisa el extractor")
    # auditoría integrada: cada línea que parece encabezado («Artículo N…») debe haberse leído como artículo
    lineas = limpia_pagina(texto.splitlines())
    fin = next((i for i, l in enumerate(lineas) if TRANSITORIOS.match(l)), len(lineas))
    sin_leer = [l.strip()[:60] for l in lineas[:fin] if INICIO.match(l) and not encabezado(l) and not NO_ENCABEZADO.match(l)]
    if sin_leer:
        sys.exit(f"{clave}: {len(sin_leer)} encabezados no se leyeron como artículo (ej.: {sin_leer[:3]}); revisa el extractor")
    dest = out_raiz / clave
    (dest / "articulos").mkdir(parents=True, exist_ok=True)
    for viejo in (dest / "articulos").glob("art-*.md"):
        viejo.unlink()
    reforma, origen_reforma = ultima_reforma(texto)
    previo = {}
    if (dest / "manifiesto.json").exists():  # el cotejo con el DOF lo hace una persona: regenerar no lo borra
        previo = json.loads((dest / "manifiesto.json").read_text(encoding="utf-8")).get("cotejado_dof", {})
    cotejo = {"ley_completa": previo.get("ley_completa"), "articulos": previo.get("articulos", {})}
    advertencias = []
    if (dest / "manifiesto.json").exists():  # advertencias puestas por una persona (p. ej. «el DOF publicó una reforma que este texto no trae»)
        advertencias = json.loads((dest / "manifiesto.json").read_text(encoding="utf-8")).get("advertencias", [])
    indice = {}
    for aid in orden:
        a = arts[aid]
        cuerpo = reflow(a["lineas"])
        cab = f"# {clave} · Artículo {aid.upper() if '-' in aid else aid}\n\n"
        c = cotejo["articulos"].get(aid) or cotejo["ley_completa"]
        meta = [f"Ley: {nombre} ({clave})",
                f"Texto según: {emisor}, última reforma {diario} {reforma or 'sin dato'} · {url}",
                f"Cotejado con {art}{diario}: " + (f"sí, {c['fecha']} ({c['decreto']})" if c else "NO (no se firma ningún parámetro que cite este artículo)")]
        if a["ubicacion"]:
            meta.insert(1, f"Ubicación: {a['ubicacion']}")
        cab += "\n".join(meta) + "\n\n"
        md = cab + cuerpo.rstrip() + "\n"
        f = dest / "articulos" / nombre_archivo(aid)
        f.write_text(md, encoding="utf-8", newline="\n")
        indice[aid] = {"archivo": f"articulos/{f.name}", "sha256": sha(cuerpo.encode()), "ubicacion": a["ubicacion"],
                       "derogado": bool(re.search(r"\bSe deroga\b", cuerpo[:400])) or bool(re.search(r"^\s*ART[ÍI]CULO\s[^\n(]{0,30}\(\s*DEROGAD", cuerpo[:120], re.I))}
    (dest / "transitorios.md").write_text(f"# {clave} · Transitorios\n\n" + reflow(trans).rstrip() + "\n", encoding="utf-8", newline="\n")
    (dest / "indice.json").write_text(json.dumps(indice, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    man = {"clave": clave, "nombre": nombre, "url": url, "fuente": f"{emisor} (texto vigente); cotejar contra {art}{diario}",
           "ultima_reforma_segun_pdf": reforma, "ultima_reforma_origen": origen_reforma, "descargado": dt.date.today().isoformat(),
           "sha256_pdf": sha(pdf.read_bytes()), "sha256_texto": sha("".join(indice[a]["sha256"] for a in orden).encode()),
           "cotejado_dof": cotejo, "advertencias": advertencias, "articulos": len(orden), "derogados": sum(1 for a in indice.values() if a["derogado"])}
    man.update({k: datos[k] for k in ("ambito", "entidad", "materia", "emisor", "diario") if k in datos})
    (dest / "manifiesto.json").write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return man


def baja(url: str, destino: Path):
    req = urllib.request.Request(url, headers={"User-Agent": "timbra-reglas/0.1 (biblioteca de leyes)"})
    with urllib.request.urlopen(req, timeout=180) as r:
        destino.write_bytes(r.read())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clave", nargs="?")
    ap.add_argument("--pdf", type=Path)
    ap.add_argument("--todas", action="store_true")
    ap.add_argument("--out", type=Path, default=RAIZ / "fuentes" / "leyes")
    ap.add_argument("--url", help="URL oficial de la ley (obligatoria si no está en el catálogo federal)")
    ap.add_argument("--nombre", help="nombre oficial de la ley (ley fuera del catálogo federal)")
    ap.add_argument("--ambito", choices=sorted(va.AMBITOS))
    ap.add_argument("--entidad", help="clave ISO de la entidad (fuentes/entidades.yaml), por ejemplo QUE")
    ap.add_argument("--materia", choices=sorted(va.MATERIAS))
    ap.add_argument("--emisor", help="quién publica el texto (congreso o periódico oficial del estado)")
    ap.add_argument("--diario", default="Periódico Oficial", help="diario donde se publican sus reformas (defecto en leyes fuera del catálogo)")
    a = ap.parse_args()
    if a.todas:
        claves = sorted(LEYES)
    elif a.clave:
        claves = [a.clave]
    else:
        ap.error("indica una clave o --todas")
    for c in claves:
        if c in LEYES:
            url, nombre, meta = BASE_URL.format(ruta=LEYES[c][0]), None, None
        else:  # ley estatal o municipal: se registra con su URL oficial y sus datos
            if not (a.url and a.nombre and a.ambito in ("estatal", "municipal") and a.entidad and a.materia and a.emisor):
                ap.error(f"{c} no está en el catálogo federal: da --url, --nombre, --ambito (estatal o municipal), --entidad, --materia y --emisor")
            entidades = va.carga_entidades()
            if a.entidad not in entidades:
                ap.error(f"entidad {a.entidad!r} no válida; usa una clave de fuentes/entidades.yaml")
            if not re.fullmatch(rf"{a.entidad}-[A-Z0-9]+(-[A-Z0-9]+)*", c):
                ap.error(f"la clave de una ley de {a.entidad} debe ser {a.entidad}-<SIGLAS> (por ejemplo {a.entidad}-XXXX)")
            if not va.dominio_oficial(a.url):
                ap.error(f"{a.url} no es de un dominio oficial (fuentes/dominios_oficiales.yaml): solo fuente primaria")
            url, nombre = a.url, a.nombre
            meta = {"ambito": a.ambito, "entidad": a.entidad, "materia": a.materia, "emisor": a.emisor, "diario": a.diario}
        with tempfile.TemporaryDirectory() as td:
            pdf = a.pdf if (a.pdf and not a.todas) else Path(td) / f"{c}.pdf"
            if not (a.pdf and not a.todas):
                baja(url, pdf)
            m = procesa(c, pdf, url, a.out, nombre, meta)
        print(f"{c}: {m['articulos']} artículos ({m['derogados']} derogados), última reforma según el PDF: {m['ultima_reforma_segun_pdf']}")


if __name__ == "__main__":
    main()
