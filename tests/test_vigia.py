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


VESPERTINA = (
    '<table><tr><td colspan="3" class="txt"><span>Fecha: 05/11/2026 - Edici&oacute;n Vespertina</span></td></tr>'
    '<tr><td bgcolor="#B2B2B2" class="txt_blanco2">&nbsp;PODER EJECUTIVO</td></tr>'
    '<tr><td colspan="3" class="subtitle_azul">&nbsp;SECRETARIA DE HACIENDA Y CREDITO PUBLICO</td></tr>'
    '<tr><td><a href="/nota_detalle.php?codigo=9999999&amp;fecha=05/11/2026" class="enlaces">'
    "Decreto por el que se modifica el diverso que otorga el subsidio para el empleo.</a></td></tr></table>"
)
MALO = "<html><body>Fecha: 05/11/2026 - Edición Matutina <p>cortado</p></body></html>"


def paginas(monkeypatch, por_edicion):
    llamadas = []

    def falsa(dia, intentos=3, edicion="MAT"):
        llamadas.append(edicion)
        v = por_edicion[edicion]
        return next(v) if hasattr(v, "__next__") else v

    monkeypatch.setattr(vigia, "descarga", falsa)
    return llamadas


def test_lee_todas_las_ediciones_del_dia_y_no_repite_notas(monkeypatch):
    """El DOF muestra por defecto solo la última edición: el 22-dic-2025 la página traía 1 nota y la matutina 30."""
    llamadas = paginas(monkeypatch, {"MAT": HTML, "VES": VESPERTINA, "EXT": "<html></html>"})
    r = vigia.lee_dia(dt.date(2026, 11, 5), None, espera=0)
    assert llamadas == ["MAT", "VES", "EXT"] and r["ediciones"] == ["MAT", "VES"]
    assert r["notas_leidas"] == 12
    subsidio = [n for n in r["posibles_cambios"] if "subsidio" in n["titulo"].lower()]
    assert len(subsidio) == 1 and subsidio[0]["edicion"] == "VES"  # solo estaba en la vespertina


def test_si_el_servidor_repite_la_misma_pagina_para_otra_edicion_no_duplica(monkeypatch):
    paginas(monkeypatch, {"MAT": HTML, "VES": HTML, "EXT": HTML})  # la etiqueta dice Matutina en las tres
    r = vigia.lee_dia(dt.date(2026, 11, 5), None, espera=0)
    assert r["ediciones"] == ["MAT"] and r["notas_leidas"] == 11


def test_una_respuesta_incompleta_se_reintenta_una_vez(monkeypatch):
    paginas(monkeypatch, {"MAT": iter([MALO, HTML]), "VES": "<html></html>", "EXT": "<html></html>"})
    r = vigia.lee_dia(dt.date(2026, 11, 5), None, espera=0)
    assert r["notas_leidas"] == 11  # el segundo intento sí leyó la página


def test_si_el_reintento_tambien_falla_la_alarma_es_real(monkeypatch):
    paginas(monkeypatch, {"MAT": MALO, "VES": "<html></html>", "EXT": "<html></html>"})
    with pytest.raises(SystemExit):
        vigia.lee_dia(dt.date(2026, 11, 5), None, espera=0)


def test_resolucion_de_conasami_con_titulo_generico_se_marca_por_su_organismo():
    c = vigia.clasifica(nota("Resolución del H. Consejo de Representantes del 3 de diciembre de 2025.", "COMISION NACIONAL DE LOS SALARIOS MINIMOS"))
    assert c and c["nivel"] == "alta" and "salario_minimo" in c["temas"]


def test_decreto_omnibus_sin_ley_en_el_titulo_se_marca_para_leer_su_texto():
    """El 1-abr-2024 un decreto «en materia de pueblos y comunidades indígenas» reformó el art. 79 de la LISR."""
    c = vigia.clasifica(nota("Decreto por el que se reforman diversos ordenamientos en materia de pueblos y comunidades indígenas y afromexicanas.", "SECRETARIA DE GOBERNACION"))
    assert c and c["leer_texto"] and "decreto_generico" in c["temas"]
    c = vigia.clasifica(nota("Decreto por el que se reforman diversas disposiciones del Reglamento del Registro Público Único.", "SECRETARIA DE HACIENDA Y CREDITO PUBLICO"))
    assert c and c["nivel"] == "media" and c["leer_texto"]   # no se vuelve «baja» por venir de Hacienda
    assert vigia.clasifica(nota("Decreto por el que se expropia por causa de utilidad pública la superficie de 5 hectáreas.")) is None


def test_leyes_mencionadas_exige_el_verbo_de_reforma_cerca():
    texto = ("Artículo Décimo Séptimo.- Se reforma el artículo 79, fracción VI, de la Ley del Impuesto sobre la Renta, para quedar como sigue. "
             + "x " * 400 + "Considerando que la Ley del Seguro Social es importante para el país.")
    assert vigia.leyes_mencionadas(texto) == ["LISR"]
