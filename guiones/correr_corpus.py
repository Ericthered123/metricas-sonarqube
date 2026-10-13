"""Corrida de producción: analiza todo el corpus con cobertura y exporta los datos (SCRUM-27 y SCRUM-28).

Para cada proyecto y cada perfil (comprehensive, el principal, y core, el
contraste; ver docs/configuracion-analisis.md) analiza los dos releases bajo la
misma clave, el viejo primero, con tests y cobertura (``analizar.py --jacoco``).
Después exporta las medidas de cada clave, cruza el código nuevo con el diff
real entre releases y verifica que cada clave use el perfil y el gate que le
corresponden.

Se puede cortar y volver a lanzar: un análisis que ya figura como correcto en
``datos/registro_analisis.csv`` (misma clave, versión y perfil, con JaCoCo y
sin "cobertura dudosa") no se repite. Si falla el release viejo de una clave,
el nuevo no se analiza, porque su código nuevo quedaría mal definido.

Orden: de los proyectos más rápidos a los más lentos, para detectar problemas
temprano. Duración estimada con los tiempos de las pruebas técnicas: unas dos
horas y media para los 16 análisis.

Uso:
    python guiones/correr_corpus.py
    python guiones/correr_corpus.py --proyecto jsoup --perfil comprehensive
    python guiones/correr_corpus.py --solo-exportar
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from datetime import datetime

from comun import DIR_DATOS, PERFILES, RAIZ, aviso, clave_corpus, info, leer_corpus, salir

GUIONES = RAIZ / "guiones"
ORDEN_PROYECTOS = ["jsoup", "jfreechart", "commons-collections", "commons-io"]
REGISTRO = DIR_DATOS / "registro_analisis.csv"


def correr(guion: str, *argumentos: str) -> bool:
    """Corre otro guion del laboratorio con el mismo intérprete. Devuelve si terminó bien."""
    comando = [sys.executable, str(GUIONES / guion), *argumentos]
    info("$ " + " ".join(comando[1:]))
    return subprocess.run(comando, cwd=RAIZ).returncode == 0


def analisis_hechos() -> set[tuple[str, str, str]]:
    """(clave, versión, perfil) de los análisis con cobertura que ya terminaron bien."""
    if not REGISTRO.exists():
        return set()
    with REGISTRO.open(encoding="utf-8", newline="") as archivo:
        return {
            (f["clave"], f["version"], f.get("perfil", ""))
            for f in csv.DictReader(archivo)
            if f["resultado"].startswith("ok") and "dudosa" not in f["resultado"] and f["jacoco"] == "sí"
        }


def ultimo_resultado(clave: str, version: str) -> str:
    """Resultado registrado del último análisis de esa clave y versión."""
    with REGISTRO.open(encoding="utf-8", newline="") as archivo:
        filas = [f for f in csv.DictReader(archivo) if f["clave"] == clave and f["version"] == version]
    return filas[-1]["resultado"] if filas else "sin registro"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--proyecto", choices=ORDEN_PROYECTOS, help="solo este proyecto")
    parser.add_argument("--perfil", choices=sorted(PERFILES), help="solo este perfil")
    parser.add_argument("--solo-exportar", action="store_true", help="no analizar: solo exportar y verificar")
    args = parser.parse_args()

    corpus = leer_corpus()
    proyectos = [p for p in ORDEN_PROYECTOS if args.proyecto in (None, p)]
    perfiles = [s for s in ("comprehensive", "core") if args.perfil in (None, s)]
    inicio = time.monotonic()
    claves: list[str] = []
    resumen: list[str] = []

    for proyecto in proyectos:
        versiones = sorted((v for v in corpus if v.proyecto == proyecto), key=lambda v: v.orden)
        if len(versiones) != 2:
            salir(f"{proyecto}: se esperaban dos releases en el corpus y hay {len(versiones)}")
        for sufijo in perfiles:
            perfil = PERFILES[sufijo]
            clave = clave_corpus(proyecto, perfil)
            claves.append(clave)
            if args.solo_exportar:
                continue
            for version in versiones:
                if (clave, version.version, perfil) in analisis_hechos():
                    info(f"{clave} {version.version}: ya está en el registro, se saltea")
                    continue
                momento = time.monotonic()
                bien = correr("analizar.py", proyecto, version.version, "--jacoco", "--perfil", sufijo)
                minutos = (time.monotonic() - momento) / 60
                resumen.append(f"{clave} {version.version}: {ultimo_resultado(clave, version.version)} ({minutos:.0f} min)")
                if not bien and version.orden == 1:
                    aviso(f"Falló el release viejo de {clave}: no se analiza el nuevo")
                    resumen.append(f"{clave} {versiones[1].version}: no se corrió")
                    break

    info(f"Análisis terminados en {(time.monotonic() - inicio) / 60:.0f} min. Exportando...")
    for clave in claves:
        proyecto = clave.removeprefix("corpus-core-").removeprefix("corpus-")
        if not correr("exportar_medidas.py", clave):
            resumen.append(f"{clave}: falló la exportación")
            continue
        if not correr("diff_releases.py", proyecto, "--comparar", clave):
            resumen.append(f"{clave}: falló la comparación con el diff")
    verificado = correr("exportar_configuracion.py", "--verificar", *claves)

    info(f"Resumen de la corrida ({datetime.now():%Y-%m-%d %H:%M}, {(time.monotonic() - inicio) / 60:.0f} min):")
    for linea in resumen:
        info("  " + linea)
    if not verificado:
        aviso("La verificación de perfiles o gates falló: ver la salida de exportar_configuracion.py")


if __name__ == "__main__":
    main()
