# Changelog

Generado por `scripts/release.py --changelog` al preparar cada versión. Cada entrada sale de la comparación contra la versión anterior.

## [v0.4.2] - 2026-11-07

Pruebas: 149 pasan · 0 fallan · 0 pendientes   (* = pasa contra un esperado aún no confirmado).

Sin cambios de valores: no cae ninguna firma. Se agregan reglas, calculadoras, parámetros por confirmar y los campos de fundamento que lee el círculo de las apps.

- **Contabilidad:** pólizas tipo con casos al centavo (R-150 a R-157): CFDI emitido, cobro (banco, caja y divisa), CFDI recibido, pago, nota de crédito, nómina con provisión, entero de retenciones y acreditamiento del IVA retenido en la declaración siguiente (LIVA 5 fr. IV). Las NIF como referencia en `fuentes/nif/`.
- **Fiscal:** plataformas digitales (R-160) separando personas físicas (LISR 113-A) y morales (LIF 2026 art. 25 fr. VI), con pago definitivo y sin RFC; anual de personas morales (R-161); actualización con INPC real y recargos (R-162) con `serie(id, fecha)` y la serie INPC del DOF.
- **Fundamento:** `citas`, `que_dice` y `correcto_si` en las reglas nuevas y en R-20, R-22, R-110, R-111, R-113, R-114, R-118, R-120 y R-131.
- **Parámetros nuevos, por confirmar contra el DOF:** `PLATAFORMAS_ISR_PF_TABLA`, `PLATAFORMAS_ISR_PM_TABLA` y `PLATAFORMAS_PD_TOPE_ANUAL`. Se corrige además un dato que ya estaba en la base: el 2.5 % de plataformas es de personas morales; a las personas físicas la LISR les retiene 1 %.
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
