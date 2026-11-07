"""La biblioteca de leyes es parte de la base: cada ley con manifiesto, índice y un archivo por artículo."""
import hashlib
import importlib.util
import json

import pytest

from conftest import RAIZ

LEYES = RAIZ / "fuentes" / "leyes"
CLAVES = ["LISR", "LIVA", "LFPIORPI", "LSS", "LINFONAVIT", "LFT", "CFF", "RLISR", "RLIVA",
          "LIEPS", "RLIEPS", "RCFF", "RLFPIORPI", "LIF2026", "LA", "LFD", "LISH", "LFISAN", "LCF", "LMV"]
CLAVE = {"LISR": ["96", "106", "151", "152"], "LIVA": ["1", "1-a", "5", "32"], "LFPIORPI": ["17"], "LSS": ["27", "28"], "LINFONAVIT": ["29"],
         "LFT": ["76", "80", "87", "117", "162", "353-ñ"], "CFF": ["17-a", "20", "21", "29", "29-a", "80"], "RLISR": ["1", "174"], "RLIVA": ["1"],
         "LIEPS": ["2", "8"], "RLIEPS": ["1"], "RCFF": ["1", "39"], "RLFPIORPI": ["1"], "LIF2026": ["1", "25"], "LA": ["1", "56", "64"],
         "LFD": ["1"], "LISH": ["1"], "LFISAN": ["1"], "LCF": ["1", "2"], "LMV": ["1"]}


def carga(c):
    d = LEYES / c
    return json.loads((d / "manifiesto.json").read_text(encoding="utf-8")), json.loads((d / "indice.json").read_text(encoding="utf-8")), d


@pytest.mark.parametrize("c", CLAVES)
def test_ley_completa(c):
    man, idx, d = carga(c)
    assert man["clave"] == c and man["url"].startswith("https://www.diputados.gob.mx/")
    assert len(man["sha256_pdf"]) == 64 and ("ultima_reforma_segun_pdf" in man)
    assert man["articulos"] == len(idx) >= 14
    assert (d / "transitorios.md").is_file()
    # sin huecos en la numeración base
    nums = sorted({int(k.split("-")[0]) for k in idx})
    assert nums == list(range(1, nums[-1] + 1))


@pytest.mark.parametrize("c", CLAVES)
def test_indice_coincide_con_los_archivos(c):
    man, idx, d = carga(c)
    archivos = sorted(p.name for p in (d / "articulos").glob("art-*.md"))
    assert archivos == sorted(v["archivo"].split("/")[-1] for v in idx.values())
    junto = ""
    for aid, v in idx.items():
        texto = (d / v["archivo"]).read_text(encoding="utf-8")
        assert texto.startswith(f"# {c} · Artículo")
        cuerpo = texto.split("\n\n", 2)[-1]
        assert "Cámara de Diputados" not in cuerpo[:50]
        junto += v["sha256"]
    assert hashlib.sha256(junto.encode()).hexdigest() == man["sha256_texto"]


@pytest.mark.parametrize("c", CLAVES)
def test_articulos_clave_existen_y_no_estan_vacios(c):
    _, idx, d = carga(c)
    for a in CLAVE[c]:
        assert a in idx, f"{c} art. {a}"
        assert len((d / idx[a]["archivo"]).read_text(encoding="utf-8")) > 300


def test_sin_basura_de_encabezado_de_pagina():
    for c in CLAVES:
        _, idx, d = carga(c)
        for v in idx.values():
            t = (d / v["archivo"]).read_text(encoding="utf-8")
            assert "Secretaría de Servicios Parlamentarios" not in t
            assert "CÁMARA DE DIPUTADOS DEL H. CONGRESO" not in t


def test_citas_de_la_base_a_leyes_incluidas_resuelven():
    spec = importlib.util.spec_from_file_location("citas", RAIZ / "scripts" / "citas_fuentes.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    import sys
    sys.argv = ["citas_fuentes.py", "--estricto"]
    m.main()  # lanza SystemExit(1) si una cita de una ley incluida no existe


def test_evidencia_conserva_sus_huellas():
    """La evidencia (datos crudos de Banxico) se guarda byte por byte: si Git le cambia los saltos de línea, la huella no cuadra."""
    carpetas = [d for d in (LEYES.parent / "evidencia").iterdir() if (d / "SHA256SUMS").exists()]
    assert len(carpetas) >= 2
    for d in carpetas:
        for linea in (d / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
            h, nombre = linea.split(None, 1)
            assert hashlib.sha256((d / nombre.strip().lstrip("*")).read_bytes()).hexdigest() == h, f"{d.name}/{nombre}"


def test_la_ley_aduanera_lleva_su_advertencia_de_texto_desactualizado():
    """El DOF reformó la Ley Aduanera el 23-oct-2026; el PDF de la Cámara no lo trae. Regenerar el texto no debe borrar la advertencia."""
    man = json.loads((LEYES / "LA" / "manifiesto.json").read_text(encoding="utf-8"))
    assert any("5802077" in a["fuente"] and "desactualizado" in a["texto"] for a in man["advertencias"])
