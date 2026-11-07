# Hallazgos del barrido del DOF · 7-nov-2026

Se leyó el índice del DOF de todos los días del 13-nov-2021 al 5-nov-2026 (unos 1,800) con `scripts/vigia_dof.py`. Un día falló el primer intento (6-may-2025: respuesta incompleta del servidor) y se repasó a mano: 21 notas, ninguna relevante.

**Qué es y qué no es.** Busca por **título y organismo**. Si un decreto trae un título que no dice la ley ni el tema, se le puede escapar (le pasó con las resoluciones de CONASAMI; ya se corrigió). Sirve para decir «no encontré decreto» con cautela, no para afirmar que no existe. Cada hallazgo debe confirmarse con la nota del DOF.

## 1. Cotejo de la biblioteca de leyes contra el DOF

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

### 3.1 Subsidio para el empleo 2026: la fuente que cita la base no aparece en el DOF
- La base cita un «Decreto que modifica el subsidio para el empleo, DOF 31-dic-2025» con 15.59 % (enero), 15.02 % (feb-dic) y límite $11,492.66.
- En el DOF del 30 y 31-dic-2025 (47 notas leídas una por una) **no hay decreto de subsidio**. En todo el periodo solo hay dos: el del 1-may-2024 (11.82 %) y el del **31-dic-2024** (nota 5746529).
- El decreto del 31-dic-2024, vigente desde el 1-ene-2025, dice: **13.8 % de la UMA mensual** (14.39 % solo en enero de 2025) y límite **$10,171.00**. Su texto no ordena ajuste automático del límite.
- Si no existe un decreto posterior, 2026 sería 13.8 % × UMA mensual (feb-dic: 3,566.22 × 13.8 % = **492.14**, no 535.65) y límite $10,171.00 (no $11,492.66).
- El número $11,492.66 se parece a 10,171 × 315.04 / 278.80 = 11,493.08 (no es idéntico); parece un ajuste por el salario mínimo que el decreto no ordena.
- **Qué se hizo:** los tres tramos de 2026 quedaron en `por_confirmar` con la alerta en `nota` (los valores no se tocaron; los casos siguen pasando). No se cambian valores sin tu decisión y firma.
- **Impacto:** la nómina de Timbra calcula el subsidio con estos valores. Si el decreto de 2025 es el vigente, el subsidio está sobrestimado y el ISR retenido subestimado.
- **Falta:** confirmar con el DOF o con el SAT si hubo un decreto posterior que mi búsqueda no halló. Tampoco hay tramos de 2025 en la base (13.8 % / 14.39 % enero / $10,171.00).

### 3.2 Salario mínimo 2025 y 2026: la fecha de DOF no se localizó
- La base cita «CONASAMI, DOF dic-2024» (278.80) y 2026 (315.04). La nota de CONASAMI del 9-feb-2026 confirma que existe una resolución del 3-dic-2025, pero **no encontré su publicación** en el DOF de diciembre de 2024, ni de diciembre de 2025 a enero de 2026, ni por título ni por organismo.
- Las cifras (278.80 y 315.04, +13 %) son coherentes con lo conocido, así que **no se tocaron**; falta la nota del DOF que las respalde. Debe buscarse a mano.

### 3.3 Lo que sí cuadra
- UMA 2026: DOF 9-ene-2026 («Unidad de medida y actualización»; la nota existe, no leí su texto). UMA 2025: el DOF del 10-ene-2025 tiene notas relacionadas; no leí su texto.
- RMF 2026 y Anexo 8: el DOF del 28-dic-2025 los trae por título. Anexo 8 de 2025: DOF 30-dic-2024 (por título; no cotejé los números aquí, eso ya lo hizo el cotejo contra el PDF del SAT).
- CFF (cancelación, plazo): DOF 7-nov-2025. LFT vacaciones: DOF 27-dic-2022. LFT jornada: DOF 1-may-2026 y reforma constitucional 3-mar-2026.
- Estímulos de frontera: DOF 31-dic-2025 (decreto que modifica los de la región fronteriza norte).

## 4. INPC

- `series/inpc.yaml`: oct-2021 a sep-2026 (60 meses). **49 meses salen de notas del DOF y coinciden con Banxico (SP1) sin una sola diferencia**; el DOF no se contradice entre notas.
- **11 meses no se localizaron en el DOF** (2022-07, 2023-04, 2023-07, 2023-12, 2024-01, 2024-10, 2024-11, 2025-01, 2025-06, 2025-09, 2026-05). Entran con el valor de Banxico marcados `cotejado_dof: false`: no se usan para recargos ni se firman hasta cotejarlos.
- Antes de oct-2021 no se barrió el DOF.
