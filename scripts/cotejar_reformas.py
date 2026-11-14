#!/usr/bin/env python3
"""Verificación de reformas: compara lo que los decretos del DOF reimprimen contra el texto de un artículo de la biblioteca.

  python scripts/cotejar_reformas.py LISR:34 CFF:28 LIVA:5 [--cache DIR] [--registrar]

El DOF no publica leyes consolidadas: sólo los decretos de reforma, que reimprimen los párrafos que cambian y dejan «...» donde
no hay cambio. Por eso esto NO es el cotejo humano de M-102 y NO marca el artículo como cotejado. Lo que sí hace:
  1. Lee en el artículo de la biblioteca las notas al pie de la Cámara («Párrafo reformado DOF 12-11-2021») para saber qué decretos lo tocaron
     (y, en la LISR, suma el decreto que expidió la ley el 11-dic-2013, que la trae completa).
  2. Baja esos decretos del DOF, ubica el artículo de la ley correcta y separa los párrafos que reimprime (lo que no son «...»).
  3. Comprueba que cada párrafo aparezca literal en el texto de la biblioteca (sin las notas al pie) y que cada cifra del decreto esté en el artículo
     (las tablas del PDF de la Cámara salen revueltas: se comparan por sus números).
  4. Mide la cobertura: qué parte del artículo quedó verificada contra una publicación del DOF.
Una pieza que no coincide en un decreto viejo suele ser un texto que un decreto posterior reformó. Estado del artículo:
  verificado_en_la_reforma_mas_reciente        todo lo que reimprime el decreto más reciente de las notas al pie está en la biblioteca
  discrepancia_en_la_reforma_mas_reciente      algo que reimprime ese decreto NO está en la biblioteca: revisar a mano
  reforma_mas_reciente_sin_verificar           una fecha de las notas al pie no tiene decreto que reimprima el artículo (no se encontró, o es de otro tipo)
  sin_decreto_que_lo_reimprima                 ningún decreto lo reimprime: sólo cubre el texto original
Con --registrar guarda el resultado en fuentes/leyes/<LEY>/manifiesto.json (clave `cotejo_reformas`), aparte de `cotejado_dof`, que sigue
reservado a la persona que coteja.
"""
import argparse
import collections
import difflib
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LEYES = RAIZ / "fuentes" / "leyes"
INDICE = "https://dof.gob.mx/index_111.php?year={y}&month={m}&day={d}&edicion={ed}"
NOTA = "https://dof.gob.mx/nota_detalle_popup.php?codigo={c}"
UA = {"User-Agent": "Mozilla/5.0"}
LEYES_NOMBRE = {"Código Fiscal de la Federación": "CFF", "Ley del Impuesto sobre la Renta": "LISR",
                "Ley del Impuesto al Valor Agregado": "LIVA", "Ley del Seguro Social": "LSS", "Ley Federal del Trabajo": "LFT",
                "Ley del Impuesto Especial sobre Producción y Servicios": "LIEPS"}
# Decretos que expidieron la ley completa: reimprimen TODOS sus artículos. (fecha DOF, nota, el documento entero es la ley).
# La LISR vigente (2014) salió en dos notas del DOF: la primera sección arranca con «Artículo Séptimo. Se expide la Ley...» y la segunda sigue sin encabezado.
ORIGEN = {"LISR": [("11-12-2013", "5325371", False), ("11-12-2013", "5325373", True)]}
ART = r"Art.{0,2}culo"   # los decretos viejos del DOF traen «ART CULO» (la tilde llega corrupta)
ORDINALES = r"(?:Primero|Segundo|Tercero|Cuarto|Quinto|Sexto|S.{0,2}ptimo|Octavo|Noveno|D.{0,2}cimo|.{0,2}nico)"
ANOTACION = re.compile(r"_[^_\n]*(?:DOF|Reforma|Fe de erratas|derogad)[^_\n]*_")
FECHA_DOF = re.compile(r"(\d{2})-(\d{2})-(\d{4})")   # todas las fechas de cada nota al pie («DOF 11-12-2013, 30-11-2016 y 09-12-2019»)
NUMERO = re.compile(r"\d[\d,]*(?:\.\d+)?%?")
SEP_ELIPSIS = re.compile(r"(?:\.\s?){3,}|\s…\s")


def limpia(s: str, conserva_parrafos: bool = False) -> str:
    s = html.unescape(s).replace(" ", " ")
    for a, b in (("“", '"'), ("”", '"'), ("«", '"'), ("»", '"'), ("’", "'"), ("‘", "'"), ("–", "-"), ("—", "-")):
        s = s.replace(a, b)
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    s = re.sub(r" +([.,;:)])", r"\1", s)                 # «II .» «Artículo 210 .» del DOF
    s = re.sub(r'"[ \t]+([^"\n]*?)[ \t]+"', r'"\1"', s)       # «" IVA incluido "» del DOF
    if conserva_parrafos:
        return "\n".join(x.strip() for x in s.split("\n") if x.strip())
    return re.sub(r"\s+", " ", s).strip()


def plano(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def texto_html(h: str) -> str:
    """El decreto como texto, con un salto de línea por párrafo (cada <p>, <br> o fila)."""
    h = re.sub(r"<style.*?</style>|<script.*?</script>", "", h, flags=re.S)
    h = re.sub(r"</?(?:p|br|div|tr|li|h\d)[^>]*>", "\n", h, flags=re.I)
    return limpia(re.sub(r"<[^>]+>", " ", h), conserva_parrafos=True)


def _patron_ley(nombre: str) -> re.Pattern:
    """El nombre de la ley tolerando acentos corruptos: «C DIGO FISCAL DE LA FEDERACI N»."""
    return re.compile("".join(".{0,2}" if c in "áéíóúÁÉÍÓÚ" else re.escape(c) for c in nombre), re.I)


PATRONES_LEY = {_patron_ley(n): c for n, c in LEYES_NOMBRE.items()}


def _ley_en(texto: str):
    mejor = None
    for pat, clave in PATRONES_LEY.items():
        for m in pat.finditer(texto):
            if mejor is None or m.start() > mejor[0]:
                mejor = (m.start(), clave)
    return mejor[1] if mejor else None


def secciones(t: str) -> list:
    """[(ley, texto)] de cada «Artículo Primero.- Se reforman ...». Dos formatos de decreto:
    nuevo  «Artículo Primero.- Se reforman los artículos ..., de la Ley X, para quedar como sigue»;
    viejo  «LEY X ARTÍCULO PRIMERO.- Se reforman los artículos ...» (el nombre de la ley va antes del encabezado)."""
    pos = [m.start() for m in re.finditer(rf"{ART} {ORDINALES}\.?-?\s+Se\s", t, re.I)]
    out = []
    for k, p in enumerate(pos):
        fin = pos[k + 1] if k + 1 < len(pos) else len(t)
        sec = t[p:fin]
        i_pq = sec.find("para quedar como sigue")
        ley = _ley_en(sec[:i_pq]) if 0 < i_pq < 20000 else None
        if ley is None and re.match(rf"{ART} {ORDINALES}\.?-?\s+Se expide", sec, re.I):
            ley = _ley_en(sec[:200])                      # «Artículo Séptimo. Se expide la Ley del Impuesto sobre la Renta:»
        if ley is None:
            ley = _ley_en(t[max(0, p - 90):p])
        out.append((ley, sec))
    return out


FIN_ENCABEZADO = r"(?=\s|\.{3}|$)"   # «Artículo 34. I.» o pegado a los puntos suspensivos: «Artículo 34....»


def articulo(sec: str, num: str):
    m0 = re.match(r"(\d+)(?:-([a-z]+))?$", num.lower())
    n, suf = m0.group(1), m0.group(2)
    pat = rf"(?:^|\n){ART} {n}o?(?:\.-?|-){suf}\.-?" if suf else rf"(?:^|\n){ART} {n}o?\.-?"
    m = re.search(pat + FIN_ENCABEZADO, sec, re.I)
    if not m:
        return None
    ini = m.start() + (1 if sec[m.start()] == "\n" else 0)
    sig = re.search(rf"\n{ART} \d+o?(?:\.-?|-)?[A-Z]*(?: BIS| Bis| TER| Ter)?\.-?" + FIN_ENCABEZADO, sec[m.end():], re.I)
    return sec[ini: m.end() + (sig.start() if sig else len(sec) - m.end())]


def piezas(txt: str) -> list:
    """Los párrafos que el decreto reimprime: cada línea que no es un «...»."""
    txt = re.sub(rf"^{ART} \d+o?(?:\.-?|-)?[A-Za-z]*\.?-?", "", txt)
    out = []
    for linea in txt.split("\n"):
        for p in SEP_ELIPSIS.split(linea):
            p = re.sub(r"^(?:Segundo|Primer|Tercer|Cuarto|Quinto)\w* p[aá]rrafo(?:\s*\((?:Se )?deroga\)|\s+derogado)\.?\s*", "", p.strip(" .;,")).strip(" .;,")
            if re.fullmatch(r"(?:[IVXL]+\.?|[a-z]\)|\d+\.)(?:\s+(?:a|y)\s+(?:[IVXL]+\.?|[a-z]\)))*", p) or len(p) < 25:
                continue
            if p.isupper() and len(p) < 160:                    # título de capítulo o nombre de la ley siguiente que se cuela
                continue
            if re.fullmatch(r"(?i)(?:\w+\s+){0,3}(?:p[aá]rrafos?|fracci[oó]n(?:es)?|incisos?|numerales?)[\s.]*\(?(?:se\s+)?deroga(?:d[oa]s?)?\)?\.?", p):
                continue                                         # «Cuarto párrafo. Se deroga»: leyenda del decreto, no texto de ley
            out.append(p)
    return out


def sin_marca(p: str) -> str:
    return re.sub(r"^(?:[IVXL]+\.|[a-z]\)|\d+\.)\s+", "", p)


def texto_biblioteca(ruta: Path) -> str:
    return plano(limpia(ANOTACION.sub("", ruta.read_text(encoding="utf-8"))).replace("_", ""))


def numeros(s: str) -> collections.Counter:
    return collections.Counter(x.rstrip(".,") for x in NUMERO.findall(s))


def tilde_perdida(p: str, lib: str) -> bool:
    """Los popups del DOF pierden algunas tildes y diéresis («antig edad»). Es la misma pieza si el ÚNICO cambio contra la biblioteca
    es un espacio donde ella tiene una letra con tilde, diéresis o ñ."""
    pp = plano(sin_marca(p))
    if len(pp) < 40:
        return False
    sm = difflib.SequenceMatcher(None, pp, lib, autojunk=False)
    b = sm.find_longest_match(0, len(pp), 0, len(lib))
    if b.size < 20:
        return False
    ini = max(0, b.b - b.a)
    ops = [o for o in difflib.SequenceMatcher(None, pp, lib[ini: ini + len(pp)], autojunk=False).get_opcodes() if o[0] != "equal"]
    return bool(ops) and all(o[0] == "replace" and pp[o[1]:o[2]] == " " and re.fullmatch("[áéíóúüñÁÉÍÓÚÜÑ]", lib[ini + o[3]: ini + o[4]] or "") for o in ops)


def encabezado_de_tabla(p: str, lib: str) -> bool:
    """Texto de una tabla sin cifras, que el PDF de la Cámara trae revuelto: todas sus palabras están en el artículo."""
    if re.search(r"\d", p) or len(p) > 250 or p.rstrip().endswith("."):
        return False
    return not (collections.Counter(re.findall(r"\w+", p.lower())) - collections.Counter(re.findall(r"\w+", lib.lower())))


def verifica(dec_txt: str, ley: str, num: str, lib: str, ley_completa: bool = False):
    """-> dict con piezas, no_coinciden, numeros_faltantes y caracteres verificados; None si el decreto no reimprime el artículo.
    ley_completa: el decreto expide la ley (todo el documento es su texto, sin encabezados «Artículo Primero.- Se reforma»)."""
    for l, sec in ([(ley, dec_txt)] if ley_completa else secciones(dec_txt)):
        if l != ley:
            continue
        a = articulo(sec, num)
        if not a:
            continue
        ps = piezas(a)
        ok = [p for p in ps if plano(p) in lib or plano(sin_marca(p)) in lib]
        mal = [p for p in ps if p not in ok]
        # las tablas del PDF de la Cámara salen revueltas: una pieza con muchas cifras se juzga por sus números
        mal_texto = []
        for p in mal:
            n = numeros(p)
            if sum(n.values()) >= 8 and not (n - numeros(lib)) or tilde_perdida(p, lib) or encabezado_de_tabla(p, lib):
                ok.append(p)
            else:
                mal_texto.append(p)
        cuerpo = re.sub(rf"^{ART} \d+o?(?:\.-?|-)?[A-Za-z]*\.?-?", "", a)
        fuera = numeros(" ".join(SEP_ELIPSIS.split(cuerpo)))
        faltan = sorted((fuera - numeros(lib)).elements())
        return {"piezas": ps, "no_coinciden": mal_texto, "numeros_faltantes": faltan, "ok": ok}
    return None


def get(url: str, cache: Path | None, nombre: str) -> str:
    if cache and (cache / nombre).is_file():
        return (cache / nombre).read_text(encoding="utf-8", errors="replace")
    h = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read().decode("utf-8", errors="replace")
    if cache:
        cache.mkdir(parents=True, exist_ok=True)
        (cache / nombre).write_text(h, encoding="utf-8")
    return h


def decretos_del_dia(fecha: str, cache: Path | None) -> list:
    d, m, y = fecha.split("-")
    notas = []
    for ed in ("MAT", "VES", "EXT"):
        try:
            h = get(INDICE.format(y=y, m=m, d=d, ed=ed), cache, f"idx-{y}{m}{d}{ed}.html")
        except Exception:  # noqa: BLE001
            continue
        for mm in re.finditer(r'nota_detalle\.php\?codigo=(\d+)&(?:amp;)?fecha=[\d/]+[^>]*>(.*?)</a>', h, re.S):
            tit = plano(re.sub("<[^>]+>", "", html.unescape(mm.group(2))))
            if re.match(r"Decreto por el que se (reforman?|expide|adicionan?|derogan?)", tit, re.I):
                notas.append((mm.group(1), tit))
    return notas


_DECRETOS: dict = {}


def decreto(codigo: str, cache: Path | None) -> str:
    if codigo not in _DECRETOS:
        _DECRETOS[codigo] = texto_html(get(NOTA.format(c=codigo), cache, f"nota-{codigo}.html"))
    return _DECRETOS[codigo]


def ruta_articulo(ley: str, num: str) -> Path:
    n0 = num.split("-")
    return LEYES / ley / "articulos" / (f"art-{int(n0[0]):04d}" + (f"-{n0[1]}" if len(n0) > 1 else "") + ".md")


def revisa(ley: str, num: str, cache: Path | None) -> dict:
    ruta = ruta_articulo(ley, num)
    crudo = ruta.read_text(encoding="utf-8")
    lib = texto_biblioteca(ruta)
    fechas = sorted({f"{d}-{m}-{y}" for d, m, y in FECHA_DOF.findall("".join(ANOTACION.findall(crudo)))}, key=lambda f: f.split("-")[::-1])
    res = {"articulo": f"{ley} {num}", "fechas_en_notas": fechas, "decretos": [], "fechas_sin_decreto": []}
    origen_ley = {(f, c): completa for f, c, completa in ORIGEN.get(ley, [])}
    candidatos = list(origen_ley)
    for f in fechas:
        candidatos += [(f, c) for c, _t in decretos_del_dia(f, cache)]
    cubiertos = set()
    for f, codigo in sorted(set(candidatos), key=lambda x: x[0].split("-")[::-1]):
        try:
            t = decreto(codigo, cache)
        except Exception as e:  # noqa: BLE001
            res["decretos"].append({"dof": f, "nota": codigo, "error": str(e)[:120]})
            continue
        es_origen = (f, codigo) in origen_ley
        v = verifica(t, ley, num, lib, ley_completa=origen_ley.get((f, codigo), False))
        if v is None:
            continue
        res["decretos"].append({"dof": f, "nota": codigo, "tipo": "expide la ley" if es_origen else "reforma",
                                "url": f"https://dof.gob.mx/nota_detalle.php?codigo={codigo}&fecha={f.replace('-', '/')}",
                                "piezas": len(v["piezas"]), "coinciden": len(v["piezas"]) - len(v["no_coinciden"]),
                                "no_coinciden": [m[:200] for m in v["no_coinciden"]], "numeros_faltantes": v["numeros_faltantes"][:20]})
        cubiertos |= {plano(sin_marca(p)) for p in v["ok"]}
    con = [d for d in res["decretos"] if "piezas" in d]
    res["caracteres_verificados"] = min(sum(len(p) for p in cubiertos), len(lib))
    res["caracteres_articulo"] = len(lib)
    res["cobertura_pct"] = round(100 * res["caracteres_verificados"] / max(len(lib), 1), 1)
    fechas_con = {d["dof"] for d in con}
    res["fechas_sin_decreto"] = [f for f in fechas if f not in fechas_con]
    reformas = [d for d in con if d["tipo"] == "reforma"]
    reciente = (reformas or con or [None])[-1]
    res["decreto_mas_reciente"] = reciente["nota"] if reciente else None
    if not con:
        res["estado"] = "sin_decreto_que_lo_reimprima"
    elif fechas and fechas[-1] in res["fechas_sin_decreto"]:
        res["estado"] = "reforma_mas_reciente_sin_verificar"
    elif reciente["no_coinciden"] or reciente["numeros_faltantes"]:
        res["estado"] = "discrepancia_en_la_reforma_mas_reciente"
    else:
        res["estado"] = "verificado_en_la_reforma_mas_reciente"
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("articulos", nargs="+", help="LEY:artículo, por ejemplo LISR:34 LIVA:2-a")
    ap.add_argument("--cache", help="carpeta donde guardar lo bajado del DOF")
    ap.add_argument("--registrar", action="store_true")
    ap.add_argument("--fecha", default=None, help="fecha del cotejo (AAAA-MM-DD)")
    x = ap.parse_args()
    import datetime as dt
    hoy = x.fecha or dt.date.today().isoformat()
    cache = Path(x.cache) if x.cache else None
    for a in x.articulos:
        ley, num = a.split(":")
        r = revisa(ley, num, cache)
        print(json.dumps(r, ensure_ascii=False, indent=1))
        if x.registrar:
            p = LEYES / ley / "manifiesto.json"
            m = json.loads(p.read_text(encoding="utf-8"))
            m.setdefault("cotejo_reformas", {})[num] = {"fecha": hoy, "como": "scripts/cotejar_reformas.py (comparación automática contra decretos del DOF; no es cotejo humano)", **r}
            p.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
