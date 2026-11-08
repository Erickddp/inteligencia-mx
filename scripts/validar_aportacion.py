#!/usr/bin/env python3
"""Valida que una aportación de fuentes (leyes, documentos oficiales) cumpla el estándar de docs/ESTANDAR_APORTACION.md.

  python scripts/validar_aportacion.py            # revisa todo fuentes/

Lo que exige (y el CI repite en cada PR):
  - fuente primaria: la URL de cada ley y de cada documento es de un dominio oficial (fuentes/dominios_oficiales.yaml);
  - cada ley trae manifiesto.json con huellas (sha256 del PDF y del texto), fecha de descarga y número de artículos
    que coincide con indice.json, y cada artículo del índice existe como archivo;
  - una ley estatal o municipal declara ámbito, entidad (ISO 3166-2:MX, fuentes/entidades.yaml) y materia, y su clave
    es  <ENTIDAD>-<SIGLAS>  con la entidad que declara;
  - ningún PDF dentro de fuentes/ (el PDF no se sube: va su URL y su huella);
  - las claves de entidad que usa la base (ISN_TASA_TABLA) existen en el catálogo de entidades.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml

RAIZ = Path(__file__).resolve().parent.parent
AMBITOS = {"federal", "estatal", "municipal"}
MATERIAS = {"fiscal", "contable", "laboral", "seguridad_social", "mercantil", "civil", "penal", "electoral", "administrativo", "otra"}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def carga_entidades(raiz: Path = RAIZ) -> dict:
    d = yaml.safe_load((raiz / "fuentes" / "entidades.yaml").read_text(encoding="utf-8"))
    return {e["iso"]: e["nombre"] for e in d["entidades"]}


def carga_dominios(raiz: Path = RAIZ) -> dict:
    return yaml.safe_load((raiz / "fuentes" / "dominios_oficiales.yaml").read_text(encoding="utf-8"))


def dominio_oficial(url: str, dominios: dict | None = None) -> bool:
    """True si el host de la URL es de un dominio oficial (regla de oro 1)."""
    dominios = dominios or carga_dominios()
    u = urlparse(url or "")
    host = (u.hostname or "").lower()
    if u.scheme not in ("http", "https") or not host:
        return False
    return any(host == s.lstrip(".") or host.endswith(s if s.startswith(".") else "." + s) for s in dominios["sufijos"] + dominios["organismos"])


def valida_manifiesto(m: dict, carpeta: str, entidades: dict, dominios: dict) -> list:
    e = []
    for k in ("clave", "nombre", "url", "descargado", "sha256_pdf", "sha256_texto", "articulos"):
        if m.get(k) in (None, "", 0):
            e.append(f"{carpeta}: falta `{k}` en el manifiesto")
    if m.get("clave") != carpeta:
        e.append(f"{carpeta}: la clave del manifiesto ({m.get('clave')!r}) no coincide con la carpeta")
    for k in ("sha256_pdf", "sha256_texto"):
        if m.get(k) and not HEX64.match(str(m[k])):
            e.append(f"{carpeta}: `{k}` no es un SHA256 válido")
    if m.get("descargado") and not FECHA.match(str(m["descargado"])):
        e.append(f"{carpeta}: `descargado` debe ser AAAA-MM-DD")
    if m.get("url") and not dominio_oficial(m["url"], dominios):
        e.append(f"{carpeta}: la URL {m['url']} no es de un dominio oficial (regla de oro 1: solo fuente primaria)")
    ambito = m.get("ambito", "federal")
    if ambito not in AMBITOS:
        e.append(f"{carpeta}: ámbito {ambito!r} no válido ({', '.join(sorted(AMBITOS))})")
    elif ambito != "federal":
        ent = m.get("entidad")
        if ent not in entidades:
            e.append(f"{carpeta}: entidad {ent!r} no está en fuentes/entidades.yaml (usa la clave ISO, por ejemplo QUE)")
        elif not re.fullmatch(rf"{ent}-[A-Z0-9]+(-[A-Z0-9]+)*", carpeta):
            e.append(f"{carpeta}: la clave de una ley de {ent} debe ser {ent}-<SIGLAS> (por ejemplo {ent}-XXXX)")
        if m.get("materia") not in MATERIAS:
            e.append(f"{carpeta}: materia {m.get('materia')!r} no válida ({', '.join(sorted(MATERIAS))})")
        if not m.get("emisor"):
            e.append(f"{carpeta}: falta `emisor` (quién publica el texto, por ejemplo el congreso o el periódico oficial del estado)")
    elif m.get("materia") is not None and m["materia"] not in MATERIAS:
        e.append(f"{carpeta}: materia {m['materia']!r} no válida")
    return e


def valida_ley(carpeta: Path, entidades: dict, dominios: dict) -> list:
    nombre = carpeta.name
    if not (carpeta / "manifiesto.json").is_file():
        return [f"{nombre}: falta manifiesto.json"]
    m = json.loads((carpeta / "manifiesto.json").read_text(encoding="utf-8"))
    e = valida_manifiesto(m, nombre, entidades, dominios)
    if not (carpeta / "indice.json").is_file():
        return e + [f"{nombre}: falta indice.json"]
    idx = json.loads((carpeta / "indice.json").read_text(encoding="utf-8"))
    if m.get("articulos") != len(idx):
        e.append(f"{nombre}: el manifiesto dice {m.get('articulos')} artículos y el índice trae {len(idx)}")
    faltan = [a for a, v in idx.items() if not (carpeta / v["archivo"]).is_file()]
    if faltan:
        e.append(f"{nombre}: {len(faltan)} artículos del índice no existen como archivo (ej.: {faltan[:3]})")
    return e


def valida_documentos(docs: list, dominios: dict) -> list:
    e = []
    for d in docs:
        i = d.get("id", "?")
        if not dominio_oficial(d.get("url"), dominios):
            e.append(f"documento {i}: la URL {d.get('url')} no es de un dominio oficial")
        if not HEX64.match(str(d.get("sha256", ""))):
            e.append(f"documento {i}: falta un `sha256` válido del PDF")
        if not FECHA.match(str(d.get("publicado", ""))):
            e.append(f"documento {i}: `publicado` debe ser AAAA-MM-DD")
    return e


def valida_repo(raiz: Path = RAIZ) -> list:
    entidades, dominios = carga_entidades(raiz), carga_dominios(raiz)
    e = []
    leyes = raiz / "fuentes" / "leyes"
    for carpeta in sorted(p for p in leyes.iterdir() if p.is_dir()):
        e += valida_ley(carpeta, entidades, dominios)
    docs = raiz / "fuentes" / "documentos.yaml"
    if docs.is_file():
        e += valida_documentos(yaml.safe_load(docs.read_text(encoding="utf-8")).get("documentos", []), dominios)
    e += [f"{p.relative_to(raiz)}: no se suben PDF al repositorio (va su URL y su huella)" for p in (raiz / "fuentes").rglob("*.pdf")]
    params = yaml.safe_load((raiz / "base" / "parametros.yaml").read_text(encoding="utf-8"))["parametros"]
    for fila in params.get("ISN_TASA_TABLA", {}).get("valores", [{}])[-1].get("valor", []):
        if fila[0] not in entidades:
            e.append(f"ISN_TASA_TABLA: la entidad {fila[0]!r} no está en fuentes/entidades.yaml")
    return e


def main() -> int:
    errores = valida_repo()
    if errores:
        print(f"APORTACIÓN NO VÁLIDA ({len(errores)}):\n  " + "\n  ".join(errores))
        return 1
    print("Aportación válida: manifiestos, índices, dominios oficiales y entidades en orden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
