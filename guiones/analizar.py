"""Analiza una versión del corpus con SonarQube.

Compila la versión dentro del contenedor de herramientas y lanza el escáner de
Maven (versión fijada en VERSIONES.md) contra la instancia del laboratorio.
Cada análisis queda registrado en ``datos/registro_analisis.csv`` con fecha,
duración, clave de proyecto y opciones usadas.

Claves de proyecto en SonarQube (decisiones D1 y D2):
  * ``corpus-<proyecto>``: análisis principal. Los dos releases de un proyecto
    se analizan bajo la MISMA clave, primero el viejo y después el nuevo, para
    que el código nuevo del Quality Gate sea la diferencia entre ambos.
  * ``extraccion-<proyecto>``: análisis aparte con el perfil de extracción de
    complejidad por método (no contamina la deuda técnica del principal).
  * ``prueba-*``: pruebas técnicas; se pueden borrar sin perder nada.

Uso:
    python guiones/analizar.py jsoup 1.23.2 --clave prueba-pt1-jsoup
    python guiones/analizar.py jsoup 1.22.2 --fecha 2026-01-10
    python guiones/analizar.py commons-io 2.22.0 --jacoco
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime

from comun import (
    DIR_DATOS,
    DIR_LOGS,
    OMITIR_PLUGINS_AJENOS,
    URL_SONAR_DESDE_CONTENEDOR,
    agregar_fila_csv,
    buscar_version,
    config,
    correr_en_herramientas,
    info,
    salir,
)

# Versiones fijadas de los plugins de Maven que se invocan por coordenada completa,
# para no depender de lo que declare (o no) el pom de cada proyecto.
PLUGIN_SONAR = "org.sonarsource.scanner.maven:sonar-maven-plugin:5.8.0.7211:sonar"
PLUGIN_JACOCO = "org.jacoco:jacoco-maven-plugin:0.8.15"

REGISTRO = DIR_DATOS / "registro_analisis.csv"
COLUMNAS_REGISTRO = [
    "fecha", "clave", "proyecto", "version", "commit", "fecha_analisis",
    "tests", "jacoco", "resultado", "duracion_s", "log",
]


def clave_por_defecto(proyecto: str) -> str:
    return f"corpus-{proyecto}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("proyecto")
    parser.add_argument("version")
    parser.add_argument("--clave", help="clave del proyecto en SonarQube (por defecto corpus-<proyecto>)")
    parser.add_argument(
        "--fecha",
        help="fecha del análisis (AAAA-MM-DD), para fecharlo en el pasado (prueba técnica 3). "
        "SonarQube exige que sea posterior al último análisis de esa clave.",
    )
    parser.add_argument("--sin-tests", action="store_true", help="no ejecutar los tests (más rápido, sin cobertura)")
    parser.add_argument("--jacoco", action="store_true", help="medir cobertura con JaCoCo e importarla (prueba técnica 4)")
    args = parser.parse_args()

    if args.fecha and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.fecha):
        salir("--fecha tiene que tener el formato AAAA-MM-DD")
    if args.jacoco and args.sin_tests:
        salir("--jacoco necesita ejecutar los tests: no se puede combinar con --sin-tests")

    version = buscar_version(args.proyecto, args.version)
    if not (version.directorio / "pom.xml").exists():
        salir(f"No está el checkout de {version.proyecto} {version.version}. Corré antes clonar_corpus.py.")

    token = config().get("SONAR_TOKEN")
    if not token:
        salir("Falta SONAR_TOKEN en laboratorio/.env. Corré antes preparar_sonarqube.py.")

    clave = args.clave or clave_por_defecto(version.proyecto)

    comando = ["mvn", "-B", "-Dstyle.color=never", "clean"]
    if args.jacoco:
        comando.append(f"{PLUGIN_JACOCO}:prepare-agent")
    comando.append("verify")
    if args.jacoco:
        # El reporte XML queda en target/site/jacoco/jacoco.xml, ruta que el
        # escáner de Java toma por defecto.
        comando.append(f"{PLUGIN_JACOCO}:report")
    comando.append(PLUGIN_SONAR)
    comando += OMITIR_PLUGINS_AJENOS
    comando.append("-DskipTests=true" if args.sin_tests else "-Dmaven.test.failure.ignore=true")
    comando += [
        f"-Dsonar.host.url={URL_SONAR_DESDE_CONTENEDOR}",
        f"-Dsonar.projectKey={clave}",
        f"-Dsonar.projectName={clave}",
        f"-Dsonar.projectVersion={version.version}",
        # Se registra el commit analizado como dato del análisis en SonarQube.
        f"-Dsonar.analysis.commit={version.commit}",
        # Sin esto, el escáner espera a que el servidor procese el reporte; con
        # qualitygate.wait el comando no termina hasta tener el resultado del gate.
        "-Dsonar.qualitygate.wait=true",
        "-Dsonar.qualitygate.timeout=900",
    ]
    if args.fecha:
        comando.append(f"-Dsonar.projectDate={args.fecha}")

    momento = datetime.now()
    ruta_log = DIR_LOGS / f"analisis-{clave}-{version.version}-{momento:%Y%m%d-%H%M%S}.log"
    info(f"Analizando {version.proyecto} {version.version} como '{clave}' (log: {ruta_log.name})")
    # El token viaja como variable de entorno (SONAR_TOKEN), que el escáner lee
    # solo; así no queda escrito en la línea de comandos ni en el log.
    codigo, duracion = correr_en_herramientas(
        comando, version.directorio_contenedor, ruta_log, variables={"SONAR_TOKEN": token}
    )

    # Con qualitygate.wait, un gate rechazado devuelve código distinto de 0 aunque
    # el análisis haya terminado bien: se distingue leyendo el log.
    log = ruta_log.read_text(encoding="utf-8", errors="replace")
    if "ANALYSIS SUCCESSFUL" in log and "QUALITY GATE STATUS: FAILED" in log:
        resultado = "ok (gate rechazado)"
    elif codigo == 0:
        resultado = "ok"
    else:
        resultado = f"falla (código {codigo})"

    agregar_fila_csv(
        REGISTRO,
        {
            "fecha": momento.isoformat(timespec="seconds"),
            "clave": clave,
            "proyecto": version.proyecto,
            "version": version.version,
            "commit": version.commit,
            "fecha_analisis": args.fecha or "",
            "tests": "no" if args.sin_tests else "sí",
            "jacoco": "sí" if args.jacoco else "no",
            "resultado": resultado,
            "duracion_s": round(duracion),
            "log": ruta_log.name,
        },
        COLUMNAS_REGISTRO,
    )
    info(f"Resultado: {resultado} en {round(duracion)} s")
    if resultado.startswith("falla"):
        salir(f"El análisis falló. Revisá trabajo/logs/{ruta_log.name}")


if __name__ == "__main__":
    main()
