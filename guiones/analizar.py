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

Cobertura (``--jacoco``, prueba técnica 4, decisión D2 bis). El agente de
JaCoCo entra por la variable de entorno ``JAVA_TOOL_OPTIONS``, que lee toda JVM
que arranca, incluidas las que lanzan Surefire y Failsafe para los tests. No se
usa la propiedad ``argLine`` del plugin de JaCoCo porque cada pom la trata
distinto: jsoup fija un ``argLine`` literal que la pisa (los tests unitarios
corrían sin agente) y los proyectos de Apache Commons activan su propio
JaCoCo, con lo que quedaban dos agentes y un ``jacoco:check`` que podía cortar
el build. Así el instrumento es el mismo en todo el corpus:

  1. ``mvn clean`` sin agente.
  2. ``mvn verify`` con el agente en el entorno y ``-Djacoco.skip=true``, que
     apaga el JaCoCo propio del proyecto. El agente solo instrumenta el paquete
     raíz del proyecto (ver paquete_raiz), no Maven ni el compilador.
  3. Reporte XML con la CLI de JaCoCo, de la misma versión que el agente.
  4. Escáner de SonarQube apuntado a ese reporte. Corre con las fases hasta
     ``process-test-resources`` para que el modelo del proyecto tenga las mismas
     carpetas de código que en la invocación única sin cobertura.

Después se cuentan las sesiones del reporte (una por JVM con agente): si hay
una sola, ninguna JVM de tests tuvo el agente y el análisis se marca con aviso.

Uso:
    python guiones/analizar.py jsoup 1.23.2 --clave prueba-pt1-jsoup
    python guiones/analizar.py jsoup 1.22.2 --fecha 2026-01-10
    python guiones/analizar.py commons-io 2.22.0 --jacoco
"""

from __future__ import annotations

import argparse
import re
import shlex
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from comun import (
    DIR_DATOS,
    DIR_TRABAJO,
    DIR_LOGS,
    OMITIR_PLUGINS_AJENOS,
    URL_SONAR_DESDE_CONTENEDOR,
    agregar_fila_csv,
    aviso,
    buscar_version,
    config,
    correr_en_herramientas,
    info,
    salir,
)

# Versiones fijadas de los plugins de Maven que se invocan por coordenada completa,
# para no depender de lo que declare (o no) el pom de cada proyecto.
PLUGIN_SONAR = "org.sonarsource.scanner.maven:sonar-maven-plugin:5.8.0.7211:sonar"
VERSION_JACOCO = "0.8.15"
PLUGIN_DEPENDENCY = "org.apache.maven.plugins:maven-dependency-plugin:3.8.1:get"
# El agente y la CLI de JaCoCo se descargan al repositorio de Maven del
# contenedor (volumen maven_repositorio) y se usan desde ahí.
REPO_MAVEN_CONTENEDOR = "/root/.m2/repository"
ARTEFACTOS_JACOCO = {
    "agente": f"org.jacoco:org.jacoco.agent:{VERSION_JACOCO}:jar:runtime",
    "cli": f"org.jacoco:org.jacoco.cli:{VERSION_JACOCO}:jar:nodeps",
}
JAR_AGENTE = (f"{REPO_MAVEN_CONTENEDOR}/org/jacoco/org.jacoco.agent/{VERSION_JACOCO}/"
              f"org.jacoco.agent-{VERSION_JACOCO}-runtime.jar")
JAR_CLI = (f"{REPO_MAVEN_CONTENEDOR}/org/jacoco/org.jacoco.cli/{VERSION_JACOCO}/"
           f"org.jacoco.cli-{VERSION_JACOCO}-nodeps.jar")
# Rutas relativas a la carpeta del checkout.
EJECUCION_JACOCO = "target/jacoco-tp.exec"
REPORTE_JACOCO = "target/site/jacoco-tp/jacoco.xml"

REGISTRO = DIR_DATOS / "registro_analisis.csv"
COLUMNAS_REGISTRO = [
    "fecha", "clave", "proyecto", "version", "commit", "fecha_analisis",
    "tests", "jacoco", "resultado", "duracion_s", "log",
]


def clave_por_defecto(proyecto: str) -> str:
    return f"corpus-{proyecto}"


def paquete_raiz(directorio: Path) -> str:
    """Paquete raíz del código principal: la carpeta más profunda de src/main/java sin bifurcaciones.

    Baja desde ``src/main/java`` mientras haya una sola subcarpeta y ningún
    archivo .java. En el corpus da ``org.jsoup``, ``org.apache.commons.io``,
    ``org.apache.commons.collections4`` y ``org.jfree``. Se usa como filtro del
    agente para no instrumentar Maven, el compilador ni el escáner.
    """
    carpeta = directorio / "src" / "main" / "java"
    partes: list[str] = []
    while True:
        subcarpetas = [c for c in carpeta.iterdir() if c.is_dir()]
        if len(subcarpetas) != 1 or any(carpeta.glob("*.java")):
            break
        carpeta = subcarpetas[0]
        partes.append(carpeta.name)
    if not partes:
        salir(f"No se pudo determinar el paquete raíz de {directorio}")
    return ".".join(partes)


def linea_shell(comando: list[str], entorno: dict[str, str] | None = None) -> str:
    """Un comando como línea de bash, con cada argumento entre comillas si hace falta."""
    prefijo = " ".join(f"{k}={shlex.quote(v)}" for k, v in (entorno or {}).items())
    return (prefijo + " " if prefijo else "") + " ".join(shlex.quote(a) for a in comando)


def guion_con_jacoco(version, comando_verify: list[str], comando_sonar: list[str]) -> list[str]:
    """Arma el guion de bash que mide cobertura con el agente en el entorno (ver el docstring del módulo)."""
    base = version.directorio_contenedor
    agente = (f"-javaagent:{JAR_AGENTE}=destfile={base}/{EJECUCION_JACOCO},append=true,"
              f"includes={paquete_raiz(version.directorio)}.*")
    descargas = [
        ["mvn", "-B", "-q", PLUGIN_DEPENDENCY, f"-Dartifact={coordenada}", "-Dtransitive=false"]
        for coordenada in ARTEFACTOS_JACOCO.values()
    ]
    reporte = [
        "java", "-jar", JAR_CLI, "report", EJECUCION_JACOCO,
        "--classfiles", "target/classes", "--sourcefiles", "src/main/java",
        "--xml", REPORTE_JACOCO,
    ]
    lineas = [
        "set -e",
        *(linea_shell(d) for d in descargas),
        linea_shell(["mvn", "-B", "-Dstyle.color=never", "clean"]),
        # La variable de entorno se define solo para este comando: la CLI y el
        # escáner corren sin agente.
        linea_shell(comando_verify, {"JAVA_TOOL_OPTIONS": agente}),
        # La CLI no crea la carpeta del reporte (lo mostró la primera corrida de la PT4).
        linea_shell(["mkdir", "-p", REPORTE_JACOCO.rsplit("/", 1)[0]]),
        linea_shell(reporte),
        linea_shell(comando_sonar),
    ]
    return ["bash", "-c", "\n".join(lineas)]


def revisar_reporte_jacoco(directorio: Path) -> bool:
    """Resume el reporte de JaCoCo y avisa si ninguna JVM de tests tuvo el agente.

    JaCoCo registra una sesión por JVM que corrió con el agente. Una es la de
    Maven; las demás, las de los tests. Con una sola sesión, la cobertura no
    viene de los tests (es lo que pasaba en jsoup con argLine). Devuelve si
    el reporte es utilizable.
    """
    ruta = directorio / REPORTE_JACOCO
    if not ruta.exists():
        aviso(f"No se generó el reporte de JaCoCo ({REPORTE_JACOCO})")
        return False
    # El reporte declara un DTD externo que no hace falta para leerlo.
    texto = re.sub(r"<!DOCTYPE[^>]*>", "", ruta.read_text(encoding="utf-8"))
    raiz = ET.fromstring(texto)
    sesiones = len(raiz.findall("sessioninfo"))
    lineas = next((c for c in raiz.findall("counter") if c.get("type") == "LINE"), None)
    resumen = f"{sesiones} sesiones"
    if lineas is not None:
        cubiertas, faltantes = int(lineas.get("covered")), int(lineas.get("missed"))
        resumen += f", {cubiertas}/{cubiertas + faltantes} líneas cubiertas según JaCoCo"
    info(f"JaCoCo: {resumen}")
    if sesiones < 2:
        aviso("El reporte tiene una sola sesión: ninguna JVM de tests corrió con el agente")
    return sesiones >= 2


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

    propiedades_sonar = [
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
        propiedades_sonar.append(f"-Dsonar.projectDate={args.fecha}")
    opciones_tests = ["-DskipTests=true" if args.sin_tests else "-Dmaven.test.failure.ignore=true"]

    if args.jacoco:
        comando_verify = ["mvn", "-B", "-Dstyle.color=never", "verify", *OMITIR_PLUGINS_AJENOS,
                          *opciones_tests, "-Djacoco.skip=true"]
        # El escáner corre en otra invocación de Maven. Las carpetas de código que
        # agregan plugins como build-helper existen solo dentro de la invocación en
        # que corrió su fase, así que se repiten las fases hasta
        # process-test-resources. Esas fases incluyen compile, que no recompila
        # porque las clases están al día; y aunque recompilara, el reporte de
        # JaCoCo ya está generado y se importa por archivo y línea. Sin esto, en
        # jsoup se perdía src/test/java11 (lo mostró la PT4).
        comando_sonar = ["mvn", "-B", "-Dstyle.color=never", "process-test-resources", PLUGIN_SONAR,
                         *OMITIR_PLUGINS_AJENOS, "-Djacoco.skip=true", *propiedades_sonar,
                         f"-Dsonar.coverage.jacoco.xmlReportPaths={REPORTE_JACOCO}"]
        comando = guion_con_jacoco(version, comando_verify, comando_sonar)
    else:
        # Sin cobertura, un solo comando de Maven (como en las pruebas 1 a 3).
        comando = ["mvn", "-B", "-Dstyle.color=never", "clean", "verify", PLUGIN_SONAR,
                   *OMITIR_PLUGINS_AJENOS, *opciones_tests, *propiedades_sonar]

    momento = datetime.now()
    ruta_log = DIR_LOGS / f"analisis-{clave}-{version.version}-{momento:%Y%m%d-%H%M%S}.log"
    info(f"Analizando {version.proyecto} {version.version} como '{clave}' (log: {ruta_log.name})")
    # El token viaja como variable de entorno (SONAR_TOKEN), que el escáner lee
    # solo; así no queda escrito en la línea de comandos ni en el log.
    codigo, duracion = correr_en_herramientas(
        comando, version.directorio_contenedor, ruta_log, variables={"SONAR_TOKEN": token}
    )

    # Con qualitygate.wait, un gate rechazado devuelve código distinto de 0 aunque
    # el análisis haya terminado bien: se distingue leyendo el log. El escáner
    # solo informa el estado del gate después de que el servidor procesó el
    # reporte, así que esa línea alcanza para saber que el análisis quedó
    # publicado. (La versión anterior buscaba además "ANALYSIS SUCCESSFUL", que
    # el escáner de Maven 5.x ya no imprime: lo mostró la prueba técnica 3.)
    log = ruta_log.read_text(encoding="utf-8", errors="replace")
    if "QUALITY GATE STATUS: FAILED" in log:
        resultado = "ok (gate rechazado)"
    elif codigo == 0:
        resultado = "ok"
    else:
        resultado = f"falla (código {codigo})"
    if args.jacoco and not resultado.startswith("falla"):
        if not revisar_reporte_jacoco(version.directorio):
            resultado += ", cobertura dudosa"

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
