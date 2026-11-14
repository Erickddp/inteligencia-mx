"""scripts/cotejar_reformas.py: lee un decreto del DOF y comprueba que lo que reimprime esté en el artículo de la biblioteca.
Sin red: el decreto es sintético, con los dos formatos que trae el DOF (nuevo y viejo, con la tilde corrupta)."""
import sys

import pytest

from conftest import RAIZ

sys.path.insert(0, str(RAIZ / "scripts"))
import cotejar_reformas as c  # noqa: E402

NUEVO = c.limpia("""Artículo Primero. Se reforman los artículos 34, fracción I, inciso b); 93, primer párrafo, de la Ley del Impuesto sobre la Renta, para quedar como sigue:
Artículo 34....
I. ...
a) ...
b) 5% en los demás casos, incluyendo las instalaciones y mejoras.
II. a XIV. ...
XV. 5% para el derecho de usufructo constituido sobre un bien inmueble.
Artículo 93. Para los efectos del Título IV, no se pagará el impuesto por las prestaciones de previsión social.
...
Artículo Segundo. Se reforma el artículo 28 del Código Fiscal de la Federación, para quedar como sigue:
Artículo 28. Las personas que lleven contabilidad deberán cumplir con lo siguiente.
...""", conserva_parrafos=True)
VIEJO = c.limpia("""LEY DEL IMPUESTO SOBRE LA RENTA
ART CULO PRIMERO.- Se reforman los artículos 7, último párrafo; 93, primer párrafo, para quedar como sigue:
ART CULO 93.- Para los efectos del Título IV, no se pagará el impuesto por la obtención de ingresos.
...
C DIGO FISCAL DE LA FEDERACI N
ART CULO SEXTO.- Se reforman los artículos 29-A, fracción VII, para quedar como sigue:
ART CULO 29-A.- Los comprobantes fiscales digitales por Internet deberán contener los siguientes requisitos.
...""", conserva_parrafos=True)


def test_separa_las_secciones_por_ley_en_los_dos_formatos():
    assert [l for l, _ in c.secciones(NUEVO)] == ["LISR", "CFF"]
    assert [l for l, _ in c.secciones(VIEJO)] == ["LISR", "CFF"]


def test_articulo_con_sufijo_y_con_o_ordinal():
    sec = dict((l, s) for l, s in c.secciones(VIEJO))["CFF"]
    assert c.articulo(sec, "29-a").startswith("ART CULO 29-A.-")
    assert c.articulo(sec, "28") is None


def test_encabezado_pegado_a_los_puntos_suspensivos_y_articulo_unico():
    """El DOF escribe «Artículo 34....» (encabezado + «...») y los decretos cortos usan «Artículo Único»."""
    d = "Artículo Único. Se reforma el artículo 28 del Código Fiscal de la Federación, para quedar como sigue: Artículo 28....\nI. ...\nII. Contar con firma electrónica avanzada vigente del contribuyente.\nArtículo 29....\nAlgo más aquí."
    d = c.limpia(d.replace("Artículo 28....\n", "\nArtículo 28....\n").replace("\nArtículo 29....", "\nArtículo 29...."), conserva_parrafos=True)
    (ley, sec), = c.secciones(d)
    assert ley == "CFF"
    a = c.articulo(sec, "28")
    assert "Contar con firma electrónica" in a and "Algo más" not in a


def test_una_tilde_perdida_en_el_dof_no_es_discrepancia_pero_un_cambio_de_palabra_si():
    lib = c.plano("XIII. Los que obtengan las personas por concepto de primas de antigüedad, retiro e indemnizaciones u otros pagos, hasta el monto por el que no esté exenta.")
    assert c.tilde_perdida("XIII. Los que obtengan las personas por concepto de primas de antig edad, retiro e indemnizaciones u otros pagos, hasta el monto por el que no esté exenta.", lib)
    assert not c.tilde_perdida("XIII. Los que obtengan las personas por concepto de primas de vejez, retiro e indemnizaciones u otros pagos, hasta el monto por el que no esté exenta.", lib)
    assert not c.tilde_perdida("XIII. Los que obtengan las personas por concepto de primas de antiguedad, retiro e indemnizaciones u otros pagos, hasta el monto por el que no esté exenta.", lib)


def test_encabezado_de_tabla_solo_si_no_trae_cifras_ni_es_una_oracion_nueva():
    lib = c.plano("Monto de los ingresos amparados por Tasa aplicable comprobantes fiscales efectivamente cobrados Hasta 25,000.00 1.00%")
    assert c.encabezado_de_tabla("Monto de los ingresos amparados por comprobantes fiscales efectivamente cobrados", lib)
    assert not c.encabezado_de_tabla("Monto de los ingresos amparados por comprobantes fiscales efectivamente cobrados a 25,000.00", lib)
    assert not c.encabezado_de_tabla("Se paga el impuesto sobre la renta al doble.", lib)


def test_decreto_que_expide_la_ley_trae_el_articulo_completo():
    d = c.limpia("Artículo Séptimo. Se expide la Ley del Impuesto sobre la Renta:\nLEY DEL IMPUESTO SOBRE LA RENTA\nArtículo 33. Los por cientos máximos autorizados son los siguientes.\nArtículo 34. Los por cientos máximos autorizados por tipo de bien son los siguientes.", conserva_parrafos=True)
    assert [l for l, _ in c.secciones(d)] == ["LISR"]
    v = c.verifica(d, "LISR", "33", c.plano("Artículo 33. Los por cientos máximos autorizados son los siguientes."))
    assert v and v["no_coinciden"] == [] and len(v["ok"]) == 1


def test_solo_lo_que_el_decreto_reimprime_cuenta_como_pieza():
    sec = c.secciones(NUEVO)[0][1]
    a34 = c.articulo(sec, "34")
    ps = c.piezas(a34)
    assert ps == ["b) 5% en los demás casos, incluyendo las instalaciones y mejoras", "XV. 5% para el derecho de usufructo constituido sobre un bien inmueble"] or \
        len(ps) == 2 and "usufructo" in ps[1] and ps[0].startswith("b) 5%")


def test_coincide_cuando_el_texto_esta_y_avisa_cuando_no():
    lib = c.plano("Artículo 34. I. a) algo. b) 5% en los demás casos, incluyendo las instalaciones y mejoras. "
                  "XV. 5% para el derecho de usufructo constituido sobre un bien inmueble.")
    v = c.verifica(NUEVO, "LISR", "34", lib)
    assert len(v["piezas"]) == 2 and v["no_coinciden"] == [] and v["numeros_faltantes"] == []
    v = c.verifica(NUEVO, "LISR", "34", lib.replace("5% en los demás casos", "6% en los demás casos"))
    assert len(v["no_coinciden"]) == 1 and "5% en los demás casos" in v["no_coinciden"][0] and v["numeros_faltantes"] == ["5%"]


def test_la_ley_equivocada_no_se_mezcla():
    """El artículo 28 es del CFF en el decreto: pedirlo a la LISR no debe encontrarlo."""
    assert c.verifica(NUEVO, "LISR", "28", "Artículo 28.") is None
    assert c.verifica(NUEVO, "CFF", "28", c.plano("Artículo 28. Las personas que lleven contabilidad deberán cumplir con lo siguiente.")) is not None


def test_las_notas_al_pie_de_la_camara_no_estorban():
    crudo = "Artículo 5.\n_Párrafo reformado DOF 12-11-2021_\ntexto del párrafo que el decreto reimprime completo\n_Fracción adicionada DOF 30-11-2016_\n"
    assert "DOF" not in c.limpia(c.ANOTACION.sub("", crudo))
    assert set(c.FECHA_DOF.findall("".join(c.ANOTACION.findall("_Fracción reformada DOF 11-12-2013, 30-11-2016 y 09-12-2019_")))) == {
        ("11", "12", "2013"), ("30", "11", "2016"), ("09", "12", "2019")}


@pytest.mark.parametrize("ley,num", [("LISR", "34"), ("LIVA", "5")])
def test_los_manifiestos_con_cotejo_de_reformas_no_se_hacen_pasar_por_cotejo_humano(ley, num):
    import json
    m = json.loads((RAIZ / "fuentes" / "leyes" / ley / "manifiesto.json").read_text(encoding="utf-8"))
    assert num not in (m.get("cotejado_dof", {}).get("articulos") or {}), "cotejado_dof es sólo para el cotejo de una persona"
