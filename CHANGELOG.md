# Changelog

Generado por `scripts/release.py --changelog` al preparar cada versión. Cada entrada sale de la comparación contra la versión anterior.

## [v0.7.0] - 2026-11-14

Pruebas: 265 pasan · 0 fallan · 0 pendientes   (* = pasa contra un esperado aún no confirmado).

Pedido 03, bloques 7 a 10: contabilidad y verificación. Ningún valor publicado cambia de valor: no cae ninguna firma. Lo único que se mueve en la base es el código agrupador.

- **Código agrupador (bloque 7):** `CONTA_CODIGO_AGRUPADOR` trae un tramo desde el 1-ene-2026 con el Anexo 24 de la RMF 2026 leído en el DOF (1,080 renglones, vigente): agrega 401.39 a 401.41 y 402.05 (zona fronteriza norte) y 000 (sector financiero), y corrige la escritura de «diésel» e «INFONAVIT». El catálogo de 2014 cierra el 31-dic-2025. Versión de los esquemas XML de catálogo, balanza y pólizas: POR CONFIRMAR (el Anexo 24 remite al documento técnico del SAT).
- **NIF (bloque 8, fuera del paquete de la base):** 35 de 47 cotejadas con los boletines del CINIF; todas las que citan las reglas y Timbra, incluidas C-1, C-6, D-1, D-3 y D-4. `datos_abiertos/nif.csv` dice qué reglas citan cada NIF. Falta la fecha de entrada en vigor de las nuevas B-1 y B-3.
- **NIIF (bloque 9, fuera del paquete):** índice de 41 IAS/IFRS con su NIF equivalente, sin cotejar (ifrs.org no abre desde el entorno de trabajo). Quién usa NIIF en México, sí cotejado en el DOF: las emisoras de la BMV desde el 1-ene-2012 (CNBV, art. 78); el resto usa NIF.
- **Verificación de artículos (bloque 10, fuera del paquete):** `scripts/cotejar_reformas.py` compara lo que reimprimen los decretos de reforma del DOF contra la biblioteca, porque el DOF no publica leyes consolidadas. 50 artículos revisados: 38 verificados contra su decreto más reciente (incluidos CFF 28, LISR 34 y 93, LIVA 5, LISR 113-E y los artículos 206 a 211 de RESICO PM), 12 sin decreto que los reimprima y 0 discrepancias. NO es el cotejo humano de M-102: ningún artículo se marca cotejado.

### Vigencias cambiadas

- CONTA_CODIGO_AGRUPADOR desde 2015-01-01: hasta None -> 2025-12-31

### Tramos nuevos

- CONTA_CODIGO_AGRUPADOR desde 2026-01-01 (vigente)

## [v0.6.0] - 2026-11-14

Pruebas: 261 pasan · 0 fallan · 0 pendientes   (* = pasa contra un esperado aún no confirmado).

Pedido 03 de Timbra, bloques 1 a 6. Cae UNA firma de valor (DEPRECIACION_TASAS_ART34, completada sin mover ninguna tasa) y cambian vigencias porque el paquete 2027 ya salió en el DOF.

- **Inversiones RESICO PM (R-172):** porcientos del LISR 209 con tope de 3 M, meses completos de uso, terreno fuera. Tramo 2027 con la reforma (construcciones 26 %, cómputo 100 %...).
- **Depreciación completa (R-121, R-173):** arts. 33, 34 (15 fracciones) y 35 (por actividad); topes de auto eléctrico (250,000) y avión (8,600,000); tasas contables de referencia por tipo de activo de Timbra (CRITERIO, por_confirmar).
- **IVA acreditable por destino (R-174) y R-17:** gravado 100 %, exento 0 %, indistinto por proporción; caso de consultorio.
- **Frontera (R-103, R-175):** RESICO PF sin crédito de ISR (RMF 11.9.23, cotejada contra el DOF); IVA 8 % norte y sur hasta el 31-dic-2026 y 16 % con aviso después. Sin prórroga publicada al 14-nov-2026.
- **Días inhábiles (R-176 a R-178):** festivos del CFF 12, serie `dias_inhabiles` del SAT (RMF 2.1.6 y modificaciones 1a. y 4a.), vencimiento recorrido con la regla del viernes en banco y plazos en días hábiles. El paquete trae ahora dos series.
- **Paquete 2027 publicado en el DOF el 13-nov-2026:** LIF 2027 (recargos 1.38/1.42/1.63/1.97, retención por intereses 0.68 %, IVA opcional 7 % para RESICO PF y PM) y reforma a la LISR (tope RESICO PF 5 M, RESICO PM 50 M, intereses netos 20 %, art. 209 duplicado). Sus tramos pasan de pendiente_dof a vigentes desde el 1-ene-2027. Nuevo: deducción inmediata Plan México 2027-2030 (R-179), que también alcanza a la RESICO PM.
- **Pendiente para la siguiente versión:** UMA 2027 (INEGI, enero), salario mínimo 2027 (CONASAMI, diciembre), Anexo 8 y RMF 2027, ISN que cambie, prórroga de frontera, y cargar a la biblioteca las 4 modificaciones de la RMF 2026 y la LIF 2027.

### Valores cambiados (firmas que se caen)

- DEPRECIACION_TASAS_ART34 desde 2014-01-01

### Estados cambiados

- INTERESES_NETOS_LIMITE_PCT desde 2027-01-01: aprobado_congreso_pendiente_dof -> vigente
- ISR_RET_INTERESES desde 2027-01-01: aprobado_congreso_pendiente_dof -> vigente
- IVA_RESICO_PF_OPCION_TASA desde 2027-01-01: aprobado_congreso_pendiente_dof -> vigente
- RECARGOS_PARCIALIDADES_12M desde 2027-01-01: aprobado_congreso_pendiente_dof -> vigente
- RECARGOS_PARCIALIDADES_24M desde 2027-01-01: aprobado_congreso_pendiente_dof -> vigente
- RECARGOS_PARCIALIDADES_MAS24M desde 2027-01-01: aprobado_congreso_pendiente_dof -> vigente
- RECARGOS_PRORROGA_MENSUAL desde 2027-01-01: aprobado_congreso_pendiente_dof -> vigente
- RESICO_PF_TOPE_ANUAL desde 2027-01-01: aprobado_congreso_pendiente_dof -> vigente
- RESICO_PM_TOPE_ANUAL desde 2027-01-01: aprobado_congreso_pendiente_dof -> vigente

### Vigencias cambiadas

- INTERESES_NETOS_LIMITE_PCT desde 2020-01-01: hasta None -> 2026-12-31
- INTERESES_NETOS_LIMITE_PCT desde 2027-01-01: hasta None -> None
- IVA_RESICO_PF_OPCION_TASA desde 2027-01-01: hasta None -> 2027-12-31
- RESICO_PF_TABLA desde 2022-01-01: hasta None -> 2026-12-31
- RESICO_PF_TOPE_ANUAL desde 2022-01-01: hasta None -> 2026-12-31
- RESICO_PF_TOPE_ANUAL desde 2027-01-01: hasta None -> None
- RESICO_PM_TOPE_ANUAL desde 2022-01-01: hasta None -> 2026-12-31
- RESICO_PM_TOPE_ANUAL desde 2027-01-01: hasta None -> None

### Tramos nuevos

- ISR_RET_INTERESES desde 2026-01-01 (vigente)
- RESICO_PF_TABLA desde 2027-01-01 (vigente)

### Parámetros nuevos

- AUTO_TOPE_DEDUCCION_ELECTRICO
- AVION_TOPE_DEDUCCION
- CFF_DIAS_INHABILES
- DEDUCCION_INMEDIATA_PLAN_MEXICO
- DEPRECIACION_CONTABLE_REFERENCIA
- DEPRECIACION_TASAS_ART33
- DEPRECIACION_TASAS_ART35
- IVA_TASA_FRONTERA_SUR
- RESICO_PM_INVERSIONES
- RESICO_PM_INVERSIONES_TOPE

### Reglas nuevas

- R-172
- R-173
- R-174
- R-175
- R-176
- R-177
- R-178
- R-179


## [v0.5.0] - 2026-11-13

Pruebas: 193 pasan · 0 fallan · 0 pendientes   (* = pasa contra un esperado aún no confirmado).

Para Timbra: toma lo que estaba en main sin publicar desde la v0.4.2 (pedido 02: factura global, servicios médicos, retención RESICO y comisión de la terminal; código agrupador). Ningún valor que ya existía cambia: no cae ninguna firma.

- **Contabilidad:** código agrupador del SAT completo y mapa de conceptos de las pólizas (R-163 y R-164).
- **Pedido 02 de Timbra (R-165 a R-171):** periodicidad de la factura global por régimen, comprobante mínimo, cancelación de la global en RESICO, IVA exento de servicios médicos (prestadores y profesiones), retención de ISR a RESICO y comisión de la terminal en el cobro.
- **INPC oct-2026 = 147.026** (DOF 10-nov-2026, nota 5803352), cruzado con Banxico SIE SP1: la serie cubre oct-2021 a oct-2026. El caso de R-162 que usaba «el último publicado (sep-2026)» pasa a pago en dic-2026 y se agrega el de pago en nov-2026, que ya usa octubre.
- **NIF cotejadas contra el CINIF (13-nov-2026):** la NIF A-1, *Marco Conceptual*, sustituyó desde 2023 a las A-1 a A-8 anteriores (pasan a `derogadas`); la A-2 vigente desde 2026 es *Incertidumbres sobre negocio en marcha*. 18 de 47 quedan cotejadas con su documento del CINIF; las demás siguen `cotejado: false` porque el listado completo es de pago. La B-1 y la B-3 tienen versión nueva en el libro 2026, con fecha de vigencia por confirmar. R-152 citaba la A-2 para la devengación: ahora cita la A-1 (cambia `citas`, no valores).
- **Citas estructuradas, `que_dice` y `correcto_si`** en 25 reglas más; leyes de la CDMX en la biblioteca; datos abiertos regenerables y capa de búsqueda.

### Parámetros nuevos

- CONTA_CODIGO_AGRUPADOR
- CONTA_CONCEPTO_AGRUPADOR
- GLOBAL_COMPROBANTE_MINIMO
- GLOBAL_PERIODICIDAD_POR_REGIMEN
- IVA_EXENTO_PRESTADORES_MEDICOS
- IVA_EXENTO_PROFESIONES_MEDICAS
- RESICO_GLOBAL_CANCELACION_MES

### Reglas nuevas

- R-163
- R-164
- R-165
- R-166
- R-167
- R-168
- R-169
- R-170
- R-171



## [v0.4.2] - 2026-11-07

Pruebas: 149 pasan · 0 fallan · 0 pendientes   (* = pasa contra un esperado aún no confirmado).

Sin cambios de valores: no cae ninguna firma. Se agregan reglas, calculadoras, parámetros por confirmar y los campos de fundamento que lee el círculo de las apps.

- **Contabilidad:** pólizas tipo con casos al centavo (R-150 a R-157): CFDI emitido, cobro (banco, caja y divisa), CFDI recibido, pago, nota de crédito, nómina con provisión, entero de retenciones y acreditamiento del IVA retenido en la declaración siguiente (LIVA 5 fr. IV). Las NIF como referencia en `fuentes/nif/`.
- **Fiscal:** plataformas digitales (R-160) separando personas físicas (LISR 113-A) y morales (LIF 2026 art. 25 fr. VI), con pago definitivo y sin RFC; anual de personas morales (R-161); actualización con INPC real y recargos (R-162) con `serie(id, fecha)` y la serie INPC del DOF.
- **Fundamento:** `citas`, `que_dice` y `correcto_si` en las reglas nuevas y en R-20, R-22, R-110, R-111, R-113, R-114, R-118, R-120 y R-131.
- **Parámetros nuevos, por confirmar contra el DOF:** `PLATAFORMAS_ISR_PF_TABLA`, `PLATAFORMAS_ISR_PM_TABLA` y `PLATAFORMAS_PD_TOPE_ANUAL`. Se corrige además un dato que ya estaba en la base: el 2.5 % de plataformas es de personas morales; a las personas físicas la LISR les retiene 1 %.
- **Paquete:** el paquete plano del release ahora trae `series/*.yaml` además de los 4 archivos (en el release, la serie se publica como `series_<id>.yaml`), con sus huellas en `SHA256SUMS` y en `integracion_vX.json`, y el CI prueba el paquete SOLO, sin el repositorio.
- **Motor:** `integracion_vX.json` en cada release, `exportar` corregido para la tabla acumulada del art. 106 y consola de Windows en UTF-8.

### Estados cambiados

- BANXICO_SERIE_TC_CFF20 desde 1990-01-01: por_confirmar -> vigente
- TIPO_CAMBIO_REGLA desde 1990-01-01: por_confirmar -> vigente

### Parámetros nuevos

- DIAS_POR_MES_SM
- PLATAFORMAS_ISR_PF_TABLA
- PLATAFORMAS_ISR_PM_TABLA
- PLATAFORMAS_PD_TOPE_ANUAL

### Reglas nuevas

- R-150
- R-151
- R-152
- R-153
- R-154
- R-155
- R-156
- R-157
- R-160
- R-161
- R-162

### Reglas que cambiaron de estado

- R-138: CORREGIR -> OK
- R-52: CORREGIR -> OK




## [v0.4.1] - 2026-11-05

Base inicial publicada en este repositorio (90 casos).

- Cotejo contra el PDF oficial del Anexo 8 RMF 2026: tarifas diaria, semanal, decenal, quincenal, mensual y anual 2026 iguales.
- Cargadas las tarifas acumuladas del art. 106 (febrero a noviembre), la trimestral de arrendamiento, la RIF bimestral y la anual 2025.
- Nueva regla R-140: las tarifas de 7, 10 y 15 días son la diaria × días.
