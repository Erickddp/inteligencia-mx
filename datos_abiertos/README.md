# Datos abiertos

La base, las leyes y lo que falta verificar, en CSV y JSON para que cualquiera los use: hojas de cálculo, análisis, tableros o entrenamiento de un buscador. Licencia **CC BY 4.0** ([LICENCIAS](../LICENCIAS.md)): úsalos citando «inteligencia-mx».

| Archivo | Qué trae |
|---|---|
| [`parametros.csv`](parametros.csv) | Cada parámetro de ley: tramos, estados, vigencia, valor del último tramo (solo si es un dato simple) y su fuente |
| [`reglas.csv`](reglas.csv) | Cada regla: estado, calculadora, número de casos, citas y si trae `que_dice` |
| [`leyes.csv`](leyes.csv) | Cada ley, código o reglamento: ámbito, entidad, materia, última reforma, huella del PDF y si tiene cotejo humano |
| [`citas.csv`](citas.csv) | Qué artículo cita cada regla o parámetro y si existe en la biblioteca |
| [`cotejo_pendiente.csv`](cotejo_pendiente.csv) | Los artículos que la base cita y nadie ha cotejado con el diario oficial, ordenados por cuántas cosas dependen de ellos |
| [`catalogo.json`](catalogo.json) | Columnas, número de filas y huella SHA256 de cada archivo |

## Cómo se mantienen

```bash
python scripts/exportar_datos_abiertos.py             # regenera estos archivos
python scripts/exportar_datos_abiertos.py --comprobar # falla si no están al día (lo corre el CI)
```

Se generan **de forma determinista** a partir de `base/` y `fuentes/`: sin fechas ni orden aleatorio. Si cambias la base, regenera y sube los archivos en el mismo PR.

## El corpus de texto

El texto de cada artículo y de cada regla de la RMF, un JSON por línea, **no se versiona** (pesa decenas de MB). Se genera cuando se necesita:

```bash
python scripts/exportar_datos_abiertos.py --corpus corpus.jsonl
```

Cada línea trae `id` (por ejemplo `LISR:106` o `RMF2026:2.7.1.21`), `ley`, `numero`, `ubicacion`, `ambito`, `entidad`, `materia`, `url`, `cotejado`, `derogado`, `sha256` y `texto`. Es la entrada de la capa de [búsqueda](../busqueda/README.md).

## Qué NO son

Orientación técnica, no asesoría fiscal ([AVISO](../AVISO.md)). Un artículo con `cotejado: no` es el texto de la Cámara de Diputados o del congreso del estado y **no está cotejado** con el diario oficial.
