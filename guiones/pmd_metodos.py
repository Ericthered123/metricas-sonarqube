"""Segunda implementación de las complejidades por método, con PMD (eje 2, SCRUM-23).

SonarQube no informa el tamaño de cada método y, según la prueba técnica 2, no
calcula la complejidad cognitiva de los métodos declarados en constantes de enum
y clases anónimas. PMD calcula la complejidad ciclomática, la cognitiva y el
tamaño en sentencias (NCSS) de cada método, y su reporte trae las líneas de
inicio y fin. Sirve para tres cosas: obtener el tamaño, contrastar las dos
complejidades contra una implementación independiente y confirmar (o refutar)
por otra vía el hallazgo de la cognitiva no medida.

Subcomandos:
    instalar   descarga la distribución de PMD (versión fija) en trabajo/herramientas/
    correr     corre PMD sobre el código principal de una versión del corpus,
               dentro del contenedor de herramientas, y deja el reporte XML en
               trabajo/pmd/<proyecto>-<version>.xml
    exportar   convierte el reporte en datos/pmd-<proyecto>-<version>/metodos.csv
               y, si existe la extracción de SonarQube de la misma versión, escribe
               la tabla del eje 2 en datos/extraccion-<proyecto>/eje2_metodos.csv

Uso:
    python guiones/pmd_metodos.py instalar
    python guiones/pmd_metodos.py correr jsoup 1.23.2
    python guiones/pmd_metodos.py exportar jsoup 1.23.2

Cómo se leen los valores (verificado en la prueba técnica 2, jsoup 1.23.2):
* Las tres reglas informan en la línea del nombre del método (beginline y
  endline son iguales), la misma que usa SonarQube: el cruce es por archivo y
  línea, y en jsoup coincidieron los 2.088 métodos.
* CyclomaticComplexity y NcssCount informan todos los métodos (umbral 1).
  CognitiveComplexity solo los que valen 1 o más: si un método aparece por las
  otras reglas y no por esta, su cognitiva es 0.
* El tamaño del método es el NCSS (sentencias sin comentarios ni líneas en
  blanco): PMD no informa la línea final del método.

PMD corre sobre el código fuente: no necesita SonarQube ni compilar. El
conjunto de reglas está en laboratorio/pmd-metodos.xml.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import shutil
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

from comun import (
    DIR_DATOS,
    DIR_LOGS,
    DIR_TRABAJO,
    DIR_TRABAJO_CONTENEDOR,
    RAIZ,
    aviso,
    buscar_version,
    correr_en_herramientas,
    escribir_csv,
    info,
    salir,
)

# Versión fijada (ver VERSIONES.md). La 7.26.0 es la estable vigente al 2026-10-13.
VERSION_PMD = "7.26.0"
URL_PMD = (
    f"https://github.com/pmd/pmd/releases/download/pmd_releases%2F{VERSION_PMD}/"
    f"pmd-dist-{VERSION_PMD}-bin.zip"
)
# Huella SHA-256 del zip, anotada el 2026-10-13 y verificada con dos descargas
# independientes. Una descarga con otra huella se rechaza (ver VERSIONES.md).
SHA256_PMD: str | None = "9f55cb7ff0e9f9a66dd2f005eaa370e84c8a4cd971b134aa14a930c4a283ebc9"

DIR_HERRAMIENTAS = DIR_TRABAJO / "herramientas"
DIR_REPORTES = DIR_TRABAJO / "pmd"
ARCHIVO_REGLAS = RAIZ / "laboratorio" / "pmd-metodos.xml"

# PMD termina con código 4 cuando encuentra infracciones: acá eso es lo esperado.
CODIGOS_OK = {0, 4}

ESPACIO_REPORTE = {"p": "http://pmd.sourceforge.net/report/2.0.0"}
# Valor que trae el mensaje de cada regla, por ejemplo
# "The method 'clean(String, String, Safelist)' has a cognitive complexity of 2, current threshold is 1".
PATRONES = {
    "CyclomaticComplexity": re.compile(r"cyclomatic complexity of (\d+)"),
    "CognitiveComplexity": re.compile(r"cognitive complexity of (\d+)"),
    "NcssCount": re.compile(r"NCSS line count of (\d+)"),
}
COLUMNA = {"CyclomaticComplexity": "ciclomatica_pmd", "CognitiveComplexity": "cognitiva_pmd", "NcssCount": "ncss_pmd"}
COLUMNAS_PMD = ["archivo", "linea", "metodo", "tipo", "ciclomatica_pmd", "cognitiva_pmd", "ncss_pmd"]
COLUMNAS_EJE2 = [
    "archivo", "linea", "metodo",
    "ciclomatica_sonar", "cognitiva_sonar", "cognitiva_origen",
    "ciclomatica_pmd", "cognitiva_pmd", "ncss_pmd",
]
ARCHIVO_REGISTRO = DIR_DATOS / "registro_analisis.csv"


def carpeta_pmd():
    """Carpeta de la distribución instalada (la que contiene bin/pmd), o None."""
    for candidata in sorted(DIR_HERRAMIENTAS.glob(f"pmd-*{VERSION_PMD}*")):
        if (candidata / "bin" / "pmd").exists():
            return candidata
    return None


def sha256(ruta) -> str:
    resumen = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1 << 20), b""):
            resumen.update(bloque)
    return resumen.hexdigest()


def instalar() -> None:
    if (existente := carpeta_pmd()) is not None:
        info(f"PMD {VERSION_PMD} ya está instalado en {existente.relative_to(RAIZ)}")
        return
    DIR_HERRAMIENTAS.mkdir(parents=True, exist_ok=True)
    zip_pmd = DIR_HERRAMIENTAS / f"pmd-dist-{VERSION_PMD}-bin.zip"
    info(f"Descargando {URL_PMD}")
    try:
        with urllib.request.urlopen(URL_PMD, timeout=120) as respuesta, zip_pmd.open("wb") as destino:
            shutil.copyfileobj(respuesta, destino)
    except OSError as error:
        salir(f"No se pudo descargar PMD: {error}")

    huella = sha256(zip_pmd)
    if SHA256_PMD is None:
        info(f"SHA-256 del zip: {huella}  (anotarlo en SHA256_PMD y en VERSIONES.md)")
    elif huella != SHA256_PMD:
        zip_pmd.unlink()
        salir(f"La huella del zip no coincide con la anotada: {huella}. No se instala.")

    with zipfile.ZipFile(zip_pmd) as archivo:
        archivo.extractall(DIR_HERRAMIENTAS)
    carpeta = carpeta_pmd()
    if carpeta is None:
        salir("El zip se extrajo, pero no aparece bin/pmd: revisar el contenido en trabajo/herramientas/")
    info(f"PMD {VERSION_PMD} instalado en {carpeta.relative_to(RAIZ)}")


def correr(proyecto: str, version: str) -> None:
    carpeta = carpeta_pmd()
    if carpeta is None:
        salir("PMD no está instalado. Corré antes: python guiones/pmd_metodos.py instalar")
    corpus = buscar_version(proyecto, version)
    if not (corpus.directorio / "src" / "main" / "java").exists():
        salir(f"No está el código de {proyecto} {version} en {corpus.directorio.relative_to(RAIZ)}")

    # El contenedor solo ve trabajo/: el conjunto de reglas se copia ahí.
    shutil.copy2(ARCHIVO_REGLAS, DIR_HERRAMIENTAS / ARCHIVO_REGLAS.name)
    DIR_REPORTES.mkdir(parents=True, exist_ok=True)
    reporte = DIR_REPORTES / f"{proyecto}-{version}.xml"

    def en_contenedor(ruta) -> str:
        return f"{DIR_TRABAJO_CONTENEDOR}/{ruta.relative_to(DIR_TRABAJO).as_posix()}"

    comando = [
        "bash", en_contenedor(carpeta / "bin" / "pmd"), "check",
        "--dir", f"{corpus.directorio_contenedor}/src/main/java",
        "--rulesets", en_contenedor(DIR_HERRAMIENTAS / ARCHIVO_REGLAS.name),
        "--format", "xml",
        "--report-file", en_contenedor(reporte),
        "--no-cache",
        "--no-progress",
    ]
    ruta_log = DIR_LOGS / f"pmd-{proyecto}-{version}.log"
    info(f"Corriendo PMD {VERSION_PMD} sobre {proyecto} {version} (log: {ruta_log.name})")
    codigo, duracion = correr_en_herramientas(comando, DIR_TRABAJO_CONTENEDOR, ruta_log)
    if codigo not in CODIGOS_OK or not reporte.exists():
        salir(f"PMD terminó con código {codigo}. Revisar trabajo/logs/{ruta_log.name}")
    info(f"Reporte en {reporte.relative_to(RAIZ)} ({reporte.stat().st_size} bytes, {round(duracion)} s)")


def leer_reporte(proyecto: str, version: str) -> list[dict]:
    """Una fila por método o constructor del reporte de PMD."""
    reporte = DIR_REPORTES / f"{proyecto}-{version}.xml"
    if not reporte.exists():
        salir(f"No está {reporte.relative_to(RAIZ)}. Corré antes: pmd_metodos.py correr {proyecto} {version}")
    raiz = ET.parse(reporte).getroot()
    errores = raiz.findall("p:error", ESPACIO_REPORTE)
    if errores:
        aviso(f"PMD no pudo procesar {len(errores)} archivos (ver el reporte): sus métodos faltan")

    prefijo = f"{DIR_TRABAJO_CONTENEDOR}/{proyecto}/{version}/"
    metodos: dict[tuple[str, int], dict] = {}
    no_leidos = 0
    for archivo in raiz.findall("p:file", ESPACIO_REPORTE):
        ruta = archivo.get("name", "").removeprefix(prefijo)
        for violacion in archivo.findall("p:violation", ESPACIO_REPORTE):
            regla = violacion.get("rule")
            if regla not in PATRONES:
                continue
            mensaje = (violacion.text or "").strip()
            encontrado = PATRONES[regla].search(mensaje)
            if not encontrado:
                no_leidos += 1
                continue
            linea = int(violacion.get("beginline", 0))
            fila = metodos.setdefault(
                (ruta, linea),
                {"archivo": ruta, "linea": linea, "metodo": violacion.get("method", ""),
                 # "The method ..." o "The constructor ...".
                 "tipo": mensaje.split()[1] if len(mensaje.split()) > 1 else ""},
            )
            fila[COLUMNA[regla]] = int(encontrado.group(1))
    if no_leidos:
        aviso(f"{no_leidos} mensajes de PMD no coincidieron con el patrón esperado")

    for fila in metodos.values():
        # Con umbral 1, la regla cognitiva calla solo cuando el valor es 0.
        if "cognitiva_pmd" not in fila and "ciclomatica_pmd" in fila:
            fila["cognitiva_pmd"] = 0
    return sorted(metodos.values(), key=lambda f: (f["archivo"], f["linea"]))


def version_extraccion(proyecto: str) -> str | None:
    """Versión del último análisis de extraccion-<proyecto> según el registro de análisis."""
    if not ARCHIVO_REGISTRO.exists():
        return None
    with ARCHIVO_REGISTRO.open(encoding="utf-8", newline="") as archivo:
        filas = [f for f in csv.DictReader(archivo) if f.get("clave") == f"extraccion-{proyecto}"]
    return filas[-1]["version"] if filas else None


def exportar(proyecto: str, version: str) -> None:
    filas_pmd = leer_reporte(proyecto, version)
    escribir_csv(DIR_DATOS / f"pmd-{proyecto}-{version}" / "metodos.csv", filas_pmd, COLUMNAS_PMD)

    ruta_sonar = DIR_DATOS / f"extraccion-{proyecto}" / "complejidad_metodo.csv"
    if not ruta_sonar.exists():
        info("No hay extracción de SonarQube para este proyecto: no se arma la tabla del eje 2")
        return
    version_sonar = version_extraccion(proyecto)
    if version_sonar != version:
        salir(
            f"La extracción de SonarQube de {proyecto} es de la versión {version_sonar}, no de {version}: "
            "no se pueden cruzar"
        )

    with ruta_sonar.open(encoding="utf-8", newline="") as archivo:
        sonar = list(csv.DictReader(archivo))
    por_clave = {(f["archivo"], f["linea"]): f for f in filas_pmd}
    tabla, sin_par = [], 0
    for fila in sonar:
        par = por_clave.get((fila["archivo"], int(fila["linea"])))
        if par is None:
            sin_par += 1
            continue
        tabla.append({
            "archivo": fila["archivo"], "linea": fila["linea"], "metodo": fila["metodo"],
            "ciclomatica_sonar": fila["ciclomatica"], "cognitiva_sonar": fila["cognitiva"],
            "cognitiva_origen": fila["cognitiva_origen"],
            "ciclomatica_pmd": par.get("ciclomatica_pmd", ""), "cognitiva_pmd": par.get("cognitiva_pmd", ""),
            "ncss_pmd": par.get("ncss_pmd", ""),
        })
    escribir_csv(DIR_DATOS / f"extraccion-{proyecto}" / "eje2_metodos.csv", tabla, COLUMNAS_EJE2)

    # Controles del cruce entre las dos implementaciones.
    if sin_par:
        aviso(f"{sin_par} métodos de SonarQube sin par en PMD: quedan fuera de la tabla del eje 2")
    info(f"Métodos de SonarQube: {len(sonar)}; con par en PMD: {len(tabla)}; solo en PMD: {len(filas_pmd) - len(tabla)} "
         f"(equals, hashCode y métodos sin cuerpo, que SonarQube no informa)")
    iguales_cic = sum(1 for f in tabla if str(f["ciclomatica_pmd"]) == f["ciclomatica_sonar"])
    medidas = [f for f in tabla if f["cognitiva_origen"] == "issue"]
    iguales_cog = sum(1 for f in medidas if str(f["cognitiva_pmd"]) == f["cognitiva_sonar"])
    ceros = [f for f in tabla if f["cognitiva_origen"] == "cero"]
    no_medidas = [f for f in tabla if f["cognitiva_origen"] == "no medida"]
    info(f"Ciclomática igual en las dos herramientas: {iguales_cic} de {len(tabla)}")
    info(f"Cognitiva igual (métodos medidos por SonarQube): {iguales_cog} de {len(medidas)}")
    info(f"Cognitiva 0 en SonarQube y 0 en PMD: {sum(1 for f in ceros if f['cognitiva_pmd'] == 0)} de {len(ceros)}")
    if no_medidas:
        info(f"Cognitiva no medida por SonarQube y mayor que 0 en PMD: "
             f"{sum(1 for f in no_medidas if f['cognitiva_pmd'] not in ('', 0))} de {len(no_medidas)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="accion", required=True)
    sub.add_parser("instalar", help="descargar e instalar la versión fijada de PMD")
    for nombre, ayuda in (("correr", "correr PMD sobre una versión del corpus"),
                          ("exportar", "convertir el reporte a CSV y armar la tabla del eje 2")):
        p_sub = sub.add_parser(nombre, help=ayuda)
        p_sub.add_argument("proyecto")
        p_sub.add_argument("version")
    args = parser.parse_args()

    if args.accion == "instalar":
        instalar()
    elif args.accion == "correr":
        correr(args.proyecto, args.version)
    else:
        exportar(args.proyecto, args.version)


if __name__ == "__main__":
    main()
