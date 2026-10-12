"""Descarga el corpus congelado en ``trabajo/<proyecto>/<version>``.

Para cada fila de ``corpus/corpus.csv`` trae solamente el commit indicado
(sin historia: ``git fetch --depth 1``) y verifica que el checkout quede
exactamente en ese hash. Si la carpeta ya existe y está en el commit correcto,
no hace nada, así que se puede correr las veces que haga falta.

Uso:
    python guiones/clonar_corpus.py                  # todo el corpus
    python guiones/clonar_corpus.py --proyecto jsoup # un proyecto
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from comun import VersionCorpus, filtrar_corpus, info, salir, aviso


def git(*argumentos: str, cwd: Path) -> str:
    """Ejecuta git en ``cwd`` y devuelve la salida estándar sin espacios finales."""
    resultado = subprocess.run(
        ["git", *argumentos], cwd=cwd, capture_output=True, text=True, check=False
    )
    if resultado.returncode != 0:
        raise RuntimeError(f"git {' '.join(argumentos)} falló en {cwd}:\n{resultado.stderr.strip()}")
    return resultado.stdout.strip()


def commit_actual(directorio: Path) -> str | None:
    """Hash del HEAD de un checkout, o None si la carpeta no es un repositorio."""
    if not (directorio / ".git").exists():
        return None
    try:
        return git("rev-parse", "HEAD", cwd=directorio)
    except RuntimeError:
        return None


def clonar(version: VersionCorpus) -> None:
    destino = version.directorio
    actual = commit_actual(destino)
    if actual == version.commit:
        info(f"{version.proyecto} {version.version}: ya está en {version.commit[:12]}, se omite")
        return
    if actual is not None:
        # No se borra nada automáticamente: puede haber trabajo local en esa carpeta.
        salir(
            f"{destino} es un repositorio en {actual[:12]}, no en {version.commit[:12]}. "
            "Revisalo y borralo a mano si corresponde."
        )

    info(f"{version.proyecto} {version.version}: descargando {version.tag} ({version.commit[:12]})")
    destino.mkdir(parents=True, exist_ok=True)
    git("init", "--quiet", cwd=destino)
    git("remote", "add", "origin", version.url_git, cwd=destino)
    # GitHub permite pedir un commit puntual por su hash.
    git("fetch", "--quiet", "--depth", "1", "origin", version.commit, cwd=destino)
    git("-c", "advice.detachedHead=false", "checkout", "--quiet", "FETCH_HEAD", cwd=destino)

    obtenido = git("rev-parse", "HEAD", cwd=destino)
    if obtenido != version.commit:
        salir(f"El checkout quedó en {obtenido}, se esperaba {version.commit}")
    info(f"{version.proyecto} {version.version}: verificado {obtenido[:12]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--proyecto", help="clonar solo este proyecto")
    parser.add_argument("--version", help="clonar solo esta versión")
    args = parser.parse_args()

    versiones = filtrar_corpus(args.proyecto, args.version)
    if not versiones:
        salir("El filtro no coincide con ninguna fila de corpus/corpus.csv")
    for version in versiones:
        try:
            clonar(version)
        except RuntimeError as error:
            aviso(str(error))
            salir(f"No se pudo descargar {version.proyecto} {version.version}")


if __name__ == "__main__":
    main()
