# Prompt para la sesión de factureedp

Pégalo tal cual en la sesión que ya trabaja en `Erickddp/factureedp` (rama del PR 5).

```text
Continúa el puente con timbra-reglas. Estado: Paso 0.5a, 2A y 2B listos en el PR 5 (CI verde en 4007a2e). Lee primero docs/MATRIZ_APP_BASE.md del repo timbra-reglas (rama claude/happy-hamilton-921w2o): ahí está, número por número, el ID de la base que le toca a cada cifra escrita a mano en Timbra.

Reglas que no cambian:
- La base se vendoriza y se verifica por huella. No se edita app/reglas/ dentro de Timbra. Si falta un ID, se pide a timbra-reglas (sección 4 de la matriz); no se inventa aquí.
- Un número de ley se pide por FECHA con valor(id, fecha), nunca por año. Sin valor vigente: avisa, no inventa.
- El timbrado no depende de la base. El trinquete numeros_de_ley.json solo baja, nunca sube.
- Cada arreglo lleva su prueba, y debe fallar con el código anterior.
- No mezcles PRs ni apruebes: eso lo hace Rick, y solo después del respaldo de Railway.

Orden de trabajo:
1. 2A cierre. Sustituye por valor(id, fecha) las apariciones de IVA 16 %, IVA 8 %, retención de IVA 2/3, 4 % / 6 % y retención RESICO 1.25 % (IDs en la sección 2 de la matriz). El front recibe los valores de /api/fiscal/parametros; no los escribe. Baja el trinquete con cada archivo que limpies.
2. 2C. (a) Tipo de cambio: TIPO_CAMBIO_REGLA y BANXICO_SERIE_TC_CFF20 (R-52, R-138), fecha de causación menos un día, en tipo_cambio.py. La serie nueva se confirma con el token de Banxico antes de cambiar el código; si no hay token, deja el cambio detrás de una bandera y dilo. (b) Saldo a favor de IVA entre años (R-13, R-14, R-18): que no muera en diciembre. (c) Proporción de IVA con exentas y no objeto (R-17): R-17 tiene un solo caso, no la marques como firmada.
3. Paso 3. Tarifas y topes del front (fiscal.ts) desde el servidor: ISR_TARIFA_MENSUAL y las de cada periodo, RESICO_PF_TOPE_ANUAL, RESICO_PM_TOPE_ANUAL, ARREND_DEDUCCION_CIEGA_PCT, ISR_PM_TASA, AUTO_TOPE_DEDUCCION.
4. Paso 5. Nómina a la base: UMA, SM_GENERAL_DIARIO, SM_ZLFN_DIARIO, SUBSIDIO_EMPLEO_*, PRIMA_RIESGO_*, IMSS_*, EXENTO_*. El 30.4 sigue a mano hasta que exista DIAS_POR_MES_SM en una versión publicada.

Pendientes de Rick (no los hagas tú): publicar el release v0.4.1 de timbra-reglas, decidir dónde va la captura de proveedores extranjeros y globales de la DIOT, decidir dónde vive el nivel A/B, crear el token fino para el workflow semanal.

Al terminar cada paso: suite completa en SQLite y Postgres, trinquete actualizado, y un resumen corto con qué IDs quedaron conectados y cuáles siguen a mano. Habla en español mexicano, directo y breve.
```
