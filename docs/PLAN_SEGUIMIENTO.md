# Plan de seguimiento · inteligencia-mx (antes timbra-reglas)

Corte: 7-nov-2026. `main` en `8b001a2`, CI verde. Release publicado: **v0.4.1** (tag en `365546f`, huellas verificadas). Siguiente: v0.4.2 (sin cambio de valores).

## Estado

| Qué | Estado |
|---|---|
| Repo renombrado a `inteligencia-mx` (el nombre viejo redirige; el paquete `timbra_reglas` y el comando `timbra-reglas` no cambian) | **Hecho** |
| Base v0.4.1, paquete, pytest, gobierno del repo, CI y release por tag | **Hecho, en main** |
| Biblioteca de leyes (20 textos) y RMF 2026 (1,208 reglas), INPC 60 meses, evidencia del tipo de cambio CFF 20, Vigía del DOF (script), IMSS e Infonavit cotejados | **Hecho, en main** |
| `integracion_vX.json` en cada release + [docs/INTEGRACION.md](INTEGRACION.md) | **Hecho** |
| Skill `/aportar-inteligencia-mx` | **Hecha** |

## Foco activo: lo que hace funcionar la app (reglas de cálculo y contabilidad)

1. **Reglas de cálculo por régimen**, con casos al centavo. Hoy hay cálculo con casos para 612 (R-20, R-110), RESICO PF (R-22), 606 (R-111), RESICO PM (R-113), 601 (R-114), plataformas (R-118), anual PF (R-120), depreciación (R-121) y nómina (R-125 a R-136). Faltan o están sin calculadora: **R-21** (606, CORREGIR), **R-23** (RESICO PM), **R-24** (601 antiguo), **R-28** (625 y 621), **R-104** (anual PM).
2. **Contabilidad.** Sin calculadora ni casos: pólizas **R-60 a R-65**, estados financieros **R-70 a R-76**, contabilidad electrónica Anexo 24 **R-101**. Las **NIF** entran como referencia y resumen propio, nunca su texto (derechos del CINIF).
3. **Insumos de la app** (prompt ya entregado a Rick): catálogo de cuentas con código agrupador, pólizas tipo, regímenes por obligación, plataformas y casos de oro sin datos de clientes.
4. **Chihuahua** (ISN, Código Fiscal del Estado, Ley de Ingresos): bloqueado hasta abrir los hosts del estado.
5. **Release v0.4.2** con lo que ya está en `main` (cero valores cambiados; 2 estados pasan a vigente y 1 parámetro nuevo): `release.py --changelog`, PR y tag. Con eso la app prueba `integracion_vX.json` de verdad.

## EN PAUSA (diferido a propósito): automatización y contribución

Nada de esto bloquea la app. Se retoma cuando Rick lo decida.

### GitHub Apps y protección del repositorio

- [ ] **GitHub App del repo** (nombre sugerido `inteligencia-mx-bot`): Contents, Pull requests e Issues en lectura y escritura; instalada solo en este repo; `.pem` guardado solo en n8n o secrets. Es la que abre los PRs automáticos (series) para que Rick pueda aprobarlos y para que se dispare el CI.
- [ ] **GitHub App de Timbra** `timbra-bump-bot`: Contents y Pull requests; instalada solo en `factureedp`. La necesita la app para abrir sola el PR «subir base a vX».
- [ ] **Protección de `main`** y de los tags (`docs/PROTECCION_DE_MAIN.md`): ruleset de rama con CODEOWNERS obligatorio, CI verde, solo «merge commit»; ruleset de tags `v*`; secret scanning. Mientras no esté activa, `main` acepta push directo.
- [ ] **Labels:** `cambio-de-ley`, `error-calculo`, `serie-automatica`, `esperando-firma`.
- [ ] Revisar la pestaña **Actions** de cada release (la primera corrida de `release.yml` está por verse).

### n8n (Rick lo tiene autoalojado)

- [ ] **Vigía DOF (diario):** ejecuta `scripts/vigia_dof.py`; si hay coincidencia abre un issue «cambio de ley» con el enlace. Nunca escribe valores.
- [ ] **Series:** tipo de cambio diario (Banxico) e INPC mensual (INEGI); abre un PR a `series/` con fuente y fecha, con la GitHub App.
- [ ] **Vigencias (semanal):** corre `timbra-reglas vigencias` a hoy + 60 días y manda el resumen a Telegram.
- [ ] **Recordatorio (semanal):** PRs abiertos esperando la firma de Rick, a Telegram.
- [ ] Entregar los 4 como JSON importable en `automatizacion/n8n/` con README.
- [ ] **Credenciales** (solo en n8n, nunca en el repo): GitHub App (con el paso que genera el token temporal desde el `.pem`), token de **Banxico** (SIE), token de **INEGI** (API INPC) y bot de **Telegram** (token y `chat_id`).

### Series automáticas

- [ ] `series/tipo_cambio_cff20.yaml` (la evidencia SF43718 contra SF60653 ya está en `fuentes/evidencia/tc_cff20/`).
- [ ] `serie(id, fecha)` en el motor y la calculadora de actualización con INPC real (CFF 17-A, factor al diezmilésimo, mínimo 1).
- [ ] CI de series: fechas sin huecos, sin duplicados y saltos de más de 5 % marcados para revisión humana.
- [ ] 11 meses del INPC sin nota del DOF localizada (marcados «sin cotejar»).

### Contribución (abrir el repo a socios y a la comunidad)

- [ ] Compartir la skill `/aportar-inteligencia-mx` con conocidos y probarla con una persona externa de principio a fin (fuente, caso, PR firmado).
- [ ] `base/niveles.yaml` (A/B por regla) con firma de Rick por CODEOWNERS; lo que no diga A es B.
- [ ] Skill de mantenedor: mover `base-fiscal-timbra` a `.claude/skills/` como `mantener-base`, con rutas nuevas (hoy es un borrador sin versionar).
- [ ] **Crecer más allá de lo fiscal** (cuando toque): `materia`, `ámbito` y `jurisdicción` como campos nuevos (sin renombrar IDs); partir la base por materia manteniendo el paquete plano de 4 archivos; citas estructuradas `{ley, artículo, fracción}` verificables contra `fuentes/`; corpus legal en repo aparte o como assets de release; versiones consolidadas de cada ley por decreto del DOF.
- [ ] Capa de aprendizaje automático separada: lee la base para clasificar, sugerir y buscar; nunca escribe cifras.
- [ ] Renombrar el paquete de Python solo en una versión 1.0 coordinada con la app.
- [ ] Cotejo humano artículo por artículo de las leyes (todas están «sin cotejar con el DOF» hasta entonces).
- [ ] Biblioteca: Ley Aduanera desactualizada (reforma del 23-oct-2026), las 4 modificaciones de la RMF 2026 y sus anexos.

## Pendiente de Rick (decisiones)

1. Abrir los hosts de Chihuahua (ISN y Código Fiscal del Estado) y decidir PR único o por tema.
2. Decir cuándo se corta el release v0.4.2.
3. Revisar los 3 RFC de los casos de R-27 (la lista exacta está en `scripts/deuda_oro.json`): si alguno es real, cambiarlo por uno genérico.
4. Mezclar a `main` solo con aprobación suya; la protección de `main` está en pausa.

## Deuda de la base (el CI la deja pasar, solo puede bajar)

`scripts/deuda_oro.json`: 81 violaciones (R-17 ya salió).

- 72 tramos con `hasta: null` sin `confirmado_hasta` (regla 5).
- 5 reglas con número y un solo caso: R-14, R-30, R-81, R-83, R-117 (regla 6).
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

## Actualización 7-nov-2026 (cierre del barrido corregido)

- Barrido del DOF repetido leyendo **todas las ediciones**: 1,819 días, 30,010 notas. Resultados en [HALLAZGOS_DOF.md](HALLAZGOS_DOF.md), que **retira** las dos alertas del primer intento (subsidio 2026 y salario mínimo): ambos existen en el DOF y la base estaba bien.
- INPC: los 60 meses (oct-2021 a sep-2026) salen del DOF y coinciden con Banxico sin diferencias.
- **Ley Aduanera desactualizada** en la biblioteca: el DOF la reformó el 23-oct-2026 y el PDF de la Cámara no lo trae (advertencia en su manifiesto).
- La RMF 2026 tiene **cuatro** modificaciones publicadas (9-jul, 1-oct, 2-oct y 30-oct), no tres; ninguna está en la biblioteca.
- El Vigía detecta decretos «ómnibus» y lee su texto: el del 1-abr-2024 reformó el art. 79 de la LISR con un título que no la nombra.
- Pendiente de Rick: abrir hosts de Chihuahua (ISN y Código Fiscal del Estado), y decidir PR único o por tema.
