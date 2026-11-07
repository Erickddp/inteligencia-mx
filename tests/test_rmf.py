"""La RMF 2026 en la biblioteca: una regla por archivo, sin huecos, con su ubicación y su fundamento."""
import collections
import hashlib
import json
import re

from conftest import RAIZ

D = RAIZ / "fuentes" / "rmf" / "2026" / "RMF2026"
MAN = json.loads((D / "manifiesto.json").read_text(encoding="utf-8"))
IDX = json.loads((D / "indice.json").read_text(encoding="utf-8"))


def cuerpo(rid):
    return (D / IDX[rid]["archivo"]).read_text(encoding="utf-8").split("\n\n", 2)[-1]


def test_manifiesto_y_conteo():
    assert MAN["clave"] == "RMF2026" and MAN["dof"]["fecha"] == "2025-12-28" and MAN["dof"]["url"].startswith("https://dof.gob.mx/")
    assert MAN["reglas"] == len(IDX) == len(list((D / "reglas").glob("regla-*.md"))) == 1208
    assert len(MAN["sha256_documento"]) == 64 and "sin revisión humana" in MAN["origen"]
    assert MAN["cotejado_dof"]["ley_completa"] is None  # nadie la ha revisado: no se firma nada que dependa de ella
    junto = "".join(v["sha256"] for v in IDX.values())
    assert hashlib.sha256(junto.encode()).hexdigest() == MAN["sha256_texto"]


def test_sin_huecos_en_ningun_capitulo_o_seccion():
    g = collections.defaultdict(list)
    for r in IDX:
        p = r.split(".")
        g[tuple(p[:-1])].append(int(p[-1]))
    assert len(g) >= 100
    for k, v in g.items():
        assert v == list(range(1, max(v) + 1)), ".".join(k)


def test_hay_reglas_de_cinco_niveles_bajo_las_subsecciones():
    """Carta Porte (2.7.7.x.y): una vez se perdieron porque el patrón aceptaba solo cuatro niveles."""
    assert {"2.7.7.1.1", "2.7.7.2.1", "2.7.7.3.1"} <= set(IDX)


def test_cada_regla_empieza_con_su_numero_y_sin_encabezados_de_estructura_dentro():
    for rid in IDX:
        c = cuerpo(rid)
        assert c.startswith(rid + "."), rid
        assert not re.search(r"(?m)^(Título|Capítulo|Sección|Subsección) \d", c), rid


def test_reglas_clave_existen_y_dicen_lo_que_la_base_les_atribuye():
    assert "24 horas siguientes al cierre" in cuerpo("2.7.1.21")                        # CFDI global (R-03)
    assert "quinto día natural del mes inmediato siguiente" in cuerpo("2.7.1.32")      # REP (R-137)
    assert "20 de abril" in cuerpo("2.8.1.6") and "22 de mayo" in cuerpo("2.8.1.6")   # balanza ajustada
    assert "4'000,000.00" in cuerpo("2.8.1.17")                                         # relevo de contabilidad electrónica y DIOT
    assert "Régimen Simplificado de Confianza" in IDX["3.13.1"]["ubicacion"] + IDX["3.13.1"]["titulo"]


def test_el_fundamento_se_separa_del_texto():
    assert IDX["2.7.1.21"]["fundamento"].startswith("CFF")
    assert not any(v["fundamento"] and len(v["fundamento"]) > 600 for v in IDX.values())
    sin = [r for r, v in IDX.items() if not v["fundamento"]]
    assert len(sin) < 15  # best-effort: es un dato auxiliar; el texto de la regla va completo


def test_transitorios_y_preambulo_aparte():
    assert "entrará en vigor el 1o. de enero de 2026" in (D / "transitorios.md").read_text(encoding="utf-8")
    assert "Considerando" in (D / "preambulo.md").read_text(encoding="utf-8") or "CONSIDERANDO" in (D / "preambulo.md").read_text(encoding="utf-8")
