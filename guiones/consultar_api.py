"""Consulta la API web de SonarQube y guarda la respuesta cruda en un archivo.

Herramienta de depuración y de evidencia: cuando un guion no se comporta como
se esperaba, o hay que confirmar qué responde la API en la versión instalada,
se consulta acá y se guarda la respuesta tal cual, en lugar de suponerla.

Seguridad:

* Solo hace pedidos GET, que en la API de SonarQube son de lectura. Las
  operaciones que modifican algo usan POST, así que este guion no puede
  cambiar nada de la instancia.
* Toma el token de ``laboratorio/.env``, como los demás guiones: no queda
  escrito ni en el comando ni en el archivo de salida.
* Guarda en ``trabajo/api/``, que no se versiona.

Cada archivo guarda la consulta (ruta, parámetros, fecha y versión de
SonarQube) junto con la respuesta, para saber después de dónde salió.

Uso:
    python guiones/consultar_api.py /api/system/status
    python guiones/consultar_api.py /api/settings/values keys=sonar.multi-quality-mode.enabled
    python guiones/consultar_api.py /api/rules/show key=java:S3776 --nombre regla-S3776
    python guiones/consultar_api.py /api/metrics/search --paginar metrics
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime

from comun import DIR_TRABAJO, RAIZ, ClienteSonar, ErrorSonar, info, salir

DIR_SALIDA = DIR_TRABAJO / "api"
# Largo máximo del nombre de archivo generado automáticamente.
LARGO_NOMBRE = 80


def leer_parametros(pares: list[str]) -> dict[str, str]:
    """Convierte argumentos ``clave=valor`` en un diccionario de parámetros."""
    parametros = {}
    for par in pares:
        clave, separador, valor = par.partition("=")
        if not separador or not clave:
            salir(f"Parámetro mal escrito: '{par}'. El formato es clave=valor")
        parametros[clave] = valor
    return parametros


def nombre_por_defecto(ruta: str, parametros: dict[str, str]) -> str:
    """Nombre de archivo legible a partir de la ruta y los parámetros.

    Ejemplo: /api/rules/show con key=java:S3776 -> rules-show__key-java-S3776
    """
    base = ruta.removeprefix("/api/").strip("/").replace("/", "-")
    extra = "__".join(f"{clave}-{valor}" for clave, valor in parametros.items())
    nombre = f"{base}__{extra}" if extra else base
    # Solo letras, números, puntos, guiones y guiones bajos: válido en Windows y Linux.
    nombre = re.sub(r"[^\w.-]+", "-", nombre).strip("-")
    return nombre[:LARGO_NOMBRE] or "consulta"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ruta", help="ruta de la API, por ejemplo /api/metrics/search")
    parser.add_argument("parametros", nargs="*", help="parámetros de la consulta, como clave=valor")
    parser.add_argument("--nombre", help="nombre del archivo de salida, sin extensión")
    parser.add_argument(
        "--paginar",
        metavar="LISTA",
        help="recorrer todas las páginas y juntar la lista con esta clave (por ejemplo metrics, issues, components)",
    )
    args = parser.parse_args()

    if not args.ruta.startswith("/api/"):
        salir("La ruta tiene que empezar con /api/, por ejemplo /api/system/status")
    parametros = leer_parametros(args.parametros)

    cliente = ClienteSonar.desde_config()
    try:
        version = cliente.get("/api/system/status").get("version", "desconocida")
        if args.paginar:
            # El paginado lo maneja el cliente; ps y p los pone él.
            parametros.pop("p", None)
            parametros.pop("ps", None)
            elementos = list(cliente.paginar(args.ruta, args.paginar, **parametros))
            respuesta = {args.paginar: elementos, "total_recibidos": len(elementos)}
        else:
            respuesta = cliente.get(args.ruta, **parametros)
    except ErrorSonar as error:
        salir(f"La API respondió HTTP {error.codigo}:\n{error.cuerpo[:2000]}")

    salida = {
        "consulta": {
            "ruta": args.ruta,
            "parametros": parametros,
            "paginada_por": args.paginar,
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "version_sonarqube": version,
        },
        "respuesta": respuesta,
    }

    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    destino = DIR_SALIDA / f"{args.nombre or nombre_por_defecto(args.ruta, parametros)}.json"
    destino.write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")

    resumen = ", ".join(respuesta.keys()) if isinstance(respuesta, dict) else type(respuesta).__name__
    info(f"Escrito {destino.relative_to(RAIZ)} ({destino.stat().st_size} bytes; claves: {resumen})")


if __name__ == "__main__":
    main()
