# PDF que faltan en la biblioteca

No hubo acceso de red a los sitios oficiales en las sesiones de trabajo, así que **no se puede dar ninguna huella (SHA256) antes de tener el archivo**: una huella inventada no sirve. Cómo se registra cada uno cuando se sube:

1. Poner el PDF en una carpeta temporal fuera del repo.
2. `sha256sum archivo.pdf` (esa es la huella que queda en el manifiesto).
3. `python scripts/extraer_ley.py CLAVE --pdf archivo.pdf --url URL_OFICIAL --nombre "..." --ambito federal --materia ...` y `python scripts/validar_aportacion.py`. El PDF no se sube al repo: sólo su URL y su huella.

| Qué | Clave sugerida | Materia | URL oficial | Huella |
|---|---|---|---|---|
| Constitución Política de los Estados Unidos Mexicanos | `CPEUM` | otra | Cámara de Diputados: forma esperada `https://www.diputados.gob.mx/LeyesBiblio/pdf/CPEUM.pdf` (no verificada) | al descargar |
| Código Penal Federal (art. 400 Bis) | `CPF` | penal | `https://www.diputados.gob.mx/LeyesBiblio/pdf/CPF.pdf` (no verificada) | al descargar |
| Código de Comercio | `CCOM` | mercantil | `https://www.diputados.gob.mx/LeyesBiblio/pdf/CCom.pdf` (no verificada) | al descargar |
| Ley General de Títulos y Operaciones de Crédito | `LGTOC` | mercantil | `https://www.diputados.gob.mx/LeyesBiblio/pdf/LGTOC.pdf` (no verificada) | al descargar |
| Ley General de Sociedades Mercantiles | `LGSM` | mercantil | `https://www.diputados.gob.mx/LeyesBiblio/pdf/LGSM.pdf` (no verificada) | al descargar |
| Código Civil Federal | `CCF` | civil | `https://www.diputados.gob.mx/LeyesBiblio/pdf/CCF.pdf` (no verificada) | al descargar |
| Anexo 20 de la RMF 2026 y guía de llenado del CFDI 4.0, con los catálogos c_TipoRelacion, c_FormaPago y c_MetodoPago | (se carga como documento de la RMF, no como ley) | fiscal | sitio del SAT (sat.gob.mx), sección de factura electrónica / CFDI 4.0. **No se da URL exacta: no se pudo abrir el sitio.** Si tú ya tienes el PDF, súbelo y se registra su huella | al descargar |

Las URL de la Cámara siguen la forma de las 27 leyes ya registradas (por ejemplo `https://www.diputados.gob.mx/LeyesBiblio/pdf/LISR.pdf`, verificada en sus manifiestos), pero el nombre exacto de cada archivo nuevo es el habitual y **no está comprobado**. Si una URL falla, pídele la correcta a la persona que mantiene el repositorio. LFPIORPI y su reglamento ya están en la biblioteca.
