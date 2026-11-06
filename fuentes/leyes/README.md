# Biblioteca de leyes

Texto de ley, **un artículo por archivo**, para que cada regla de `base/` cite un artículo que se pueda abrir.

| Ley | Clave | Última reforma según el PDF de la Cámara | Artículos |
|---|---|---|---|
| Ley del Impuesto sobre la Renta | `LISR` | 01-abr-2024 | 236 |
| Ley del Impuesto al Valor Agregado | `LIVA` | 12-nov-2021 | 80 |
| Ley del Seguro Social | `LSS` | 15-ene-2026 | 385 |
| Ley del Infonavit | `LINFONAVIT` | 21-feb-2025 | 95 |
| Ley antilavado (LFPIORPI) | `LFPIORPI` | 16-jul-2025 | 73 |
| Ley Federal del Trabajo | `LFT` | 14-may-2026 | 1,266 |
| Código Fiscal de la Federación | `CFF` | 09-abr-2026 | 421 |
| Reglamento de la LISR | `RLISR` | 06-may-2016 | 313 |
| Reglamento de la LIVA | `RLIVA` | 25-sep-2014 | 84 |

## Cómo está guardado y por qué

- `fuentes/leyes/<CLAVE>/articulos/art-0106.md`, `art-0001-a.md`, `art-0018-h-bis.md`. Un cambio de ley aparece en git como el artículo que cambió.
- `indice.json`: artículo → archivo, SHA256 de su texto, ubicación (título, capítulo, sección) y si está derogado.
- `manifiesto.json`: URL oficial, fecha de descarga, SHA256 del PDF y del texto, última reforma que dice el PDF.
- `transitorios.md`: los de la ley y los de los decretos de reforma.
- **Los PDF no entran al repo**: se guarda su URL y su huella. Son unos 5 MB de texto en total; un repo aparte no hace falta.
- Es público: la ley no tiene dueño ([LICENCIAS.md](../../LICENCIAS.md)). Un repo privado solo serviría para criterios propios del despacho.

## Cómo se regenera

```bash
python scripts/extraer_ley.py --todas        # requiere pdftotext (poppler-utils)
python scripts/citas_fuentes.py --detalle    # cruza las citas de la base contra la biblioteca
python -m pytest tests/test_biblioteca.py
```

## Límites que hay que saber

1. **Orientación hasta cotejar con el DOF.** Cada artículo trae «Cotejado con el DOF: NO» hasta que una persona lo cotee (campo `cotejado_dof` del manifiesto, que regenerar no borra), y `citas_fuentes.py` lista los parámetros que citan artículos sin cotejar: esos no se firman. El texto es el de la Cámara de Diputados, que puede ir atrás del DOF. Hoy su índice marca la LISR en 2024 y la LIVA en 2021, y la base ya cita reformas posteriores (paquete económico 2026): **esos artículos hay que cotejarlos contra el decreto publicado** antes de firmar.
2. **Las tablas se aplanan.** La tarifa del art. 96 o las tablas del art. 113-E salen como texto corrido. Los números de tarifa viven en `base/parametros.yaml` (cotejados con el Anexo 8), no aquí.
3. Falta la RMF con sus Anexos (se guarda por año y por resolución de modificación: `fuentes/rmf/2026/…`, con los anexos aparte), la LIEPS y la LIF.
4. Los encabezados se reconocen por forma. Si la Cámara cambia el formato del PDF, `extraer_ley.py` falla en vez de guardar basura (mínimo 20 artículos).

## Cómo entra una reforma

Una reforma no se sobrescribe en silencio: cada decreto entra en **su propio PR**, con el decreto (URL del DOF y fecha), el texto regenerado y la actualización de `cotejado_dof`. El historial de git guarda el texto anterior, así que se puede saber qué texto estaba vigente en una fecha.
