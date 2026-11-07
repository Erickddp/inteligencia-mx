# Hallazgos del barrido del DOF · 7-nov-2026

Se leyó el DOF de **todos los días del 13-nov-2021 al 5-nov-2026** (1,819 días, 30,010 notas, ediciones matutina y vespertina) con `scripts/vigia_dof.py`. Sin días faltantes y sin fallos; los 7 días hábiles con pocas notas son feriados.

## Cómo leerlo (y qué NO prueba)

- **Es una búsqueda por título y por el texto de los decretos genéricos.** No es una lectura de todo el DOF. Un decreto cuyo título no nombra la ley ni el tema, y que no es de los que el Vigía lee entero, se le puede escapar.
- **Un «no encontré decreto» es evidencia, no prueba.** Cada hallazgo debe confirmarse con la nota del DOF.
- El DOF no publica leyes consolidadas, solo decretos. Cotejar una ley es comprobar que no haya decretos posteriores a su fecha de reforma.

> **Errata (primer intento, retirada).** La primera versión de este documento se escribió con un lector que leía **una sola edición por día**: la página del DOF muestra por defecto solo la última (el 22-dic-2025 traía 1 nota; la matutina tenía 30). Con eso concluí, mal, que no existía el decreto del subsidio para el empleo 2026 y que no se localizaba la resolución del salario mínimo. **Ambos existen y la base estaba bien.** El lector se corrigió (`lee_dia`), se repitió el barrido y todo lo de abajo sale de la versión corregida. Ese primer intento leyó unas 9,000 notas; el definitivo, 30,010.
>
> Una segunda lección: el decreto del 1-abr-2024 que reformó el art. 79 de la LISR se titula «…en materia de pueblos y comunidades indígenas…» y no nombra la ley. Por eso el Vigía ahora lee el texto de los decretos genéricos.

## 1. Cotejo de la biblioteca de leyes contra el DOF

Para cada ley: la última reforma que declara la Cámara, y los decretos del DOF que la reforman (por título, o por el texto de los decretos genéricos), y si hay alguno **posterior**.

| Ley | Última reforma según la Cámara | Último decreto que la reforma en el DOF | ¿Posteriores? |
|---|---|---|---|
| LISR | 01-abr-2024 | 01-abr-2024 (decreto «pueblos indígenas», art. 79) | No encontrados |
| LIVA | 12-nov-2021 | Ninguno en 2021-11 a 2026-11 | No encontrados |
| CFF | 09-abr-2026 | 09-abr-2026 | No encontrados |
| LSS | 15-ene-2026 | 15-ene-2026 | No encontrados |
| LFT | 14-may-2026 | 14-may-2026 | No encontrados |
| Ley del Infonavit | 21-feb-2025 | 21-feb-2025 | No encontrados |
| LFPIORPI | 16-jul-2025 | 16-jul-2025 | No encontrados |
| LIEPS | 07-nov-2025 | 07-nov-2025 | No encontrados |
| LMV | 14-nov-2025 | 14-nov-2025 | No encontrados |
| LFD | 07-nov-2025 | 07-nov-2025 | No encontrados |
| **Ley Aduanera** | 19-nov-2025 (PDF) | **23-oct-2026** (nota 5802077) | **Sí: el texto de la biblioteca está desactualizado** |

- **Ley Aduanera.** El DOF publicó el 23-oct-2026 un decreto que reforma y adiciona la ley. El PDF de la Cámara se modificó por última vez en enero de 2026 y no lo incluye. El manifiesto de `LA` lleva una advertencia. Esa ley no debe usarse para firmar nada hasta regenerar el texto.
- **Discrepancia índice contra PDF (por revisar).** El índice de la Cámara marca reformas más recientes que el encabezado de los PDF para Ley Aduanera (27-dic-2025), LFD (28-dic-2025), Ley de Ingresos sobre Hidrocarburos (28-dic-2025) y Ley del ISAN (28-dic-2025). En el DOF no encontré decretos de esas leyes en esas fechas, así que no sé si el índice o el PDF van mal.
- Los decretos de **reglamentos** (del Reglamento de la Ley de Ingresos sobre Hidrocarburos, 3-oct-2025; del Reglamento de la LFPIORPI, 27-mar-2026; del Reglamento de la Ley Aduanera, 23-feb-2026) los marqué aparte: no reforman la ley.
- Reglamentos del ISR, del IVA, del CFF y de la LIEPS: la Cámara no trae fecha de reforma confiable en los PDF; no se cotejaron.

Esto **no** es un cotejo artículo por artículo: `cotejado_dof` sigue vacío en todas hasta que una persona lo haga.

## 2. Lista de trabajo de la RMF (lo que publicó el DOF)

- **RMF 2026:** 28-dic-2025, con anexos 1, 4, 5, 6, 8, 15 y 25 el mismo día; anexo 2 el 29-dic; anexos 3, 7, 10, 11, 12, 13, 14, 16 y 29 el 9-ene-2026; anexos 17, 21, 22, 23, 24, 27, 28 y 30 el 13-ene; anexo 18 el 19-ene; anexo 19 el 26-ene.
- **Resolución de facilidades administrativas 2026:** 17-feb-2026.
- **Modificaciones a la RMF 2026 (cuatro, no tres):** primera 9-jul-2026 (anexos 1, 2, 3, 9, 14, 15, 21, 22 y 29 el 17-jul); segunda 1-oct-2026 (con anexo 2); tercera 2-oct-2026 (con anexo 7); **cuarta 30-oct-2026**. La RMF de la biblioteca es la original: faltan estas cuatro.

## 3. Valores de la base verificados contra el DOF

### 3.1 Subsidio para el empleo 2026: la base estaba bien
- Decreto **DOF 31-dic-2025**, edición matutina, nota 5777649. Verificado contra su texto: **15.02 %** de la UMA mensual, **15.59 %** en enero de 2026 (sobre la UMA de 2025), límite **$11,492.66**, y los $536.22 del considerando. La base coincide tal cual; no se cambió ningún valor.
- Decretos anteriores, por referencia: 1-may-2024 (11.82 %); 31-dic-2024 (13.8 %, 14.39 % en enero de 2025, límite $10,171.00).
- Sigue pendiente (no es de este decreto): la base no tiene tramos de 2025 para el subsidio.

### 3.2 Salario mínimo 2025 y 2026: la base estaba bien
- Resolución del H. Consejo de Representantes de CONASAMI, **DOF 19-dic-2024** (nota 5745678): **278.80** (zona general) y **419.88** (frontera norte) para 2025.
- Resolución del 3-dic-2025, **DOF 9-dic-2025** (nota 5775534): **315.04** (zona general, +13.0 %) y **440.87** (frontera norte, +5.0 %) para 2026.
- Se precisaron las cuatro citas de la base; los valores no cambian.

### 3.3 Lo que sí cuadra por fecha
- UMA 2026: DOF 9-ene-2026 (la nota existe; no leí su texto). UMA 2025: el DOF del 10-ene-2025 tiene notas relacionadas.
- RMF 2026 y Anexo 8: DOF 28-dic-2025. Anexo 8 de 2025: DOF 30-dic-2024.
- CFF (cancelación, plazo): DOF 7-nov-2025. LFT vacaciones: DOF 27-dic-2022. LFT jornada: DOF 1-may-2026.
- Estímulos de frontera: DOF 31-dic-2025.

## 4. INPC

- `series/inpc.yaml`: oct-2021 a sep-2026 (60 meses). **Los 60 meses salen de notas del DOF y coinciden con Banxico (SP1) sin una sola diferencia**, y el DOF no se contradice entre notas.
- Con la primera lectura faltaban 11 meses; eran notas de la edición que no se leía.
- Antes de oct-2021 no se barrió el DOF.

## 5. RMF 2026: citas de la base verificadas contra el texto

| Regla | La base dice | El texto del DOF |
|---|---|---|
| 2.7.1.21 | CFDI global dentro de 24 horas | Confirmado: «a más tardar dentro de las 24 horas siguientes al cierre de las operaciones» |
| 2.7.1.32 | REP a más tardar el día 5 del mes siguiente | Confirmado: «quinto día natural del mes inmediato siguiente» |
| 2.8.1.6 | Contabilidad electrónica: día 3 (PM) y día 5 (PF) del segundo mes | Confirmado |
| 2.8.1.7 | Balanza ajustada: 20 de abril (PM), 22 de mayo (PF) | **Cita equivocada.** La 2.8.1.7 trata de información de usuarios (telefonía, energía, casas de bolsa). Las fechas están en la **2.8.1.6, fracción II**. Se corrigió la cita; los valores no cambian |
| 2.8.1.17 | Relevo para PF con ingresos hasta 4 millones | Confirmado: «$4'000,000.00»; releva de contabilidad electrónica y DIOT |
| 3.13.x | RESICO PM relevado de contabilidad electrónica | Sigue «por confirmar» en la base |

Las cuatro modificaciones a la RMF 2026 (sección 2) aún no están en la biblioteca: una regla citada arriba pudo cambiar después.

## 6. IMSS e Infonavit: parámetros cotejados contra la ley y el DOF

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

**Chihuahua (ISN, otros gravámenes estatales y Código Fiscal del Estado): sin hacer.** Los sitios del Congreso, del gobierno y del Periódico Oficial de Chihuahua no responden desde el entorno de trabajo (solo están permitidos los de leyes federales, DOF, SAT, IMSS e Infonavit). Hace falta abrir esos hosts.
