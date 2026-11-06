# Plan de seguimiento · timbra-reglas

Corte: 6-nov-2026. Base vigente: **v0.4.1** (90 casos). `main` en `79a9ee9`. Tag `v0.4.1` en `365546f`.

## Estado por punto

| Punto | Qué | Estado | Evidencia |
|---|---|---|---|
| 0 | Base v0.4.1 cargada tal cual, `.gitignore`, README UTF-8 | **Hecho, en main** | huellas = `SHA256_v0.4.1.txt` |
| A | Paquete `timbra_reglas`, comando `timbra-reglas`, pytest | **Hecho, en main** | 138 pruebas; wheel instalado en entorno limpio |
| B | Licencias, AVISO, CODEOWNERS, CONTRIBUTING, plantillas, CHANGELOG | **Hecho, en main** | `docs/PROTECCION_DE_MAIN.md` |
| C | CI por PR (probar, pytest, reglas de oro, diff comentado, DCO) y release por tag | **Hecho, en main; sin verlo correr** | revisar pestaña Actions |
| D | Series INPC y tipo de cambio CFF 20 | **Bloqueado** | faltan tokens Banxico e INEGI |
| E | Flujos n8n (Vigía DOF, Series, Vigencias, Recordatorio) | **Pendiente** | faltan credenciales y bot de Telegram |
| F | Skill `base-fiscal-timbra` en `.claude/skills/` | **Pendiente** | archivos sin versionar en la raíz |

## Pendiente de Rick (en GitHub)

1. **Publicar el release v0.4.1** sobre el tag existente, con los 7 archivos de `out/release-v0.4.1/` (zip, 4 sueltos, ORDEN, SHA256). Decidir si la ORDEN_CAMBIO_04 va pública.
2. **Mirar la pestaña Actions**: es la primera corrida de `ci.yml`. Avisar si algo falla.
3. **Activar la protección** de `docs/PROTECCION_DE_MAIN.md` (ruleset de rama, ruleset de tags, merge commits, secret scanning) y crear los labels `cambio-de-ley`, `error-calculo`, `serie-automatica`, `esperando-firma`.
4. **Crear la GitHub App** `timbra-reglas-bot` (Contents, Pull requests, Issues: lectura y escritura; instalada solo en este repo) y guardar su `.pem` en n8n.
5. **Revisar 3 RFC** de `base/reglas.yaml` (`GOMA850317H23`, `ABC970528UHA`, `XOJI740911U48`): si alguno es real, cambiarlo por uno genérico.
6. **Mover el repo fuera de Drive** (por ejemplo `C:\dev\timbra-reglas`): Drive mete `desktop.ini` en `.git/refs` y rompe `fetch`.
7. Para D: tokens de **Banxico (SIE)** e **INEGI (API INPC)**, guardados como variables de entorno locales, nunca en el repo.
8. Para E: bot de **Telegram** (token y `chat_id`) en las credenciales de n8n.

## Mañana (orden)

1. **F · Skill:** mover `SKILL.md`, `references/` y `assets/` a `.claude/skills/base-fiscal-timbra/`, adaptar rutas (`base/`, `timbra_reglas/`, `scripts/`, `timbra-reglas probar`), quitar los duplicados de la raíz. Un PR.
2. **E · n8n:** cuatro JSON importables en `automatizacion/n8n/` con README y los tokens de permisos mínimos. El Vigía nunca escribe valores; solo abre issues «cambio de ley».
3. **D · Series** (si hay tokens): `series/inpc.yaml`, `series/tipo_cambio_cff20.yaml`, `serie(id, fecha)` en el motor, calculadora de actualización CFF 17-A con INPC real, CI de series (huecos, duplicados, saltos > 5 %). Evidencia de SF60653 contra SF43718.
4. **Release v0.5.0** cuando D traiga función nueva: `release.py --changelog`, PR, tag.

## Deuda de la base (el CI la deja pasar, solo puede bajar)

`scripts/deuda_oro.json`: 82 violaciones.

- 72 tramos con `hasta: null` sin `confirmado_hasta` (regla 5).
- 6 reglas con número y un solo caso: R-14, R-17, R-30, R-81, R-83, R-117 (regla 6).
- 3 RFC no genéricos en `reglas.yaml` (regla 8).
- 1 ID con año: `DIOT_LAYOUT_2025` (regla 2). Renombrarlo cambia valores que usa la app: coordinar con un tramo nuevo, no editando el publicado.

Cada una la resuelve la investigación con fuente y la firma Rick en un PR aparte.

## Matriz de cobertura: huecos que la app aún escribe a mano

Sin ID en la base o sin fuente primaria cotejada:

- Calendario de vacaciones del SAT y festivos del CFF 12 (candidatos a serie).
- Retención de plataformas a persona moral.
- Plazo de cancelación CFF 29-A: está en la base; el código de la app aún no lo usa.
- Tabla RESICO PF 2027 si cambia con la reforma.
- Serie de tipo de cambio: SF43718 (app hoy) contra SF60653 (CFF 20), por confirmar.
- Pendientes de v0.4.1: NOM111, RESICO 3.13.x, DIOT pipe final y país, IDs de la API del INPC, ISN de 24 entidades.

## Decisiones tomadas

- Licencias: Apache-2.0 (código), CC BY 4.0 (datos).
- El release es un paquete **plano** de 4 archivos; la estructura interna del repo no se nota afuera.
- `nivel` (A/B) vivirá en `base/niveles.yaml`, con firma de Rick por CODEOWNERS; lo que no diga A es B. **Aún no creado.**
- Texto de ley en `fuentes/` como texto extraído con URL y SHA256; los PDF no entran al historial.
- Merge solo con «merge commit» para conservar el `Signed-off-by`.

## Riesgos

- Los workflows no se han visto correr: pueden requerir ajustes menores.
- Mientras no haya protección, `main` acepta push directo.
- El tag `v0.4.1` apunta al estado previo al paquete: no debe moverse (la app verifica por huella y commit).
