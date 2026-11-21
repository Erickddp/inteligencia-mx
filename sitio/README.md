# Sitio público (fase 1)

La consola de consulta de Inteligencia MX: leyes, cifras de ley y reglas de cálculo, con buscador.

- `plantilla.html`: diseño y lógica de la página. Los datos entran en `__DATOS__`.
- `construir.py`: lee `datos_abiertos/` y escribe `_site/index.html`. No toca `base/`.
- `.github/workflows/pages.yml`: arma y publica en GitHub Pages en cada push a `main`.

Probar en local:

```bash
python sitio/construir.py
python -m http.server -d _site 8000
```

## Activarlo (una sola vez, lo hace quien administra el repo)

1. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
2. Corre el workflow «Sitio público» (Actions → Sitio público → Run workflow) o espera al siguiente push a `main`.
3. Queda en `https://erickddp.github.io/inteligencia-mx/`.

## Dominio propio

1. Crea `sitio/CNAME` con una sola línea: el dominio (por ejemplo `inteligenciamx.mx`).
2. En tu proveedor de dominio:
   - Dominio raíz: registros `A` a `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`.
   - Subdominio (por ejemplo `consulta.inteligenciamx.mx`): `CNAME` a `erickddp.github.io`.
3. En **Settings → Pages** escribe el dominio y marca **Enforce HTTPS** cuando aparezca.
