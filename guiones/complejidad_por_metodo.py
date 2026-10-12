"""Prueba técnica 2 (decisión D1): complejidad ciclomática y cognitiva por método.

SonarQube publica ambas complejidades solo hasta el nivel de archivo. El valor
por método aparece en el mensaje de los issues de dos reglas de Java:

* ``java:S3776``: "Refactor this method to reduce its Cognitive Complexity from 16 to the 15 allowed."
* ``java:S1541``: "The Cyclomatic Complexity of this method "x" is 11 which is greater than 10 authorized."

La técnica es crear un perfil de calidad que contenga SOLO esas dos reglas, con
el umbral en 0 para que salten en todos los métodos, asignarlo a una clave de
proyecto aparte (``extraccion-<proyecto>``) y leer los números de los mensajes.
El análisis principal no se toca: si estos issues cayeran ahí, inflarían la
deuda técnica y cambiarían las letras del eje 1.

Subcomandos:
    perfil    crea el perfil de extracción y lo asigna a extraccion-<proyecto>
    exportar  lee los issues y escribe datos/extraccion-<proyecto>/complejidad_metodo.csv

Flujo completo para un proyecto:
    python guiones/complejidad_por_metodo.py perfil jsoup
    python guiones/analizar.py jsoup 1.23.2 --clave extraccion-jsoup --sin-tests
    python guiones/complejidad_por_metodo.py exportar jsoup

Limitaciones conocidas (a documentar en la prueba técnica):
* Un método con complejidad cognitiva 0 no genera issue de S3776: se registra
  como 0 si el método sí aparece en S1541 (todo método tiene ciclomática >= 1).
* La ubicación del issue es el nombre del método, no su cuerpo: el tamaño del
  método no sale de acá y hay que obtenerlo de otra forma.
"""

from __future__ import annotations

import argparse
import re

from comun import DIR_DATOS, ClienteSonar, ErrorSonar, aviso, escribir_csv, info, salir

NOMBRE_PERFIL = "TP extraccion complejidad"
REGLA_COGNITIVA = "java:S3776"
REGLA_CICLOMATICA = "java:S1541"

PATRON_COGNITIVA = re.compile(r"Cognitive Complexity from (\d+) to")
PATRON_CICLOMATICA = re.compile(r'method "([^"]+)" is (\d+) which')


def clave_extraccion(proyecto: str) -> str:
    return f"extraccion-{proyecto}"


def parametros_umbral(cliente: ClienteSonar, regla: str) -> str:
    """Arma el parámetro de activación que pone en 0 los umbrales de la regla.

    En lugar de suponer el nombre del parámetro, lo lee de la definición de la
    regla en esta versión de SonarQube y deja constancia en consola.
    """
    try:
        definicion = cliente.get("/api/rules/show", key=regla)["rule"]
    except ErrorSonar as error:
        salir(f"La regla {regla} no existe en esta instancia ({error.codigo}). Hay que usar el plan B.")
    umbrales = [
        p["key"] for p in definicion.get("params", [])
        if "threshold" in p["key"].lower() or p["key"].lower().startswith("max")
    ]
    if not umbrales:
        salir(f"La regla {regla} no tiene un parámetro de umbral reconocible: {definicion.get('params')}")
    info(f"{regla} ({definicion.get('name')}): umbral(es) {', '.join(umbrales)} -> 0")
    return ";".join(f"{u}=0" for u in umbrales)


def crear_perfil(cliente: ClienteSonar, proyecto: str) -> None:
    clave = clave_extraccion(proyecto)

    # 1. Perfil con solo las dos reglas de complejidad (se reutiliza si ya existe).
    perfiles = cliente.get("/api/qualityprofiles/search", language="java")["profiles"]
    perfil = next((p for p in perfiles if p["name"] == NOMBRE_PERFIL), None)
    if perfil is None:
        perfil = cliente.post("/api/qualityprofiles/create", name=NOMBRE_PERFIL, language="java")["profile"]
        info(f"Perfil '{NOMBRE_PERFIL}' creado")
    for regla in (REGLA_COGNITIVA, REGLA_CICLOMATICA):
        cliente.post(
            "/api/qualityprofiles/activate_rule",
            key=perfil["key"],
            rule=regla,
            params=parametros_umbral(cliente, regla),
        )

    # 2. Proyecto aparte, para no tocar el análisis principal.
    try:
        cliente.post("/api/projects/create", project=clave, name=clave)
        info(f"Proyecto '{clave}' creado")
    except ErrorSonar as error:
        if error.codigo != 400:  # 400 = ya existe
            raise
    cliente.post("/api/qualityprofiles/add_project", language="java", qualityProfile=NOMBRE_PERFIL, project=clave)
    info(f"'{clave}' usa el perfil '{NOMBRE_PERFIL}'. Siguiente paso: analizar.py {proyecto} <version> --clave {clave}")


def exportar(cliente: ClienteSonar, proyecto: str) -> None:
    clave = clave_extraccion(proyecto)
    metodos: dict[tuple[str, int], dict] = {}
    no_reconocidos = 0

    for regla in (REGLA_CICLOMATICA, REGLA_COGNITIVA):
        for issue in cliente.paginar("/api/issues/search", "issues", componentKeys=clave, rules=regla):
            archivo = issue["component"].split(":", 1)[-1]
            linea = issue.get("textRange", {}).get("startLine", issue.get("line", 0))
            fila = metodos.setdefault((archivo, linea), {"archivo": archivo, "linea": linea})
            mensaje = issue.get("message", "")
            if regla == REGLA_CICLOMATICA and (m := PATRON_CICLOMATICA.search(mensaje)):
                fila["metodo"], fila["ciclomatica"] = m.group(1), int(m.group(2))
            elif regla == REGLA_COGNITIVA and (m := PATRON_COGNITIVA.search(mensaje)):
                fila["cognitiva"] = int(m.group(1))
            else:
                no_reconocidos += 1

    for fila in metodos.values():
        # Sin issue de S3776 pero con ciclomática: el método tiene cognitiva 0.
        if "cognitiva" not in fila and "ciclomatica" in fila:
            fila["cognitiva"] = 0
            fila["cognitiva_imputada"] = "sí"
    if no_reconocidos:
        aviso(f"{no_reconocidos} mensajes no coincidieron con el patrón esperado: revisar los patrones")

    filas = sorted(metodos.values(), key=lambda f: (f["archivo"], f["linea"]))
    escribir_csv(
        DIR_DATOS / clave / "complejidad_metodo.csv",
        filas,
        ["archivo", "linea", "metodo", "ciclomatica", "cognitiva", "cognitiva_imputada"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("accion", choices=["perfil", "exportar"])
    parser.add_argument("proyecto")
    args = parser.parse_args()

    cliente = ClienteSonar.desde_config()
    if args.accion == "perfil":
        crear_perfil(cliente, args.proyecto)
    else:
        exportar(cliente, args.proyecto)


if __name__ == "__main__":
    main()
