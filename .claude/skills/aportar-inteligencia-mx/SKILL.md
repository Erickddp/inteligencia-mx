---
name: aportar-inteligencia-mx
description: Aportar a inteligencia-mx (antes timbra-reglas; base fiscal abierta de México) una regla, un valor de ley, un caso o un texto de ley desde Claude Code. Úsala cuando alguien quiera agregar o corregir un parámetro (UMA, salario mínimo, tarifas del Anexo 8, tasas, topes, recargos, subsidio, INPC, tipo de cambio), una regla con su fórmula y sus casos, reportar un error de cálculo, o cotejar un artículo de ley contra el DOF. Guía paso a paso desde la fuente primaria hasta el PR firmado.
---

# aportar-inteligencia-mx: llevar un dato fiscal de la fuente al PR

timbra-reglas es la **inteligencia fiscal abierta**: la usan apps como Timbra, que la fijan por versión y huella. Un número equivocado aquí
termina en la declaración de alguien. Por eso aquí nada entra sin **fuente primaria**, **casos al centavo** y la **firma** del CODEOWNER.
Lee `CONTRIBUTING.md` y `AVISO.md` del repo antes de empezar; esta skill es el camino práctico para seguirlos con Claude Code.

## 0. Pregunta primero (en palabras de persona)
- ¿Qué cambió o qué falta? (un valor nuevo, un error, una regla nueva, un artículo por cotejar)
- ¿Desde qué fecha aplica y hasta cuándo?
- ¿Dónde está publicado? Si la persona sólo tiene un blog o una nota de prensa, sirve para **encontrar** la fuente, no para citarla.
Llena con ella `docs/ficha_regla.md` tal como habla; lo que no sepa va como «no sé».

## 1. La fuente (sin esto no se sigue)
Sólo fuentes primarias:
- DOF;
- PDF oficial del SAT (RMF y sus anexos, Paquete Económico);
- la ley vigente en diputados.gob.mx;
- INEGI (UMA, INPC);
- Banxico (tipo de cambio);
- IMSS;
- CONASAMI.

**Al buscar en el DOF lee todas las ediciones del día (matutina y vespertina).** La página por defecto muestra solo la última: un decreto puede estar en la otra.
`python scripts/vigia_dof.py --fecha AAAA-MM-DD` ya lee todas. Buscar solo por título también falla (las resoluciones de CONASAMI se llaman «Resolución del H. Consejo de Representantes…»).
Un «no encontré el decreto» no prueba que no exista: dilo así y pide la nota.

Cita publicación y fecha (`DOF dd-mmm-aaaa`), y el enlace si es un PDF. **No subas el PDF**: en `fuentes/` va su URL y su SHA256.
Si sólo hay fuentes secundarias, el tramo entra como `por_confirmar` y el PR lo dice.

## 2. Abre o busca el issue
Antes de editar, busca si ya hay un issue del tema. Si no, ábrelo con la publicación, la fecha, el enlace y qué parámetros toca, para que
nadie trabaje dos veces lo mismo.

## 3. Edita la base (rama propia, nunca `main`)
`git checkout -b <tema-corto>` y edita `base/parametros.yaml` y/o `base/reglas.yaml`:
- **Un valor publicado NUNCA se edita: se agrega un tramo** con `desde` y `hasta`.
- IDs sin año ni mes (`UMA_DIARIA`, no `UMA_2026`).
- Números como **texto** (`"117.31"`), jamás float.
- Lo que depende de otro dato es **fórmula**, no un número copiado.
- Ley vigente: `hasta: null` y `confirmado_hasta`. Sólo vence lo que tiene plazo.
- Estados: `vigente`, `por_confirmar`, `propuesta` o `aprobado_congreso_pendiente_dof`. Nada más: otro estado frena la carga en las apps.
- Si es una tabla (tarifa del art. 96, Anexo 8), cotéjala renglón por renglón contra el PDF:
  `python scripts/cotejar_tabla.py --param ID --desde AAAA-MM-DD --texto tabla.txt`.

## 4. Casos al centavo
Toda regla con número lleva **al menos dos casos**, uno normal y uno en el límite:
- se calculan con el motor y se revisan a mano;
- si un caso falla, se investiga: **nunca se mueve el esperado para que pase**;
- en los casos sólo van RFC genéricos (`XAXX010101000`, `AAA010101AAA`). Nunca datos de clientes, RFC reales, secretos ni tokens.

## 5. Las tres pruebas, en verde
```bash
pip install -e ".[test]"
timbra-reglas probar
python -m pytest -q
python scripts/validar_oro.py
```
`validar_oro.py` no acepta violaciones nuevas. Si arreglaste una de la deuda: `python scripts/validar_oro.py --actualizar-deuda`.
**Ojo:** `validar_oro.py` y algunas pruebas solo revisan archivos **versionados**. Haz `git add -A` antes de correrlas; si no, pasan en tu máquina y el CI las rechaza.

## 6. Commit firmado y PR
- Cada commit se firma con `git commit -s` (DCO: `Signed-off-by: Nombre <correo>`). El CI rechaza el PR sin firma.
- El PR usa la plantilla y dice:
  - la fuente primaria;
  - los casos agregados;
  - el nivel A o B (`base/niveles.yaml` aún no existe: di cuál propones y decide el CODEOWNER);
  - **qué firmas se caen**: cada valor cambiado es una firma de Rick que se cae en las apps que usan la base, y el CI lo comenta en el PR.
- Tú no mezclas ni publicas releases: eso lo hace el CODEOWNER. Aprobar el PR es firmar la base.

## 7. Cotejar un artículo de ley con el DOF (`fuentes/leyes/`, `fuentes/rmf/`)
El texto viene de la Cámara de Diputados (leyes) o del archivo Word del DOF (RMF) y puede ir atrás del DOF. **El DOF no publica leyes consolidadas, solo decretos**: cotejar es leer los decretos posteriores a la «última reforma» del manifiesto y comprobar el artículo. Para marcar un artículo como cotejado:
1. busca en el DOF (todas las ediciones) los decretos posteriores a `ultima_reforma_segun_pdf` que lo toquen;
2. compara el texto párrafo por párrafo;
3. anota en el `manifiesto.json` de esa ley, en `cotejado_dof.articulos`, con el id en minúsculas (`"113-e"`, `"29-a"`; en la RMF `"2.7.1.21"`): `{"fecha": "AAAA-MM-DD", "decreto": "DOF dd-mmm-aaaa, nota NNNNNNN"}`.
Regenerar con `extraer_ley.py` / `extraer_rmf.py` no borra el cotejo. Claude puede proponerlo, pero **solo una persona confirma** que leyó el decreto.

Si el texto no coincide, **no lo corrijas a mano**: abre un issue con el decreto. El texto se regenera con `scripts/extraer_ley.py` en su propio PR.
Para ver qué parámetros de la base citan artículos sin cotejar (y por tanto no se firman): `python scripts/citas_fuentes.py --detalle`.

## 8. Agregar una ley o resolución nueva a la biblioteca
Agrega su clave y su ruta oficial (diputados.gob.mx, o la nota del DOF) a `LEYES` en `scripts/extraer_ley.py` y corre `python scripts/extraer_ley.py CLAVE`.
El extractor falla si algún encabezado de artículo no se lee: no lo saltes, arregla el patrón. Después `python -m pytest -q tests/test_biblioteca.py` y `scripts/citas_fuentes.py`.
Una ley estatal o municipal entra igual, con la URL del Periódico Oficial; si es un PDF escaneado sin texto, no entra (no hay forma de verificarlo).

## Nunca
- Editar un valor ya publicado en vez de agregar un tramo.
- Inventar una fuente o citar una que no leíste.
- Subir PDFs, datos personales, RFC reales, tokens o llaves.
- Marcar un artículo como cotejado sin haber leído el decreto.
- Concluir «no existe» porque tu búsqueda no lo encontró.
- Cambiar el formato de `fuentes/leyes/` sin avisar a quienes la consumen (Timbra la copia con su propio script `traer_leyes.py` —vive en el repo de Timbra, no en este— y comprueba huellas).
