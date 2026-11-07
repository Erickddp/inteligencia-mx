# Cómo una app toma una versión (contrato de integración)

Cada release trae un **paquete plano** y un **`integracion_vX.json`**. La app no revisa nada a mano: lee ese JSON.

## Archivos del release

| Archivo | Para qué |
|---|---|
| `parametros.yaml`, `reglas.yaml`, `motor.py`, `FASES.md` | Los 4 archivos que la app copia (nombre plano, sin sufijo de versión) |
| `series/<id>.yaml` (en el release: `series_<id>.yaml`) | Las series de datos (INPC hoy; tipo de cambio después). El motor las busca en `series/` junto a `motor.py`: sin ellas, las calculadoras que leen una serie avisan con `SinValor` |
| `SHA256SUMS` | Huella de esos 4 archivos **y de cada serie** (las series con su ruta `series/<id>.yaml`) |
| `integracion_vX.json` | Qué cambió, con IDs, antes y después, y qué firmas se caen |
| `*_vX.Y.Z.*`, `ORDEN_CAMBIO_vX.Y.Z.txt`, `timbra-reglas-vX.Y.Z.zip` | Copias con sufijo, la orden de cambio para leer y el zip |

La app verifica cada archivo contra `SHA256SUMS` **antes** de copiarlo, y fija en su `VERSION.json`: repo, tag, commit y huellas.

**El contrato es «4 archivos + `series/*.yaml`».** Los assets de un release de GitHub son planos, así que una serie se publica como `series_<id>.yaml`; en el paquete, en `SHA256SUMS`, en el zip y en `huellas` su ruta es `series/<id>.yaml`. El campo `assets` de `integracion_vX.json` traduce de una a otra. La app copia `series_inpc.yaml` a `app/reglas/series/inpc.yaml`.

**El paquete se prueba solo.** Antes de publicar, el CI copia a una carpeta vacía exactamente los archivos que lista `SHA256SUMS`, verifica cada huella y corre `python -I motor.py probar` ahí, sin el repositorio al lado (`scripts/probar_paquete.py`). Un paquete al que le falte algo no se publica.

## `integracion_vX.json` (schema 1)

| Campo | Contenido |
|---|---|
| `version`, `tag`, `commit`, `generado`, `anterior` | Identidad de la versión y de la anterior (`version_base`) |
| `huellas` | `{ruta en el paquete: sha256}` de los 4 archivos planos y de cada serie (`series/inpc.yaml`) |
| `assets` | `{ruta en el paquete: nombre del asset en el release}`; solo difiere en las series (`series/inpc.yaml` → `series_inpc.yaml`) |
| `pruebas` | Resumen de `timbra-reglas probar` |
| `parametros_nuevos` | `{id, nombre, tipo, formula}` |
| `parametros_quitados` | IDs |
| `tramos_nuevos` | `{id, desde, hasta, confirmado_hasta, estado, fuente}` |
| `valores_cambiados` | `{id, desde, antes, despues, hash_antes, hash_despues}`: un valor publicado que se editó |
| `formulas_cambiadas` | `{id, antes, despues}` |
| `vigencias_cambiadas` | `{id, desde, antes, despues}` con `hasta` y `confirmado_hasta` |
| `estados_cambiados` | `{id, desde, antes, despues}` |
| `reglas_nuevas`, `reglas_quitadas`, `reglas_estado` | Reglas R-xx que entran, salen o cambian de estado |
| `calculadoras_nuevas` | Nombres de calculadoras que ninguna regla usaba en la versión anterior |
| `meta_cambiada` | `{id, campo, antes, despues}`: cambios de `citas`, `que_dice` y `correcto_si` (el texto de apoyo del círculo de fundamento; **no** tira firmas) |
| `firmas_que_se_caen` | `{id, desde, hash_antes}`: exactamente qué firmas deben invalidarse |
| `ids_afectados` | Todos los IDs tocados (parámetros y reglas) |

## La huella de un valor

`hash_valor` es la misma que usan las firmas de Timbra:

```python
json.dumps({"param": pid, "desde": desde, "valor": valor}, sort_keys=True, ensure_ascii=False, default=str)  # UTF-8 → sha256
```

No entran `hasta`, `fuente` ni `estado`. Por eso un cambio de fuente o de vigencia **no** tira la firma; un cambio de valor sí.

## Lo que la base promete a las apps

- **Un ID publicado no se renombra.** Los campos nuevos (por ejemplo `materia`, `ámbito`, `jurisdicción`) se agregan sin tocar los IDs existentes.
- **Un valor publicado no se edita:** se agrega un tramo. Si alguna vez se corrige una errata, aparece en `valores_cambiados` y en `firmas_que_se_caen`.
- **El paquete plano de 4 archivos se mantiene**, aunque la base se parta por materia dentro del repo.
- Un tramo `propuesta` o `aprobado_congreso_pendiente_dof` **nunca se aplica**: la app solo avisa.
