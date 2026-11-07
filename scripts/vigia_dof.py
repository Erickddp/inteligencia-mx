#!/usr/bin/env python3
"""Vigía del DOF: lee el índice diario del Diario Oficial y marca las notas que pueden cambiar la base fiscal.

  python scripts/vigia_dof.py --fecha 2026-11-05                 # un día
  python scripts/vigia_dof.py --desde 2026-10-20 --hasta 2026-11-05
  python scripts/vigia_dof.py --html guardado.html --fecha 2026-11-05   # sin red (pruebas)
  python scripts/vigia_dof.py --fecha 2026-11-05 --todas         # también las que no tocan la base

Salida: JSON. Cada nota relevante trae código, título, organismo, URL, temas y los parámetros / reglas / leyes que podría tocar.

IMPORTANTE (qué es y qué NO es):
- El DOF no publica una API documentada. Esto lee el HTML del índice del día (https://dof.gob.mx/index_111.php); si el DOF cambia
  su página, `parsea` devuelve 0 notas y el script SALE CON ERROR en vez de decir «no hubo nada». Un Vigía mudo es peor que ninguno.
- Usa el dominio sin «www» (el certificado de www.dof.gob.mx falla).
- El Vigía NUNCA escribe valores de ley. Solo avisa: un humano abre el issue «cambio de ley», investiga la fuente primaria y firma.
- Tipo de cambio, TIIE, UDI, INPC y los estímulos semanales de combustibles salen aparte en `datos_periodicos`: son datos de serie, no cambios de ley.
"""
import argparse, datetime as dt, html, json, re, sys, time, urllib.request

URL = "https://dof.gob.mx/index_111.php?year={y}&month={m:02d}&day={d:02d}"
NOTA = "https://dof.gob.mx/nota_detalle.php?codigo={codigo}&fecha={fecha}"

PODER = re.compile(r'class="txt_blanco2">\s*(?:&nbsp;)*\s*([^<]+?)\s*</td>', re.S)
SECCION = re.compile(r'class="txt_blanco">\s*(?:&nbsp;)*\s*([^<]+?)\s*</td>', re.S)
EDICION = re.compile(r"Fecha:\s*(\d{2}/\d{2}/\d{4})\s*-\s*Edici(?:&oacute;|ó)n\s+(\w+)", re.I)
ORGANISMO = re.compile(r'class="subtitle_azul">\s*(?:&nbsp;)*\s*([^<]+?)\s*(?:<a|</td>)', re.S)
LINK = re.compile(r'<a[^>]+href="/?nota_detalle\.php\?codigo=(\d+)&amp;fecha=(\d{2}/\d{2}/\d{4})"[^>]*>\s*(.*?)\s*</a>', re.S)

# tema -> (patrón en el título, qué toca de la base)
TEMAS = [
    ("rmf", r"Resoluci[óo]n Miscel[áa]nea Fiscal|Resoluci[óo]n de Facilidades Administrativas|Anexo\s+\d+[^.]*Resoluci[óo]n Miscel[áa]nea|Resoluci[óo]n que modifica la Resoluci[óo]n Miscel", {"reglas": "R-* (RMF)", "leyes": ["RMF"]}),
    ("isr", r"Impuesto sobre la Renta|\bISR\b|tarifa[s]? (?:del )?art[íi]culo (?:96|106|113|152)|subsidio para el empleo", {"parametros": ["ISR_TARIFA_*", "SUBSIDIO_EMPLEO_*", "RESICO_*", "ISR_PM_TASA"], "leyes": ["LISR"]}),
    ("iva", r"Impuesto al Valor Agregado|\bIVA\b|franja fronteriza|regi[óo]n fronteriza", {"parametros": ["IVA_*"], "leyes": ["LIVA"]}),
    ("ieps", r"Impuesto Especial sobre Producci[óo]n y Servicios|\bIEPS\b", {"leyes": ["LIEPS"]}),
    ("cff", r"C[óo]digo Fiscal de la Federaci[óo]n|factor de actualizaci[óo]n|tasa de recargos|recargos|comprobantes? fiscal|CFDI|contabilidad electr[óo]nica", {"parametros": ["RECARGOS_*", "CFDI_*", "CONTA_ELEC_*"], "leyes": ["CFF"]}),
    ("ingresos", r"Ley de Ingresos de la Federaci[óo]n|Paquete Econ[óo]mico|Criterios Generales de Pol[íi]tica Econ[óo]mica|Miscel[áa]nea de Contribuciones", {"leyes": ["LIF", "LISR", "LIVA", "CFF"]}),
    ("estimulos", r"Decreto[^.]*(?:est[íi]mulo|beneficio|facilidad)[^.]*fiscal|est[íi]mulos? fiscal", {"parametros": ["FRONTERA_*"], "reglas": "R-103"}),
    ("uma", r"Unidad de Medida y Actualizaci[óo]n|\bUMA\b", {"parametros": ["UMA_*"]}),
    ("salario_minimo", r"salarios? m[íi]nimos?|Comisi[óo]n Nacional de los Salarios M[íi]nimos", {"parametros": ["SM_*"]}),
    ("imss", r"Seguro Social|\bIMSS\b|cuotas obrero|prima de riesgo|[Uu]nidad de Medida", {"parametros": ["IMSS_*", "PRIMA_RIESGO_*", "SBC_*"], "leyes": ["LSS"]}),
    ("infonavit", r"Infonavit|Fondo Nacional de la Vivienda|aportaciones? patronales?", {"parametros": ["INFONAVIT_*"], "leyes": ["LINFONAVIT"]}),
    ("trabajo", r"Ley Federal del Trabajo|reparto de utilidades|aguinaldo|vacaciones dignas|jornada (?:laboral|de trabajo)|\bPTU\b|subcontrataci[óo]n", {"parametros": ["LFT_*", "PTU_*"], "leyes": ["LFT"]}),
    ("antilavado", r"Procedencia Il[íi]cita|lavado de dinero|actividades vulnerables|Unidad de Inteligencia Financiera|\bUIF\b", {"leyes": ["LFPIORPI"]}),
    ("nomina_estatal", r"impuesto sobre n[óo]minas|Impuesto sobre Erogaciones", {"parametros": ["ISN_TASA_TABLA"]}),
    ("inpc", r"[ÍI]ndice Nacional de Precios al Consumidor|\bINPC\b", {"parametros": ["ACTUALIZACION_*"], "serie": "INPC"}),
]
TEMAS = [(n, re.compile(p, re.I), toca) for n, p, toca in TEMAS]
# organismos cuyas notas pesan aunque el título no diga la palabra
ORGANISMOS = re.compile(r"HACIENDA Y CREDITO PUBLICO|SERVICIO DE ADMINISTRACION TRIBUTARIA|SEGURO SOCIAL|FONDO NACIONAL DE LA VIVIENDA|SALARIOS MINIMOS|TRABAJO Y PREVISION SOCIAL|INSTITUTO NACIONAL DE ESTADISTICA", re.I)
# ruido: no cambian la base aunque mencionen un impuesto
RUIDO = re.compile(r"convenio (?:modificatorio|de coordinaci[óo]n|espec[íi]fico)|recinto portuario|nombramiento|licitaci[óo]n|aviso de deslinde|cambio de domicilio|subdelegaci|se destina[^.]*inmueble|inmueble federal|seguros y fianzas|sociedades controladoras|per[íi]odo vacacional|calendario oficial de suspensi[óo]n|ejecutorias de amparo", re.I)
# publicaciones periódicas: son DATOS de una serie, no cambios de ley (alimentan series/, no abren issue)
DATOS = [(re.compile(p, re.I), s) for p, s in [
    (r"Tipo de cambio para solventar obligaciones", "tipo_cambio_dof"),
    (r"Tasa de inter[ée]s interbancaria|TIIE", "tiie"),
    (r"Valor de la Unidad de Inversi[óo]n", "udi"),
    (r"Costo de captaci[óo]n|Tasa de rendimiento|CETES", "tasas"),
    (r"^[ÍI]ndice nacional de precios al consumidor\.?$", "inpc"),
    (r"est[íi]mulos? fiscal[^.]*(?:gasolina|di[ée]sel|combustibles)|cuotas disminuidas|enajenaci[óo]n de gasolinas", "estimulo_combustibles"),
]]


def limpia(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def parsea(doc: str) -> list[dict]:
    """Recorre el HTML en orden: la última sección/poder/organismo vista es la de cada nota."""
    doc = re.sub(r"<!--.*?-->", "", doc, flags=re.S)  # el DOF deja imágenes y etiquetas comentadas dentro de los encabezados
    eventos = []
    for rx, tipo in ((SECCION, "seccion"), (PODER, "poder"), (ORGANISMO, "organismo"), (LINK, "nota"), (EDICION, "edicion")):
        for m in rx.finditer(doc):
            eventos.append((m.start(), tipo, m))
    eventos.sort(key=lambda e: e[0])
    cur = {"seccion": "", "poder": "", "organismo": "", "edicion": ""}
    notas = []
    for _, tipo, m in eventos:
        if tipo == "nota":
            codigo, fecha, titulo = m.group(1), m.group(2), limpia(m.group(3))
            notas.append({"codigo": codigo, "fecha": dt.datetime.strptime(fecha, "%d/%m/%Y").date().isoformat(), "titulo": titulo,
                          "seccion": cur["seccion"], "poder": cur["poder"], "organismo": cur["organismo"], "edicion": cur["edicion"],
                          "url": NOTA.format(codigo=codigo, fecha=fecha)})
        elif tipo == "edicion":
            cur["edicion"] = m.group(2).capitalize()
        else:
            v = limpia(m.group(1))
            if v:
                cur[tipo] = v
    return notas


def clasifica(n: dict) -> dict | None:
    """None si no toca la base. Si toca: temas y qué parámetros, reglas o leyes revisar."""
    t = n["titulo"]
    for rx, serie in DATOS:
        if rx.search(t):
            return {"tipo": "dato_periodico", "serie": serie}
    temas = [nombre for nombre, rx, _ in TEMAS if rx.search(t)]
    if not temas and re.search(r"SALARIOS MINIMOS", n["organismo"], re.I):
        temas = ["salario_minimo"]  # las resoluciones de CONASAMI traen títulos genéricos («Resolución del H. Consejo de Representantes…»)
    por_organismo = bool(ORGANISMOS.search(n["organismo"])) and not temas
    if RUIDO.search(t):
        return None
    if not temas and not por_organismo:
        return None
    toca = {"parametros": [], "reglas": [], "leyes": []}
    for nombre, _, d in TEMAS:
        if nombre in temas:
            toca["parametros"] += d.get("parametros", [])
            toca["leyes"] += d.get("leyes", [])
            if d.get("reglas"):
                toca["reglas"].append(d["reglas"])
    nivel = "alta" if any(x in temas for x in ("rmf", "isr", "iva", "cff", "ingresos", "uma", "salario_minimo", "imss", "infonavit", "estimulos")) else "media"
    if por_organismo:
        nivel, temas = "baja", ["organismo_relevante"]
    return {"tipo": "posible_cambio", "nivel": nivel, "temas": temas, **{k: sorted(set(v)) for k, v in toca.items()}}


def descarga(dia: dt.date, intentos: int = 3) -> str:
    url = URL.format(y=dia.year, m=dia.month, d=dia.day)
    req = urllib.request.Request(url, headers={"User-Agent": "timbra-reglas-vigia/0.1 (lectura del indice diario del DOF)"})
    for i in range(intentos):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            if i == intentos - 1:
                raise SystemExit(f"No pude leer el DOF del {dia}: {e}")
            time.sleep(2 ** (i + 1))


def vigila(dia: dt.date, doc: str, todas: bool = False, bajas: bool = False) -> dict:
    notas = parsea(doc)
    if not notas and "Fecha:" in doc:
        # la página dice que hay edición pero no se leyó ninguna nota: el DOF cambió su HTML. Un Vigía mudo es peor que ninguno.
        raise SystemExit(f"{dia}: la página del DOF tiene edición pero cero notas leídas. Probable cambio de formato: revisa el lector, no confíes en «sin novedades».")
    if not notas:
        aviso = {"fecha": dia.isoformat(), "notas_leidas": 0, "sin_edicion": True, "posibles_cambios": [], "datos_periodicos": [], "otras": 0}
        if dia.weekday() < 5:
            aviso["alerta"] = "día hábil sin edición: puede ser un feriado o un cambio de formato de la página; si se repite, revísalo"
        return aviso
    out = {"fecha": dia.isoformat(), "notas_leidas": len(notas), "posibles_cambios": [], "datos_periodicos": [], "otras": 0}
    for n in notas:
        c = clasifica(n)
        if c is None:
            out["otras"] += 1
            if todas:
                out.setdefault("descartadas", []).append(n)
        elif c["tipo"] == "dato_periodico":
            out["datos_periodicos"].append({"serie": c["serie"], "codigo": n["codigo"], "titulo": n["titulo"], "url": n["url"]})
        elif c["nivel"] == "baja" and not bajas:
            out["otras"] += 1
        else:
            out["posibles_cambios"].append({**n, **c})
    return out


def lee_dia(dia: dt.date, html_local: str | None, todas: bool = False, bajas: bool = False, espera: float = 3.0) -> dict:
    """Lee y clasifica un día. Una respuesta incompleta del servidor se ve igual que un cambio de formato (edición sin notas): se
    reintenta una vez con la página bajada de nuevo antes de dar la alarma. Con --html no hay reintento (el archivo es el mismo)."""
    if html_local:
        return vigila(dia, open(html_local, encoding="utf-8", errors="replace").read(), todas, bajas)
    try:
        return vigila(dia, descarga(dia), todas, bajas)
    except SystemExit as e:
        if "cero notas" not in str(e):
            raise
        time.sleep(espera)
        return vigila(dia, descarga(dia), todas, bajas)  # si vuelve a fallar, la alarma es real


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fecha")
    ap.add_argument("--desde")
    ap.add_argument("--hasta")
    ap.add_argument("--html", help="usa este archivo en vez de bajar el DOF (solo con --fecha)")
    ap.add_argument("--todas", action="store_true", help="incluye también las notas descartadas")
    ap.add_argument("--bajas", action="store_true", help="incluye las de prioridad baja (solo coinciden por el organismo)")
    a = ap.parse_args()
    d0 = dt.date.fromisoformat(a.desde or a.fecha or dt.date.today().isoformat())
    d1 = dt.date.fromisoformat(a.hasta or a.fecha or d0.isoformat())
    res, d = [], d0
    while d <= d1:
        res.append(lee_dia(d, a.html, a.todas, a.bajas))
        d += dt.timedelta(days=1)
        if not a.html and d <= d1:
            time.sleep(1.5)  # cortesía con el servidor
    json.dump(res if len(res) > 1 else res[0], sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
