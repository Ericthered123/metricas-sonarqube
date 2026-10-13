"""Exporta al repositorio la configuración de SonarQube con la que se analiza el corpus (SCRUM-26).

Para que la sección 4.3 pueda citar la configuración tal cual, y para que
cualquiera pueda comprobar que su instancia es igual, se guarda en
``laboratorio/configuracion/``:

* ``perfil-java-comprehensive.xml`` y ``perfil-java-core.xml``: copia de
  respaldo de los dos perfiles de Java que se usan (principal y contraste, ver
  comun.PERFILES), en el formato que SonarQube permite volver a importar.
* ``reglas-perfil-java-comprehensive.csv`` y ``reglas-perfil-java-core.csv``:
  sus reglas activas, una por fila, con tipo, severidad e impactos.
* ``perfiles-java.csv``: todos los perfiles de Java de la instancia, con su
  cantidad de reglas y cuál es el predeterminado.
* ``quality-gate.json``: el Quality Gate por defecto y sus condiciones.
* ``ajustes.json``: versión de SonarQube, definición de código nuevo y los
  parámetros que afectan las medidas (costo por línea, grilla de la
  calificación, modo MQR, exclusiones, cambios chicos), con su valor vigente
  y su valor por defecto.

Con ``--verificar CLAVE ...`` además comprueba que cada proyecto usa el perfil
que le corresponde según su clave (comun.perfil_esperado) y el gate por
defecto, y termina con error si alguno no (control para SCRUM-27).

Uso:
    python guiones/exportar_configuracion.py
    python guiones/exportar_configuracion.py --verificar corpus-jsoup corpus-commons-io
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime

from comun import (
    DIR_LABORATORIO,
    PERFILES,
    RAIZ,
    ClienteSonar,
    ErrorSonar,
    aviso,
    escribir_csv,
    info,
    perfil_esperado,
    salir,
)

DIR_SALIDA = DIR_LABORATORIO / "configuracion"
LENGUAJE = "java"

# Parámetros que cambian lo que miden los ejes. Si la instancia no conoce
# alguno, se informa como "no existe en esta versión".
AJUSTES = [
    "sonar.technicalDebt.developmentCost",   # minutos por línea en el ratio de deuda (eje 1)
    "sonar.technicalDebt.ratingGrid",        # cortes de la letra de mantenibilidad (eje 1)
    "sonar.multi-quality-mode.enabled",      # modo MQR o estándar (taxonomía de issues)
    "sonar.qualitygate.ignoreSmallChanges",  # gate: ignora cobertura y duplicación con menos de 20 líneas nuevas (eje 3)
    "sonar.exclusions",
    "sonar.test.exclusions",
    "sonar.coverage.exclusions",
    "sonar.cpd.exclusions",
    "sonar.global.exclusions",
]


def perfiles_java(cliente: ClienteSonar) -> dict[str, dict]:
    """Todos los perfiles de calidad del lenguaje, indexados por nombre."""
    return {p["name"]: p for p in cliente.get("/api/qualityprofiles/search", language=LENGUAJE)["profiles"]}


def gate_por_defecto(cliente: ClienteSonar) -> dict:
    """El Quality Gate por defecto, con sus condiciones."""
    gates = cliente.get("/api/qualitygates/list")["qualitygates"]
    defecto = [g for g in gates if g.get("isDefault")]
    if len(defecto) != 1:
        salir(f"Se esperaba un Quality Gate por defecto y hay {len(defecto)}")
    return cliente.get("/api/qualitygates/show", name=defecto[0]["name"])


def reglas_activas(cliente: ClienteSonar, clave_perfil: str) -> list[dict]:
    """Reglas activas del perfil, una fila por regla."""
    filas = []
    # Sin el parámetro "f": en la 26.10 ya no acepta "type" ni otros campos de la
    # taxonomía estándar, y la respuesta por defecto trae lo que se usa acá. Lo
    # que no venga queda vacío.
    for regla in cliente.paginar("/api/rules/search", "rules", qprofile=clave_perfil, activation="true"):
        filas.append({
            "regla": regla["key"],
            "nombre": regla.get("name", ""),
            "tipo": regla.get("type", ""),
            "severidad": regla.get("severity", ""),
            "impactos": ";".join(f"{i['softwareQuality']}:{i['severity']}" for i in regla.get("impacts", [])),
            "atributo_clean_code": regla.get("cleanCodeAttribute", ""),
            "etiquetas": ";".join(regla.get("tags", [])),
        })
    return sorted(filas, key=lambda f: f["regla"])


def ajustes_vigentes(cliente: ClienteSonar) -> dict:
    """Valor vigente y valor por defecto de cada parámetro de AJUSTES."""
    definiciones = {d["key"]: d for d in cliente.get("/api/settings/list_definitions").get("definitions", [])}
    # Se consulta de a uno: si la versión no conoce una clave, la API puede
    # rechazar el pedido entero. Según la versión, /api/settings/values devuelve
    # o no los valores por defecto; por eso "modificado" compara contra la definición.
    cambiados = {}
    for clave in AJUSTES:
        try:
            ajustes = cliente.get("/api/settings/values", keys=clave).get("settings", [])
        except ErrorSonar:
            continue
        for v in ajustes:
            cambiados[v["key"]] = v.get("value", v.get("values", v.get("fieldValues")))
    resultado = {}
    for clave in AJUSTES:
        if clave not in definiciones and clave not in cambiados:
            resultado[clave] = "no existe en esta versión"
            continue
        por_defecto = definiciones.get(clave, {}).get("defaultValue", "")
        vigente = cambiados.get(clave, por_defecto)
        resultado[clave] = {
            "vigente": vigente,
            "por_defecto": por_defecto,
            "modificado": vigente not in (por_defecto, None, "", []),
        }
    return resultado


def verificar_proyectos(cliente: ClienteSonar, claves: list[str], gate: dict) -> None:
    """Termina con error si algún proyecto no usa el perfil que le corresponde o el gate por defecto."""
    problemas = []
    for clave in claves:
        perfiles = cliente.get("/api/qualityprofiles/search", project=clave, language=LENGUAJE)["profiles"]
        nombre_perfil = perfiles[0]["name"] if perfiles else "(ninguno)"
        nombre_gate = cliente.get("/api/qualitygates/get_by_project", project=clave)["qualityGate"]["name"]
        esperado = perfil_esperado(clave)
        bien = (esperado is None or nombre_perfil == esperado) and nombre_gate == gate["name"]
        info(f"{clave}: perfil '{nombre_perfil}', gate '{nombre_gate}' -> {'OK' if bien else 'DISTINTO'}")
        if not bien:
            problemas.append(clave)
    if problemas:
        salir(f"No usan la configuración por defecto: {', '.join(problemas)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verificar", nargs="+", metavar="CLAVE", help="proyectos a comprobar")
    args = parser.parse_args()

    cliente = ClienteSonar.desde_config()
    version = cliente.get("/api/system/status")["version"]
    perfiles = perfiles_java(cliente)
    gate = gate_por_defecto(cliente)

    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    escribir_csv(
        DIR_SALIDA / "perfiles-java.csv",
        [{"perfil": p["name"], "reglas_activas": p.get("activeRuleCount"), "predefinido": p.get("isBuiltIn"),
          "predeterminado": p.get("isDefault"), "reglas_actualizadas": p.get("rulesUpdatedAt")}
         for p in perfiles.values()],
        ["perfil", "reglas_activas", "predefinido", "predeterminado", "reglas_actualizadas"],
    )
    usados = {}
    for sufijo, nombre in PERFILES.items():
        if nombre not in perfiles:
            salir(f"La instancia no tiene el perfil '{nombre}'")
        perfil = perfiles[nombre]
        xml = cliente.get_texto("/api/qualityprofiles/backup", language=LENGUAJE, qualityProfile=nombre)
        (DIR_SALIDA / f"perfil-java-{sufijo}.xml").write_text(xml, encoding="utf-8")
        reglas = reglas_activas(cliente, perfil["key"])
        escribir_csv(DIR_SALIDA / f"reglas-perfil-java-{sufijo}.csv", reglas,
                     ["regla", "nombre", "tipo", "severidad", "impactos", "atributo_clean_code", "etiquetas"])
        if len(reglas) != perfil.get("activeRuleCount"):
            aviso(f"'{nombre}' informa {perfil.get('activeRuleCount')} reglas activas y se exportaron {len(reglas)}")
        usados[sufijo] = {"nombre": nombre, "predefinido": perfil.get("isBuiltIn"),
                          "reglas_activas": len(reglas), "reglas_actualizadas": perfil.get("rulesUpdatedAt")}
    predeterminado = next((n for n, p in perfiles.items() if p.get("isDefault")), "(ninguno)")

    condiciones = [
        {"metrica": c["metric"], "comparador": c["op"], "umbral": c["error"]} for c in gate.get("conditions", [])
    ]
    (DIR_SALIDA / "quality-gate.json").write_text(json.dumps({
        "nombre": gate["name"], "predefinido": gate.get("isBuiltIn"), "condiciones": condiciones,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    (DIR_SALIDA / "ajustes.json").write_text(json.dumps({
        "fecha_exportacion": datetime.now().isoformat(timespec="seconds"),
        "version_sonarqube": version,
        "perfiles_java": usados,
        "perfil_java_predeterminado": predeterminado,
        "codigo_nuevo": cliente.get("/api/new_code_periods/show"),
        "parametros": ajustes_vigentes(cliente),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    info("Escritos quality-gate.json y ajustes.json")

    info(f"SonarQube {version}; perfil predeterminado de Java: '{predeterminado}'")
    for sufijo, datos in usados.items():
        info(f"  {sufijo}: '{datos['nombre']}', {datos['reglas_activas']} reglas")
    info(f"Gate '{gate['name']}':")
    for c in condiciones:
        info(f"  {c['metrica']} {c['comparador']} {c['umbral']}")

    if args.verificar:
        verificar_proyectos(cliente, args.verificar, gate)


if __name__ == "__main__":
    main()
