"""SCRUM-22: verifica que cada versión del corpus compila y corre sus tests.

Para cada versión (o las que se filtren) ejecuta, dentro del contenedor de
herramientas (Maven y JDK fijos, ver VERSIONES.md):

    mvn clean verify  +  plugins ajenos al estudio desactivados

Los tests que fallan no cortan el build (``-Dmaven.test.failure.ignore``):
se cuentan a partir de los reportes de Surefire, porque lo que interesa saber
es si el proyecto se puede analizar y con qué cobertura de tests.

Resultado: ``datos/compilacion.csv`` con una fila por versión, y el log
completo de cada build en ``trabajo/logs/compilacion-<proyecto>-<version>.log``.
El CSV se reescribe al terminar cada versión: si la corrida se corta, las
versiones ya compiladas quedan registradas.

Las columnas ``fallas`` y ``errores`` describen el build en este entorno, no la
calidad del proyecto: hay tests que fallan por el entorno (ver
``docs/pruebas-tecnicas.md``, sección de SCRUM-22).

Uso:
    python guiones/compilar_corpus.py
    python guiones/compilar_corpus.py --proyecto jfreechart
    python guiones/compilar_corpus.py --sin-tests   # solo compila
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from comun import (
    DIR_DATOS,
    DIR_LOGS,
    OMITIR_PLUGINS_AJENOS,
    VersionCorpus,
    comando_compose,
    correr_en_herramientas,
    escribir_csv,
    filtrar_corpus,
    info,
    salir,
)

ARCHIVO_RESULTADO = DIR_DATOS / "compilacion.csv"
COLUMNAS = [
    "proyecto", "version", "tag", "commit", "jdk", "maven",
    "resultado", "duracion_s", "tests", "fallas", "errores", "omitidos",
    "fecha", "log",
]


def versiones_de_herramientas() -> tuple[str, str]:
    """Versión de JDK y de Maven del contenedor de herramientas, para registrarlas."""
    resultado = subprocess.run(
        comando_compose("run", "--rm", "-T", "herramientas", "mvn", "-v"),
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    if resultado.returncode != 0:
        salir("No se pudo ejecutar Maven en el contenedor. ¿Está corriendo Docker?\n" + resultado.stderr)
    maven = jdk = "desconocida"
    for linea in resultado.stdout.splitlines():
        if linea.startswith("Apache Maven"):
            maven = linea.split()[2]
        elif linea.startswith("Java version:"):
            jdk = linea.split(":", 1)[1].split(",")[0].strip()
    return jdk, maven


def contar_tests(directorio: Path) -> dict[str, int]:
    """Suma los totales de todos los reportes de Surefire del proyecto (todos los módulos)."""
    totales = {"tests": 0, "fallas": 0, "errores": 0, "omitidos": 0}
    for reporte in directorio.rglob("surefire-reports/TEST-*.xml"):
        try:
            raiz = ET.parse(reporte).getroot()
        except ET.ParseError:
            continue  # reporte truncado por un test que mató la JVM: se ignora
        totales["tests"] += int(raiz.get("tests", 0))
        totales["fallas"] += int(raiz.get("failures", 0))
        totales["errores"] += int(raiz.get("errors", 0))
        totales["omitidos"] += int(raiz.get("skipped", 0))
    return totales


def compilar(version: VersionCorpus, jdk: str, maven: str, sin_tests: bool) -> dict:
    if not (version.directorio / "pom.xml").exists():
        salir(f"No está el checkout de {version.proyecto} {version.version}. Corré antes clonar_corpus.py.")

    comando = ["mvn", "-B", "-Dstyle.color=never", "clean", "verify", *OMITIR_PLUGINS_AJENOS]
    comando.append("-DskipTests=true" if sin_tests else "-Dmaven.test.failure.ignore=true")

    ruta_log = DIR_LOGS / f"compilacion-{version.proyecto}-{version.version}.log"
    info(f"Compilando {version.proyecto} {version.version} (log: {ruta_log.name})")
    codigo, duracion = correr_en_herramientas(comando, version.directorio_contenedor, ruta_log)

    fila = {
        "proyecto": version.proyecto,
        "version": version.version,
        "tag": version.tag,
        "commit": version.commit,
        "jdk": jdk,
        "maven": maven,
        "resultado": "ok" if codigo == 0 else f"falla (código {codigo})",
        "duracion_s": round(duracion),
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "log": ruta_log.name,
    }
    fila.update(contar_tests(version.directorio))
    info(
        f"  {fila['resultado']} en {fila['duracion_s']} s: {fila['tests']} tests, "
        f"{fila['fallas']} fallas, {fila['errores']} errores, {fila['omitidos']} omitidos"
    )
    return fila


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--proyecto")
    parser.add_argument("--version")
    parser.add_argument("--sin-tests", action="store_true", help="compilar sin ejecutar los tests")
    args = parser.parse_args()

    versiones = filtrar_corpus(args.proyecto, args.version)
    if not versiones:
        salir("El filtro no coincide con ninguna fila de corpus/corpus.csv")

    jdk, maven = versiones_de_herramientas()
    info(f"Contenedor de herramientas: Maven {maven}, JDK {jdk}")

    # Si ya hay resultados de otras versiones, se conservan y se actualizan las corridas ahora.
    previas: dict[tuple[str, str], dict] = {}
    if ARCHIVO_RESULTADO.exists():
        with ARCHIVO_RESULTADO.open(encoding="utf-8", newline="") as archivo:
            previas = {(f["proyecto"], f["version"]): f for f in csv.DictReader(archivo)}

    for version in versiones:
        previas[(version.proyecto, version.version)] = compilar(version, jdk, maven, args.sin_tests)
        # Se guarda después de cada versión para no perder lo hecho si se corta la corrida.
        escribir_csv(ARCHIVO_RESULTADO, list(previas.values()), COLUMNAS)


if __name__ == "__main__":
    main()
