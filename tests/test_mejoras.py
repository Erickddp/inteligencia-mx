"""El plan de mejora, el backlog y la capa de búsqueda: bien formados, medibles y apuntando a artículos que existen."""
import json
import re
import unicodedata

import yaml

from conftest import RAIZ

MEJORAS = yaml.safe_load((RAIZ / "mejoras" / "backlog.yaml").read_text(encoding="utf-8"))["mejoras"]
PLAN = (RAIZ / "docs" / "PLAN_DE_MEJORA.md").read_text(encoding="utf-8")
PERFILES = yaml.safe_load((RAIZ / "busqueda" / "perfiles.yaml").read_text(encoding="utf-8"))
SINONIMOS = yaml.safe_load((RAIZ / "busqueda" / "sinonimos.yaml").read_text(encoding="utf-8"))["grupos"]
DORADAS = yaml.safe_load((RAIZ / "busqueda" / "preguntas_doradas.yaml").read_text(encoding="utf-8"))["preguntas"]
MATERIAS = {"fiscal", "contable", "laboral", "seguridad_social", "mercantil", "civil", "penal", "electoral", "administrativo", "otra"}


def sin_acentos(t):
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")


def articulo(ley, art, anio=None):
    """Texto del artículo o regla de la biblioteca, o None si no existe."""
    if ley == "RMF":
        base = RAIZ / "fuentes" / "rmf" / str(anio) / f"RMF{anio}"
    else:
        base = RAIZ / "fuentes" / "leyes" / ley
    if not (base / "indice.json").is_file():
        return None
    ix = json.loads((base / "indice.json").read_text(encoding="utf-8"))
    return (base / ix[str(art)]["archivo"]).read_text(encoding="utf-8") if str(art) in ix else None


# ---------- backlog ----------
def test_backlog_bien_formado():
    ids = [m["id"] for m in MEJORAS]
    assert len(ids) == len(set(ids)) and all(re.fullmatch(r"M-\d{3}", i) for i in ids)
    for m in MEJORAS:
        assert m["fase"] in (1, 2, 3, "futuro"), m["id"]
        assert m["estado"] in ("abierta", "en_curso", "hecha"), m["id"]
        assert m["quien"] in ("abierto", "dueno"), m["id"]
        assert m["rama"] is None or re.fullmatch(r"mejora/[a-z0-9-]+", m["rama"]), m["id"]
        for k in ("titulo", "que_es", "criterio_de_aceptacion", "como_aportar"):
            assert m[k] and len(m[k]) > 20, f"{m['id']}: falta {k}"
        for d in m["datos"]:
            assert (RAIZ / d).exists(), f"{m['id']}: {d} no existe"


def test_las_tres_fases_de_hoy_estan_completas():
    por_fase = {f: [m["id"] for m in MEJORAS if m["fase"] == f] for f in (1, 2, 3)}
    assert len(por_fase[1]) >= 5 and len(por_fase[2]) >= 3 and len(por_fase[3]) >= 4


def test_el_plan_menciona_cada_mejora_y_cada_rama():
    faltan = [m["id"] for m in MEJORAS if m["id"] not in PLAN]
    assert not faltan, f"el plan no menciona: {faltan}"
    ramas = {m["rama"] for m in MEJORAS if m["rama"]}
    assert len(ramas) >= 8 and all(f"`{r}`" in PLAN for r in ramas), [r for r in ramas if f"`{r}`" not in PLAN]


def test_el_plan_declara_su_principio():
    assert "Nunca escribe una cifra" in PLAN and "lee" in PLAN.lower()


def test_los_enlaces_de_los_documentos_nuevos_existen():
    for doc in ("docs/PLAN_DE_MEJORA.md", "busqueda/README.md", "datos_abiertos/README.md"):
        p = RAIZ / doc
        for destino in re.findall(r"\]\(((?!http)[^)#]+)", p.read_text(encoding="utf-8")):
            assert (p.parent / destino).exists(), f"{doc} enlaza a {destino} y no existe"


def test_la_plantilla_de_propuesta_de_mejora():
    t = yaml.safe_load((RAIZ / ".github" / "ISSUE_TEMPLATE" / "propuesta_de_mejora.yml").read_text(encoding="utf-8"))
    ids = {b["id"] for b in t["body"] if "id" in b}
    assert {"area", "problema", "propuesta", "medida"} <= ids and t["labels"] == ["mejora"]


# ---------- perfiles de búsqueda ----------
def test_perfiles_bien_formados():
    metodos = set(PERFILES["metodos"])
    assert {"palabras_clave", "bm25", "semantico", "hibrido"} <= metodos
    ids = [p["id"] for p in PERFILES["perfiles"]]
    assert len(ids) == len(set(ids)) >= 6
    for p in PERFILES["perfiles"]:
        assert p["metodo"] in metodos and isinstance(p["k"], int) and 1 <= p["k"] <= 50, p["id"]
        assert set(p["filtros"]) <= {"ambito", "entidad", "materia", "cotejado", "derogado", "tipo"}, p["id"]
        assert set(p["campos"]) <= {"numero", "ubicacion", "texto"} and all(v > 0 for v in p["campos"].values()), p["id"]
        assert isinstance(p["expandir_sinonimos"], bool) and len(p["descripcion"]) > 20, p["id"]
        if "materia" in p["filtros"]:
            assert p["filtros"]["materia"] in MATERIAS, p["id"]
        if "ambito" in p["filtros"]:
            assert p["filtros"]["ambito"] in ("federal", "estatal", "municipal"), p["id"]


# ---------- sinónimos ----------
def test_cada_sinonimo_tiene_evidencia_real():
    assert len(SINONIMOS) >= 10
    for g in SINONIMOS:
        assert len(g["terminos"]) >= 2 and g["evidencia"], g["terminos"]
        for e in g["evidencia"]:
            texto = articulo(e["ley"], e["articulo"], e.get("anio"))
            assert texto is not None, f"{e['ley']} {e['articulo']} no existe en la biblioteca"
            assert sin_acentos(re.sub(r"\s+", " ", e["contiene"])) in sin_acentos(re.sub(r"\s+", " ", texto)), \
                f"{e['ley']} art. {e['articulo']} no contiene «{e['contiene']}»"


# ---------- preguntas doradas ----------
def test_preguntas_doradas_resuelven_a_articulos_reales():
    ids = [q["id"] for q in DORADAS]
    assert len(DORADAS) >= 20 and len(ids) == len(set(ids)) and all(re.fullmatch(r"G-\d{3}", i) for i in ids)
    for q in DORADAS:
        assert q["pregunta"].startswith("¿") and q["pregunta"].endswith("?"), q["id"]
        assert q["materia"] in MATERIAS and q["esperado"], q["id"]
        for e in q["esperado"]:
            assert articulo(e["ley"], e["articulo"], e.get("anio")) is not None, f"{q['id']}: {e} no existe en la biblioteca"


def test_las_preguntas_doradas_cubren_varios_ambitos_y_materias():
    leyes = {e["ley"] for q in DORADAS for e in q["esperado"]}
    assert {"LISR", "LIVA", "CFF", "LFT", "RMF", "CMX-CP"} <= leyes          # federal, reglas, y una ley estatal
    assert {q["materia"] for q in DORADAS} >= {"fiscal", "laboral", "contable", "penal"}


def test_los_articulos_esperados_no_estan_derogados():
    for q in DORADAS:
        for e in q["esperado"]:
            if e["ley"] != "RMF":
                ix = json.loads((RAIZ / "fuentes" / "leyes" / e["ley"] / "indice.json").read_text(encoding="utf-8"))
                assert not ix[str(e["articulo"])]["derogado"], f"{q['id']}: {e['ley']} {e['articulo']} está derogado"
