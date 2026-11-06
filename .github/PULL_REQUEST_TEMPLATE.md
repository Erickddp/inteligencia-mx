## Qué cambia (en palabras de contador)

<!-- Qué número, regla o serie se agrega o se corrige y desde cuándo. -->

## Fuente primaria

<!-- DOF / PDF oficial del SAT / ley vigente / INEGI / Banxico / IMSS / CONASAMI. Enlace y fecha de publicación. Si no hay: el tramo es `por_confirmar` y lo digo aquí. -->

## Casos agregados

<!-- Uno normal y uno en el límite, al centavo, por cada regla con número. Confirmo que no moví ningún `esperado` para que pase. -->

## Nivel

- [ ] **A** (producción: lo opera el despacho con clientes reales)
- [ ] **B** (experimental)

## Firmas que se caen

<!-- Mira el comentario automático «Diferencias contra main»: cada valor cambiado es una firma que se cae en Timbra. Si es corrección de un valor ya publicado (no cambio de ley), explícalo. «Ninguna» si solo agregas tramos o reglas. -->

## Lista de verificación

- [ ] `timbra-reglas probar`, `python -m pytest -q` y `python scripts/validar_oro.py` en verde
- [ ] Un valor publicado no se editó: se agregó un tramo
- [ ] Sin años ni meses en los IDs; números como texto
- [ ] Sin datos de clientes, RFC reales, secretos ni tokens
- [ ] Todos los commits llevan `Signed-off-by` (`git commit -s`)
