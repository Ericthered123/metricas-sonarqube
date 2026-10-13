"""Extracción del eje 2 en todo el corpus (SCRUM-29, decisión D1).

Para el release nuevo de cada proyecto (la referencia de los ejes 1 y 2):

1. ``complejidad_por_metodo.py perfil``: crea el perfil de extracción (solo
   java:S1541 y java:S3776, umbral 0) y lo asigna a ``extraccion-<proyecto>``.
2. ``analizar.py ... --clave extraccion-<proyecto> --sin-tests``: el análisis
   aparte, que no toca el principal ni su deuda.
3. ``complejidad_por_metodo.py exportar``: una fila por método con las dos
   complejidades según SonarQube.
4. ``pmd_metodos.py correr`` y ``exportar``: las dos complejidades y el NCSS
   según PMD, y la tabla del eje 2 cruzada con SonarQube
   (``datos/extraccion-<proyecto>/eje2_metodos.csv``).

jsoup se vuelve a extraer aunque ya estuviera de la prueba técnica 2: su
proyecto en SonarQube se perdió con la base (13/10) y PMD ahora corre con el
classpath del proyecto, así que los cuatro proyectos salen del mismo
procedimiento. Si un paso falla, el proyecto se abandona y se sigue con el
siguiente; al final se imprime un resumen.

Uso:
    python guiones/extraer_eje2.py
    python guiones/extraer_eje2.py --proyecto jfreechart
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time

from comun import RAIZ, info, leer_corpus, salir

GUIONES = RAIZ / "guiones"
ORDEN_PROYECTOS = ["jsoup", "jfreechart", "commons-collections", "commons-io"]


def correr(guion: str, *argumentos: str) -> bool:
    """Corre otro guion del laboratorio con el mismo intérprete. Devuelve si terminó bien."""
    comando = [sys.executable, str(GUIONES / guion), *argumentos]
    info("$ " + " ".join(comando[1:]))
    return subprocess.run(comando, cwd=RAIZ).returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--proyecto", choices=ORDEN_PROYECTOS, help="solo este proyecto")
    args = parser.parse_args()

    corpus = leer_corpus()
    inicio = time.monotonic()
    resumen = []
    for proyecto in [p for p in ORDEN_PROYECTOS if args.proyecto in (None, p)]:
        nuevas = [v for v in corpus if v.proyecto == proyecto and v.orden == 2]
        if len(nuevas) != 1:
            salir(f"{proyecto}: se esperaba un release nuevo en el corpus y hay {len(nuevas)}")
        version = nuevas[0].version
        clave = f"extraccion-{proyecto}"
        momento = time.monotonic()
        pasos = [
            ("complejidad_por_metodo.py", "perfil", proyecto),
            ("analizar.py", proyecto, version, "--clave", clave, "--sin-tests"),
            ("complejidad_por_metodo.py", "exportar", proyecto),
            ("pmd_metodos.py", "correr", proyecto, version),
            ("pmd_metodos.py", "exportar", proyecto, version),
        ]
        fallo = next((" ".join(p[:2]) for p in pasos if not correr(*p)), None)
        minutos = (time.monotonic() - momento) / 60
        resumen.append(f"{proyecto} {version}: {'ok' if fallo is None else 'falló en ' + fallo} ({minutos:.0f} min)")

    info(f"Resumen de la extracción del eje 2 ({(time.monotonic() - inicio) / 60:.0f} min):")
    for linea in resumen:
        info("  " + linea)


if __name__ == "__main__":
    main()
