# Entrega del pedido 06 de Timbra (21-nov-2026)

Base de partida: v0.6.0. Propuesta de release: **v0.7.0** (los 5 bloques; la firma de Rick es aprobar el PR). Estado de las pruebas al cierre: `timbra-reglas probar` 358 pasan · 0 fallan · 0 pendientes; `pytest` 795 pasan; `validar_oro` 0 violaciones nuevas (sale una de la deuda).

Regla de la entrega: lo que la base no trae, Timbra lo marca «la base no lo trae» o [CONFIRMAR]. Aquí cada punto dice si quedó **resuelto**, **por_confirmar** (con su motivo) o **sin respuesta en las fuentes**.

## Lo que necesita la firma o el criterio de Rick (por orden de importancia)

1. **RESICO_PF_TABLA_ANUAL desde 2027 es `por_confirmar`.** El DOF del 13-nov-2026 sube el tope del 113-E a 5 M y el último renglón de su TABLA MENSUAL; el texto del decreto sobre la TABLA ANUAL del 113-F no está en la biblioteca. Se supuso que sólo cambia el último renglón (5,000,000.00). Quien firme debe leer la nota 5803758 y compararla.
2. **Redondeo del coeficiente de utilidad (R-182).** El RLISR art. 10 dice «hasta el diezmilésimo»; no dice si se redondea o se trunca. Se redondea (igual que R-114). El caso que distingue (1,234,567 / 10 M = 0.1235 o 0.1234) queda con `confirmado: false`.
3. **Plataformas, cuándo cesa el pago definitivo (R-186).** El 113-B fr. I mide el tope con el ejercicio inmediato anterior; la RMF 12.3.9 dice «a partir del ejercicio inmediato siguiente a aquel en que dejen de reunir los requisitos». Se aplicó la lectura de la ley (si el año anterior rebasó, este año ya no es definitivo). Si el SAT entiende que se pierde un año después, cambia un caso.
4. **Plazo para cancelar CFDI de ejercicios anteriores a 2026 (R-193).** El decreto del 7-nov-2025 no trae transitorio para eso (sólo entrada en vigor, procedimientos iniciados, CNE y presupuesto). Se aplica la ley vigente a la fecha de la cancelación. El texto anterior del 29-A no está en la biblioteca.
5. **Dividendos (R-188):** el 10 % de retención sólo aplica a utilidades generadas desde 2014 (disposición transitoria que no está en la biblioteca; la calculadora avisa); el estímulo de utilidades 2014-2016 reinvertidas (1 %, 2 % o 5 %) **no** está modelado.
6. **REVISAR un valor ya publicado:** `DONATARIA_INGRESOS_NO_RELACIONADOS_PCT` trae 10 % desde 2014-01-01, pero el séptimo párrafo del art. 80 fue reformado por el DOF 30-nov-2016. La biblioteca no trae el texto anterior para saber si de 2014 a 2016 era otro porcentaje. No se tocó.
7. **Ningún texto se cotejó contra el DOF** en esta sesión (sin acceso a dof.gob.mx): todo viene de la biblioteca (Cámara de Diputados y Word del DOF de la RMF) y los PR dicen «sin cotejar». Marcar artículos como cotejados sigue siendo cosa de una persona.
8. **Firma DCO y ramas.** Los commits traen `Signed-off-by` con la identidad de la sesión; si el DCO debe ir a nombre de una persona: `git rebase --signoff main`. Por la política de ramas de esta sesión (una sola rama) los 5 bloques van como 5 commits en un PR, en el orden de los bloques; se pueden separar en 5 PR con `git cherry-pick` si se prefiere.

## Bloque 1 · RESICO persona física: la anual

| ID | Tipo | Qué trae |
|---|---|---|
| `RESICO_PF_TABLA_ANUAL` | parámetro nuevo | Tabla anual del 113-F: 300 mil 1.00 %, 600 mil 1.10 %, 1 M 1.50 %, 2.5 M 2.00 %, 3.5 M 2.50 % (2022-2026). Desde 2027 último renglón a 5 M, `por_confirmar` |
| `R-180` | regla nueva | `resico_pf_anual(ingresos_del_anio, pagos_mensuales, retenciones)` → `{isr_anual, a_cargo, a_favor}`; casos 900,000 y 3,000,000 y los límites 1,000,000 / 1,000,000.01 |
| `R-181` | regla nueva | `resico_pf_salida(motivo, ...)`: sale a partir del día 1 del mes siguiente al supuesto (113-E, 113-I, RMF 3.13.5); tras rebasar el tope puede volver con condiciones; tras incumplir, no |

- `hash_valor` nuevos: `RESICO_PF_TABLA_ANUAL@2022-01-01` 63981167654dde73 · `@2027-01-01` 0b84f201bdfd73fc. No cambia ningún hash existente.
- Por confirmar: tramo 2027; que las omisiones del 113-I salgan también al mes siguiente y no puedan volver.
- Motor de Timbra: **Motor626PF.anual** (R-180) y la salida del régimen (R-181).

## Bloque 2 · Personas morales (601 y 626 PM)

| ID | Tipo | Qué trae |
|---|---|---|
| `R-182` | regla nueva | `coeficiente_utilidad(utilidad_fiscal, ingresos_nominales, ptu_pagada, perdidas_aplicadas)`: cuatro decimales, pérdida → 0.0000. La utilidad entra antes de PTU y pérdidas; las pérdidas de ejercicios anteriores **no** cambian el coeficiente |
| `R-183` | regla nueva | `coeficiente_aplicable(ejercicio_pagos, coeficientes)`: el del último ejercicio con coeficiente, máximo cinco años atrás |
| `R-184` | regla nueva | `perdida_fiscal_actualizada(...)`: LISR 57 con el INPC real (julio-diciembre y diciembre-junio), diez ejercicios |
| `R-114` | casos nuevos | `pm_coeficiente_provisional`: mayo (1/8 de la PTU), diciembre (8/8), pérdida de 2023 actualizada a 2025 (546,021.52) y pérdida que absorbe todo |
| `R-185` | regla nueva | `resico_pm_anual(...)`. Respuesta a 2.3: **sí es el mismo acumulado de diciembre** (211 y 212 llevan al art. 9); lo propio de la anual es acreditar el impuesto de los arts. 5 y 10; no hay coeficiente ni ajuste anual por inflación |

- Sin parámetros nuevos ni hashes cambiados.
- Por confirmar: redondeo del coeficiente (punto 2); qué factor de actualización de pérdidas se usa en provisionales de enero a junio (se usa siempre el de junio); el acreditamiento del art. 10 (topes y tres ejercicios) no se calcula: la app captura el monto acreditable.
- Motor de Timbra: **Motor601.anual** (R-182, R-183, R-184), **Motor601** provisional (R-114) y **Motor626PM.anual** (R-185).

## Bloque 3 · Plataformas (625) en la anual

| ID | Tipo | Qué trae |
|---|---|---|
| `R-186` | regla nueva | `plataformas_en_anual(...)`: optó y cumple → **no se acumulan** y la retención no se acredita (LISR 113-B y 150); no optó o rebasó el año anterior → se acumulan y se acredita. Casos: optó y cumple, límite 300,000, optó y rebasa en el ejercicio, optó y el año anterior rebasó, no optó |
| `OBLIGACIONES_625_PF` | parámetro nuevo (`por_confirmar`) | Fila del 625: pago provisional (día 17), anual (abril), DIOT (relevada con ingresos del año anterior hasta 4 M) |
| `R-187` | regla nueva | `obligaciones_625_pf(...)` → `{pago_provisional, declaracion_anual, diot}` |

- `hash_valor` nuevo: `OBLIGACIONES_625_PF@2026-01-01` a341f9af47cce979.
- Por confirmar: punto 3 y que el art. 150 sólo manda informar ingresos definitivos de más de 500 mil citando el art. 138 (no el 113-B).
- Motor de Timbra: **Motor625.anual** (R-186) y la matriz de obligaciones de R-109 (R-187).

## Bloque 4 · Dividendos y donatarias

| ID | Tipo | Qué trae |
|---|---|---|
| `DIVIDENDOS_FACTOR_PIRAMIDACION` | parámetro nuevo | 1.4286 desde 2014-01-01 (LISR 10 y 140) |
| `DIVIDENDOS_RETENCION_ADICIONAL_PCT` | parámetro nuevo | 10 % desde 2014-01-01 (LISR 140, segundo párrafo) |
| `DONATARIA_PERDIDA_AUTORIZACION_PCT` | parámetro nuevo | 50 % desde 2021-01-01 (LISR 80, octavo párrafo; DOF 08-12-2020) |
| `R-188` | regla nueva | `dividendos_pf(dividendo, isr_corporativo_pagado, ...)`: ingreso acumulable = dividendo + ISR corporativo (30 % × dividendo × 1.4286), acreditamiento y retención de 10 %. El ISR corporativo lo fija la fórmula de la ley; la constancia sólo se compara |
| `R-189` | regla nueva | `donataria_remanente(...)`: remanente distribuible (no tiene tasa propia: lo gravan sus perceptores), remanente ficto y su impuesto a la tasa máxima del art. 152 (35 %), entero en febrero |
| `R-190` | regla nueva | `donataria_actividades_distintas(...)`: tope de 10 %, excedente, ISR del excedente (30 % de la utilidad que se pase) y pérdida de autorización arriba de 50 % |

- `hash_valor` nuevos: `DIVIDENDOS_FACTOR_PIRAMIDACION@2014-01-01` 77344f6c72f3b811 · `DIVIDENDOS_RETENCION_ADICIONAL_PCT@2014-01-01` 01283a9b9edb3573 · `DONATARIA_PERDIDA_AUTORIZACION_PCT@2021-01-01` 6031725da62f29ea.
- Por confirmar: puntos 5 y 6; el prorrateo de la utilidad del excedente (la ley no da fórmula: la calculadora recibe la utilidad ya determinada); cuando la mayoría de los integrantes son del Título II o de la Sección I del Capítulo II del Título IV el remanente se calcula con sus reglas (no modelado).
- Motor de Timbra: accionista de una SAPI en el régimen 611 (R-188) y régimen 603 (R-189, R-190).

## Bloque 5 · Chicos

| ID | Tipo | Qué trae |
|---|---|---|
| `R-191` | regla nueva | `isr_tasa_marginal(base, meses)` (fecha = la del caso): % del renglón de los arts. 96, 106 o 152 |
| `R-192` | regla nueva | `isr_ahorro_deduccion(base, deduccion, meses)`: el ahorro exacto de una deducción (la tasa marginal sólo aproxima si la deducción cruza renglón) |
| `LFT_VACACIONES_TABLA` | **valor cambiado** | Completada hasta 60 años (36 a 40: 34 días ... 56 a 60: 42), sin mover ningún renglón; `confirmado_hasta`. `vacaciones_dias` sigue +2 días por cada cinco años más allá de la tabla. Desde 2023-01-01 (Transitorio Primero del DOF 27-dic-2022); antes de 2023 la base avisa (no trae la tabla anterior) |
| `R-136` | casos nuevos | años 25, 26, 36, 61, 66; primer día de vigencia; antes de 2023 |
| `R-193` | regla nueva | `cfdi_plazo_cancelacion(tipo, ejercicio_emision)` (fecha = la de la cancelación): último día PM marzo y PF abril del año siguiente; requiere aceptación del receptor |
| `R-194` | regla nueva (CRITERIO) | `poliza_nomina_desglosada(...)`: ISR sueldos 216.01, asimilados 216.02, IMSS retenido 216.11, provisión patronal 211.01 / 211.02 / 211.03, gasto SAR 601.28 |
| `CONTA_CONCEPTO_AGRUPADOR` | **valor cambiado** (`por_confirmar`, criterio, sin firma) | Seis conceptos nuevos: `imss_patronal_por_pagar`, `sar_por_pagar`, `imss_retenido_trabajadores`, `isr_retenido_asimilados_por_pagar`, `aportaciones_sar` y contexto `asimilados` de `isr_retenido_por_pagar` |

- **Firmas que se caen (2):** `LFT_VACACIONES_TABLA@2023-01-01` (`5e98e71cace3…` → `67fd89c07ba98dcf`; completa la tabla, ninguna cifra publicada cambia) y `CONTA_CONCEPTO_AGRUPADOR@2026-01-01` (`cc4887cc9905…` → `225b457f28f2bf7c`; sólo se agregan filas, ninguna cambia). No cae ninguna firma de ley vigente.
- Vigencia cambiada: `LFT_VACACIONES_TABLA@2023-01-01` `confirmado_hasta` null → 2026-12-31. Sale de la deuda de oro `R5:LFT_VACACIONES_TABLA@2023-01-01`.
- Por confirmar: punto 4. Para los pendientes del pedido 05: la tabla de vacaciones (resuelto), el plazo de cancelación (parcial: sin transitorio) y el mapa de nómina (resuelto como criterio).
- Motor de Timbra: la estimación de ahorro de una deducción en persona física (R-191, R-192), cancelación de CFDI, pólizas de nómina (R-155 sigue vigente; R-194 la desglosa) y vacaciones.

## Lista de IDs nuevos y cambiados (para `scripts/actualizar_reglas.py`)

- Parámetros nuevos (5): `RESICO_PF_TABLA_ANUAL`, `OBLIGACIONES_625_PF`, `DIVIDENDOS_FACTOR_PIRAMIDACION`, `DIVIDENDOS_RETENCION_ADICIONAL_PCT`, `DONATARIA_PERDIDA_AUTORIZACION_PCT`.
- Parámetros cambiados (2, con firma que se cae): `LFT_VACACIONES_TABLA`, `CONTA_CONCEPTO_AGRUPADOR`.
- Reglas nuevas (15): `R-180` a `R-194`.
- Reglas con casos nuevos (2): `R-114`, `R-136`.
- Calculadoras nuevas (15): `resico_pf_anual`, `resico_pf_salida`, `coeficiente_utilidad`, `coeficiente_aplicable`, `perdida_fiscal_actualizada`, `resico_pm_anual`, `plataformas_en_anual`, `obligaciones_625_pf`, `dividendos_pf`, `donataria_remanente`, `donataria_actividades_distintas`, `isr_tasa_marginal`, `isr_ahorro_deduccion`, `cfdi_plazo_cancelacion`, `poliza_nomina_desglosada`. Cambia también `vacaciones_dias` (ya no se queda en 32 días después de 35 años).
- `ids_afectados` del `integracion_v0.7.0.json` (22): los 7 parámetros de arriba y `R-180` a `R-194`.

## Cómo se publica v0.7.0 (lo hace quien mantiene el repositorio)

```bash
mkdir -p /tmp/ant && git fetch --tags
git show v0.6.0:base/parametros.yaml > /tmp/ant/parametros.yaml   # base anterior (o la carpeta del release v0.6.0)
git show v0.6.0:base/reglas.yaml     > /tmp/ant/reglas.yaml
python scripts/release.py --version 0.7.0 --anterior /tmp/ant --out dist --changelog
```

`release.py` sube `version_base` a 0.7.0, corre las pruebas, arma el paquete plano con sus huellas y escribe `integracion_v0.7.0.json`. Esta entrega **no** sube la versión ni crea la etiqueta: eso es del CODEOWNER (CONTRIBUTING §6). La versión del motor (`VERSION_MOTOR`) la sube el mismo script.
