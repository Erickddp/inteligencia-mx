# Hallazgos del barrido del DOF · 7-nov-2026

> **ERRATA (7-nov-2026, noche).** La primera versión de este documento se escribió con un lector del DOF que leía **una sola edición por día**: la página del DOF muestra por defecto solo la última (el 22-dic-2025 traía 1 nota; la matutina tenía 30). Por eso concluí, mal, que no había decreto del subsidio para el empleo 2026. **Sí existe** (DOF 31-dic-2025, nota 5777649) y trae exactamente los valores de la base. Todas las conclusiones del tipo «no encontré decreto» de este documento quedan **en revisión** hasta repetir el barrido con las dos ediciones (en curso). El lector ya está corregido (`lee_dia`).


Se leyó el índice del DOF de todos los días del 13-nov-2021 al 5-nov-2026 (unos 1,800) con `scripts/vigia_dof.py`. Un día falló el primer intento (6-may-2025: respuesta incompleta del servidor) y se repasó a mano: 21 notas, ninguna relevante.

**Qué es y qué no es.** Busca por **título y organismo**. Si un decreto trae un título que no dice la ley ni el tema, se le puede escapar (le pasó con las resoluciones de CONASAMI; ya se corrigió). Sirve para decir «no encontré decreto» con cautela, no para afirmar que no existe. Cada hallazgo debe confirmarse con la nota del DOF.

## 1. Cotejo de la biblioteca de leyes contra el DOF  *(EN REVISIÓN: repetir con las dos ediciones)*

La Cámara de Diputados marca una «última reforma» por ley. Esto es lo que el DOF muestra **después** de esa fecha:

| Ley | Última reforma según la Cámara | Decretos que la reforman, publicados después | Conclusión |
|---|---|---|---|
| LISR | 01-abr-2024 | Ninguno encontrado (2-abr-2024 a 5-nov-2026) | El texto parece vigente. Los cambios del paquete 2026 que la base marca «aprobado, sin DOF» siguen sin publicarse |
| LIVA | 12-nov-2021 | Ninguno encontrado (13-nov-2021 a 5-nov-2026) | Igual |
| CFF | 09-abr-2026 | Ninguno después. Antes de esa fecha: 16-oct-2025 (con Ley de Amparo), 7-nov-2025 y 9-abr-2026 | Al día |
| LSS | 15-ene-2026 | Ninguno después | Al día |
| LFT | 14-may-2026 | Ninguno después (1-may-2026: jornada de 40 horas; 14-may-2026) | Al día |
| Ley del Infonavit | 21-feb-2025 | Ninguno encontrado | El texto parece vigente |
| LFPIORPI | 16-jul-2025 | Ninguno después | Al día |
| RLISR / RLIVA | 06-may-2016 / 25-sep-2014 | No se barrió antes de nov-2021 | Sin cotejar |

Esto **no** cotea artículo por artículo: dice que no se encontró un decreto posterior a la fecha de la Cámara. Hasta que una persona lo confirme en el DOF, `cotejado_dof` sigue en «NO».

**Faltan en la biblioteca** (el DOF muestra cambios recientes): Ley del IEPS (reforma 7-nov-2025), Reglamento de la LFPIORPI (reforma 27-mar-2026), y la RMF 2026 con sus modificaciones y anexos.

## 2. Lista de trabajo de la RMF (de lo que publicó el DOF)

- RMF 2026: 28-dic-2025, con los anexos 1, 4, 5, 6, 8, 15 y 25 el mismo día; anexo 2 el 29-dic; anexos 3, 7, 10, 11, 12, 13, 14, 16 y 29 el 9-ene-2026; anexo 18 el 19-ene; anexo 19 el 26-ene.
- Resolución de facilidades administrativas 2026: 17-feb-2026.
- Modificaciones a la RMF 2026: primera 9-jul-2026; segunda 1-oct-2026 (con anexo 2); tercera 2-oct-2026 (con anexo 7).
- RMF 2025 (por si hay actos que cotejar): publicada 30-dic-2024, seis modificaciones.

## 3. Hallazgos que cambian la base

### 3.1 Subsidio para el empleo 2026: la base estaba bien
- **Retractación.** La versión anterior de este documento decía que el decreto del 31-dic-2025 no aparecía en el DOF. Era un error del lector (una edición por día). El decreto existe: DOF 31-dic-2025, edición matutina, nota 5777649.
- Verificado contra su texto: **15.02 % de la UMA mensual**, **15.59 % en enero de 2026** (sobre la UMA de 2025), límite de ingresos **$11,492.66**, y los $536.22 del considerando. La base coincide tal cual; no se cambió ningún valor y se quitó la marca `por_confirmar` que le había puesto.
- Decretos anteriores, por referencia: 1-may-2024 (11.82 %); 31-dic-2024 (13.8 %, 14.39 % en enero de 2025, límite $10,171.00).
- Sigue pendiente (no es de este decreto): la base no tiene tramos de 2025 para el subsidio.

### 3.2 Salario mínimo 2025 y 2026: la fecha de DOF no se localizó  *(EN REVISIÓN: pudo estar en la otra edición)*
- La base cita «CONASAMI, DOF dic-2024» (278.80) y 2026 (315.04). La nota de CONASAMI del 9-feb-2026 confirma que existe una resolución del 3-dic-2025, pero **no encontré su publicación** en el DOF de diciembre de 2024, ni de diciembre de 2025 a enero de 2026, ni por título ni por organismo.
- Las cifras (278.80 y 315.04, +13 %) son coherentes con lo conocido, así que **no se tocaron**; falta la nota del DOF que las respalde. Debe buscarse a mano.

### 3.3 Lo que sí cuadra
- UMA 2026: DOF 9-ene-2026 («Unidad de medida y actualización»; la nota existe, no leí su texto). UMA 2025: el DOF del 10-ene-2025 tiene notas relacionadas; no leí su texto.
- RMF 2026 y Anexo 8: el DOF del 28-dic-2025 los trae por título. Anexo 8 de 2025: DOF 30-dic-2024 (por título; no cotejé los números aquí, eso ya lo hizo el cotejo contra el PDF del SAT).
- CFF (cancelación, plazo): DOF 7-nov-2025. LFT vacaciones: DOF 27-dic-2022. LFT jornada: DOF 1-may-2026 y reforma constitucional 3-mar-2026.
- Estímulos de frontera: DOF 31-dic-2025 (decreto que modifica los de la región fronteriza norte).

## 4. INPC  *(EN REVISIÓN: los 11 meses faltantes pudieron estar en la otra edición)*

- `series/inpc.yaml`: oct-2021 a sep-2026 (60 meses). **49 meses salen de notas del DOF y coinciden con Banxico (SP1) sin una sola diferencia**; el DOF no se contradice entre notas.
- **11 meses no se localizaron en el DOF** (2022-07, 2023-04, 2023-07, 2023-12, 2024-01, 2024-10, 2024-11, 2025-01, 2025-06, 2025-09, 2026-05). Entran con el valor de Banxico marcados `cotejado_dof: false`: no se usan para recargos ni se firman hasta cotejarlos.
- Antes de oct-2021 no se barrió el DOF.

## 5. RMF 2026: citas de la base verificadas contra el texto

Con la RMF 2026 en `fuentes/rmf/` (1,208 reglas) se comprobaron las seis reglas que cita la base:

| Regla | La base dice | El texto del DOF |
|---|---|---|
| 2.7.1.21 | CFDI global dentro de 24 horas | Confirmado: «a más tardar dentro de las 24 horas siguientes al cierre de las operaciones» |
| 2.7.1.32 | REP a más tardar el día 5 del mes siguiente | Confirmado: «quinto día natural del mes inmediato siguiente» |
| 2.8.1.6 | Contabilidad electrónica: día 3 (PM) y día 5 (PF) del segundo mes | Confirmado |
| 2.8.1.7 | Balanza ajustada: 20 de abril (PM), 22 de mayo (PF) | **Cita equivocada.** La 2.8.1.7 trata de información de usuarios (telefonía, energía, casas de bolsa). Las fechas están en la **2.8.1.6, fracción II**. Se corrigió la cita; los valores no cambian |
| 2.8.1.17 | Relevo para PF con ingresos hasta 4 millones | Confirmado: «$4'000,000.00»; releva de contabilidad electrónica y DIOT |
| 3.13.x | RESICO PM relevado de contabilidad electrónica | Sigue «por confirmar» en la base |

Faltan las tres modificaciones a la RMF 2026 (9-jul, 1-oct y 2-oct de 2026): una regla citada arriba pudo cambiar después.

## 6. IMSS e Infonavit: parámetros cotejados contra la ley y el DOF (7-nov-2026)

Cotejo contra el texto de la LSS y de la Ley del Infonavit de `fuentes/leyes/` y contra los decretos del DOF. **Ningún valor cambia.**

| Parámetro | Valor en la base | Respaldo | Resultado |
|---|---|---|---|
| `IMSS_EYM_CUOTA_FIJA_PATRON` | 20.40 % de la UMA | LSS 106 fr. I dice 13.9 %; el transitorio décimo noveno (DOF 21-dic-1995) suma 0.65 puntos cada 1-jul de 1998 a 2007: 13.9 + 6.5 = 20.40 | ✔ por aritmética del transitorio |
| `IMSS_EYM_EXCEDENTE_PATRON` / `_OBRERO` | 1.10 % / 0.40 % sobre el excedente de 3 UMA | LSS 106 fr. II dice 6 % y 2 %; el mismo transitorio resta 0.49 y 0.16 puntos por año: 6 − 4.9 y 2 − 1.6 | ✔ |
| `IMSS_PD_PATRON` / `_OBRERO` | 0.70 % / 0.25 % | LSS 107: cuota de 1 %; 70 % patrones, 25 % trabajadores | ✔ |
| `IMSS_GMP_PATRON` / `_OBRERO` | 1.05 % / 0.375 % | LSS 25 | ✔ |
| `IMSS_IV_PATRON` / `_OBRERO` | 1.75 % / 0.625 % | LSS 147 | ✔ |
| `IMSS_GUARDERIAS_PATRON` | 1 % | LSS 211 | ✔ |
| `IMSS_RETIRO_PATRON`, `IMSS_CEAV_OBRERO` | 2 %, 1.125 % | LSS 168 | ✔ |
| `IMSS_CEAV_PATRON_TABLA` 2026 y 2027 | 8 renglones por año | Tabla del transitorio segundo del decreto DOF 16-dic-2020. **Es una imagen**: ni la Cámara ni el HTML ni el Word la traen como texto. Se leyó la imagen celda por celda | ✔ las dos columnas coinciden en sus 16 cifras |
| `PRIMA_RIESGO_INICIAL_POR_CLASE`, `_MINIMA`, `_MAXIMA` | 0.54355 … 7.58875; 0.5; 15 | LSS 73 y 74 | ✔ |
| `SBC_TOPE_VECES_UMA` | 25 | LSS 28 dice «veinticinco veces el salario mínimo» | ✔ con el decreto DOF 27-ene-2016, transitorio tercero (las menciones al salario mínimo como referencia se entienden hechas a la UMA) |
| `INFONAVIT_APORTACION_PATRON` | 5 % | Ley del Infonavit 29 fr. II | ✔ |
| `DIAS_POR_MES_SM` | 30.4 | Decreto DOF 27-ene-2016, transitorio segundo: valor mensual de la UMA = diario × 30.4 | ✔ fuente primaria (se corrigió la cita y el inicio de vigencia a 28-ene-2016) |

Se precisaron las citas de esos parámetros. Ninguno estaba `por_confirmar`, así que no hubo nada que pasar a vigente. Los textos de ley siguen sin cotejo humano contra el DOF.

**Chihuahua (ISN, otros gravámenes estatales y Código Fiscal del Estado): sin hacer.** Los sitios del Congreso, del gobierno y del Periódico Oficial de Chihuahua no responden desde el entorno de trabajo (solo están permitidos los de leyes federales, DOF, SAT, IMSS e Infonavit). Hace falta abrir esos hosts.
