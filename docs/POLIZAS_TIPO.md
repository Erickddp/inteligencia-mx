# Pólizas tipo y NIF

Las reglas **R-150 a R-155** dicen, para cada evento contable, qué se carga y qué se abona. Es criterio contable, no cifra de ley: no tienen firma hasta que la persona que mantiene el repositorio las firme.

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
| R-155 | Nómina pagada | `poliza_nomina` | `sueldos_y_salarios`, `cuotas_patronales`, `aportaciones_infonavit`, `bancos`, `isr_retenido_por_pagar`, `imss_por_pagar`, `infonavit_por_pagar` |

## Todavía no cubierto

Depreciación en pólizas, determinación y compensación mensual del IVA, provisión del ISR, saldos iniciales, cierre de resultados, subsidio para el empleo acreditable en la nómina y el IVA retenido que solo se acredita al enterarlo (LIVA 5 fr. IV).

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
