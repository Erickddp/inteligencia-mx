#!/usr/bin/env python3
"""Publica una versión de la base fiscal de Timbra en un solo paso.

  python scripts/release.py --version 0.5.0 --anterior DIR_ANTERIOR --out DIR_SALIDA [--raiz .] [--notas notas.md]

--raiz es el repo (base/ con parametros.yaml, reglas.yaml y FASES.md; timbra_reglas/motor.py).
--changelog agrega la entrada de la versión a CHANGELOG.md (se hace en el PR de la versión, antes del tag).
--anterior es el paquete plano de la versión anterior (parametros.yaml, reglas.yaml...), sin sufijo.
Hace: sube versiones -> corre timbra-reglas probar (si falla, no publica) -> compara contra la versión
anterior -> copia con sufijo de versión (y copia con el nombre plano + SHA256SUMS, que es lo que baja Timbra)
-> SHA256 -> ORDEN_CAMBIO con las huellas DENTRO -> zip.
El paquete que sale es PLANO (los 4 archivos juntos): es lo que Timbra vendoriza y verifica por huella.
"""
import argparse, datetime as dt, hashlib, json, os, re, shutil, subprocess, sys, zipfile
from pathlib import Path
import yaml

# nombre en el paquete -> ruta dentro del repo
ARCH = {"parametros.yaml": "base/parametros.yaml", "reglas.yaml": "base/reglas.yaml",
        "motor.py": "timbra_reglas/motor.py", "FASES.md": "base/FASES.md"}


def sube_version(raiz: Path, v: str):
    for f in ["base/parametros.yaml", "base/reglas.yaml"]:
        p = raiz / f
        t, n = re.subn(r'^version_base: ".*"$', f'version_base: "{v}"', p.read_text(encoding="utf-8"), count=1, flags=re.M)
        if n != 1:
            sys.exit(f"{f}: no encontré version_base")
        p.write_text(t, encoding="utf-8")
    p = raiz / "timbra_reglas/motor.py"
    t, n = re.subn(r'^VERSION_MOTOR = ".*"$', f'VERSION_MOTOR = "{v}"', p.read_text(encoding="utf-8"), count=1, flags=re.M)
    if n != 1:
        sys.exit("motor.py: no encontré VERSION_MOTOR")
    p.write_text(t, encoding="utf-8")


def carga(d: Path):
    P = yaml.safe_load((d / "parametros.yaml").read_text(encoding="utf-8"))["parametros"]
    R = {r["id"]: r for r in yaml.safe_load((d / "reglas.yaml").read_text(encoding="utf-8"))["reglas"]}
    return P, R


def compara(ant: Path, nue: Path):
    Pa, Ra = carga(ant)
    Pn, Rn = carga(nue)
    out = {"param_nuevos": sorted(set(Pn) - set(Pa)), "param_quitados": sorted(set(Pa) - set(Pn)),
           "valor_cambiado": [], "estado_cambiado": [], "vigencia_cambiada": [], "tramos_nuevos": [],
           "reglas_nuevas": sorted(set(Rn) - set(Ra)), "reglas_quitadas": sorted(set(Ra) - set(Rn)),
           "regla_estado": []}
    for pid in sorted(set(Pa) & set(Pn)):
        ta = {v["desde"]: v for v in Pa[pid].get("valores", [])}
        tn = {v["desde"]: v for v in Pn[pid].get("valores", [])}
        for d in sorted(set(tn) - set(ta)):
            out["tramos_nuevos"].append(f"{pid} desde {d} ({tn[d].get('estado', 'vigente')})")
        for d in sorted(set(ta) & set(tn)):
            if ta[d].get("valor") != tn[d].get("valor"):
                out["valor_cambiado"].append(f"{pid} desde {d}")
            if (ta[d].get("hasta"), ta[d].get("confirmado_hasta")) != (tn[d].get("hasta"), tn[d].get("confirmado_hasta")):
                out["vigencia_cambiada"].append(f"{pid} desde {d}: hasta {ta[d].get('hasta')} -> {tn[d].get('hasta')}")
            if ta[d].get("estado", "vigente") != tn[d].get("estado", "vigente"):
                out["estado_cambiado"].append(f"{pid} desde {d}: {ta[d].get('estado', 'vigente')} -> {tn[d].get('estado', 'vigente')}")
        if Pa[pid].get("formula") != Pn[pid].get("formula"):
            out["valor_cambiado"].append(f"{pid} (fórmula)")
    for rid in sorted(set(Ra) & set(Rn)):
        if Ra[rid].get("estado") != Rn[rid].get("estado"):
            out["regla_estado"].append(f"{rid}: {Ra[rid].get('estado')} -> {Rn[rid].get('estado')}")
    return out


def entrada_changelog(v: str, dif, resumen: str, fecha: str, notas: str = "") -> str:
    """Entrada de CHANGELOG.md para la versión v, con lo que cambió contra la anterior."""
    L = [f"## [v{v}] - {fecha}", "", f"Pruebas: {resumen}.", ""]
    if notas:
        L += [notas.strip(), ""]
    if dif is None:
        L += ["Sin versión anterior con la cual comparar.", ""]
        return "\n".join(L)
    secciones = [("Valores cambiados (firmas que se caen)", "valor_cambiado"), ("Estados cambiados", "estado_cambiado"),
                 ("Vigencias cambiadas", "vigencia_cambiada"), ("Tramos nuevos", "tramos_nuevos"),
                 ("Parámetros nuevos", "param_nuevos"), ("Parámetros quitados", "param_quitados"),
                 ("Reglas nuevas", "reglas_nuevas"), ("Reglas quitadas", "reglas_quitadas"),
                 ("Reglas que cambiaron de estado", "regla_estado")]
    hubo = False
    for titulo, k in secciones:
        if dif[k]:
            hubo = True
            L += [f"### {titulo}", ""] + [f"- {i}" for i in dif[k]] + [""]
    if not hubo:
        L += ["Sin cambios en parámetros, vigencias, estados ni reglas.", ""]
    return "\n".join(L)


def escribe_changelog(raiz: Path, entrada: str, v: str):
    """Inserta la entrada arriba de las anteriores; si ya existe la de esa versión, la reemplaza."""
    p = raiz / "CHANGELOG.md"
    t = p.read_text(encoding="utf-8") if p.exists() else "# Changelog\n\n"
    partes = re.split(r"(?m)^(?=## \[v)", t)
    cabecera, entradas = partes[0], [e for e in partes[1:] if not e.startswith(f"## [v{v}]")]
    cuerpo = "\n".join([entrada.rstrip("\n") + "\n"] + entradas)
    p.write_text(cabecera.rstrip("\n") + "\n\n" + cuerpo, encoding="utf-8", newline="\n")


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--raiz", default=".")
    a.add_argument("--version", required=True)
    a.add_argument("--anterior")
    a.add_argument("--out", required=True)
    a.add_argument("--notas")
    a.add_argument("--changelog", action="store_true", help="agrega la entrada de esta versión a CHANGELOG.md")
    x = a.parse_args()
    raiz, out, v = Path(x.raiz).resolve(), Path(x.out), x.version

    sube_version(raiz, v)
    r = subprocess.run([sys.executable, "-m", "timbra_reglas", "probar"], cwd=raiz, capture_output=True, text=True,
                       encoding="utf-8", env={**os.environ, "PYTHONUTF8": "1"})
    resumen = (r.stdout.strip().splitlines() or ["sin salida"])[-1]
    if r.returncode != 0:
        print(r.stdout[-3000:], r.stderr[-3000:])
        sys.exit(f"NO SE PUBLICA: timbra-reglas probar falló -> {resumen}")

    dif = compara(Path(x.anterior), raiz / "base") if x.anterior else None
    out.mkdir(parents=True, exist_ok=True)
    copias = []
    for nombre, ruta in ARCH.items():
        stem, suf = nombre.rsplit(".", 1)
        dest = out / f"{stem}_v{v}.{suf}"
        shutil.copy(raiz / ruta, dest)
        copias.append(dest)
    huellas = "\n".join(f"{hashlib.sha256(c.read_bytes()).hexdigest()}  {c.name}" for c in copias)
    # Timbra baja los 4 archivos del release POR SU NOMBRE (sin sufijo) y compara huellas: van también así, byte por byte iguales.
    planos = []
    for nombre, ruta in ARCH.items():
        shutil.copy(raiz / ruta, out / nombre)
        planos.append(out / nombre)
    (out / "SHA256SUMS").write_text("\n".join(f"{hashlib.sha256(c.read_bytes()).hexdigest()}  {c.name}" for c in planos) + "\n", encoding="utf-8")

    L = [f"ORDEN DE CAMBIO · Base fiscal v{v}", "Autoriza: Rick (C.P.).", "",
         "=== HUELLAS (verifica con sha256sum ANTES de cargar; si una no coincide, no cargues nada) ===", huellas, "",
         "=== CÓMO CARGAR ===",
         f"1) Verifica las huellas. 2) Revisa version_base \"{v}\" y VERSION_MOTOR \"{v}\".",
         "3) Quita el sufijo de versión, copia los 4 archivos a app/reglas/ y vuelve a fijar VERSION.json (tag, commit y huellas).",
         "4) Corre el CI de Timbra: su revisión sin red compara con VERSION.json y la de red con los assets de este release.",
         f"5) Resultado esperado de timbra-reglas probar: {resumen}", ""]
    if dif:
        def bloque(titulo, items):
            L.append(f"--- {titulo} ({len(items)}) ---")
            L.extend(f"  {i}" for i in items) if items else L.append("  ninguno")
        L.append("=== DIFERENCIAS CONTRA LA VERSIÓN ANTERIOR ===")
        bloque("VALORES CAMBIADOS = FIRMAS QUE SE CAEN", dif["valor_cambiado"])
        bloque("Estados cambiados", dif["estado_cambiado"])
        bloque("Vigencias cambiadas", dif["vigencia_cambiada"])
        bloque("Tramos nuevos", dif["tramos_nuevos"])
        bloque("Parámetros nuevos", dif["param_nuevos"])
        bloque("Parámetros quitados", dif["param_quitados"])
        bloque("Reglas nuevas", dif["reglas_nuevas"])
        bloque("Reglas quitadas", dif["reglas_quitadas"])
        bloque("Reglas que cambiaron de estado", dif["regla_estado"])
        L.append("")
    if x.notas:
        L += ["=== NOTAS DE LA INVESTIGACIÓN ===", Path(x.notas).read_text(encoding="utf-8"), ""]
    if x.changelog:
        notas = Path(x.notas).read_text(encoding="utf-8") if x.notas else ""
        escribe_changelog(raiz, entrada_changelog(v, dif, resumen, dt.date.today().isoformat(), notas), v)
    orden = out / f"ORDEN_CAMBIO_v{v}.txt"
    orden.write_text("\n".join(L), encoding="utf-8")
    (out / f"SHA256_v{v}.txt").write_text(huellas + "\n", encoding="utf-8")
    # Contrato para las apps (Timbra): qué IDs cambian, antes y después, y qué firmas se caen.
    if str(Path(__file__).resolve().parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
    import integracion
    commit = os.environ.get("GITHUB_SHA") or integracion.commit_actual()
    huellas_planas = {c.name: hashlib.sha256(c.read_bytes()).hexdigest() for c in planos}
    datos = integracion.integracion(Path(x.anterior) if x.anterior else None, raiz / "base", v, commit, huellas_planas, resumen)
    (out / f"integracion_v{v}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1, default=str) + "\n", encoding="utf-8")
    z = out / f"timbra-reglas-v{v}.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for c in copias + [orden, out / f"SHA256_v{v}.txt"]:
            zf.write(c, c.name)
    print(f"PUBLICADA v{v}: {resumen}\n{z}\n")
    print("MENSAJE PARA CLAUDE CODE:\n"
          f"Va la v{v}. Las huellas vienen dentro de ORDEN_CAMBIO_v{v}.txt (y en SHA256_v{v}.txt). "
          f"Verifica, quita el sufijo, copia a app/reglas/, fija VERSION.json y aplica la orden. Debe salir: {resumen}")


if __name__ == "__main__":
    main()
