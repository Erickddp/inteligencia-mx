# Matriz app ↔ base · qué ID le toca a cada número escrito a mano en factureedp

Corte: 6-nov-2026. Base vigente **v0.4.1**. App: PR 5 de `Erickddp/factureedp` (rama `ccr-54159374-pvzljr`, commit `4007a2e`).

Fuente del lado de la app: `Timbra/backend/tests/numeros_de_ley.json` (el trinquete: 66 apariciones de números de ley escritas a mano; solo puede bajar).

## 1. Lo que el puente ya hace (verificado en el PR 5)

- `app/reglas/` trae la base v0.4.1 vendorizada, con `VERSION.json` y las huellas. El CI las compara sin red.
- `services/base_reglas.py` carga la base y pide cada número **por fecha** con `valor(id, fecha)`.
- Ya leen de la base: `UMA_DIARIA`, `UMA_MENSUAL`, `UMA_ANUAL`, `ISR_TARIFA_MENSUAL`, `RESICO_PF_TABLA`, `RESICO_PF_TOPE_ANUAL`, `RESICO_PM_TOPE_ANUAL`, `ISR_PM_TASA`, `DED_PERS_VECES_UMA_ANUAL`, `DED_PERS_PCT_INGRESO`, `IVA_TASA_GENERAL`, `IVA_RET_DOS_TERCIOS`, `DEDUCCION_EFECTIVO_TOPE`, `DIOT_LAYOUT_2025`.
- Falta publicar el release **v0.4.1** de este repo para que la revisión (b) de la app (contra el release) deje de avisar.

## 2. Números escritos a mano → ID de la base

Cada fila es una categoría del trinquete. «Archivos» son los que el trinquete cuenta hoy.

| Número en la app | ID de la base | Regla | Archivos en la app (apariciones) | Paso |
|---|---|---|---|---|
| IVA 16 % | `IVA_TASA_GENERAL` | R-15 | `services/lotes.py` (7), `demo_escenarios.py` (4), `semillas.py` (3), `cfdi.py` (2), `validacion.py` (2), `xmlsat/lector.py`, `models.py`, `schemas.py`, `pac.py`, `ventas.py`, `mandato.py`, `credito_timbres.py`, `revision_cfdi.py`, `xml_indice.py`, `routers/portal.py`; front: `format.ts` (2), `sat.ts` (2), `facturar/page.tsx` (3), `portal/page.tsx` (3), `perfil-lote.tsx` (3), `atajos.tsx` | 2A (cierre) |
| IVA 8 % frontera | `IVA_TASA_FRONTERA_NORTE` | R-15 | `validacion.py` (3), `cfdi.py`, `semillas.py`, `productos_io.py`, `revision_cfdi.py`, `xml_indice.py`, `xmlsat/lector.py`, `xmlsat/pdf.py`, `routers/portal.py`; front: `format.ts` (3), `movimiento.ts` (4), `portal/page.tsx` (2), `perfil-lote.tsx` | 2A (cierre) |
| Retención de IVA 2/3 | `IVA_RET_DOS_TERCIOS` | R-16 | `semillas.py` (6), `routers/emisores.py` (2), `cfdi.py`, `productos_io.py`; front: `format.ts` (6), `calculadora/page.tsx` (4), `fiscal.ts` (2), `emisores/page.tsx` (2), `facturar-listas.tsx` (2) | 2A (cierre) |
| Retención de IVA 4 % / 6 % | `IVA_RET_AUTOTRANSPORTE` (4 %), `IVA_RET_SERV_ESPECIALIZADOS` (6 %) | R-16 | `semillas.py` (2); front: `format.ts` (2) | 2A (cierre) |
| Retención RESICO 1.25 % | `RESICO_PF_RETENCION_PM` | R-22, R-106 | `validacion.py`, `semillas.py`, `productos_io.py`; front: `format.ts` | 2A (cierre) |
| Deducción ciega 35 % | `ARREND_DEDUCCION_CIEGA_PCT` | R-21, R-111 | `validacion.py`; front: `fiscal.ts`, `movimiento.ts` | 3 |
| ISR personas morales 30 % | `ISR_PM_TASA` | R-24, R-114 | `estados_financieros.py`; front: `fiscal.ts` | 3 |
| Tope de automóvil | `AUTO_TOPE_DEDUCCION` | R-121 | `estados_financieros.py` | 3 |
| Tarifa de ISR (6 tramos) | `ISR_TARIFA_MENSUAL` (y, para cada periodo, `ISR_TARIFA_DIARIA`, `ISR_TARIFA_SEMANAL`, `ISR_TARIFA_DECENAL`, `ISR_TARIFA_QUINCENAL`, `ISR_TARIFA_ANUAL`) | R-20, R-82, R-120, R-140 | front: `fiscal.ts` (6) | 3 |
| Topes RESICO | `RESICO_PF_TOPE_ANUAL`, `RESICO_PM_TOPE_ANUAL` | R-22, R-23 | front: `fiscal.ts` (2) | 3 |
| UMA | `UMA_DIARIA`, `UMA_MENSUAL`, `UMA_ANUAL` | R-81 y las que usan fórmula | `nomina_params.py` (7); front: `fiscal.ts` (6) | 3 y 5 |
| Salario mínimo | `SM_GENERAL_DIARIO`, `SM_ZLFN_DIARIO` | R-81 | `nomina_params.py` (4) | 5 |
| Subsidio para el empleo | `SUBSIDIO_EMPLEO_PCT_UMA`, `SUBSIDIO_EMPLEO_MENSUAL`, `SUBSIDIO_EMPLEO_LIMITE_INGRESO` | R-82, R-131 | `nomina_params.py` (8) | 5 |
| Prima de riesgo | `PRIMA_RIESGO_INICIAL_POR_CLASE`, `PRIMA_RIESGO_MINIMA`, `PRIMA_RIESGO_MAXIMA` | R-84 | `nomina_calculo.py` (2); front: `nomina-calculo.tsx` | 5 |
| 30.4 días | `DIAS_POR_MES_SM` (en la base desde la próxima versión; ver sección 4) | R-82, R-128, R-140 | `nomina_calculo.py` (7), `nomina_params.py` (3), `estados_balance.py` | 5 |

## 3. Lo que la app aún no usa y sí tiene ID

| Tema | IDs | Regla | Qué falta en la app | Paso |
|---|---|---|---|---|
| Tipo de cambio por fecha de publicación en el DOF | `TIPO_CAMBIO_REGLA`, `BANXICO_SERIE_TC_CFF20` | R-52, R-138 | `services/tipo_cambio.py:29` usa la serie de fecha de determinación; la base manda la de liquidación (publicación en el DOF), con fecha de causación menos un día. Evidencia de ambas series contra el token: tarea de D en este repo | 2C |
| Saldo a favor de IVA entre años | sin parámetro (es lógica de la regla) | R-13, R-14, R-18 | El saldo se arrastra solo dentro del año; que no muera en diciembre | 2C |
| Proporción de IVA con exentas y no objeto | sin parámetro | R-17 | La base ya calcula: R-17 (proporción, 7 casos) y R-174 (acreditamiento por destino, LIVA 5 fr. V, con caso de consultorio); falta que la app clasifique cada gasto como gravado, exento o indistinto | 2C |
| Vencimiento día 17 y sexto dígito | `DIA_VENCIMIENTO_MENSUAL`, `DIAS_EXTRA_SEXTO_DIGITO` | R-27 | Vencimiento sin días extra. Espera la revisión de Rick (LISTO_FIRMA) | 3 |
| DIOT: tipo de tercero 04 / 05 / 15 | `DIOT_NUM_CAMPOS`, `DIOT_LAYOUT_2025` | R-30, R-32 | El 2B ya usa el orden oficial; falta la captura de proveedores extranjeros y globales (decisión de Rick) | 2B (cierre) |
| Plazo de cancelación | `CFDI_CANCELACION_MES_LIMITE_PM`, `CFDI_CANCELACION_MES_LIMITE_PF` | R-90 | El código de la app aún no lo usa | 3 |
| REP y global | `REP_DIA_LIMITE`, `CFDI_EMISION_HORAS_MAX`, `CFDI_GLOBAL_HORAS_MAX` | R-137, R-03 | Aviso de extemporánea; las 24 h de la global | 3 |
| Recargos y actualización | `RECARGOS_*`, `ACTUALIZACION_FACTOR_DECIMALES` | R-100, R-108 | La serie INPC ya está en la base (`series/inpc.yaml`, oct-2021 a oct-2026, DOF cruzado con Banxico) y R-162 la usa con `serie(id, fecha)`; falta que la app la llame | D |
| Aguinaldo, PTU, separación, IMSS, Infonavit, ISN, LFT | `EXENTO_*`, `SBC_*`, `IMSS_*`, `INFONAVIT_*`, `LFT_*`, `PTU_*`, `ISN_TASA_TABLA` | R-83 a R-134, R-102 | Pasan de `ParametroNomina` a la base. Los 3 recibos demo ya coinciden al centavo | 5 |

## 4. Huecos que van de regreso a esta base

No tienen ID y la app los escribe a mano:

1. **Divisor de 30.4 días** de nómina y estados. Hoy vive dentro de la fórmula de `UMA_MENSUAL` y en el texto de R-128 y R-140. Ya agregado como `DIAS_POR_MES_SM` (30.4, tipo número) en `base/parametros.yaml`, ligado a R-82 con dos casos. Sale publicado con la próxima versión de la base; hasta entonces la app lo sigue escribiendo a mano. No se cambió la fórmula de `UMA_MENSUAL` para no soltar su firma en Timbra. Pendiente de Rick: confirmar que SM = SD × 30.4 es práctica y no artículo.
2. **Calendario de vacaciones del SAT y festivos del CFF 12** (serie). Sin ID.
3. **Retención de plataformas a persona moral.** Sin ID (por confirmar).
4. **`nivel` A/B por regla.** `base/niveles.yaml` aún no existe; la app propone un mapa `cálculo → [R-xx]` y bandas Experimental / Estimación / normal. Decide Rick; CODEOWNERS exige su firma.

## 5. Orden recomendado en factureedp

1. Mezclar el PR 5 (después del respaldo de Railway).
2. **2A cierre:** sustituir las 5 categorías de IVA y retenciones (sección 2, pasos «2A») por `valor(id, fecha)` y dejar el trinquete en el mínimo (hoy 66). El front las recibe de `/api/fiscal/parametros`, no las escribe.
3. **2C:** tipo de cambio, saldo a favor entre años, proporción de IVA.
4. **3:** tarifas y topes del front desde el servidor; pasar el ISR anual completo (R-120).
5. **5:** nómina a la base (parámetros, UMA, SM, subsidio, IMSS).
6. **0.5b / 0.5c:** pantalla Base fiscal, bandas de nivel, `actualizar_reglas.py` y workflow semanal (cuando exista el release v0.4.1 y el token fino).
