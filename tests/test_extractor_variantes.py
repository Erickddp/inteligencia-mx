"""El extractor entiende las variantes de numeración de las leyes estatales (CDMX) sin confundir citas con artículos."""
import importlib.util
import sys

import pytest

from conftest import RAIZ

sys.path.insert(0, str(RAIZ / "scripts"))
spec = importlib.util.spec_from_file_location("extraer_ley", RAIZ / "scripts" / "extraer_ley.py")
el = importlib.util.module_from_spec(spec)
spec.loader.exec_module(el)


@pytest.mark.parametrize("linea,esperado", [
    # lo que ya entendía (leyes federales)
    ("Artículo 1o.- Esta ley es de orden público.", "1"),
    ("Artículo 18-J.- Los residentes en el extranjero", "18-j"),
    ("ARTÍCULO 5-A. Texto", "5-a"),
    ("Artículo 82 Quáter. Texto", "82-quater"),
    # variantes de las leyes de la CDMX
    ("Artículo 276 Quater: Comete el delito de corrupción inmobiliaria", "276-quater"),
    ("ARTÍCULO 356 CUARTER.- Lo dispuesto en el artículo anterior", "356-cuarter"),
    ("Artículo 135 Quitus. Existirá un consejo integrado", "135-quitus"),
    ("ARTICULO 469 Quintos.- (artículo derogado)", "469-quintos"),
    ("Artículo 100 Undecies. En materia de hipoteca", "100-undecies"),
    ("ARTICULO 2448 (SIC) E.- La renta debe pagarse", "2448-e"),
    # el encabezado solo en su línea, con sufijo o con nota de derogación
    ("ARTICULO 12", "12"),
    ("ARTICULO 12 BIS", "12-bis"),
    ("ARTICULO 498 BIS 1", "498-bis-1"),
    ("ARTICULO 737 A", "737-a"),
    ("ARTICULO 737 F (DEROGADO, G.O. 19 DE DICIEMBRE DE 2005)", "737-f"),
    ("ARTICULO 5 (DEROGADO, G.O. 10 DE MARZO DE 1999)", "5"),
])
def test_encabezados_que_si_son_articulo(linea, esperado):
    assert el.encabezado(linea) == esperado


@pytest.mark.parametrize("linea", [
    "ARTÍCULO 14 DE LAS DISPOSICIONES TRANSITORIAS DE LA CITADA LEY, PUBLICADA EN EL DIARIO OFICIAL",   # cita de transitorios de un decreto
    "ARTÍCULO 117, SE RECOMIENDA CONSULTAR EL CONSIDERANDO TRIGÉSIMO PRIMERO DEL DICTAMEN",           # nota editorial
    "Artículo 5 de la Ley del Impuesto sobre la Renta establece que",                                  # cita dentro de un párrafo
    "Artículo 12 A partir de la fecha de entrada en vigor se aplicará",                                # no es sufijo A
    "el artículo 5-A de esta ley",                                                                     # en minúscula y a media línea
    "Texto cualquiera del cuerpo de un artículo.",
])
def test_lineas_que_no_son_encabezado(linea):
    assert el.encabezado(linea) is None


def test_ultima_reforma_en_formato_de_la_gaceta_oficial_de_la_cdmx():
    texto = ("CÓDIGO FISCAL DE LA CIUDAD DE MÉXICO\nPUBLICADO EN LA GACETA OFICIAL DE LA CIUDAD DE MÉXICO\nEL 29 DE DICIEMBRE DE 2009\n"
             "TEXTO VIGENTE\nÚltima reforma publicada en la G.O. CDMX\nel 8 de octubre de 2026\n")
    assert el.ultima_reforma(texto) == ("2026-10-08", "encabezado del PDF (Gaceta Oficial)")
    assert el.ultima_reforma("Última reforma publicada en la G.O.C.D.M.X.\nel 18 de julio de 2018\n")[0] == "2018-07-18"


def test_el_formato_federal_de_la_ultima_reforma_sigue_igual():
    assert el.ultima_reforma("Última Reforma DOF 01-04-2024\nLey del Impuesto sobre la Renta") == ("2024-04-01", "encabezado del PDF")


def test_derogado_por_nota_en_el_encabezado():
    import re
    patron = r"^\s*ART[ÍI]CULO\s[^\n(]{0,30}\(\s*DEROGAD"
    assert re.search(patron, "ARTICULO 737 F (DEROGADO, G.O. 19 DE DICIEMBRE DE 2005)", re.I)
    assert not re.search(patron, "ARTICULO 737 G\nLa interposición de la acción de nulidad (derogado en 2005)", re.I)
