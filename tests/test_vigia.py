"""El Vigía del DOF: lee el índice real del día y separa cambios de ley, datos de serie y ruido."""
import datetime as dt
import importlib.util

import pytest

from conftest import RAIZ

spec = importlib.util.spec_from_file_location("vigia", RAIZ / "scripts" / "vigia_dof.py")
vigia = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vigia)
HTML = (RAIZ / "tests" / "fixtures" / "dof_2026-11-05.html").read_text(encoding="utf-8")


def nota(titulo, organismo=""):
    return {"titulo": titulo, "organismo": organismo}


def test_lee_el_indice_real_del_dia():
    notas = vigia.parsea(HTML)
    assert len(notas) == 11
    assert notas[0]["organismo"] == "SECRETARIA DE MARINA" and notas[0]["poder"] == "PODER EJECUTIVO"
    assert notas[0]["url"].startswith("https://dof.gob.mx/nota_detalle.php?codigo=")
    assert {n["fecha"] for n in notas} == {"2026-11-05"}


def test_dia_real_sin_cambios_de_ley_pero_con_datos_de_serie():
    r = vigia.vigila(dt.date(2026, 11, 5), HTML)
    assert r["notas_leidas"] == 11 and r["posibles_cambios"] == []
    assert {d["serie"] for d in r["datos_periodicos"]} >= {"tipo_cambio_dof", "tiie"}


@pytest.mark.parametrize("titulo,tema", [
    ("Resolución Miscelánea Fiscal para 2027.", "rmf"),
    ("Decreto por el que se reforman diversas disposiciones de la Ley del Impuesto sobre la Renta.", "isr"),
    ("Acuerdo por el que se da a conocer el valor de la Unidad de Medida y Actualización.", "uma"),
    ("Resolución de la Comisión Nacional de los Salarios Mínimos por la que se fijan los salarios mínimos.", "salario_minimo"),
    ("Decreto por el que se reforma la Ley del Seguro Social.", "imss"),
    ("Decreto por el que se reforma la Ley Federal para la Prevención e Identificación de Operaciones con Recursos de Procedencia Ilícita.", "antilavado"),
])
def test_cambios_de_ley_se_marcan(titulo, tema):
    c = vigia.clasifica(nota(titulo))
    assert c and c["tipo"] == "posible_cambio" and tema in c["temas"]


@pytest.mark.parametrize("titulo", [
    "Convenio de Coordinación para la construcción de planteles educativos.",
    "Aviso mediante el cual se da a conocer el cambio de domicilio legal de la Subdelegación del Instituto Mexicano del Seguro Social.",
    "Acuerdo por el que se destina a la Secretaría de Marina el inmueble federal denominado Sanatorio.",
])
def test_el_ruido_no_se_marca(titulo):
    assert vigia.clasifica(nota(titulo, "INSTITUTO MEXICANO DEL SEGURO SOCIAL")) is None


def test_series_no_abren_issue():
    assert vigia.clasifica(nota("Índice nacional de precios al consumidor."))["serie"] == "inpc"
    assert vigia.clasifica(nota("Tipo de cambio para solventar obligaciones denominadas en moneda extranjera."))["tipo"] == "dato_periodico"


def test_si_el_dof_cambia_el_formato_el_vigia_falla_en_vez_de_callar():
    roto = "<html><body>Fecha: 05/11/2026 - Edición Matutina <p>otra estructura</p></body></html>"
    with pytest.raises(SystemExit):
        vigia.vigila(dt.date(2026, 11, 5), roto)


def test_dia_sin_edicion_no_es_error():
    r = vigia.vigila(dt.date(2026, 10, 17), "<html><body>sin ejemplar</body></html>")
    assert r["sin_edicion"] and r["posibles_cambios"] == []
    assert "alerta" not in r  # sábado
    assert "alerta" in vigia.vigila(dt.date(2026, 10, 14), "<html></html>")  # día hábil: avisa


def test_una_respuesta_incompleta_se_reintenta_una_vez(monkeypatch):
    malo = "<html><body>Fecha: 05/11/2026 - Edición Matutina <p>cortado</p></body></html>"
    paginas = iter([malo, HTML])
    monkeypatch.setattr(vigia, "descarga", lambda dia, intentos=3: next(paginas))
    r = vigia.lee_dia(dt.date(2026, 11, 5), None, espera=0)
    assert r["notas_leidas"] == 11  # el segundo intento sí leyó la página


def test_si_el_reintento_tambien_falla_la_alarma_es_real(monkeypatch):
    malo = "<html><body>Fecha: 05/11/2026 - Edición Matutina <p>cortado</p></body></html>"
    monkeypatch.setattr(vigia, "descarga", lambda dia, intentos=3: malo)
    with pytest.raises(SystemExit):
        vigia.lee_dia(dt.date(2026, 11, 5), None, espera=0)
