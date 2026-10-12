"""Exporta a CSV los datos de un proyecto analizado en SonarQube.

Genera tres archivos en ``datos/<clave>/``:

* ``medidas_archivo.csv``: una fila por archivo de código con tamaño,
  complejidades, deuda técnica, ratio de deuda, calificación, duplicación,
  cobertura y cantidad de issues (insumo del eje 1).
* ``issues.csv``: una fila por issue con regla, tipo, severidad, archivo,
  línea y esfuerzo de remediación (insumo de los ejes 1 y 3).
* ``quality_gate.csv``: estado del gate y valor de cada condición (eje 3).

Antes de pedir las medidas consulta qué métricas existen en la instancia,
porque algunas cambian de nombre entre versiones (modo estándar y modo MQR).

Uso:
    python guiones/exportar_medidas.py prueba-pt1-jsoup
    python guiones/exportar_medidas.py corpus-jsoup
"""

from __future__ import annotations

import argparse
from collections import defaultdict

from comun import DIR_DATOS, ClienteSonar, ErrorSonar, aviso, escribir_csv, info, salir

# Métricas por archivo que se piden. Se agrupan por concepto; las que la
# instancia no tenga se omiten y se avisa (ver métricas_disponibles).
METRICAS_ARCHIVO = [
    # Tamaño
    "ncloc", "lines", "statements", "functions", "classes",
    # Complejidad (eje 2, nivel archivo)
    "complexity", "cognitive_complexity",
    # Deuda técnica y calificación, modo estándar (eje 1)
    "sqale_index", "sqale_debt_ratio", "sqale_rating", "code_smells",
    # Las mismas en modo MQR (taxonomía Clean Code), para comparar
    "software_quality_maintainability_remediation_effort",
    "software_quality_maintainability_debt_ratio",
    "software_quality_maintainability_rating",
    "software_quality_maintainability_issues",
    # Variables descriptivas (sección 3.2)
    "duplicated_lines_density", "coverage", "violations",
]

# La API de árbol de componentes acepta como máximo 15 métricas por pedido.
METRICAS_POR_PEDIDO = 15

# Las calificaciones vienen como número (1.0 = A ... 5.0 = E).
LETRAS = {"1.0": "A", "2.0": "B", "3.0": "C", "4.0": "D", "5.0": "E"}
METRICAS_CALIFICACION = {"sqale_rating", "software_quality_maintainability_rating"}


def metricas_disponibles(cliente: ClienteSonar, pedidas: list[str]) -> list[str]:
    """Filtra las métricas pedidas a las que existen en esta instancia."""
    existentes = {m["key"] for m in cliente.paginar("/api/metrics/search", "metrics")}
    faltantes = [m for m in pedidas if m not in existentes]
    if faltantes:
        aviso(f"Métricas que esta versión de SonarQube no tiene (se omiten): {', '.join(faltantes)}")
    return [m for m in pedidas if m in existentes]


def exportar_medidas_archivo(cliente: ClienteSonar, clave: str, metricas: list[str]) -> list[dict]:
    """Medidas de cada archivo del proyecto (calificador FIL)."""
    filas: dict[str, dict] = defaultdict(dict)
    for i in range(0, len(metricas), METRICAS_POR_PEDIDO):
        grupo = metricas[i : i + METRICAS_POR_PEDIDO]
        for componente in cliente.paginar(
            "/api/measures/component_tree",
            "components",
            component=clave,
            qualifiers="FIL",
            strategy="all",
            metricKeys=",".join(grupo),
        ):
            fila = filas[componente["key"]]
            fila["archivo"] = componente.get("path", componente["key"])
            fila["lenguaje"] = componente.get("language", "")
            for medida in componente.get("measures", []):
                valor = medida.get("value", "")
                if medida["metric"] in METRICAS_CALIFICACION:
                    fila[medida["metric"] + "_letra"] = LETRAS.get(valor, "")
                fila[medida["metric"]] = valor
    return sorted(filas.values(), key=lambda f: f["archivo"])


def _pagina_issues(cliente: ClienteSonar, clave: str, **filtros: str):
    return cliente.paginar(
        "/api/issues/search",
        "issues",
        componentKeys=clave,
        additionalFields="_all",
        **filtros,
    )


def exportar_issues(cliente: ClienteSonar, clave: str) -> list[dict]:
    """Todos los issues abiertos del proyecto.

    La API no devuelve más de 10.000 resultados por consulta. Si el proyecto
    tiene más, se parte la consulta por regla (ninguna regla sola debería
    superar el tope en este corpus) y se avisa si alguna lo supera.
    """
    total = cliente.get("/api/issues/search", componentKeys=clave, ps=1).get("total", 0)
    if total <= ClienteSonar.LIMITE_ISSUES:
        crudos = list(_pagina_issues(cliente, clave))
    else:
        info(f"{total} issues: supera el tope de la API, se consulta regla por regla")
        facetas = cliente.get("/api/issues/search", componentKeys=clave, ps=1, facets="rules")
        reglas = [v["val"] for f in facetas.get("facets", []) if f["property"] == "rules" for v in f["values"]]
        crudos = []
        for regla in reglas:
            parte = list(_pagina_issues(cliente, clave, rules=regla))
            if len(parte) >= ClienteSonar.LIMITE_ISSUES:
                aviso(f"La regla {regla} sola supera el tope: faltan issues")
            crudos += parte

    filas = []
    for issue in crudos:
        rango = issue.get("textRange", {})
        impactos = issue.get("impacts", [])
        filas.append(
            {
                "clave_issue": issue["key"],
                "regla": issue["rule"],
                "tipo": issue.get("type", ""),
                "severidad": issue.get("severity", ""),
                # Modo MQR: cualidad de software afectada y su severidad.
                "impactos": ";".join(f"{i['softwareQuality']}:{i['severity']}" for i in impactos),
                "atributo_clean_code": issue.get("cleanCodeAttribute", ""),
                "archivo": issue["component"].split(":", 1)[-1],
                "linea_inicio": rango.get("startLine", issue.get("line", "")),
                "linea_fin": rango.get("endLine", ""),
                "esfuerzo": issue.get("effort", ""),
                "estado": issue.get("issueStatus", issue.get("status", "")),
                "mensaje": issue.get("message", ""),
            }
        )
    return filas


def exportar_gate(cliente: ClienteSonar, clave: str) -> list[dict]:
    """Estado del Quality Gate y de cada una de sus condiciones."""
    estado = cliente.get("/api/qualitygates/project_status", projectKey=clave)["projectStatus"]
    filas = [{"condicion": "(gate)", "estado": estado["status"]}]
    for condicion in estado.get("conditions", []):
        filas.append(
            {
                "condicion": condicion["metricKey"],
                "estado": condicion["status"],
                "comparador": condicion.get("comparator", ""),
                "umbral": condicion.get("errorThreshold", ""),
                "valor": condicion.get("actualValue", ""),
            }
        )
    return filas


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("clave", help="clave del proyecto en SonarQube")
    args = parser.parse_args()

    cliente = ClienteSonar.desde_config()
    try:
        cliente.get("/api/components/show", component=args.clave)
    except ErrorSonar as error:
        if error.codigo == 404:
            salir(f"No existe el proyecto '{args.clave}' en SonarQube. ¿Ya corriste analizar.py?")
        raise

    destino = DIR_DATOS / args.clave
    metricas = metricas_disponibles(cliente, METRICAS_ARCHIVO)

    medidas = exportar_medidas_archivo(cliente, args.clave, metricas)
    columnas = ["archivo", "lenguaje"]
    for metrica in metricas:
        columnas.append(metrica)
        if metrica in METRICAS_CALIFICACION:
            columnas.append(metrica + "_letra")
    escribir_csv(destino / "medidas_archivo.csv", medidas, columnas)

    issues = exportar_issues(cliente, args.clave)
    escribir_csv(
        destino / "issues.csv",
        issues,
        ["clave_issue", "regla", "tipo", "severidad", "impactos", "atributo_clean_code",
         "archivo", "linea_inicio", "linea_fin", "esfuerzo", "estado", "mensaje"],
    )

    escribir_csv(
        destino / "quality_gate.csv",
        exportar_gate(cliente, args.clave),
        ["condicion", "estado", "comparador", "umbral", "valor"],
    )


if __name__ == "__main__":
    main()
