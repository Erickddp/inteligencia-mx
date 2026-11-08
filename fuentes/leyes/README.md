# Biblioteca de leyes

Texto de ley, **un artículo por archivo**, para que cada regla de `base/` cite un artículo que se pueda abrir.

| Ley | Clave | Última reforma según el PDF de la Cámara | Artículos |
|---|---|---|---|
| Código Fiscal de la Federación | `CFF` | 2026-04-09 | 421 |
| Ley Aduanera | `LA` | 2025-11-19 | 277 |
| Ley de Coordinación Fiscal | `LCF` | 2024-01-03 | 67 |
| Ley Federal de Derechos | `LFD` | 2025-11-07 | 699 |
| Ley Federal del Impuesto sobre Automóviles Nuevos | `LFISAN` | 2021-11-12 | 14 |
| Ley Federal para la Prevención e Identificación de Operaciones con Recursos de Procedencia Ilícita | `LFPIORPI` | 2025-07-16 | 73 |
| Ley Federal del Trabajo | `LFT` | 2026-05-14 | 1,266 |
| Ley del Impuesto Especial sobre Producción y Servicios | `LIEPS` | 2025-11-07 | 69 |
| Ley de Ingresos de la Federación para el Ejercicio Fiscal de 2026 | `LIF2026` | sin dato | 34 |
| Ley del Instituto del Fondo Nacional de la Vivienda para los Trabajadores | `LINFONAVIT` | 2025-02-21 | 95 |
| Ley de Ingresos sobre Hidrocarburos | `LISH` | 2025-03-18 | 64 |
| Ley del Impuesto sobre la Renta | `LISR` | 2024-04-01 | 236 |
| Ley del Impuesto al Valor Agregado | `LIVA` | 2021-11-12 | 80 |
| Ley del Mercado de Valores | `LMV` | 2025-11-14 | 463 |
| Ley del Seguro Social | `LSS` | 2026-01-15 | 385 |
| Reglamento del Código Fiscal de la Federación | `RCFF` | sin dato | 113 |
| Reglamento de la Ley Federal para la Prevención e Identificación de Operaciones con Recursos de Procedencia Ilícita | `RLFPIORPI` | 2026-03-27 | 70 |
| Reglamento de la Ley del Impuesto Especial sobre Producción y Servicios | `RLIEPS` | sin dato | 19 |
| Reglamento de la Ley del Impuesto sobre la Renta | `RLISR` | 2016-05-06 | 313 |
| Reglamento de la Ley del Impuesto al Valor Agregado | `RLIVA` | 2014-09-25 | 84 |

## Leyes estatales y municipales

Se registran con la clave `<ENTIDAD>-<SIGLAS>` (clave ISO de la entidad: `CMX` es la Ciudad de México) y su ámbito, entidad y materia en el manifiesto. Estándar: [docs/ESTANDAR_APORTACION.md](../../docs/ESTANDAR_APORTACION.md). Fuente: portal de la Consejería Jurídica y de Servicios Legales de la CDMX (data.consejeria.cdmx.gob.mx); el texto **no está cotejado** con la Gaceta Oficial.

| Ley | Clave | Materia | Última reforma según el PDF | Artículos |
|---|---|---|---|---|
| Código Civil para el Distrito Federal | `CMX-CC` | civil | 2026-08-20 | 3,194 |
| Código de Ética de la Administración Pública y Alcaldías de la Ciudad de México | `CMX-CEAP` | administrativo | sin dato | 24 |
| Código Fiscal de la Ciudad de México | `CMX-CF` | fiscal | sin dato | 589 |
| Código de Instituciones y Procedimientos Electorales de la Ciudad de México | `CMX-CIPE` | electoral | sin dato | 524 |
| Código Penal para el Distrito Federal | `CMX-CP` | penal | 2026-08-21 | 478 |
| Código de Procedimientos Civiles para el Distrito Federal | `CMX-CPC` | civil | 2018-07-18 | 1,137 |
| Código de Responsabilidad Parlamentaria del Congreso de la Ciudad de México | `CMX-CRP` | electoral | sin dato | 42 |

## Cómo está guardado y por qué

- `fuentes/leyes/<CLAVE>/articulos/art-0106.md`, `art-0001-a.md`, `art-0018-h-bis.md`. Un cambio de ley aparece en git como el artículo que cambió.
- `indice.json`: artículo → archivo, SHA256 de su texto, ubicación (título, capítulo, sección) y si está derogado.
- `manifiesto.json`: URL oficial, fecha de descarga, SHA256 del PDF y del texto, última reforma que dice el PDF.
- `transitorios.md`: los de la ley y los de los decretos de reforma.
- **Los PDF no entran al repo**: se guarda su URL y su huella. Son unos 33 MB de texto en total (la LFT y la LFD pesan más); un repo aparte no hace falta.
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
3. La RMF 2026 está en `fuentes/rmf/`; faltan sus modificaciones y los anexos. Siguen sin estar: Ley del ISSSTE, Código de Comercio, LGSM, Ley de Amparo y los reglamentos de la LSS.
4. Los encabezados se reconocen por forma. Si la Cámara cambia el formato del PDF, `extraer_ley.py` falla en vez de guardar basura (mínimo 20 artículos).

## Cómo entra una reforma

Una reforma no se sobrescribe en silencio: cada decreto entra en **su propio PR**, con el decreto (URL del DOF y fecha), el texto regenerado y la actualización de `cotejado_dof`. El historial de git guarda el texto anterior, así que se puede saber qué texto estaba vigente en una fecha.
