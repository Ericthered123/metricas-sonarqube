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

Limitaciones conocidas (verificadas en la prueba técnica 2, jsoup):
* Un método con complejidad cognitiva 0 no genera issue de S3776. Si el método
  no tiene issue de S3776 y su ciclomática es 1 (ningún punto de decisión), se
  registra cognitiva 0 (``cognitiva_origen`` = ``cero``).
* Si no tiene issue de S3776 pero su ciclomática es mayor que 1, la cognitiva
  NO es 0: todo punto de decisión que cuenta la ciclomática (if, bucle, case,
  catch, ternario, && o ||) suma al menos 1 a la cognitiva, así que la regla
  debería haber saltado. En jsoup pasa con todos los métodos declarados dentro
  de constantes de enum y de clases anónimas: SonarQube no les calcula la
  cognitiva (tampoco a nivel archivo). Se deja vacía (``cognitiva_origen`` =
  ``no medida``) y esos métodos no entran en la correlación.
* Ninguna de las dos reglas informa los métodos ``equals`` y ``hashCode``.
* La ubicación del issue es el nombre del método, no su cuerpo: el tamaño del
  método no sale de acá y hay que obtenerlo de otra forma.
* Los métodos sin cuerpo (abstractos, de interfaces) no generan issue, así que
  la cantidad de métodos extraídos es menor que la medida ``functions``.

Controles que informa ``exportar``:
* Issues de S3776 sin su par de S1541 en la misma línea (deberían ser 0: si
  aparecen, las dos reglas marcan ubicaciones distintas y el cruce falla).
* Métodos extraídos contra la medida ``functions`` del proyecto.
* Issues en archivos de test, si los hubiera.

Solo se leen issues abiertos (``resolved=false``): si la clave se analiza más
de una vez, los issues cerrados de análisis anteriores no se mezclan. Si una
regla supera el tope de 10.000 resultados de la API, se consulta archivo por
archivo.
"""

from __future__ import annotations

import argparse
import re

from typing import Iterator

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


def issues_abiertos(cliente: ClienteSonar, clave: str, regla: str) -> Iterator[dict]:
    """Issues abiertos de una regla, sorteando el tope de 10.000 resultados de la API.

    Si la regla tiene más issues que el tope, consulta archivo por archivo.
    """
    total = cliente.get("/api/issues/search", componentKeys=clave, rules=regla, resolved="false", ps=1).get("total", 0)
    info(f"{regla}: {total} issues abiertos")
    if total <= ClienteSonar.LIMITE_ISSUES:
        yield from cliente.paginar("/api/issues/search", "issues", componentKeys=clave, rules=regla, resolved="false")
        return
    info(f"{regla} supera el tope de la API: se consulta archivo por archivo")
    for archivo in cliente.paginar("/api/components/tree", "components", component=clave, qualifiers="FIL"):
        yield from cliente.paginar(
            "/api/issues/search", "issues", componentKeys=archivo["key"], rules=regla, resolved="false"
        )


def medida_proyecto(cliente: ClienteSonar, clave: str, metrica: str) -> str:
    """Valor de una medida del proyecto completo, o vacío si no está."""
    respuesta = cliente.get("/api/measures/component", component=clave, metricKeys=metrica)
    medidas = respuesta.get("component", {}).get("measures", [])
    return medidas[0].get("value", "") if medidas else ""


def exportar(cliente: ClienteSonar, proyecto: str) -> None:
    clave = clave_extraccion(proyecto)
    metodos: dict[tuple[str, int], dict] = {}
    no_reconocidos = 0

    for regla in (REGLA_CICLOMATICA, REGLA_COGNITIVA):
        for issue in issues_abiertos(cliente, clave, regla):
            archivo = issue["component"].split(":", 1)[-1]
            linea = issue.get("textRange", {}).get("startLine", issue.get("line", 0))
            mensaje = issue.get("message", "")
            patron = PATRON_CICLOMATICA if regla == REGLA_CICLOMATICA else PATRON_COGNITIVA
            m = patron.search(mensaje)
            if not m:
                # Se cuenta y no se crea la fila: un mensaje ilegible no es un método medido.
                no_reconocidos += 1
                continue
            fila = metodos.setdefault((archivo, linea), {"archivo": archivo, "linea": linea})
            if regla == REGLA_CICLOMATICA:
                fila["metodo"], fila["ciclomatica"] = m.group(1), int(m.group(2))
            else:
                fila["cognitiva"] = int(m.group(1))

    for fila in metodos.values():
        if "cognitiva" in fila:
            fila["cognitiva_origen"] = "issue"
        elif fila.get("ciclomatica") == 1:
            # Sin puntos de decisión no hay nada que sume cognitiva: vale 0.
            fila["cognitiva"] = 0
            fila["cognitiva_origen"] = "cero"
        elif "ciclomatica" in fila:
            # Con puntos de decisión la cognitiva es al menos 1; si la regla no
            # saltó, SonarQube no la midió (métodos en constantes de enum o
            # clases anónimas). Se deja vacía en lugar de inventar un 0.
            fila["cognitiva_origen"] = "no medida"
    if no_reconocidos:
        aviso(f"{no_reconocidos} mensajes no coincidieron con el patrón esperado: revisar los patrones")

    # Controles de completitud del cruce entre las dos reglas.
    huerfanos = [f for f in metodos.values() if "ciclomatica" not in f]
    if huerfanos:
        ejemplos = ", ".join(f"{f['archivo']}:{f['linea']}" for f in huerfanos[:5])
        aviso(f"{len(huerfanos)} issues de S3776 sin par de S1541 en la misma línea (ej.: {ejemplos})")
    else:
        info("Cruce entre reglas: todos los issues de S3776 tienen su par de S1541")
    en_tests = sum(1 for f in metodos.values() if "/src/test/" in f"/{f['archivo']}")
    if en_tests:
        aviso(f"{en_tests} métodos están en archivos de test")
    completos = sum(1 for f in metodos.values() if "ciclomatica" in f)
    funciones = medida_proyecto(cliente, clave, "functions")
    ceros = sum(1 for f in metodos.values() if f.get("cognitiva_origen") == "cero")
    no_medidos = sum(1 for f in metodos.values() if f.get("cognitiva_origen") == "no medida")
    info(
        f"Métodos con ciclomática: {completos}; medida functions del proyecto: {funciones or '(sin dato)'} "
        f"(la diferencia esperable son los métodos sin cuerpo y equals/hashCode)"
    )
    info(f"Cognitiva: {completos - ceros - no_medidos} por issue, {ceros} en 0 por no tener puntos de decisión")
    if no_medidos:
        aviso(
            f"{no_medidos} métodos con ciclomática > 1 sin issue de S3776: cognitiva no medida por SonarQube "
            f"(quedan vacíos y fuera de la correlación)"
        )

    filas = sorted(metodos.values(), key=lambda f: (f["archivo"], f["linea"]))
    escribir_csv(
        DIR_DATOS / clave / "complejidad_metodo.csv",
        filas,
        ["archivo", "linea", "metodo", "ciclomatica", "cognitiva", "cognitiva_origen"],
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
