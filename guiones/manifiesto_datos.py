"""Genera ``datos/MANIFIESTO.md``: de qué análisis sale cada CSV de ``datos/`` (SCRUM-31).

Para cada carpeta de ``datos/`` lista sus archivos con la cantidad de filas y la
huella SHA-256, y la cruza con ``datos/registro_analisis.csv`` (clave de
SonarQube, versión, commit, perfil, fecha, tests y cobertura). Las versiones de
las herramientas están en ``VERSIONES.md`` y la configuración de la instancia en
``laboratorio/configuracion/``.

El manifiesto se versiona junto con los datos y el tag ``datos-corpus-v1``:
cualquiera puede comprobar que tiene los mismos datos volviendo a correr este
guion y comparando las huellas.

Uso:
    python guiones/manifiesto_datos.py
"""

from __future__ import annotations

import csv
import hashlib
from collections import defaultdict
from datetime import date

from comun import DIR_DATOS, RAIZ, info

DESTINO = DIR_DATOS / "MANIFIESTO.md"


def huella(ruta) -> str:
    """SHA-256 del archivo con los fines de línea normalizados a LF.

    El repositorio guarda los archivos de texto con LF (``.gitattributes``),
    pero en Windows los CSV que escribe Python quedan con CRLF en la copia de
    trabajo. Normalizando, la huella es la misma en cualquier clon.
    """
    contenido = ruta.read_bytes()
    if ruta.suffix.lower() in {".csv", ".md", ".txt", ".json"}:
        contenido = contenido.replace(b"\r\n", b"\n")
    return hashlib.sha256(contenido).hexdigest()


def filas(ruta) -> int:
    with ruta.open(encoding="utf-8", errors="replace") as archivo:
        return max(sum(1 for _ in archivo) - 1, 0)


def main() -> None:
    with (DIR_DATOS / "registro_analisis.csv").open(encoding="utf-8", newline="") as archivo:
        registro = list(csv.DictReader(archivo))
    por_clave = defaultdict(list)
    for r in registro:
        por_clave[r["clave"]].append(r)

    lineas = [
        "# Manifiesto de `datos/`",
        "",
        f"Generado el {date.today().isoformat()} con `guiones/manifiesto_datos.py`. No editar a mano.",
        "",
        "Cada carpeta se cruza con `registro_analisis.csv` por la clave de SonarQube. Las carpetas `extraccion-*`, "
        "`pmd-*` y `diff-*` salen del release nuevo de cada proyecto (SCRUM-29 y PT3). Versiones de las herramientas "
        "en `VERSIONES.md`; perfiles, gate y parámetros de la instancia en `laboratorio/configuracion/`.",
        "",
    ]
    for carpeta in sorted(p for p in DIR_DATOS.iterdir() if p.is_dir()):
        lineas += [f"## `{carpeta.name}/`", ""]
        analisis = por_clave.get(carpeta.name, [])
        if analisis:
            lineas += ["| Fecha | Versión | Commit | Perfil | Tests | JaCoCo | Resultado |", "|---|---|---|---|---|---|---|"]
            lineas += [f"| {a['fecha']} | {a['version']} | `{a['commit'][:12]}` | {a['perfil']} | {a['tests']} | "
                       f"{a['jacoco']} | {a['resultado']} |" for a in analisis]
            lineas.append("")
        lineas += ["| Archivo | Filas | SHA-256 |", "|---|---|---|"]
        for ruta in sorted(carpeta.rglob("*")):
            if ruta.is_file():
                lineas.append(f"| `{ruta.relative_to(carpeta).as_posix()}` | {filas(ruta)} | `{huella(ruta)}` |")
        lineas.append("")
    lineas += ["## Archivos sueltos", "", "| Archivo | Filas | SHA-256 |", "|---|---|---|"]
    for ruta in sorted(p for p in DIR_DATOS.iterdir() if p.is_file() and p.name != DESTINO.name):
        lineas.append(f"| `{ruta.name}` | {filas(ruta)} | `{huella(ruta)}` |")
    DESTINO.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    info(f"Escrito {DESTINO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
