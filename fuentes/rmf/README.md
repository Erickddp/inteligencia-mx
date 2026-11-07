# Biblioteca de la RMF

Resolución Miscelánea Fiscal, **una regla por archivo**, con el mismo formato que `fuentes/leyes/` (`manifiesto.json`, `indice.json`, `cotejado_dof`).

| Carpeta | Qué es | Reglas | DOF |
|---|---|---|---|
| `2026/RMF2026/` | Resolución Miscelánea Fiscal para 2026 | 1,208 (82 de 2 niveles, 849 de 3, 258 de 4 y 19 de 5) | 28-dic-2025, nota 5777217 |

## Cómo está guardado
- `reglas/regla-2-7-1-21.md`: título de la regla, ubicación (título, capítulo, sección, subsección), **fundamento** (CFF 29-A, RMF 2.7.1.21…) y el texto.
- `indice.json`: regla → archivo, SHA256, ubicación, título, fundamento.
- `preambulo.md` (considerandos) y `transitorios.md`.
- El Word del DOF **no** entra al repo: su URL y su huella van en el manifiesto. Para regenerar: `python scripts/extraer_rmf.py RMF2026` (requiere LibreOffice).

## Límites que hay que saber
1. **El texto sale del DOF pero nadie lo ha revisado**: `cotejado_dof` está vacío y cada regla dice «Cotejado con el DOF: NO». La extracción se probó (sin huecos de numeración, sin encabezados colados), pero una persona debe revisar las reglas que respaldan parámetros antes de firmarlos.
2. **Los anexos no están.** El Anexo 8 (tarifas) y los demás van en otras notas del DOF y son tablas; sus cifras viven en `base/parametros.yaml`, cotejadas contra el PDF del SAT. Las tablas del Word se aplanan.
3. **Las modificaciones no están todavía**: primera (9-jul-2026), segunda (1-oct-2026) y tercera (2-oct-2026). Cada una entra en su carpeta (`RMF2026-M1/`…) con solo las reglas que toca, en su propio PR. Mientras tanto, la RMF 2026 puede estar desactualizada en esas reglas.
4. El fundamento (última línea de cada regla) se detecta por forma; en 7 reglas no se separó y queda dentro del texto.

## Verificación de las citas de la base
`python scripts/citas_fuentes.py` cruza «RMF 2026 regla N» de la base contra este índice. Al cargarla se encontró una cita equivocada (2.8.1.7 en lugar de 2.8.1.6, fracción II) y se corrigió; el valor no cambió.
