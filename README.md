# timbra-reglas

Base fiscal y contable de **Timbra**: los números de la ley mexicana con su vigencia y su fuente, las reglas que los usan y un motor que los resuelve por fecha. Es pública y contribuible: socios y otros contadores proponen cambios; la persona que mantiene el repositorio los firma.

> **Aviso:** es orientación técnica, no asesoría fiscal. Cada contador valida antes de usarlo. Lee el [AVISO](AVISO.md).

## Qué hay aquí

| Carpeta | Contenido |
|---|---|
| `base/` | `parametros.yaml` (números de ley con `desde`/`hasta`, fuente y estado) y `reglas.yaml` (catálogo R-xx, calculadora y casos al centavo) |
| `timbra_reglas/` | El motor como paquete: resuelve por fecha con `Decimal`, valida, prueba, mide impacto, simula y exporta |
| `scripts/` | `release.py`, `cotejar_tabla.py` y los validadores del CI |
| `series/` | Datos automáticos (INPC, tipo de cambio) |
| `fuentes/` | Índice de documentos oficiales: URL, fecha de publicación y SHA256 del PDF (no el PDF) |
| `docs/` | Documentación y la ficha de regla |
| `automatizacion/n8n/` | Flujos de n8n importables |

Versión actual: **0.4.1** (90 casos).

## Reglas que no se rompen

1. Fuente primaria o no entra (DOF, PDF oficial del SAT, ley vigente, INEGI, Banxico, IMSS, CONASAMI). Sin ella: `por_confirmar`.
2. Un ID, muchos tramos. Sin años ni meses en los IDs. Un valor publicado nunca se edita: se agrega un tramo.
3. Lo que depende de otro dato es fórmula.
4. Estados válidos: `vigente`, `por_confirmar` (se aplican); `propuesta`, `aprobado_congreso_pendiente_dof` (nunca se aplican).
5. Ley vigente no caduca por calendario: `hasta: null` + `confirmado_hasta`.
6. Toda regla con número lleva casos al centavo: uno normal y uno en el límite.
7. Números como texto, `Decimal` siempre, nunca `float`.
8. Sin datos de clientes, RFC reales, secretos ni tokens.

## Instalar y usar

```bash
pip install "git+https://github.com/Erickddp/timbra-reglas.git"      # o un release: ...@v0.4.1
timbra-reglas probar                                  # corre los casos de reglas.yaml
timbra-reglas valor UMA_DIARIA 2026-03-15             # valor + estado en una fecha
timbra-reglas impacto IVA_TASA_GENERAL                # qué depende de este parámetro
timbra-reglas vigencias 2027-01-01                    # qué vence y qué se arrastra
timbra-reglas simular IVA_TASA_GENERAL=10 2027-01-01  # «¿y si baja el IVA?»
timbra-reglas exportar 2026-01 2026-12                # JSON mes por mes
```

Cada release publica un paquete plano (`parametros`, `reglas`, `motor`, `FASES`) con sus huellas SHA256, para que quien lo use verifique cada archivo.

## Contribuir

Lee [CONTRIBUTING.md](CONTRIBUTING.md). Resumen: abre un issue de «cambio de ley», propón el cambio en un PR con fuente primaria y casos, y firma tus commits (`git commit -s`).

## Licencias

Código: Apache-2.0. Datos (`base/`, `series/`, `fuentes/`, `docs/`): CC BY 4.0. Detalle en [LICENCIAS.md](LICENCIAS.md).
