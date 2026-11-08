# Cómo contribuir

Gracias por ayudar a mantener la base al día. Aquí cambia un número de ley solo con **fuente primaria**, **casos al centavo** y la **firma** de la persona que mantiene el repositorio (el `CODEOWNER`). Aprobar el PR es firmar la base.

## 1. Antes de empezar

Abre un issue:
- **Cambio de ley:** publicación, fecha, enlace oficial y qué parámetros toca.
- **Error en un cálculo:** el caso, lo esperado, lo obtenido y la fuente.

Así nadie trabaja dos veces lo mismo.

## 2. Qué fuente se acepta

Solo fuentes primarias:

- DOF (Diario Oficial de la Federación)
- PDF oficial del SAT (Anexos de la RMF, Paquete Económico)
- Ley vigente en diputados.gob.mx
- INEGI (UMA, INPC)
- Banxico (tipo de cambio)
- IMSS (cuotas)
- CONASAMI (salarios mínimos)

Un blog, un video o una nota de prensa sirven para **encontrar** la fuente, no para citarla. Si solo hay secundarias, el tramo entra como `por_confirmar` y el PR lo dice.

Cada tramo cita la fuente con la publicación y la fecha (`DOF dd-mmm-aaaa`) y, cuando es un PDF, su enlace. No subas el PDF: va su enlace y su SHA256 en `fuentes/`.

## 3. Cómo se propone un cambio

1. Llena la [ficha de regla](docs/ficha_regla.md) como hablas; si no sabes algo, pon «no sé».
2. Haz un fork y una rama.
3. Edita `base/parametros.yaml` y `base/reglas.yaml`:
   - **Un valor publicado nunca se edita: se agrega un tramo** con su `desde`/`hasta`.
   - IDs sin año ni mes. Números como **texto** (`"117.31"`).
   - Lo que depende de otro dato es **fórmula**.
   - Ley vigente: `hasta: null` y `confirmado_hasta`. Solo vence lo que tiene plazo.
   - Estados válidos: `vigente`, `por_confirmar`, `propuesta`, `aprobado_congreso_pendiente_dof`.
4. Toda regla con número lleva **al menos dos casos**: uno normal y uno en el límite, calculados con el motor y revisados a mano. Si un caso falla, se investiga; **nunca se mueve el esperado para que pase**.
5. En los casos usa RFC genéricos (`XAXX010101000`, `AAA010101AAA`). **Nunca** datos de clientes, RFC reales, secretos ni tokens.
6. Abre el PR con la plantilla: fuente primaria, casos agregados, nivel A o B y qué firmas se caen.

El CI comenta en tu PR las diferencias contra `main`: valores cambiados (cada uno es una firma que se cae), vigencias, estados, tramos y reglas nuevas.

### Mejorar el proyecto en sí

Si quieres mejorar cómo se verifica, se mide o se busca (no una cifra concreta), mira el [plan de mejora](docs/PLAN_DE_MEJORA.md): elige algo del [backlog](mejoras/backlog.yaml) o propón algo con la plantilla «Propuesta de mejora». Toda mejora trae su medida: una pregunta dorada nueva, una prueba o una cifra de `datos_abiertos/` que cambia. Si tocaste la base, regenera los datos abiertos con `python scripts/exportar_datos_abiertos.py`.

### Con Claude Code

Si usas Claude Code dentro del repositorio, `/inteligencia-fiscal leyes estatales de Querétaro, fiscales` hace este recorrido por ti para el texto de una ley, y `/aportar-inteligencia-mx` para un número o una regla. Las dos siguen el [estándar de aportación](docs/ESTANDAR_APORTACION.md): fuente de dominio oficial, claves `<ENTIDAD>-<SIGLAS>`, PR separados para el texto y para los números, y `python scripts/validar_aportacion.py` en verde.

## 4. Cómo correr las pruebas

```bash
pip install -e ".[test]"
timbra-reglas probar          # los casos de reglas.yaml
python -m pytest -q           # casos + pruebas del motor
python scripts/validar_oro.py # reglas de oro (IDs, fuentes, float, casos, RFC, secretos)
```

Las tres deben salir en verde. `validar_oro.py` trae una lista de deuda (`scripts/deuda_oro.json`): un PR no puede agregar violaciones nuevas, y si arreglas una de la lista, quítala con `python scripts/validar_oro.py --actualizar-deuda`.

Para cotejar una tabla contra el PDF oficial: `python scripts/cotejar_tabla.py --param ID --desde AAAA-MM-DD --texto tabla.txt`.

## 5. DCO: firma cada commit

Este proyecto usa el [Developer Certificate of Origin](https://developercertificate.org/). Al firmar certificas que tienes derecho a aportar lo que subes bajo las licencias del repositorio ([LICENCIAS.md](LICENCIAS.md)). Cada commit lleva la línea:

```
Signed-off-by: Tu Nombre <tu@correo.com>
```

Se agrega con `git commit -s`. Si olvidaste alguno: `git rebase --signoff main` y `git push --force-with-lease`. El CI rechaza el PR si algún commit no la trae.

## 6. Qué pasa después

- Una persona del equipo revisa la fuente y los casos. Los cambios en `base/`, `timbra_reglas/`, `scripts/` y `.github/` requieren la aprobación del `CODEOWNER`.
- Los releases (`vX.Y.Z`) solo los crea quien mantiene el repositorio. Cada uno trae sus huellas SHA256.
- La base es orientación técnica ([AVISO](AVISO.md)); tu aporte no te hace responsable de su uso, pero sí de que la fuente exista y sea la que dices.

## Código de conducta breve

Se discute la fuente y el caso, no a la persona. Sin datos personales de nadie.
