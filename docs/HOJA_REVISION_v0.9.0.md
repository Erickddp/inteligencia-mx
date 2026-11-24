# Hoja de revisión · bases v0.8.0 y v0.9.0 (una página)

Marca ☐ al revisar. Contador = valida criterio y práctica; Rick = firma la base (aprobar el PR). Sin firma, todo sigue `por_confirmar` o `CRITERIO` y Timbra lo muestra así.

## Contador: confirmar o corregir el criterio
| ☐ | ID | Qué se decidió | Pregunta concreta |
|---|---|---|---|
| ☐ | R-195 | RESICO PF: la nota sólo resta lo ya cobrado de su factura; PPD sin cobrar no resta; el sobrante se reconcilia en la anual | ¿Es correcto restar en el mes de la nota y no reabrir el mes original? |
| ☐ | R-200 | Por régimen: 601 deduce la nota completa; 612 y 626 PM sólo la parte ya acumulada; 606 y 626 PF restan del cobrado; IVA en proporción a lo ya cobrado o pagado | ¿Aplica la misma lógica de caja al IVA de todos? ¿La nota RECIBIDA en 612 reduce la deducción pagada? ¿606? |
| ☐ | R-200 | Ejercicio anterior: se aplica en el mes y ejercicio de la nota, sin complementaria (salvo 625 e IVA retenido) | ¿Qué se hace con la anual del año anterior ya presentada? |
| ☐ | R-200 | 625: la RMF 12.3.16 (complementaria del mes original) y la 12.3.18 (pagos provisionales) se traslapan | ¿Cuál vía conviene? |
| ☐ | R-201 | Varias facturas: se aplica primero al saldo por cobrar (`saldo_primero`) | ¿Hay práctica distinta? |
| ☐ | R-202 | Retención de 1.25 % revertida: se calcula sobre lo que sí resta y manda sobre lo que traiga la nota | ¿Cómo se refleja en la constancia del cliente y qué pasa si ya enteró? |
| ☐ | R-203 | Nota en moneda extranjera: resta al tipo de cambio del día anterior a la nota (CFF 20) | ¿Y si el cobro se convirtió al tipo de adquisición real? |
| ☐ | R-204 | 01 y 03 restan; 07 no | Cotejar con el catálogo c_TipoRelacion vigente (Anexo 20) |
| ☐ | R-196 a R-199 | Pena del CFF 108 por monto, 113 Bis, plazo de 30 días del 69-B y estimación del impuesto omitido (R-199) | ¿Los 30 días son hábiles y corren desde el DOF o desde la página del SAT? ¿R-199 sirve para advertir al despacho? |
| ☐ | R-182 | Coeficiente de utilidad: redondeo a cuatro decimales | ¿Se redondea o se trunca? (RLISR 10: «hasta el diezmilésimo») |
| ☐ | R-186 | Pago definitivo del 625: cesa si el año anterior rebasó el tope | ¿Lectura de la ley (113-B) o de la RMF 12.3.9? |
| ☐ | R-193 | Cancelación de CFDI de ejercicios anteriores a 2026 | ¿Aplica la ley vigente a la fecha de cancelación? |
| ☐ | R-188 | Dividendos: 10 % sólo de utilidades desde 2014; estímulo 2014-2016 sin modelar | ¿Se modela el estímulo? |

## Rick: firmar (cada línea cae a «firmado» sólo con tu aprobación)
| ☐ | Qué | Estado actual |
|---|---|---|
| ☐ | `CFF_DEFRAUDACION_TOPES` (2,531,920.00 y 3,797,870.00) desde 2026-01-01 | `por_confirmar`: las cantidades son las del texto «actualizada DOF 28-12-2025»; la fecha de inicio se supone |
| ☐ | `CFF_DEFRAUDACION_PENAS`, `CFF_DEFRAUDACION_AJUSTES_PCT`, `CFF_113BIS_PENA`, `CFF_69B_PLAZOS_DIAS` | `por_confirmar`, sin cotejar con el DOF |
| ☐ | `RESICO_PF_TABLA_ANUAL` desde 2027 | `por_confirmar`: falta leer el decreto del 13-nov-2026 sobre el 113-F |
| ☐ | `DONATARIA_PERDIDA_AUTORIZACION_PCT` y revisar `DONATARIA_INGRESOS_NO_RELACIONADOS_PCT` (10 % desde 2014; el párrafo se reformó en 2016) | confirmar contra el DOF |
| ☐ | `LFT_VACACIONES_TABLA` y `CONTA_CONCEPTO_AGRUPADOR` (v0.7.0) | cayeron sus firmas: firmar de nuevo |
| ☐ | `CFDI_EGRESO_TIPO_RELACION` | `por_confirmar`: falta el Anexo 20 |
| ☐ | Aprobar el PR de v0.9.0 | firma de la base; no garantiza el resultado para un caso concreto (AVISO.md) |

Nada de lo anterior está cotejado contra el DOF: no hubo acceso de red a dof.gob.mx, sat.gob.mx ni diputados.gob.mx. Orientación técnica, no asesoría.
