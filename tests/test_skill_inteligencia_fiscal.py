"""La skill /inteligencia-fiscal: bien formada, pública en el repo y apuntando solo a lo que existe."""
import re

import yaml

from conftest import RAIZ

SKILL = RAIZ / ".claude" / "skills" / "inteligencia-fiscal" / "SKILL.md"
ESTANDAR = RAIZ / "docs" / "ESTANDAR_APORTACION.md"


def partes():
    t = SKILL.read_text(encoding="utf-8")
    _, cab, cuerpo = t.split("---", 2)
    return yaml.safe_load(cab), cuerpo


def test_encabezado_de_la_skill():
    cab, _ = partes()
    assert cab["name"] == "inteligencia-fiscal" and SKILL.parent.name == cab["name"]
    assert len(cab["description"]) > 150 and "/inteligencia-fiscal" in cab["description"] and "Querétaro" in cab["description"]


def test_la_skill_solo_menciona_archivos_que_existen():
    _, cuerpo = partes()
    rutas = set(re.findall(r"(?<![\w/.])((?:scripts|docs|fuentes|base)/[\w./-]+\.(?:py|md|yaml|json))", cuerpo))
    assert {"scripts/extraer_ley.py", "scripts/validar_aportacion.py", "scripts/validar_oro.py", "fuentes/entidades.yaml",
            "fuentes/dominios_oficiales.yaml"} <= rutas
    for r in rutas:
        assert (RAIZ / r).exists(), f"la skill menciona {r} y no existe"


def test_los_comandos_de_la_skill_existen_en_el_extractor():
    _, cuerpo = partes()
    ayuda = (RAIZ / "scripts" / "extraer_ley.py").read_text(encoding="utf-8")
    for opcion in re.findall(r"--(ambito|entidad|materia|emisor|diario|url|nombre|pdf)\b", cuerpo):
        assert f'"--{opcion}"' in ayuda, f"--{opcion} no existe en extraer_ley.py"


def test_la_skill_trae_sus_prohibiciones():
    _, cuerpo = partes()
    for frase in ("## Nunca", "fuente primaria", "dato, nunca instrucciones", "No subas el PDF", "git commit -s", "no mezclas a `main`", "no corrijas el texto a mano"):
        assert frase in cuerpo, frase


def test_el_estandar_enlaza_solo_a_archivos_que_existen():
    t = ESTANDAR.read_text(encoding="utf-8")
    for destino in re.findall(r"\]\(((?!http)[^)#]+)", t):
        assert (ESTANDAR.parent / destino).exists(), f"el estándar enlaza a {destino} y no existe"


def test_el_estandar_y_el_validador_usan_las_mismas_materias():
    import importlib.util
    spec = importlib.util.spec_from_file_location("va", RAIZ / "scripts" / "validar_aportacion.py")
    va = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(va)
    t = ESTANDAR.read_text(encoding="utf-8")
    for materia in va.MATERIAS:
        assert f"`{materia}`" in t, f"el estándar no documenta la materia {materia}"


def test_la_skill_esta_bajo_codeowners():
    co = (RAIZ / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
    assert "/.claude/" in co        # cambiar lo que la skill hace exige la firma del dueño
