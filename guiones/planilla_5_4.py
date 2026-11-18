"""Arma la planilla de clasificación de la sección 5.4 a partir de los issues del proyecto propio.

Lee ``datos/<clave>/issues.csv`` (lo genera exportar_medidas.py) y escribe
``datos/<clave>/planilla-clasificacion.csv``, que cada clasificador copia como
``clasificacion-eric.csv`` o ``clasificacion-brenda.csv`` y completa.

Sigue el protocolo de ``docs/protocolo-5-4.md``:
  * entran todos los issues abiertos, uno por fila;
  * no se incluyen la severidad, el tipo ni el esfuerzo, para que la
    clasificación no se ancle en la opinión de la herramienta;
  * cada fila trae un enlace a la línea en GitHub, en el commit congelado, y
    otro a la descripción de la regla;
  * las filas van ordenadas por archivo y línea, para leer cada archivo una vez.

El CSV se escribe en UTF-8 con BOM para que Excel muestre bien los acentos;
Google Sheets lo importa igual.

Uso:
    python guiones/planilla_5_4.py                    # clave propio-poo2025
    python guiones/planilla_5_4.py --clave propio-otro
"""

from __future__ import annotations

import argparse
import csv
import re

from comun import DIR_DATOS, RAIZ, info, leer_proyecto_propio, salir

COLUMNAS = [
    "n", "clave_issue", "regla", "archivo", "linea", "mensaje",
    "codigo", "descripcion_regla",
    # Columnas que completa cada clasificador (protocolo, sección 4).
    "categoria", "confianza", "nota",
]


def enlace_codigo(repositorio: str, commit: str, subdirectorio: str, archivo: str, linea: str) -> str:
    """Enlace a la línea del issue en GitHub, fijado al commit analizado."""
    ruta = f"{subdirectorio}/{archivo}" if subdirectorio else archivo
    ancla = f"#L{linea}" if linea else ""
    return f"https://github.com/{repositorio}/blob/{commit}/{ruta}{ancla}"


def enlace_regla(regla: str) -> str:
    """Descripción pública de la regla: java:S1234 -> RSPEC-1234."""
    coincidencia = re.fullmatch(r"(\w+):S(\d+)", regla)
    if not coincidencia:
        return ""
    lenguaje, numero = coincidencia.groups()
    return f"https://rules.sonarsource.com/{lenguaje}/RSPEC-{numero}/"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--clave", default="propio-poo2025", help="clave del proyecto propio en SonarQube")
    args = parser.parse_args()

    propios = leer_proyecto_propio()
    if len(propios) != 1:
        salir("corpus/proyecto-propio.csv tiene que tener exactamente una fila")
    propio = propios[0]

    origen = DIR_DATOS / args.clave / "issues.csv"
    if not origen.exists():
        salir(f"No existe {origen.relative_to(RAIZ)}. Corré antes exportar_medidas.py {args.clave}")
    with origen.open(encoding="utf-8", newline="") as archivo:
        issues = list(csv.DictReader(archivo))
    if not issues:
        salir("El proyecto no tiene issues abiertos: no hay nada que clasificar")

    # Orden por archivo y línea (los issues sin línea van primero en su archivo).
    issues.sort(key=lambda i: (i["archivo"], int(i["linea_inicio"] or 0), i["regla"], i["clave_issue"]))

    filas = []
    for numero, issue in enumerate(issues, start=1):
        filas.append({
            "n": numero,
            "clave_issue": issue["clave_issue"],
            "regla": issue["regla"],
            "archivo": issue["archivo"],
            "linea": issue["linea_inicio"],
            "mensaje": issue["mensaje"],
            "codigo": enlace_codigo(propio.repositorio, propio.commit, propio.subdirectorio,
                                    issue["archivo"], issue["linea_inicio"]),
            "descripcion_regla": enlace_regla(issue["regla"]),
            "categoria": "", "confianza": "", "nota": "",
        })

    destino = DIR_DATOS / args.clave / "planilla-clasificacion.csv"
    with destino.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=COLUMNAS)
        escritor.writeheader()
        escritor.writerows(filas)
    archivos = len({f["archivo"] for f in filas})
    reglas = len({f["regla"] for f in filas})
    info(f"Escrito {destino.relative_to(RAIZ)}: {len(filas)} issues en {archivos} archivos, {reglas} reglas")


if __name__ == "__main__":
    main()
