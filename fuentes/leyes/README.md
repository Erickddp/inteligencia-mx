# Biblioteca de leyes

Texto de ley, **un artículo por archivo**, para que cada regla de `base/` cite un artículo que se pueda abrir.

| Ley | Clave | Última reforma según el PDF de la Cámara | Artículos |
|---|---|---|---|
| Ley del Impuesto sobre la Renta | `LISR` | 01-abr-2024 | 236 |
| Ley del Impuesto al Valor Agregado | `LIVA` | 12-nov-2021 | 80 |
| Ley del Seguro Social | `LSS` | 15-ene-2026 | 385 |
| Ley del Infonavit | `LINFONAVIT` | 21-feb-2025 | 95 |
| Ley antilavado (LFPIORPI) | `LFPIORPI` | 16-jul-2025 | 73 |

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

1. **Orientación hasta cotejar con el DOF.** El texto es el de la Cámara de Diputados, que puede ir atrás del DOF. Hoy su índice marca la LISR en 2024 y la LIVA en 2021, y la base ya cita reformas posteriores (paquete económico 2026): **esos artículos hay que cotejarlos contra el decreto publicado** antes de firmar.
2. **Las tablas se aplanan.** La tarifa del art. 96 o las tablas del art. 113-E salen como texto corrido. Los números de tarifa viven en `base/parametros.yaml` (cotejados con el Anexo 8), no aquí.
3. Falta el Código Fiscal de la Federación, la LFT, la LIEPS, los reglamentos (RLISR, RLIVA), la RMF con sus anexos y la LIF. La base ya cita CFF y LFT 14 veces cada una: son lo siguiente.
4. Los encabezados se reconocen por forma. Si la Cámara cambia el formato del PDF, `extraer_ley.py` falla en vez de guardar basura (mínimo 20 artículos).
