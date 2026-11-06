# Timbra · Base de reglas fiscales · 4 fases

Tres archivos, una sola verdad: `parametros.yaml` (números de ley con vigencia y fuente), `reglas.yaml` (catálogo R-xx, qué parámetros usa cada regla, casos al centavo) y `motor.py` (resuelve por fecha, prueba, mide impacto, simula y exporta). Ninguna regla trae números de ley escritos adentro.

Estados: OK · CORREGIR (investigado, el código debe cambiar) · NUEVA · LISTO_FIRMA (espera tu firma o una prueba real) · CRITERIO (no es ley: lo defines tú con fichas) · REVISAR/FALTA (fases 3 y 4).

## Fase 1 · Base de ley y motor · HECHA
UMA, salarios mínimos, tarifa art. 96 (2023-2025 y 2026) con cuotas fijas, subsidio, RESICO, IVA y retenciones, estímulo frontera con vencimiento, exentos de nómina, factor de integración, recargos, plazo de cancelación. Arrastre para que enero no quede en blanco. Validador de vigencias y tarifas.

## Fase 2 · IVA, CFDI, DIOT, bancos, contabilidad electrónica y pagos tardíos · HECHA (5-nov-2026)
Saldo a favor entre años y devolución (R-14/R-18), REP por fecha de pago (R-10), factura global 24 h (R-03), proporción con exentas y no objeto (R-17), pedimentos (R-19), DIOT de 54 campos con el orden oficial y tipos de tercero (R-30/R-32), tipo de cambio CFF 20 (R-52), depósitos y pagos sin CFDI (R-53), pólizas para Anexo 24 (R-60/R-61/R-64), contabilidad electrónica con relevos (R-101), actualización, recargos y ajuste a pesos (R-100/R-108), sexto dígito (R-27), plazos de CFDI (R-90).
Resultado: 40 casos pasan.
Queda esperando: tu firma (R-15, R-27, R-30, R-90), una carga real de DIOT (pipe final), la serie INPC del INEGI conectada, y tus fichas de criterio (R-40, R-54, R-64).

## Fase 3 · ISR por régimen, anuales y estados financieros · INVESTIGADA, en base v0.4.0 como casos de oro
Matriz régimen × obligación (601, 603, 605, 606, 612, 621, 625, 626 PF/PM): qué declara, cuándo y con qué base. R-20 a R-28 (tablas acumuladas oficiales, 606 con predial y trimestral, coeficiente y PTU/pérdidas, plataformas 2026), R-65, R-70 a R-76, estímulo ISR frontera (R-103), anuales PF/PM (R-104), donatarias (603).

## Fase 4 · Nómina y cambio de ejercicio · INVESTIGADA, en base v0.4.0 (aguinaldo, IMSS, SBC, periodicidades, finiquito, ISN parcial)
IMSS por ramo, prima de riesgo, Infonavit, ISN por estado (R-102), PTU (R-105), ajuste anual, finiquito, póliza de nómina (R-80 a R-87). Carga de 2027 en cuanto salga en DOF: Paquete 2027 (tope RESICO 5 M, IVA opcional 7%), Anexo 8, UMA, salarios mínimos, subsidio y prórroga (o no) de frontera.

## Regla de firma
Números en el YAML; la firma vive en la base de datos amarrada al valor. Si el número cambia, la firma se cae sola.

## v0.4.0 (5-nov-2026)
83 casos pasan. Estado aprobado_congreso_pendiente_dof excluido y avisado. Sin IDs con año; exentos como fórmula. Pendientes en ORDEN_CAMBIO_03.txt.

## v0.4.1 (5-nov-2026)
Cotejo contra el PDF oficial del Anexo 8 RMF 2026 (sat.gob.mx): diaria, semanal, decenal, quincenal, mensual y anual 2026 IGUALES. Cargadas oficiales: acumuladas art. 106 feb-nov, trimestral de arrendamiento, RIF bimestral y anual 2025. R-20 resuelto (febrero 300,000 = 79,540.53). Nueva R-140: las tarifas de 7/10/15 días son la diaria × días. 90 casos pasan.
