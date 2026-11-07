"""Estándar de aportación: fuente primaria, entidades, claves de ley estatal y el camino completo de registrar una ley."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys

import pytest
import yaml

from conftest import RAIZ

spec = importlib.util.spec_from_file_location("validar_aportacion", RAIZ / "scripts" / "validar_aportacion.py")
va = importlib.util.module_from_spec(spec)
spec.loader.exec_module(va)

ENT, DOM = va.carga_entidades(), va.carga_dominios()


def manifiesto(**cambios):
    m = {"clave": "QUE-PRUEBA", "nombre": "Ley de prueba", "url": "https://congreso.ejemplo.gob.mx/ley.pdf", "descargado": "2026-11-07",
         "sha256_pdf": "a" * 64, "sha256_texto": "b" * 64, "articulos": 12, "ambito": "estatal", "entidad": "QUE", "materia": "fiscal",
         "emisor": "Congreso del Estado"}
    m.update(cambios)
    return {k: v for k, v in m.items() if v is not None}


def test_el_repositorio_cumple_el_estandar():
    assert va.valida_repo() == []


def test_hay_32_entidades_con_clave_iso_y_la_base_las_usa():
    assert len(ENT) == 32 and len(set(ENT)) == 32
    assert {"CMX", "MEX", "PUE", "OAX", "JAL", "BCN", "CHH", "NLE", "QUE"} <= set(ENT)
    assert all(len(k) == 3 and k.isupper() for k in ENT)


@pytest.mark.parametrize("url,esperado", [
    ("https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf", True),
    ("http://m.sat.gob.mx/fichas_tematicas/x.pdf", True),
    ("https://dof.gob.mx/nota_detalle.php?codigo=1", True),
    ("https://www.inegi.org.mx/app/indicesdeprecios", True),
    ("https://www.banxico.org.mx/SieAPIRest", True),
    ("https://blog.ejemplo.com/ley.pdf", False),
    ("https://despacho.com.mx/ley.pdf", False),
    ("https://gob.mx.evil.com/ley.pdf", False),
    ("https://evilgob.mx/ley.pdf", False),
    ("ftp://congreso.gob.mx/ley.pdf", False),
    ("congreso.gob.mx/ley.pdf", False),
    ("", False),
])
def test_dominios_oficiales(url, esperado):
    assert va.dominio_oficial(url, DOM) is esperado


def test_un_manifiesto_estatal_correcto_pasa():
    assert va.valida_manifiesto(manifiesto(), "QUE-PRUEBA", ENT, DOM) == []


@pytest.mark.parametrize("cambios,carpeta,texto", [
    ({"url": "https://blog.ejemplo.com/ley.pdf"}, "QUE-PRUEBA", "dominio oficial"),
    ({"entidad": "QRO"}, "QRO-PRUEBA", "no está en fuentes/entidades.yaml"),
    ({"entidad": "CHH"}, "QUE-PRUEBA", "debe ser CHH-"),
    ({"materia": "astrologia"}, "QUE-PRUEBA", "materia"),
    ({"emisor": None}, "QUE-PRUEBA", "emisor"),
    ({"sha256_pdf": "xyz"}, "QUE-PRUEBA", "SHA256"),
    ({"descargado": "ayer"}, "QUE-PRUEBA", "AAAA-MM-DD"),
    ({"ambito": "planetario"}, "QUE-PRUEBA", "ámbito"),
    ({"articulos": None}, "QUE-PRUEBA", "falta `articulos`"),
    ({}, "OTRA-CLAVE", "no coincide con la carpeta"),
])
def test_un_manifiesto_defectuoso_falla(cambios, carpeta, texto):
    errores = va.valida_manifiesto(manifiesto(**cambios), carpeta, ENT, DOM)
    assert any(texto in e for e in errores), errores


def test_una_ley_federal_sin_ambito_sigue_valiendo():
    m = manifiesto(ambito=None, entidad=None, materia=None, emisor=None, clave="LISR", url="https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf")
    assert va.valida_manifiesto(m, "LISR", ENT, DOM) == []


def test_documentos_oficiales_deben_traer_huella_y_fecha():
    bien = {"id": "d1", "url": "https://www.sat.gob.mx/x.pdf", "sha256": "c" * 64, "publicado": "2026-01-01"}
    assert va.valida_documentos([bien], DOM) == []
    assert len(va.valida_documentos([{**bien, "url": "https://blog.com/x.pdf", "sha256": "", "publicado": "hoy"}], DOM)) == 3


def test_no_se_suben_pdf(tmp_path):
    raiz = tmp_path / "r"
    (raiz / "fuentes" / "leyes").mkdir(parents=True)
    (raiz / "base").mkdir()
    shutil.copy(RAIZ / "fuentes" / "entidades.yaml", raiz / "fuentes")
    shutil.copy(RAIZ / "fuentes" / "dominios_oficiales.yaml", raiz / "fuentes")
    shutil.copy(RAIZ / "base" / "parametros.yaml", raiz / "base")
    (raiz / "fuentes" / "ley.pdf").write_bytes(b"%PDF-1.4")
    assert any("no se suben PDF" in e for e in va.valida_repo(raiz))


# ---------- camino completo: registrar una ley estatal con el extractor ----------
def pdf_sintetico(n=12) -> bytes:
    lineas = [f"BT /F1 11 Tf 40 {760 - 18 * i} Td (Art\\355culo {i + 1}.- Texto del art\\355culo {i + 1} de la ley de prueba.) Tj ET" for i in range(n)]
    contenido = "\n".join(lineas).encode("latin-1")
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 5 0 R /Resources << /Font << /F1 4 0 R >> >> >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
            b"<< /Length " + str(len(contenido)).encode() + b" >>\nstream\n" + contenido + b"\nendstream"]
    out, pos = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        pos.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode() + b"".join(f"{p:010d} 00000 n \n".encode() for p in pos)
    return out + f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()


@pytest.mark.skipif(shutil.which("pdftotext") is None, reason="falta pdftotext (poppler-utils)")
def test_registrar_una_ley_estatal_de_punta_a_punta(tmp_path):
    pdf = tmp_path / "ley.pdf"
    pdf.write_bytes(pdf_sintetico())
    out = tmp_path / "leyes"
    r = subprocess.run([sys.executable, str(RAIZ / "scripts" / "extraer_ley.py"), "QUE-PRUEBA", "--pdf", str(pdf), "--out", str(out),
                        "--url", "https://congreso.ejemplo.gob.mx/ley.pdf", "--nombre", "Ley de prueba del Estado", "--ambito", "estatal",
                        "--entidad", "QUE", "--materia", "fiscal", "--emisor", "Congreso del Estado de prueba"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONUTF8": "1"})
    assert r.returncode == 0, r.stdout + r.stderr
    carpeta = out / "QUE-PRUEBA"
    m = json.loads((carpeta / "manifiesto.json").read_text(encoding="utf-8"))
    assert m["articulos"] == 12 and m["ambito"] == "estatal" and m["entidad"] == "QUE" and m["materia"] == "fiscal"
    assert m["emisor"] == "Congreso del Estado de prueba" and m["url"].startswith("https://congreso.ejemplo.gob.mx")
    assert len(m["sha256_pdf"]) == 64 and "Congreso del Estado de prueba" in m["fuente"]
    art = (carpeta / "articulos" / "art-0003.md").read_text(encoding="utf-8")
    assert "Texto según: Congreso del Estado de prueba" in art and "Cotejado con Periódico Oficial: NO" in art
    assert va.valida_ley(carpeta, ENT, DOM) == []                      # lo que registra el extractor cumple el estándar
    assert not list(carpeta.rglob("*.pdf"))                             # el PDF no se guarda


def test_el_extractor_rechaza_una_fuente_que_no_es_oficial(tmp_path):
    r = subprocess.run([sys.executable, str(RAIZ / "scripts" / "extraer_ley.py"), "QUE-PRUEBA", "--pdf", str(tmp_path / "x.pdf"), "--out", str(tmp_path),
                        "--url", "https://blog.ejemplo.com/ley.pdf", "--nombre", "X", "--ambito", "estatal", "--entidad", "QUE", "--materia", "fiscal", "--emisor", "Y"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", env={**os.environ, "PYTHONUTF8": "1"})
    assert r.returncode != 0 and "dominio oficial" in r.stderr
