# Búsqueda y aprendizaje: la capa que lee

Esta carpeta es el punto de partida para que cualquier persona mejore **cómo se encuentra** un artículo o una regla, sin tocar el motor de cálculo.

> **Principio:** la búsqueda y cualquier modelo **leen** el corpus. **Nunca escriben cifras** en `base/`. Una cifra declarada debe tener un artículo, un caso y una firma; un modelo puede ayudar a encontrar el artículo, no a decidir el número.

## Qué hay aquí

| Archivo | Para qué | Cómo se mejora |
|---|---|---|
| [`perfiles.yaml`](perfiles.yaml) | **Modos de búsqueda**: cómo se busca (exacto, amplio, fiscal, estatal, vigente, cotejado, significado). | Agrega o ajusta un perfil: método, filtros, pesos de campo, sinónimos, `k`. |
| [`sinonimos.yaml`](sinonimos.yaml) | Cómo lo dice la gente y cómo lo dice la ley («aguinaldo» = «gratificaciones»). | Agrega un grupo con su evidencia (un artículo y la frase que contiene). |
| [`preguntas_doradas.yaml`](preguntas_doradas.yaml) | La vara de medir: una pregunta de persona y el artículo que la responde. | Agrega preguntas con el artículo esperado y por qué. |

La entrada de cualquier búsqueda es el **corpus**: el texto de cada artículo y regla, un JSON por línea.

```bash
python scripts/exportar_datos_abiertos.py --corpus corpus.jsonl
```

## Cómo se adapta a lo que se necesita

Los **modos** son datos, no código. Si tu caso es «solo leyes de Querétaro vigentes» o «solo materia laboral», agregas un perfil con esos filtros. Si una palabra de la gente no aparece en la ley, agregas un sinónimo con su evidencia. Si la búsqueda falla con una pregunta real, agregas esa pregunta dorada: desde ese momento nadie puede empeorarla sin que las pruebas lo noten.

## Cómo se mide que una mejora sirve

1. Las **preguntas doradas** deben seguir acertando: el artículo esperado entre los primeros `k` resultados (recall@k). Una mejora no puede bajar ese número.
2. Todo par de la vara se **verifica contra la biblioteca**: `python -m pytest -q tests/test_mejoras.py`.
3. Si usas un modelo, **registra cuál** (nombre, versión y huella) para que el resultado se pueda reproducir.

## Qué sigue (fase 3 del [plan de mejora](../docs/PLAN_DE_MEJORA.md))

- **3a** corpus abierto. *Hecho: el script ya lo genera.*
- **3b** búsqueda base por palabras clave y BM25, sin dependencias pesadas, que lea estos perfiles.
- **3c** medir con las preguntas doradas (recall@k) como puerta de calidad en el CI.
- **3d** backend semántico opcional y enchufable, para cualquier modelo de embeddings.

## Reglas de esta capa

- Texto de leyes y datos abiertos solo de fuentes oficiales; nada de datos de clientes ni RFC reales.
- Un resultado de búsqueda siempre **cita su artículo** y dice si está cotejado o no.
- Un modelo es un componente reemplazable: el repositorio no se casa con ninguno.
