"""SCRUM-22: verifica que cada versión del corpus compila y corre sus tests.

Para cada versión (o las que se filtren) ejecuta, dentro del contenedor de
herramientas (Maven y JDK fijos, ver VERSIONES.md):

    mvn clean verify  +  plugins ajenos al estudio desactivados

Los tests que fallan no cortan el build (``-Dmaven.test.failure.ignore``):
lo que interesa saber es si el proyecto se puede analizar y cuántos tests
tiene, para la cobertura.

Los tests se cuentan con los resúmenes que imprime Maven al terminar cada
ejecución de Surefire (tests unitarios) y de Failsafe (tests de integración).
No se usan los reportes XML de Surefire porque se quedan cortos: las clases de
test anidadas (``@Nested``) definidas en clases abstractas se ejecutan una vez
por subclase y no dejan un XML propio (en commons-collections 4.6.0 faltaban
6.507 de 18.024 tests).

Resultado: ``datos/compilacion.csv`` con una fila por versión, y el log
completo de cada build en ``trabajo/logs/compilacion-<proyecto>-<version>.log``.
El CSV se reescribe al terminar cada versión: si la corrida se corta, las
versiones ya compiladas quedan registradas.

Las columnas de fallas describen el build en este entorno, no la calidad del
proyecto: hay tests que fallan por el entorno (ver ``docs/pruebas-tecnicas.md``,
sección de SCRUM-22).

Uso:
    python guiones/compilar_corpus.py
    python guiones/compilar_corpus.py --proyecto jfreechart
    python guiones/compilar_corpus.py --sin-tests   # solo compila
    python guiones/compilar_corpus.py --recontar    # recuenta desde los logs, sin compilar
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
from datetime import datetime
from pathlib import Path

from comun import (
    DIR_DATOS,
    DIR_LOGS,
    OMITIR_PLUGINS_AJENOS,
    VersionCorpus,
    aviso,
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
    "tests_integracion", "fallas_integracion", "fecha", "log",
]

# Encabezado con que Maven anuncia cada ejecución de un plugin, por ejemplo
# "[INFO] --- surefire:3.5.6:test (default-test) @ jsoup ---".
PATRON_PLUGIN = re.compile(r"^\[INFO\] --- (?P<plugin>[\w.-]+):")
# Resumen de una ejecución de Surefire o Failsafe. Las líneas por clase de test
# siguen con ", Time elapsed: ..." y no coinciden porque el patrón exige que la
# línea termine después de "Skipped" (o de "Flakes", si hay reintentos).
PATRON_RESUMEN = re.compile(
    r"^\[(?:INFO|WARNING|ERROR)\] Tests run: (?P<tests>\d+), Failures: (?P<fallas>\d+), "
    r"Errors: (?P<errores>\d+), Skipped: (?P<omitidos>\d+)(?:, Flakes: \d+)?\s*$"
)


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


def contar_tests(ruta_log: Path) -> dict[str, int]:
    """Suma los resúmenes de Surefire y Failsafe de un log de Maven.

    En un proyecto de varios módulos hay un resumen por módulo y se suman.
    Cada resumen se atribuye al último plugin anunciado antes que él: los de
    Failsafe son tests de integración y todo lo demás, tests unitarios.
    """
    totales = {
        "tests": 0, "fallas": 0, "errores": 0, "omitidos": 0,
        "tests_integracion": 0, "fallas_integracion": 0,
    }
    plugin_actual = ""
    with ruta_log.open(encoding="utf-8", errors="replace") as log:
        for linea in log:
            if encabezado := PATRON_PLUGIN.match(linea):
                plugin_actual = encabezado.group("plugin")
                continue
            resumen = PATRON_RESUMEN.match(linea)
            if not resumen:
                continue
            numeros = {clave: int(valor) for clave, valor in resumen.groupdict().items()}
            if plugin_actual == "failsafe":
                totales["tests_integracion"] += numeros["tests"]
                totales["fallas_integracion"] += numeros["fallas"] + numeros["errores"]
            else:
                for clave in ("tests", "fallas", "errores", "omitidos"):
                    totales[clave] += numeros[clave]
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
    fila.update(contar_tests(ruta_log))
    info(
        f"  {fila['resultado']} en {fila['duracion_s']} s: {fila['tests']} tests, "
        f"{fila['fallas']} fallas, {fila['errores']} errores, {fila['omitidos']} omitidos, "
        f"{fila['tests_integracion']} de integración"
    )
    return fila


def recontar(version: VersionCorpus, previa: dict | None) -> dict | None:
    """Vuelve a contar los tests de una versión ya compilada a partir de su log.

    Conserva lo demás de la fila anterior (resultado, duración, fecha). No
    necesita Docker ni vuelve a compilar.
    """
    if previa is None:
        aviso(f"{version.proyecto} {version.version}: no hay fila previa en el CSV, se omite")
        return None
    ruta_log = DIR_LOGS / previa.get("log", "")
    if not previa.get("log") or not ruta_log.exists():
        aviso(f"{version.proyecto} {version.version}: no está el log {previa.get('log')}, se omite")
        return None
    fila = dict(previa)
    fila.update(contar_tests(ruta_log))
    info(
        f"{version.proyecto} {version.version}: {fila['tests']} tests "
        f"(antes {previa.get('tests', '?')}), {fila['tests_integracion']} de integración"
    )
    return fila


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--proyecto")
    parser.add_argument("--version")
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument("--sin-tests", action="store_true", help="compilar sin ejecutar los tests")
    modo.add_argument("--recontar", action="store_true", help="recontar los tests desde los logs, sin compilar")
    args = parser.parse_args()

    versiones = filtrar_corpus(args.proyecto, args.version)
    if not versiones:
        salir("El filtro no coincide con ninguna fila de corpus/corpus.csv")

    # Si ya hay resultados de otras versiones, se conservan y se actualizan las corridas ahora.
    previas: dict[tuple[str, str], dict] = {}
    if ARCHIVO_RESULTADO.exists():
        with ARCHIVO_RESULTADO.open(encoding="utf-8", newline="") as archivo:
            previas = {(f["proyecto"], f["version"]): f for f in csv.DictReader(archivo)}

    if args.recontar:
        for version in versiones:
            clave = (version.proyecto, version.version)
            if fila := recontar(version, previas.get(clave)):
                previas[clave] = fila
        escribir_csv(ARCHIVO_RESULTADO, list(previas.values()), COLUMNAS)
        return

    jdk, maven = versiones_de_herramientas()
    info(f"Contenedor de herramientas: Maven {maven}, JDK {jdk}")

    for version in versiones:
        previas[(version.proyecto, version.version)] = compilar(version, jdk, maven, args.sin_tests)
        # Se guarda después de cada versión para no perder lo hecho si se corta la corrida.
        escribir_csv(ARCHIVO_RESULTADO, list(previas.values()), COLUMNAS)


if __name__ == "__main__":
    main()
