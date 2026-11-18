"""Eje 3 (sección 5.3): el Quality Gate sobre el corpus (SCRUM-52).

Lee de ``datos/corpus-<proyecto>/`` y ``datos/corpus-core-<proyecto>/`` (corrida de
producción del 2026-10-13, D2 y D7) el resultado del gate "Sonar way", las
medidas de código nuevo y los issues, y escribe en ``resultados/eje3/``:

* ``gate_por_proyecto.csv``: una fila por proyecto y perfil, con el valor y el
  estado de cada condición, el tamaño del código nuevo y el resultado del gate
  en cuatro escenarios contrafácticos:
    - ``real``: lo que decidió SonarQube;
    - ``sin_cobertura``: sacando la condición de cobertura (pedido de SCRUM-52);
    - ``sin_issues_de_test``: contando en ``new_violations`` solo los issues
      nuevos del código principal (los del código de test también rechazan);
    - ``sin_ambos``: las dos cosas a la vez.
  El gate se vuelve a evaluar con el comparador y el umbral exportados de
  la instancia; el escenario ``real`` se controla contra el estado que dio
  SonarQube.
* ``issues_nuevos_por_regla.csv``: los issues nuevos por regla, cuántos están en
  código de test y su tipo de calidad.
* ``duplicacion_codigo_nuevo.csv``: los archivos con duplicación en el código
  nuevo, para entender qué hace fallar esa condición.

Son cuatro proyectos: el análisis es descriptivo, no estadístico (SCRUM-52).

Solo usa la biblioteca estándar.

Uso:
    python guiones/eje3_quality_gate.py
"""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict

from comun import DIR_DATOS, RAIZ, escribir_csv, info, leer_corpus, salir

DIR_RESULTADOS = RAIZ / "resultados" / "eje3"
PERFILES = (("comprehensive", "corpus"), ("core", "corpus-core"))
CONDICION_COBERTURA = "new_coverage"
CONDICION_ISSUES = "new_violations"
CODIGO_DE_TEST = re.compile(r"(^|/)src/test/")


def leer_csv(ruta) -> list[dict]:
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


def falla(valor: float, comparador: str, umbral: float) -> bool:
    """Una condición falla si el valor está del lado prohibido del umbral (API de SonarQube)."""
    if comparador == "GT":
        return valor > umbral
    if comparador == "LT":
        return valor < umbral
    salir(f"Comparador desconocido: {comparador}")
    raise AssertionError


def evaluar(condiciones: list[dict], valores: dict[str, float], omitir: set[str]) -> str:
    """Resultado del gate con los valores dados, sin las condiciones omitidas."""
    for c in condiciones:
        if c["condicion"] in omitir:
            continue
        if falla(valores[c["condicion"]], c["comparador"], float(c["umbral"])):
            return "rechaza"
    return "aprueba"


def main() -> None:
    proyectos = [v.proyecto for v in leer_corpus() if v.orden == 2]
    filas_gate, filas_reglas, filas_dup = [], [], []

    for proyecto in proyectos:
        for perfil, prefijo in PERFILES:
            carpeta = DIR_DATOS / f"{prefijo}-{proyecto}"
            gate = leer_csv(carpeta / "quality_gate.csv")
            estado_real = next(c["estado"] for c in gate if c["condicion"] == "(gate)")
            condiciones = [c for c in gate if c["condicion"] != "(gate)"]
            valores = {c["condicion"]: float(c["valor"]) for c in condiciones}
            medidas = leer_csv(carpeta / "medidas_proyecto.csv")[0]

            nuevos = [i for i in leer_csv(carpeta / "issues.csv") if i["codigo_nuevo"] == "sí"]
            en_test = sum(bool(CODIGO_DE_TEST.search(i["archivo"])) for i in nuevos)
            if len(nuevos) != int(valores[CONDICION_ISSUES]):
                salir(f"{prefijo}-{proyecto}: {len(nuevos)} issues nuevos en issues.csv y "
                      f"{valores[CONDICION_ISSUES]:g} en el gate")

            solo_principal = dict(valores, **{CONDICION_ISSUES: len(nuevos) - en_test})
            real = evaluar(condiciones, valores, set())
            # Control: la reevaluación tiene que dar lo mismo que SonarQube.
            if (real == "rechaza") != (estado_real == "ERROR"):
                salir(f"{prefijo}-{proyecto}: la reevaluación no coincide con el gate de SonarQube")

            fila = {
                "proyecto": proyecto, "perfil": perfil,
                "codigo_nuevo_desde": medidas.get("periodo_parametro", ""),
                "new_lines": medidas.get("new_lines", ""), "new_lines_to_cover": medidas.get("new_lines_to_cover", ""),
                "issues_nuevos": len(nuevos), "issues_nuevos_en_test": en_test,
            }
            for c in condiciones:
                fila[c["condicion"]] = c["valor"]
                fila[c["condicion"] + "_estado"] = "falla" if c["estado"] == "ERROR" else "ok"
            fila.update({
                "gate_real": real,
                "gate_sin_cobertura": evaluar(condiciones, valores, {CONDICION_COBERTURA}),
                "gate_sin_issues_de_test": evaluar(condiciones, solo_principal, set()),
                "gate_sin_ambos": evaluar(condiciones, solo_principal, {CONDICION_COBERTURA}),
            })
            filas_gate.append(fila)

            por_regla: dict[str, Counter] = defaultdict(Counter)
            for i in nuevos:
                por_regla[i["regla"]]["n"] += 1
                por_regla[i["regla"]]["en_test"] += bool(CODIGO_DE_TEST.search(i["archivo"]))
                por_regla[i["regla"]][i["impactos"].split(":")[0]] += 1
            for regla, cuenta in sorted(por_regla.items(), key=lambda par: -par[1]["n"]):
                tipo = max((k for k in cuenta if k not in ("n", "en_test")), key=cuenta.get)
                filas_reglas.append({"proyecto": proyecto, "perfil": perfil, "regla": regla,
                                     "issues_nuevos": cuenta["n"], "en_test": cuenta["en_test"], "tipo": tipo})

            if perfil == "comprehensive":  # la duplicación no depende del perfil
                for a in leer_csv(carpeta / "codigo_nuevo_archivo.csv"):
                    densidad = a.get("new_duplicated_lines_density") or ""
                    if densidad and float(densidad) > 0:
                        filas_dup.append({"proyecto": proyecto, "archivo": a["archivo"],
                                          "new_lines": a["new_lines"], "new_duplicated_lines_density": densidad})

    filas_dup.sort(key=lambda f: (f["proyecto"], -float(f["new_duplicated_lines_density"])))
    DIR_RESULTADOS.mkdir(parents=True, exist_ok=True)
    columnas = list(dict.fromkeys(k for f in filas_gate for k in f))
    escribir_csv(DIR_RESULTADOS / "gate_por_proyecto.csv", filas_gate, columnas)
    escribir_csv(DIR_RESULTADOS / "issues_nuevos_por_regla.csv", filas_reglas, list(filas_reglas[0]))
    escribir_csv(DIR_RESULTADOS / "duplicacion_codigo_nuevo.csv", filas_dup, list(filas_dup[0]))

    for f in filas_gate:
        info(f"{f['proyecto']:>20} {f['perfil']:>13}: real {f['gate_real']}, sin cobertura {f['gate_sin_cobertura']}, "
             f"sin issues de test {f['gate_sin_issues_de_test']} ({f['issues_nuevos_en_test']} de "
             f"{f['issues_nuevos']} en test), sin ambos {f['gate_sin_ambos']}")


if __name__ == "__main__":
    main()
