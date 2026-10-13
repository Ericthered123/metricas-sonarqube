"""Exporta a CSV los datos de un proyecto analizado en SonarQube.

Genera hasta cinco archivos en ``datos/<clave>/``:

* ``medidas_archivo.csv``: una fila por archivo de código con tamaño,
  complejidades, deuda técnica, ratio de deuda, calificación, duplicación,
  cobertura y cantidad de issues (insumo del eje 1).
* ``medidas_proyecto.csv``: las mismas medidas para el proyecto completo, para
  comparar con la suma de los archivos.
* ``issues.csv``: una fila por issue con regla, tipo, severidad, archivo,
  línea, esfuerzo de remediación, fecha de creación y si SonarQube lo cuenta
  como código nuevo (insumo de los ejes 1 y 3).
* ``quality_gate.csv``: estado del gate y valor de cada condición (eje 3).
* ``codigo_nuevo_archivo.csv``: medidas de código nuevo por archivo (líneas,
  issues y deuda nuevos). Solo se genera si la clave tiene período de código
  nuevo, es decir, desde el segundo análisis (prueba técnica 3, decisión D2).
  Las mismas medidas a nivel proyecto, junto con la definición del período,
  se agregan a ``medidas_proyecto.csv``.

Antes de pedir las medidas consulta qué métricas existen en la instancia,
porque algunas cambian de nombre entre versiones (modo estándar y modo MQR).

Dos correcciones para que cada celda diga lo que parece decir:

* Mejor valor omitido. SonarQube no guarda, por archivo, las medidas cuyo
  valor es el mejor posible (por ejemplo deuda 0), y la API las devuelve
  vacías. En los archivos Java se completan con 0 las métricas de
  ``CERO_SI_VACIO`` y la columna ``imputadas`` dice cuáles se completaron.
  La lista es explícita porque ``/api/metrics/search`` no informa el mejor
  valor de cada métrica (se comprobó en la prueba 1). La cobertura no se
  completa nunca (ver el punto siguiente).
* Cobertura sin tests. Si el último análisis de la clave se corrió sin tests
  (según ``datos/registro_analisis.csv``), SonarQube informa cobertura 0,0 %,
  que no es una medición: la columna ``coverage`` se deja vacía.

Uso:
    python guiones/exportar_medidas.py prueba-pt1-jsoup
    python guiones/exportar_medidas.py corpus-jsoup
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict

from comun import DIR_DATOS, ClienteSonar, ErrorSonar, aviso, escribir_csv, info, salir

ARCHIVO_REGISTRO = DIR_DATOS / "registro_analisis.csv"

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
METRICAS_CALIFICACION = {
    "sqale_rating", "software_quality_maintainability_rating",
    "new_maintainability_rating", "new_software_quality_maintainability_rating",
}

# Métricas de código nuevo (prueba técnica 3, decisión D2). Solo tienen valor
# cuando la clave tiene un período de código nuevo, es decir, a partir del
# segundo análisis. La API no las devuelve en "value" sino en "period": ver
# valor_de_medida. Se piden aparte de METRICAS_ARCHIVO para no mezclarlas con
# los insumos del eje 1, que se miden sobre todo el código.
METRICAS_CODIGO_NUEVO = [
    # Tamaño del código nuevo
    "new_lines", "new_lines_to_cover",
    # Issues nuevos (lo que evalúa el gate por defecto)
    "new_violations", "new_code_smells",
    # Deuda del código nuevo, modo estándar y modo MQR
    "new_technical_debt", "new_sqale_debt_ratio", "new_maintainability_rating",
    "new_software_quality_maintainability_issues",
    "new_software_quality_maintainability_remediation_effort",
    "new_software_quality_maintainability_debt_ratio",
    "new_software_quality_maintainability_rating",
    # Las otras dos condiciones del gate por defecto
    "new_duplicated_lines_density", "new_coverage",
]

# La imputación del mejor valor se limita al lenguaje del estudio: en otros
# archivos (por ejemplo pom.xml) algunas métricas, como la complejidad, no aplican.
LENGUAJES_IMPUTABLES = {"java"}

# Métricas cuyo mejor valor es 0 y que SonarQube omite por archivo cuando lo
# valen. Verificado en la prueba 1 (jsoup) contra issues.csv: en todos los
# archivos Java con deuda, ratio, code smells, issues de mantenibilidad o
# violaciones vacías no hay ningún issue que debiera haberlas sumado. La
# complejidad cognitiva y la duplicación no tienen un control cruzado posible
# con los datos exportados; se completan por la misma regla de mejor valor.
# La cobertura no está: su mejor valor es 100 % y un vacío puede significar
# "no hay líneas para cubrir" o "no se midió".
CERO_SI_VACIO = {
    "sqale_index": "0",
    "sqale_debt_ratio": "0.0",
    "code_smells": "0",
    "software_quality_maintainability_remediation_effort": "0",
    "software_quality_maintainability_debt_ratio": "0.0",
    "software_quality_maintainability_issues": "0",
    "violations": "0",
    "cognitive_complexity": "0",
    "duplicated_lines_density": "0.0",
}


def valor_de_medida(medida: dict) -> str:
    """Valor de una medida tal como lo devuelve la API de medidas.

    Las medidas comunes traen el valor en ``value``. Las de código nuevo
    (``new_*``) lo traen en ``period.value``, y las versiones viejas de la API
    usaban la lista ``periods``. Si no viene ninguno, devuelve cadena vacía.
    """
    if "value" in medida:
        return medida["value"]
    if "period" in medida:
        return medida["period"].get("value", "")
    periodos = medida.get("periods") or []
    return periodos[0].get("value", "") if periodos else ""


def definiciones_metricas(cliente: ClienteSonar) -> dict[str, dict]:
    """Definición de cada métrica de la instancia, indexada por su clave."""
    return {m["key"]: m for m in cliente.paginar("/api/metrics/search", "metrics")}


def metricas_disponibles(definiciones: dict[str, dict], pedidas: list[str]) -> list[str]:
    """Filtra las métricas pedidas a las que existen en esta instancia."""
    faltantes = [m for m in pedidas if m not in definiciones]
    if faltantes:
        aviso(f"Métricas que esta versión de SonarQube no tiene (se omiten): {', '.join(faltantes)}")
    return [m for m in pedidas if m in definiciones]


def mejores_valores(metricas: list[str]) -> dict[str, str]:
    """De las métricas exportadas, las que se completan con 0 cuando vienen vacías."""
    return {m: CERO_SI_VACIO[m] for m in metricas if m in CERO_SI_VACIO}


def imputar_mejores_valores(filas: list[dict], mejores: dict[str, str]) -> int:
    """Completa las medidas omitidas por ser el mejor valor. Devuelve cuántas celdas completó."""
    completadas = 0
    for fila in filas:
        imputadas = []
        if fila.get("lenguaje") in LENGUAJES_IMPUTABLES:
            for metrica, valor in mejores.items():
                if fila.get(metrica, "") == "":
                    fila[metrica] = valor
                    if metrica in METRICAS_CALIFICACION:
                        fila[metrica + "_letra"] = LETRAS.get(valor, "")
                    imputadas.append(metrica)
        fila["imputadas"] = ";".join(imputadas)
        completadas += len(imputadas)
    return completadas


def ultimo_analisis_sin_tests(clave: str) -> bool | None:
    """Dice si el último análisis registrado de la clave se corrió sin tests.

    Devuelve None si la clave no figura en el registro (por ejemplo, si el
    análisis no se lanzó con analizar.py).
    """
    if not ARCHIVO_REGISTRO.exists():
        return None
    with ARCHIVO_REGISTRO.open(encoding="utf-8", newline="") as archivo:
        filas = [f for f in csv.DictReader(archivo) if f.get("clave") == clave]
    if not filas:
        return None
    return filas[-1].get("tests") == "no"


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
                valor = valor_de_medida(medida)
                if medida["metric"] in METRICAS_CALIFICACION:
                    fila[medida["metric"] + "_letra"] = LETRAS.get(valor, "")
                fila[medida["metric"]] = valor
    return sorted(filas.values(), key=lambda f: f["archivo"])


def exportar_medidas_proyecto(cliente: ClienteSonar, clave: str, metricas: list[str]) -> dict:
    """Medidas del proyecto completo (incluye lo que no está en los archivos de código, como los tests)."""
    fila: dict = {"proyecto": clave}
    for i in range(0, len(metricas), METRICAS_POR_PEDIDO):
        grupo = metricas[i : i + METRICAS_POR_PEDIDO]
        respuesta = cliente.get("/api/measures/component", component=clave, metricKeys=",".join(grupo))
        for medida in respuesta.get("component", {}).get("measures", []):
            valor = valor_de_medida(medida)
            if medida["metric"] in METRICAS_CALIFICACION:
                fila[medida["metric"] + "_letra"] = LETRAS.get(valor, "")
            fila[medida["metric"]] = valor
    return fila


def periodo_codigo_nuevo(cliente: ClienteSonar, clave: str) -> dict[str, str]:
    """Definición del período de código nuevo con el que se calculó el último análisis.

    ``periodo_modo`` es el criterio (por ejemplo ``PREVIOUS_VERSION``),
    ``periodo_parametro`` la referencia (la versión anterior) y ``periodo_fecha``
    el comienzo del período. Quedan vacíos si la clave tiene un solo análisis.
    """
    respuesta = cliente.get(
        "/api/measures/component", component=clave, metricKeys="ncloc", additionalFields="period"
    )
    periodo = respuesta.get("period") or next(iter(respuesta.get("periods") or []), {})
    return {
        "periodo_modo": periodo.get("mode", ""),
        "periodo_parametro": periodo.get("parameter", ""),
        "periodo_fecha": periodo.get("date", ""),
    }


def claves_issues_codigo_nuevo(cliente: ClienteSonar, clave: str) -> set[str] | None:
    """Claves de los issues abiertos que SonarQube cuenta como código nuevo.

    Usa el filtro ``inNewCodePeriod`` de la API, que es el criterio con el que
    se calcula ``new_violations``: así la columna ``codigo_nuevo`` de
    issues.csv cuadra con la medida. Devuelve None si no se pudo obtener.
    """
    try:
        total = cliente.get(
            "/api/issues/search", componentKeys=clave, resolved="false", inNewCodePeriod="true", ps=1
        ).get("total", 0)
    except ErrorSonar as error:
        aviso(f"La API no aceptó el filtro inNewCodePeriod ({error}): codigo_nuevo queda vacía")
        return None
    if total > ClienteSonar.LIMITE_ISSUES:
        aviso(f"{total} issues en código nuevo superan el tope de la API: codigo_nuevo queda vacía")
        return None
    return {issue["key"] for issue in _pagina_issues(cliente, clave, inNewCodePeriod="true")}


def _pagina_issues(cliente: ClienteSonar, clave: str, **filtros: str):
    # resolved=false: solo issues abiertos. Sin este filtro la API devuelve también
    # los cerrados, y en las claves corpus-* (dos releases bajo la misma clave)
    # aparecerían los issues que se arreglaron entre una versión y la otra.
    return cliente.paginar(
        "/api/issues/search",
        "issues",
        componentKeys=clave,
        resolved="false",
        additionalFields="_all",
        **filtros,
    )


def exportar_issues(cliente: ClienteSonar, clave: str, nuevos: set[str] | None = None) -> list[dict]:
    """Todos los issues abiertos del proyecto (los cerrados no se exportan).

    ``nuevos`` son las claves de los issues en código nuevo (ver
    claves_issues_codigo_nuevo). Si es None, la columna codigo_nuevo queda vacía.

    La API no devuelve más de 10.000 resultados por consulta. Si el proyecto
    tiene más, se parte la consulta por regla (ninguna regla sola debería
    superar el tope en este corpus) y se avisa si alguna lo supera.
    """
    total = cliente.get("/api/issues/search", componentKeys=clave, resolved="false", ps=1).get("total", 0)
    if total <= ClienteSonar.LIMITE_ISSUES:
        crudos = list(_pagina_issues(cliente, clave))
    else:
        info(f"{total} issues: supera el tope de la API, se consulta regla por regla")
        facetas = cliente.get("/api/issues/search", componentKeys=clave, resolved="false", ps=1, facets="rules")
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
                # Sin historia de git (checkouts con --depth 1) SonarQube no puede
                # fechar el issue por la línea, y la fecha es la del análisis que
                # lo detectó por primera vez.
                "fecha_creacion": issue.get("creationDate", ""),
                "codigo_nuevo": "" if nuevos is None else ("sí" if issue["key"] in nuevos else "no"),
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
    definiciones = definiciones_metricas(cliente)
    metricas = metricas_disponibles(definiciones, METRICAS_ARCHIVO)
    columnas_metricas = []
    for metrica in metricas:
        columnas_metricas.append(metrica)
        if metrica in METRICAS_CALIFICACION:
            columnas_metricas.append(metrica + "_letra")

    medidas = exportar_medidas_archivo(cliente, args.clave, metricas)
    proyecto = exportar_medidas_proyecto(cliente, args.clave, metricas)

    # Código nuevo: solo si hay período (desde el segundo análisis de la clave).
    periodo = periodo_codigo_nuevo(cliente, args.clave)
    hay_periodo = bool(periodo["periodo_fecha"])
    metricas_nuevas = metricas_disponibles(definiciones, METRICAS_CODIGO_NUEVO) if hay_periodo else []
    columnas_nuevas = []
    for metrica in metricas_nuevas:
        columnas_nuevas.append(metrica)
        if metrica in METRICAS_CALIFICACION:
            columnas_nuevas.append(metrica + "_letra")
    medidas_nuevas: list[dict] = []
    if hay_periodo:
        info(f"Período de código nuevo: {periodo['periodo_modo']} {periodo['periodo_parametro']} "
             f"desde {periodo['periodo_fecha']}")
        # Sin imputación: un vacío por archivo puede ser "sin código nuevo" o
        # "mejor valor omitido", y la prueba técnica 3 es justamente la que mira eso.
        medidas_nuevas = exportar_medidas_archivo(cliente, args.clave, metricas_nuevas)
        proyecto.update(exportar_medidas_proyecto(cliente, args.clave, metricas_nuevas))
        proyecto.update(periodo)
    else:
        info("La clave no tiene período de código nuevo (un solo análisis): no se exportan medidas de código nuevo")

    mejores = mejores_valores(metricas)
    completadas = imputar_mejores_valores(medidas, mejores)
    info(
        f"Mejor valor completado en {completadas} celdas de archivos Java "
        f"(métricas: {', '.join(f'{m}={v}' for m, v in mejores.items()) or 'ninguna'})"
    )

    sin_tests = ultimo_analisis_sin_tests(args.clave)
    if sin_tests:
        for fila in [*medidas, *medidas_nuevas, proyecto]:
            for metrica in ("coverage", "new_coverage"):
                if metrica in fila:
                    fila[metrica] = ""
        info("El último análisis se corrió sin tests: la cobertura queda vacía")
    elif sin_tests is None:
        aviso(f"{args.clave} no figura en el registro de análisis: no se sabe si la cobertura es una medición")

    escribir_csv(destino / "medidas_archivo.csv", medidas, ["archivo", "lenguaje", *columnas_metricas, "imputadas"])
    columnas_periodo = ["periodo_modo", "periodo_parametro", "periodo_fecha"] if hay_periodo else []
    escribir_csv(
        destino / "medidas_proyecto.csv",
        [proyecto],
        ["proyecto", *columnas_metricas, *columnas_periodo, *columnas_nuevas],
    )
    if hay_periodo:
        escribir_csv(destino / "codigo_nuevo_archivo.csv", medidas_nuevas, ["archivo", "lenguaje", *columnas_nuevas])

    nuevos = claves_issues_codigo_nuevo(cliente, args.clave) if hay_periodo else None
    issues = exportar_issues(cliente, args.clave, nuevos)
    escribir_csv(
        destino / "issues.csv",
        issues,
        ["clave_issue", "regla", "tipo", "severidad", "impactos", "atributo_clean_code",
         "archivo", "linea_inicio", "linea_fin", "esfuerzo", "estado", "fecha_creacion", "codigo_nuevo",
         "mensaje"],
    )

    escribir_csv(
        destino / "quality_gate.csv",
        exportar_gate(cliente, args.clave),
        ["condicion", "estado", "comparador", "umbral", "valor"],
    )


if __name__ == "__main__":
    main()
