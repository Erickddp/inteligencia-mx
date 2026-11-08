# Pólizas tipo y NIF

Las reglas **R-150 a R-157 y R-171** dicen, para cada evento contable, qué se carga y qué se abona. Es criterio contable, no cifra de ley: no tienen firma hasta que la persona que mantiene el repositorio las firme.

## Cómo se usan

- La calculadora recibe los importes del evento (como texto, `Decimal`) y regresa la póliza como texto: `D concepto monto; ...; H concepto monto`. Primero los cargos, luego los abonos, cada grupo por orden alfabético de concepto, montos a dos decimales.
- **La póliza siempre cuadra**: si el debe no es igual al haber, la calculadora falla en lugar de regresar algo descuadrado.
- Los **conceptos** son nombres estables, no números de cuenta. Cada app los apunta a su catálogo (idealmente al código agrupador del SAT, Anexo 24 / RMF [2.8.1.6](../fuentes/rmf/2026/RMF2026/reglas/regla-2-8-1-6.md)).

## Eventos y conceptos

| Regla | Evento | Calculadora | Conceptos |
|---|---|---|---|
| R-150 | CFDI emitido | `poliza_emitido` | `clientes`, `ingreso_gravado`, `ingreso_tasa0`, `ingreso_exento`, `iva_trasladado_no_cobrado`, `isr_retenido_por_clientes`, `iva_retenido_por_clientes` |
| R-151 | Cobro | `poliza_cobro` | `bancos` o `caja`, `clientes`, `iva_trasladado_no_cobrado`, `iva_trasladado_cobrado`, `utilidad_cambiaria`, `perdida_cambiaria` |
| R-152 | CFDI recibido | `poliza_recibido` | `gasto` o `inventario`, `gasto_no_deducible`, `iva_acreditable_pendiente`, `proveedores`, `isr_retenido_por_pagar`, `iva_retenido_por_pagar` |
| R-153 | Pago a proveedor | `poliza_pago` | `proveedores`, `bancos` o `caja`, `iva_acreditable_pendiente`, `iva_acreditable_pagado` |
| R-154 | Nota de crédito emitida | `poliza_nota_credito_emitida` | `devoluciones_y_descuentos`, `iva_trasladado_no_cobrado`, `clientes`, retenciones de R-150 |
| R-156 | Entero de retenciones al SAT | `poliza_entero_retenciones` | `isr_retenido_por_pagar`, `iva_retenido_por_pagar`, `bancos` o `caja` |
| R-157 | Acreditamiento del IVA retenido enterado (mes siguiente) | `poliza_acreditamiento_iva_retenido` | `iva_acreditable_pendiente`, `iva_acreditable_pagado` |
| R-171 | Cobro con tarjeta (la terminal deposita neto) | `poliza_cobro_terminal` | `bancos`, `comisiones_bancarias`, `iva_acreditable_pagado`, `clientes`, `iva_trasladado_no_cobrado`, `iva_trasladado_cobrado` |
| R-155 | Nómina pagada | `poliza_nomina` | `sueldos_y_salarios`, `cuotas_patronales`, `aportaciones_infonavit`, `bancos`, `isr_retenido_por_pagar`, `imss_por_pagar`, `infonavit_por_pagar` |

## Todavía no cubierto

Depreciación en pólizas, determinación y compensación mensual del IVA, provisión del ISR, saldos iniciales, cierre de resultados y el subsidio para el empleo acreditable en la nómina. El IVA retenido ya se separa: al pagar queda pendiente (R-153), se entera (R-156) y se acredita en la declaración siguiente (R-157, LIVA 5 fr. IV).

## Mapa al código agrupador del SAT

Cada concepto de las pólizas apunta a un código del catálogo del SAT (`CONTA_CODIGO_AGRUPADOR`, 1,075 renglones; `CONTA_CONCEPTO_AGRUPADOR`, el mapa). Reglas **R-163** (buscar un código) y **R-164** (de concepto a código). Es sugerencia: cada app puede usar su propio catálogo mientras asocie cada cuenta con el agrupador a nivel de subcuenta (RMF 2.8.1.5).

> **El catálogo cargado es el PDF del SAT de dic-2014**, no el Anexo 24 de la RMF 2026 (no se pudo descargar desde aquí). Está `por_confirmar` y el motor lo marca `arrastrado` hasta cotejarlo con el anexo vigente.

| Concepto | Código | Nombre en el catálogo del SAT |
|---|---|---|
| `caja` | `101.01` | Caja y efectivo |
| `bancos` | `102.01` | Bancos nacionales |
| `clientes` | `105.01` | Clientes nacionales |
| `inventario` | `115.01` | Inventario |
| `isr_retenido_por_clientes` | `113.02` | ISR a favor |
| `iva_retenido_por_clientes` | `113.01` | IVA a favor |
| `iva_acreditable_pagado` | `118.01` | IVA acreditable pagado |
| `iva_acreditable_pendiente` | `119.01` | IVA pendiente de pago |
| `proveedores` | `201.01` | Proveedores nacionales |
| `iva_trasladado_cobrado` | `208.01` | IVA trasladado cobrado |
| `iva_trasladado_no_cobrado` | `209.01` | IVA trasladado no cobrado |
| `cuentas_terceros` | `205.06` | Otros acreedores diversos a corto plazo |
| `isr_retenido_por_pagar` | `216.04` | Impuestos retenidos de ISR por servicios profesionales |
| `isr_retenido_por_pagar` (sueldos) | `216.01` | Impuestos retenidos de ISR por sueldos y salarios |
| `isr_retenido_por_pagar` (arrendamiento) | `216.03` | Impuestos retenidos de ISR por arrendamiento |
| `iva_retenido_por_pagar` | `216.10` | Impuestos retenidos de IVA |
| `imss_por_pagar` | `211.01` | Provisión de IMSS patronal por pagar |
| `infonavit_por_pagar` | `211.03` | Provisión de infonavit por pagar |
| `ingreso_gravado` | `401.01` | Ventas y/o servicios gravados a la tasa general |
| `ingreso_tasa0` | `401.04` | Ventas y/o servicios gravados al 0% |
| `ingreso_exento` | `401.07` | Ventas y/o servicios exentos |
| `devoluciones_y_descuentos` | `402.01` | Devoluciones, descuentos o bonificaciones sobre ventas y/o servicios a la tasa general |
| `costo_de_venta` | `501.01` | Costo de venta |
| `sueldos_y_salarios` | `601.01` | Sueldos y salarios |
| `cuotas_patronales` | `601.26` | Cuotas al IMSS |
| `aportaciones_infonavit` | `601.27` | Aportaciones al infonavit |
| `gasto` | `601.84` | Otros gastos generales |
| `gasto_no_deducible` | `601.83` | Gastos no deducibles (sin requisitos fiscales) |
| `perdida_cambiaria` | `701.01` | Pérdida cambiaria |
| `utilidad_cambiaria` | `702.01` | Utilidad cambiaria |

### Dónde difiere el catálogo de Timbra del del SAT

| Cuenta de Timbra | En el SAT | Qué conviene |
|---|---|---|
| `113.08` IVA retenido por clientes | «Otros impuestos a favor» | Usar `113.01` «IVA a favor» |
| `216.04` ISR retenido por pagar (genérico) | Solo «ISR por servicios profesionales» | `216.01` en nómina, `216.03` en arrendamiento, `216.04` en honorarios |
| `213.01` impuestos por pagar | «IVA por pagar» | ISR por pagar es `213.03`; otros `213.07` |
| `701.01` gastos financieros y pérdida cambiaria | Solo «Pérdida cambiaria» | Intereses `701.04` a `701.09`, comisiones bancarias `701.10` |
| `imss_por_pagar` de R-155 | `211.01` IMSS patronal y `216.11` retenciones a trabajadores | Separar obrero y patronal en una versión próxima |

Los demás códigos de Timbra (`101.01`, `102.01`, `105.01`, `115.01`, `118.01`, `119.01`, `201.01`, `205.06`, `208.01`, `209.01`, `216.10`, `401.01`, `401.04`, `401.07`, `402.01`, `501.01`, `601.01`, `601.74`, `601.83`, `601.84`, `702.01`) coinciden en nombre y significado con el catálogo.

## Las NIF

[`fuentes/nif/indice.yaml`](../fuentes/nif/indice.yaml) lista las NIF como **referencia**: identificador, título, tema y para qué se usan aquí. El texto de las NIF tiene derechos reservados del CINIF y **no se copia**. Todas están marcadas `cotejado: false` hasta que se verifiquen contra la edición vigente. Las reglas las citan con `citas: [{nif: "C-3"}]`.

## Citas estructuradas

Cada regla o parámetro puede traer, además del texto de `fuente`:

```yaml
citas: [{ley: LIVA, articulo: "1-b"}, {ley: RMF, anio: "2026", articulo: "2.8.1.6"}, {nif: "C-3"}]
que_dice: "Una línea en palabras de persona."
correcto_si: "La condición que hace correcta la operación."
```

`ley` y `articulo` usan la misma clave que el índice de `fuentes/leyes/<LEY>/indice.json`; una prueba verifica que cada cita exista. Quien tenga `citas` debe traer también `que_dice` y `correcto_si`.
