# Plan de seguimiento · timbra-reglas

Corte: 6-nov-2026. Base vigente: **v0.4.1** (90 casos). `main` en `79a9ee9`. Tag `v0.4.1` en `365546f`.

## Estado por punto

| Punto | Qué | Estado | Evidencia |
|---|---|---|---|
| 0 | Base v0.4.1 cargada tal cual, `.gitignore`, README UTF-8 | **Hecho, en main** | huellas = `SHA256_v0.4.1.txt` |
| A | Paquete `timbra_reglas`, comando `timbra-reglas`, pytest | **Hecho, en main** | 138 pruebas; wheel instalado en entorno limpio |
| B | Licencias, AVISO, CODEOWNERS, CONTRIBUTING, plantillas, CHANGELOG | **Hecho, en main** | `docs/PROTECCION_DE_MAIN.md` |
| C | CI por PR (probar, pytest, reglas de oro, diff comentado, DCO) y release por tag | **Hecho, en main; sin verlo correr** | revisar pestaña Actions |
| D | Series INPC y tipo de cambio CFF 20 | **Bloqueado** | faltan tokens Banxico e INEGI |
| E | Flujos n8n (Vigía DOF, Series, Vigencias, Recordatorio) | **Pendiente** | faltan credenciales y bot de Telegram |
| F | Skill `base-fiscal-timbra` en `.claude/skills/` | **Pendiente** | archivos sin versionar en la raíz |

## Pendiente de Rick (en GitHub)

1. **Publicar el release v0.4.1** sobre el tag existente, con los 7 archivos de `out/release-v0.4.1/` (zip, 4 sueltos, ORDEN, SHA256). Decidir si la ORDEN_CAMBIO_04 va pública.
2. **Mirar la pestaña Actions**: es la primera corrida de `ci.yml`. Avisar si algo falla.
3. **Activar la protección** de `docs/PROTECCION_DE_MAIN.md` (ruleset de rama, ruleset de tags, merge commits, secret scanning) y crear los labels `cambio-de-ley`, `error-calculo`, `serie-automatica`, `esperando-firma`.
4. **Crear la GitHub App** `timbra-reglas-bot` (Contents, Pull requests, Issues: lectura y escritura; instalada solo en este repo) y guardar su `.pem` en n8n.
5. **Revisar 3 RFC** de los casos de R-27 en `base/reglas.yaml` (la lista exacta está en `scripts/deuda_oro.json`): si alguno es real, cambiarlo por uno genérico.
6. **Mover el repo fuera de Drive** (por ejemplo `C:\dev\timbra-reglas`): Drive mete `desktop.ini` en `.git/refs` y rompe `fetch`.
7. Para D: tokens de **Banxico (SIE)** e **INEGI (API INPC)**, guardados como variables de entorno locales, nunca en el repo.
8. Para E: bot de **Telegram** (token y `chat_id`) en las credenciales de n8n.

## Mañana (orden)

1. **F · Skill:** mover `SKILL.md`, `references/` y `assets/` a `.claude/skills/base-fiscal-timbra/`, adaptar rutas (`base/`, `timbra_reglas/`, `scripts/`, `timbra-reglas probar`), quitar los duplicados de la raíz. Un PR.
2. **E · n8n:** cuatro JSON importables en `automatizacion/n8n/` con README y los tokens de permisos mínimos. El Vigía nunca escribe valores; solo abre issues «cambio de ley».
3. **D · Series** (si hay tokens): `series/inpc.yaml`, `series/tipo_cambio_cff20.yaml`, `serie(id, fecha)` en el motor, calculadora de actualización CFF 17-A con INPC real, CI de series (huecos, duplicados, saltos > 5 %). Evidencia de SF60653 contra SF43718.
4. **Release v0.5.0** cuando D traiga función nueva: `release.py --changelog`, PR, tag.

## Deuda de la base (el CI la deja pasar, solo puede bajar)

`scripts/deuda_oro.json`: 82 violaciones.

- 72 tramos con `hasta: null` sin `confirmado_hasta` (regla 5).
- 6 reglas con número y un solo caso: R-14, R-17, R-30, R-81, R-83, R-117 (regla 6).
- 3 RFC no genéricos en `reglas.yaml` (regla 8).
- 1 ID con año: `DIOT_LAYOUT_2025` (regla 2). Renombrarlo cambia valores que usa la app: coordinar con un tramo nuevo, no editando el publicado.

Cada una la resuelve la investigación con fuente y la firma Rick en un PR aparte.

## Matriz de cobertura: huecos que la app aún escribe a mano

Sin ID en la base o sin fuente primaria cotejada:

- Calendario de vacaciones del SAT y festivos del CFF 12 (candidatos a serie).
- Retención de plataformas a persona moral.
- Plazo de cancelación CFF 29-A: está en la base; el código de la app aún no lo usa.
- Tabla RESICO PF 2027 si cambia con la reforma.
- Serie de tipo de cambio: SF43718 (app hoy) contra SF60653 (CFF 20), por confirmar.
- Pendientes de v0.4.1: NOM111, RESICO 3.13.x, DIOT pipe final y país, IDs de la API del INPC, ISN de 24 entidades.

## Decisiones tomadas

- Licencias: Apache-2.0 (código), CC BY 4.0 (datos).
- El release es un paquete **plano** de 4 archivos; la estructura interna del repo no se nota afuera.
- `nivel` (A/B) vivirá en `base/niveles.yaml`, con firma de Rick por CODEOWNERS; lo que no diga A es B. **Aún no creado.**
- Texto de ley en `fuentes/` como texto extraído con URL y SHA256; los PDF no entran al historial.
- Merge solo con «merge commit» para conservar el `Signed-off-by`.

## Riesgos

- Los workflows no se han visto correr: pueden requerir ajustes menores.
- Mientras no haya protección, `main` acepta push directo.
- El tag `v0.4.1` apunta al estado previo al paquete: no debe moverse (la app verifica por huella y commit).

## Actualización 6-nov-2026 (tarde): conocimiento fiscal antes que integración

Se midió la base y es corta: 86 reglas, 38 con casos (92 casos), 8 con fuente a nivel de regla; ~12 reglas de contabilidad; sin biblioteca de leyes ni vigía. El «80 %» se retira.

Hecho en esta rama:

- `fuentes/leyes/`: LISR, LIVA, LSS, Ley del Infonavit y LFPIORPI, un artículo por archivo, con huellas ([README](../fuentes/leyes/README.md)). Las 72 citas de ley de la base a estas cinco resuelven; ninguna apunta a un artículo inexistente.
- `scripts/vigia_dof.py`: lee el índice diario del DOF (`dof.gob.mx`, sin «www»; el certificado de `www` falla). No hay API oficial: es HTML, y si cambia el script falla en vez de callar. En 25 días reales leyó 213 notas y marcó 1 posible cambio (decreto de aguinaldo del 23-oct); tipo de cambio, TIIE, UDI, INPC y estímulos de combustibles salen aparte como datos de serie.
- `DIAS_POR_MES_SM` (30.4) en la base.

Falta, en orden: CFF, LFT, LIEPS, RLISR, RLIVA, RMF y Anexos → matriz obligaciones × régimen con artículo y parámetro → reglas nuevas (deducciones LISR 25/28, retenciones, ajuste anual, cierre) → contabilidad → n8n con el Vigía como primera pieza.

Pendiente de Rick: dar acceso de red a `omawww.sat.gob.mx` para la RMF (hoy solo está permitido en el entorno de esta sesión) y elegir qué sigue primero.

Hallazgo por verificar: la sesión de factureedp reporta, con datos de Banxico de 675 días, que la regla de tipo de cambio que Timbra ya usa coincide con SF60653, lo que contradice R-52 y R-138 (CORREGIR, «Timbra usa SF43718»). No se cambia la base con un resumen: se necesita el script y los datos de la comparación en un archivo; con eso, R-138 pasa a OK en un PR con su caso.

## Actualización 6-nov-2026 (noche)

- **R-52 y R-138 pasan a OK.** La evidencia de factureedp (675 días, SF43718 contra SF60653, 0 diferencias) está en `fuentes/evidencia/tc_cff20/` con sus huellas, y la recalculé desde los JSON crudos con código propio: mismo resultado. No hay que cambiar de serie: la app guarda SF43718 y deriva la regla del DOF anterior (el segundo FIX previo), que equivale a SF60653. R-52 tiene ahora 4 casos reales (con el puente del 2-nov) y una calculadora nueva en el motor (`tipo_cambio_dof_anterior`).
- **Biblioteca de leyes: 9 textos.** LISR, LIVA, LSS, Ley del Infonavit, LFPIORPI, LFT, CFF, RLISR y RLIVA. Cada artículo trae ley, ubicación, fuente, última reforma y «Cotejado con el DOF: NO» hasta que una persona lo cotee; los parámetros que citan artículos sin cotejar no se firman. Las 98 citas de la base a estas leyes resuelven.
- Falta: RMF con Anexos (necesita `omawww.sat.gob.mx` en el entorno donde se trabaje), LIEPS, LIF.
- Cuidado con los reglamentos: la Cámara tiene el RLISR en la versión de 2016 y el RLIVA en la de 2014; cotejar contra el DOF antes de firmar.

## Actualización 7-nov-2026

- Barrido del DOF de ~1,800 días: resultados y alertas en [HALLAZGOS_DOF.md](HALLAZGOS_DOF.md). **Alerta mayor: los valores del subsidio para el empleo 2026 citan un decreto del 31-dic-2025 que no aparece en el DOF**; el vigente (31-dic-2024) da 13.8 % y $10,171.00. Los tramos quedaron `por_confirmar`; falta tu decisión.
- `series/inpc.yaml` (oct-2021 a sep-2026): 49 meses del DOF coinciden con Banxico sin diferencias; 11 meses sin nota del DOF localizada, marcados sin cotejar.
- R-17 con 5 casos (sale de la deuda de reglas de oro).
- Falta: Ley del IEPS, Reglamento de la LFPIORPI, RMF 2026 con anexos y modificaciones; cotejo humano artículo por artículo.

- RMF 2026 en la biblioteca (`fuentes/rmf/`, 1,208 reglas, texto del DOF, sin revisión humana). Faltan sus tres modificaciones y los anexos. Una cita de la base estaba equivocada (2.8.1.7 → 2.8.1.6 fracc. II) y se corrigió.
