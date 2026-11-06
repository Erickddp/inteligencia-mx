# Protección de `main` (casillas de GitHub)

Las activa quien administra el repositorio. Hazlo **después** de que el CI haya corrido al menos una vez, para que los checks aparezcan en la lista.

## 1. Ruleset de la rama (Settings → Rules → Rulesets → New ruleset → New branch ruleset)

- **Ruleset name:** `main`
- **Enforcement status:** Active
- **Bypass list:** vacía (ni administradores, ni la GitHub App)
- **Target branches:** Add target → Include default branch
- Marca:
  - [x] **Restrict deletions**
  - [x] **Block force pushes**
  - [x] **Require a pull request before merging**
    - Required approvals: **1**
    - [x] Dismiss stale pull request approvals when new commits are pushed
    - [x] **Require review from Code Owners**
    - [x] Require approval of the most recent reviewable push
    - [x] Require conversation resolution before merging
    - Allowed merge methods: **Merge** (quita Squash y Rebase: así cada commit conserva su `Signed-off-by`)
  - [x] **Require status checks to pass**
    - [x] Require branches to be up to date before merging
    - Agrega: `Pruebas (Python 3.11)`, `Pruebas (Python 3.13)`, `Diferencias contra main` y `Signed-off-by en cada commit`
- Lo demás, sin marcar.

> Con una sola persona dueña, ella no puede aprobar su propio PR. Los cambios que proponga el dueño entran mediante un PR abierto por otra cuenta (la GitHub App) o con un segundo revisor con permiso de escritura. No actives el bypass para administradores: anularía la firma.

## 2. Ruleset de tags (New ruleset → New tag ruleset)

- **Ruleset name:** `releases`
- **Enforcement status:** Active
- **Target tags:** Include by pattern → `v*`
- Marca: [x] **Restrict updates**, [x] **Restrict deletions**
- Bypass list: vacía. Los tags no se mueven: Timbra fija la versión por tag y commit.

## 3. Otras casillas

- **Settings → General → Pull Requests:** [x] Allow merge commits; [ ] Allow squash merging; [ ] Allow rebase merging; [x] Automatically delete head branches.
- **Settings → Actions → General:**
  - Fork pull request workflows: **Require approval for all outside collaborators**
  - Workflow permissions: **Read repository contents and packages permissions**
- **Settings → Code security:** [x] Dependabot alerts; [x] Secret scanning; [x] Push protection; [x] Private vulnerability reporting.
- **Settings → Collaborators:** nadie con rol Admin además del dueño.
- **Labels** (Issues → Labels): `cambio-de-ley`, `error-calculo`, `serie-automatica`, `esperando-firma`.
