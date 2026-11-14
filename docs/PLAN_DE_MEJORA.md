# Plan de mejora

Documento **vivo**: cualquiera puede proponer cambios con un PR o con la plantilla de issue «Propuesta de mejora». La versión legible por máquinas es [`mejoras/backlog.yaml`](../mejoras/backlog.yaml); este documento explica el porqué y el orden.

## Principio rector

> **La inteligencia lee; las cifras se verifican.** Un modelo o un buscador puede ayudar a encontrar el artículo correcto, a sugerir una clasificación o a vigilar cambios. **Nunca escribe una cifra en `base/`.** Una cifra declarada tiene fuente primaria, artículo que se puede abrir, casos al centavo y la firma de una persona.

Hoy el proyecto es un motor de reglas determinista y no usa aprendizaje automático (la única dependencia de ejecución es PyYAML). Eso es deliberado y es lo que lo hace auditable. Este plan agrega, en capas aparte, lo que lo hace **verificable** (fases 1 y 2) y **fácil de consultar** (fase 3).

## Dónde estamos (corte de nov-2026)

| | |
|---|---|
| Parámetros de ley con vigencia y fuente | 122 |
| Reglas / con calculadora / casos al centavo | 106 / 59 / 192 |
| Reglas con citas a un artículo que se puede abrir | 54 de 106 |
| Leyes en la biblioteca / artículos | 27 / 10,830 |
| Leyes con **algún cotejo humano** contra el diario oficial | **0** |
| Artículos que la base cita y nadie ha cotejado | 80 ([`cotejo_pendiente.csv`](../datos_abiertos/cotejo_pendiente.csv)) |
| …de ellos, **verificados automáticamente** contra los decretos de reforma del DOF (no es cotejo humano) | 38 verificados · 12 sin decreto que los reimprima · 30 sin revisar. Ninguna discrepancia. Ver [`scripts/cotejar_reformas.py`](../scripts/cotejar_reformas.py) |
| Deuda de las reglas de oro | 81 ([`deuda_oro.json`](../scripts/deuda_oro.json)) |

Las cifras salen de [`datos_abiertos/`](../datos_abiertos/README.md), que se regenera con `python scripts/exportar_datos_abiertos.py` y el CI comprueba que esté al día.

## Hoy, en tres fases

El orden importa: **antes de enseñar a un modelo a buscar, hay que poder confiar en lo que busca.**

### Fase 1 · Verificar lo que ya hay · rama `mejora/fase1-verificar`

Objetivo: que cada cifra que la base entrega tenga detrás un artículo comprobado por una persona.

| ID | Qué |
|---|---|
| **M-101** | Proteger `main` (PR obligatorio, CI verde, revisión de CODEOWNERS) |
| **M-102** | Cotejo humano de los **73** artículos que la base cita (no de los 10,830) |
| **M-103** | Cerrar la deuda de las reglas de oro (81) |
| **M-104** | Citas estructuradas en las reglas que aún no las traen |
| **M-105** | Subir de `por_confirmar` a `vigente` con evidencia |

**Se termina cuando:** `main` está protegida; los artículos con más dependencias (CFF 28, LISR 93, LIVA 5...) están cotejados y registrados con fecha, decreto y persona; y la deuda de reglas de oro bajó.

### Fase 2 · Medir · rama `mejora/fase2-medir`

Objetivo: tener una vara de medir **independiente del motor**. Hoy los casos los calcula el asistente y el motor coincide: eso detecta errores de programación, no errores de interpretación.

| ID | Qué |
|---|---|
| **M-201** | Casos firmados por contadores: cifra, fecha, fuente y firmante, sin datos de clientes |
| **M-202** | Pruebas por propiedades: toda póliza cuadra, una tarifa nunca baja al subir la base... |
| **M-203** | Cada calculadora principal contrastada con un ejemplo oficial citado |

**Se termina cuando:** existe un formato de casos firmados que el CI corre, y las calculadoras principales tienen una referencia que no salió del propio motor.

### Fase 3 · Buscar (la capa que lee) · rama `mejora/fase3-busqueda`

Objetivo: encontrar el artículo correcto con una pregunta en lenguaje de persona. Vive en [`busqueda/`](../busqueda/README.md).

| ID | Qué |
|---|---|
| **M-301** | Corpus abierto en JSONL (el script ya lo genera; falta publicarlo como asset de un release) |
| **M-302** | Búsqueda base por palabras clave y BM25, en Python puro, que lea los perfiles |
| **M-303** | Medirla con las preguntas doradas (recall@k) como puerta de calidad en el CI |
| **M-304** | Backend semántico opcional y enchufable (cualquier modelo de embeddings) |

**Se termina cuando:** una pregunta y un perfil regresan artículos con su ley y su estado de cotejo, y el CI falla si el recall@k de las preguntas doradas baja.

## Después

| ID | Qué | Rama |
|---|---|---|
| **M-401** | Historia de las leyes por fecha (qué texto regía un día dado) | `mejora/historia-por-fecha` |
| **M-402** | Escalar la estructura: partir por materia y separar el corpus cuando se acerque a 1 GB | `mejora/escalar-estructura` |
| **M-403** | Plugin y skills en un repositorio aparte y pequeño (después de M-101) | `mejora/plugin-skills` |
| **M-404** | Más leyes y reglamentos: el resto de la CDMX y otros estados | `mejora/mas-leyes` |
| **M-405** | Clasificadores con revisión humana (código agrupador, régimen, clave de producto) | `mejora/clasificadores-y-vigilancia` |
| **M-406** | Vigilancia de cambios con un modelo de lenguaje (solo avisa) | `mejora/clasificadores-y-vigilancia` |
| **M-407** | Limpiar las ramas viejas ya mezcladas | — |

## Cómo mejorar esto

1. **Elige** algo del [backlog](../mejoras/backlog.yaml) o **propón** algo nuevo con la plantilla de issue «Propuesta de mejora» (o un PR a `backlog.yaml`).
2. **Trabaja en una rama** `mejora/<tema>` creada desde `main`; antes de abrir el PR, rebásala sobre `main`.
3. **Trae su medida.** Toda mejora dice cómo se sabrá que mejoró: una pregunta dorada nueva, una prueba, o una cifra de `datos_abiertos/` que cambia. Sin medida no se mezcla.
4. **Corre lo de siempre:** `python -m pytest -q`, `python scripts/validar_oro.py`, `python scripts/validar_aportacion.py` y `python scripts/exportar_datos_abiertos.py` si cambiaste la base.
5. **PR firmado** (`git commit -s`). Aprobar el PR es firmar el cambio; en lo que toca a cifras, firma quien mantiene el repositorio.

## Cómo se adaptan los modos de aprendizaje y de conocimiento

Lo que decide cómo se busca y qué se sabe son **datos que cualquiera puede ajustar sin tocar el motor**:

| Qué se ajusta | Dónde | Cómo se comprueba |
|---|---|---|
| **Modos de búsqueda**: método, filtros (ámbito, entidad, materia, vigente, cotejado), pesos, sinónimos | [`busqueda/perfiles.yaml`](../busqueda/perfiles.yaml) | Las preguntas doradas no deben empeorar |
| **Sinónimos** entre cómo lo dice la gente y cómo lo dice la ley | [`busqueda/sinonimos.yaml`](../busqueda/sinonimos.yaml) | Cada grupo trae un artículo y la frase que contiene; una prueba lo verifica |
| **Preguntas doradas**: la vara de medir | [`busqueda/preguntas_doradas.yaml`](../busqueda/preguntas_doradas.yaml) | Cada artículo esperado debe existir en la biblioteca |
| **Conocimiento nuevo** (leyes, reglamentos, estados) | `/inteligencia-fiscal` y [`docs/ESTANDAR_APORTACION.md`](ESTANDAR_APORTACION.md) | `scripts/validar_aportacion.py` |
| **Modelos** (embeddings, clasificadores) | Un método enchufable de `perfiles.yaml` | Se registra el modelo (nombre, versión, huella) y se mide contra casos firmados |

Si algo falla con una pregunta real, **esa pregunta es la mejor contribución**: se agrega como pregunta dorada y desde ese día nadie puede empeorarla sin que las pruebas lo noten.

## Datos abiertos

Todo en [`datos_abiertos/`](../datos_abiertos/README.md), licencia CC BY 4.0, regenerable y con huella: `parametros.csv`, `reglas.csv`, `leyes.csv`, `citas.csv`, `cotejo_pendiente.csv` y `catalogo.json`. El **corpus** de texto (`--corpus`) no se versiona porque pesa decenas de MB: se genera cuando se necesita o se publica como asset de un release.

## Ramas

Se crean desde `main` y existen desde hoy para que el trabajo tenga dónde empezar. Se rebasan sobre `main` antes de abrir un PR y se borran al mezclarse.

| Rama | Para |
|---|---|
| `mejora/fase1-verificar` | M-102 a M-105 |
| `mejora/fase2-medir` | M-201 a M-203 |
| `mejora/fase3-busqueda` | M-301 a M-304 |
| `mejora/historia-por-fecha` | M-401 |
| `mejora/escalar-estructura` | M-402 |
| `mejora/plugin-skills` | M-403 |
| `mejora/mas-leyes` | M-404 |
| `mejora/clasificadores-y-vigilancia` | M-405 y M-406 |

## Lo que NO haremos

- Que un modelo escriba, corrija o «complete» una cifra de `base/`.
- Citar una fuente que no sea oficial, ni guardar PDFs en el repositorio.
- Casarnos con un modelo, un proveedor o una librería de IA: todo modelo es un componente reemplazable.
- Entrenar con datos de clientes ni subirlos: este repositorio es público.

## Registro de decisiones

- **Búsqueda antes que predicción.** Lo primero que aporta valor es encontrar el artículo correcto; clasificar y vigilar vienen después, y solo con casos firmados con los que medirlos.
- **Cotejar 73 artículos, no 10,830.** El esfuerzo humano se concentra en lo que la base cita, ordenado por cuántas cosas dependen de cada artículo.
- **Modos como datos.** Un perfil de búsqueda es un archivo, no código: cualquiera lo ajusta y se mide.
