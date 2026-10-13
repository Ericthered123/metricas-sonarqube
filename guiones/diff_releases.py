"""Cambio real entre los dos releases de un proyecto, para contrastar el código nuevo de SonarQube.

La prueba técnica 3 (SCRUM-24, decisión D2) pregunta si SonarQube toma como
código nuevo la diferencia entre los dos releases analizados bajo la misma
clave. Para responderla hace falta una referencia independiente de SonarQube:
este guion la calcula con ``git diff --no-index`` entre los dos checkouts, que
no traen historia (``--depth 1``) pero sí el contenido de cada versión.

Qué escribe:

* ``datos/diff-<proyecto>/archivos.csv``: una fila por archivo ``.java`` que
  cambió entre el release viejo (orden 1 del corpus) y el nuevo (orden 2), con
  las líneas agregadas y borradas.
* Con ``--comparar CLAVE``: ``datos/<CLAVE>/comparacion_codigo_nuevo.csv``, que
  cruza ese diff con ``codigo_nuevo_archivo.csv`` (lo exporta
  ``exportar_medidas.py``) y resume en pantalla cuánto coinciden.

Decisiones de medición:

* Solo archivos ``.java``: es el lenguaje del estudio.
* Un renombrado aparece como un archivo borrado y otro agregado. SonarQube
  tiene detección de archivos movidos, así que si algún proyecto los tiene
  hay que mirarlos aparte (en jsoup 1.22.2 a 1.23.2 no hay).
* ``agregadas_codigo`` es una aproximación de las líneas agregadas que son
  código: descarta las vacías y las que empiezan como comentario (``//``,
  ``/*``, ``*``). No reconoce un comentario que empieza a mitad de línea ni el
  interior de un bloque cuyas líneas no empiezan con ``*``. Sirve para ver de
  qué tipo de líneas se acerca ``new_lines``, no como medida exacta.

Uso:
    python guiones/diff_releases.py jsoup
    python guiones/diff_releases.py jsoup --comparar prueba-pt3-jsoup
"""

from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path

from comun import DIR_DATOS, aviso, escribir_csv, filtrar_corpus, info, salir

COLUMNAS_DIFF = ["archivo", "ambito", "estado", "agregadas", "borradas", "agregadas_codigo"]
PREFIJOS_COMENTARIO = ("//", "/*", "*")


def archivos_java(raiz: Path) -> dict[str, Path]:
    """Archivos .java de un checkout, indexados por su ruta relativa con barras '/' (como los nombra SonarQube)."""
    return {p.relative_to(raiz).as_posix(): p for p in raiz.rglob("*.java") if "target" not in p.parts}


def ambito(ruta: str) -> str:
    """Código principal, de test u otro, según la convención de carpetas de Maven."""
    if ruta.startswith("src/main/"):
        return "main"
    if ruta.startswith("src/test/"):
        return "test"
    return "otro"


def contar_diff(viejo: Path | None, nuevo: Path | None) -> tuple[int, int, int]:
    """Cuenta líneas agregadas, borradas y agregadas de código entre dos versiones de un archivo.

    Usa git (el mismo algoritmo con el que se ven los cambios en el repositorio
    del proyecto). Si falta uno de los dos lados, se compara contra un archivo
    vacío: todo el archivo es agregado o borrado.
    """
    # En modo --no-index git trata /dev/null como archivo vacío en todas las plataformas.
    nulo = "/dev/null"
    comando = ["git", "diff", "--no-index", "--no-color", "-U0", str(viejo or nulo), str(nuevo or nulo)]
    # git diff --no-index devuelve 1 cuando hay diferencias: no es un error.
    resultado = subprocess.run(comando, capture_output=True)
    if resultado.returncode not in (0, 1):
        salir(f"Falló git diff: {resultado.stderr.decode(errors='replace')}")
    agregadas = borradas = codigo = 0
    # Algunos archivos de test no son UTF-8 (lo mostró la PT2): se reemplazan los bytes inválidos.
    for linea in resultado.stdout.decode("utf-8", errors="replace").splitlines():
        if linea.startswith(("+++", "---")):
            continue
        if linea.startswith("+"):
            agregadas += 1
            contenido = linea[1:].strip()
            if contenido and not contenido.startswith(PREFIJOS_COMENTARIO):
                codigo += 1
        elif linea.startswith("-"):
            borradas += 1
    return agregadas, borradas, codigo


def calcular_diff(dir_viejo: Path, dir_nuevo: Path) -> list[dict]:
    """Una fila por archivo .java que cambió entre los dos checkouts."""
    viejos, nuevos = archivos_java(dir_viejo), archivos_java(dir_nuevo)
    filas = []
    for ruta in sorted(viejos.keys() | nuevos.keys()):
        anterior, actual = viejos.get(ruta), nuevos.get(ruta)
        if anterior and actual and anterior.read_bytes() == actual.read_bytes():
            continue  # sin cambios: no se llama a git
        estado = "agregado" if anterior is None else "borrado" if actual is None else "modificado"
        agregadas, borradas, codigo = contar_diff(anterior, actual)
        if estado == "modificado" and agregadas == borradas == 0:
            continue  # solo cambió el fin de línea u otro byte que git no informa como línea
        filas.append({
            "archivo": ruta, "ambito": ambito(ruta), "estado": estado,
            "agregadas": agregadas, "borradas": borradas, "agregadas_codigo": codigo,
        })
    return filas


def entero(valor: str | None) -> int:
    """Celda numérica de un CSV exportado; vacía cuenta como 0 (SonarQube omite los ceros por archivo)."""
    return int(float(valor)) if valor not in (None, "") else 0


def comparar(diff: list[dict], clave: str) -> None:
    """Cruza el diff real con el código nuevo que informó SonarQube y resume la coincidencia."""
    ruta_nuevo = DIR_DATOS / clave / "codigo_nuevo_archivo.csv"
    if not ruta_nuevo.exists():
        salir(f"No está {ruta_nuevo.name} de '{clave}'. Corré antes exportar_medidas.py {clave}.")
    with ruta_nuevo.open(encoding="utf-8", newline="") as archivo:
        sonar = {f["archivo"]: f for f in csv.DictReader(archivo) if f["archivo"].endswith(".java")}

    # Issues nuevos por archivo, según la marca codigo_nuevo de issues.csv.
    issues_nuevos: dict[str, int] = {}
    ruta_issues = DIR_DATOS / clave / "issues.csv"
    if ruta_issues.exists():
        with ruta_issues.open(encoding="utf-8", newline="") as archivo:
            for issue in csv.DictReader(archivo):
                if issue.get("codigo_nuevo") == "sí":
                    issues_nuevos[issue["archivo"]] = issues_nuevos.get(issue["archivo"], 0) + 1

    reales = {f["archivo"]: f for f in diff if f["estado"] != "borrado"}
    filas = []
    for ruta in sorted(sonar.keys() | reales.keys()):
        real, medido = reales.get(ruta, {}), sonar.get(ruta)
        filas.append({
            "archivo": ruta,
            "ambito": ambito(ruta),
            "estado_real": real.get("estado", "sin cambios"),
            "agregadas": real.get("agregadas", 0),
            "agregadas_codigo": real.get("agregadas_codigo", 0),
            # Un archivo que SonarQube no informa (por ejemplo, excluido) queda vacío, no en 0.
            "new_lines": "" if medido is None else entero(medido.get("new_lines")),
            "new_violations": "" if medido is None else entero(medido.get("new_violations")),
            "issues_nuevos": issues_nuevos.get(ruta, 0),
        })
    escribir_csv(
        DIR_DATOS / clave / "comparacion_codigo_nuevo.csv",
        filas,
        ["archivo", "ambito", "estado_real", "agregadas", "agregadas_codigo",
         "new_lines", "new_violations", "issues_nuevos"],
    )

    # Resumen: tabla de contingencia "cambió de verdad" contra "SonarQube lo marca como nuevo".
    main = [f for f in filas if f["ambito"] == "main" and f["new_lines"] != ""]
    cambio = lambda f: f["estado_real"] != "sin cambios"
    marcado = lambda f: f["new_lines"] > 0
    info(f"Archivos main informados por SonarQube: {len(main)}")
    info(f"  cambiaron y SonarQube los marca:     {sum(cambio(f) and marcado(f) for f in main)}")
    info(f"  cambiaron y SonarQube NO los marca:  {sum(cambio(f) and not marcado(f) for f in main)}")
    info(f"  no cambiaron y SonarQube los marca:  {sum(not cambio(f) and marcado(f) for f in main)}")
    info(f"  no cambiaron y no los marca:         {sum(not cambio(f) and not marcado(f) for f in main)}")
    info(f"Líneas agregadas (git): {sum(f['agregadas'] for f in main)}, "
         f"de código aprox.: {sum(f['agregadas_codigo'] for f in main)}; "
         f"new_lines (SonarQube): {sum(f['new_lines'] for f in main)}")
    info(f"Issues en código nuevo: new_violations suma {sum(f['new_violations'] for f in main)}, "
         f"issues.csv marca {sum(f['issues_nuevos'] for f in main)}")
    sin_informar = [f["archivo"] for f in filas if f["ambito"] == "main" and f["new_lines"] == ""]
    if sin_informar:
        aviso(f"{len(sin_informar)} archivos main del diff que SonarQube no informa: {', '.join(sin_informar[:5])}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("proyecto")
    parser.add_argument("--comparar", metavar="CLAVE", help="clave de SonarQube cuyo código nuevo se contrasta con el diff")
    args = parser.parse_args()

    versiones = sorted(filtrar_corpus(args.proyecto, None), key=lambda v: v.orden)
    if len(versiones) != 2:
        salir(f"Se esperaban dos releases de '{args.proyecto}' en el corpus y hay {len(versiones)}")
    viejo, nuevo = versiones
    for version in versiones:
        if not version.directorio.exists():
            salir(f"No está el checkout de {version.proyecto} {version.version}. Corré antes clonar_corpus.py.")

    info(f"Diff de {args.proyecto}: {viejo.version} -> {nuevo.version}")
    diff = calcular_diff(viejo.directorio, nuevo.directorio)
    escribir_csv(DIR_DATOS / f"diff-{args.proyecto}" / "archivos.csv", diff, COLUMNAS_DIFF)
    for nombre in ("main", "test"):
        parte = [f for f in diff if f["ambito"] == nombre]
        estados = {e: sum(f["estado"] == e for f in parte) for e in ("agregado", "modificado", "borrado")}
        info(f"  {nombre}: {len(parte)} archivos ({estados}), +{sum(f['agregadas'] for f in parte)} "
             f"-{sum(f['borradas'] for f in parte)} (código aprox. +{sum(f['agregadas_codigo'] for f in parte)})")

    if args.comparar:
        comparar(diff, args.comparar)


if __name__ == "__main__":
    main()
