"""Eje 2 (sección 5.2): complejidad cognitiva frente a ciclomática (SCRUM-47 y SCRUM-48).

Lee ``datos/extraccion-<proyecto>/eje2_metodos.csv`` de los cuatro proyectos del
corpus (release nuevo) y escribe en ``resultados/eje2/``:

* ``descriptivos.csv``: distribución de cada métrica por proyecto (mínimo,
  cuartiles, media, percentil 90 y máximo), solo métodos medidos.
* ``correlaciones.csv``: Spearman entre ciclomática y cognitiva de SonarQube,
  por método y por archivo, por proyecto y en conjunto, con intervalo del 95 %
  (aproximación de Fieller, Hartley y Pearson, 1957) y la correlación parcial
  controlando el tamaño (NCSS de PMD, D1 y D5). Incluye un análisis de
  sensibilidad sin los métodos triviales (ciclomática 1).
* ``no_medidos.csv``: métodos con cognitiva ``no medida`` en SonarQube, con los
  valores de PMD (quedan fuera de la correlación y se informan aparte).
* ``acuerdo_herramientas.csv``: proporción de métodos en que SonarQube y PMD
  dan el mismo valor, y en qué dirección difieren (confiabilidad, 6.2).
* ``discrepancias.csv``: los métodos donde el orden según una métrica y según la
  otra más se separa, para la revisión cualitativa de SCRUM-48.

Decisiones (D5): Spearman porque las complejidades son conteos muy asimétricos;
la parcial se calcula como la correlación de Pearson parcial sobre los rangos;
los métodos ``no medida`` se excluyen; el nivel archivo suma los métodos
medidos de cada archivo, para mostrar cuánto infla la agregación.

Solo usa la biblioteca estándar.

Uso:
    python guiones/eje2_correlacion.py
"""

from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

from comun import DIR_DATOS, RAIZ, escribir_csv, info, leer_corpus

DIR_RESULTADOS = RAIZ / "resultados" / "eje2"
Z_95 = 1.959963984540054
# Para la revisión cualitativa solo interesan métodos con algo de lógica.
MINIMO_COMPLEJIDAD_DISCREPANCIA = 5
CANTIDAD_DISCREPANCIAS = 15


# ---------------------------------------------------------------------------
# Estadística (biblioteca estándar)
# ---------------------------------------------------------------------------


def rangos(valores: list[float]) -> list[float]:
    """Rangos con empates promediados (1 = menor), como en la definición de Spearman."""
    orden = sorted(range(len(valores)), key=valores.__getitem__)
    resultado = [0.0] * len(valores)
    i = 0
    while i < len(orden):
        j = i
        while j + 1 < len(orden) and valores[orden[j + 1]] == valores[orden[i]]:
            j += 1
        promedio = (i + j) / 2 + 1
        for k in range(i, j + 1):
            resultado[orden[k]] = promedio
        i = j + 1
    return resultado


def pearson(x: list[float], y: list[float]) -> float:
    mx, my = statistics.fmean(x), statistics.fmean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy) if sxx and syy else math.nan


def spearman(x: list[float], y: list[float]) -> float:
    return pearson(rangos(x), rangos(y))


def intervalo_spearman(rho: float, n: int) -> tuple[float, float]:
    """IC del 95 % por la transformación z de Fisher con el error 1,03/sqrt(n-3) de Fieller y col."""
    if n < 4 or abs(rho) >= 1:
        return (math.nan, math.nan)
    z = math.atanh(rho)
    error = 1.03 / math.sqrt(n - 3)
    return (math.tanh(z - Z_95 * error), math.tanh(z + Z_95 * error))


def parcial(rxy: float, rxz: float, ryz: float) -> float:
    """Correlación parcial de x e y dado z, a partir de las tres correlaciones."""
    return (rxy - rxz * ryz) / math.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))


def fila_correlacion(proyecto: str, nivel: str, subconjunto: str,
                     cic: list[float], cog: list[float], tam: list[float]) -> dict:
    """Spearman ciclomática-cognitiva, su IC, y la parcial controlando el tamaño."""
    r_cic, r_cog, r_tam = rangos(cic), rangos(cog), rangos(tam)
    rxy, rxz, ryz = pearson(r_cic, r_cog), pearson(r_cic, r_tam), pearson(r_cog, r_tam)
    rxy_p = parcial(rxy, rxz, ryz)
    inf, sup = intervalo_spearman(rxy, len(cic))
    # La parcial con una variable controlada pierde un grado de libertad.
    inf_p, sup_p = intervalo_spearman(rxy_p, len(cic) - 1)
    return {
        "proyecto": proyecto, "nivel": nivel, "subconjunto": subconjunto, "n": len(cic),
        "rho": round(rxy, 4), "rho_ic_inf": round(inf, 4), "rho_ic_sup": round(sup, 4),
        "rho_ciclomatica_tamano": round(rxz, 4), "rho_cognitiva_tamano": round(ryz, 4),
        "rho_parcial_tamano": round(rxy_p, 4), "parcial_ic_inf": round(inf_p, 4),
        "parcial_ic_sup": round(sup_p, 4),
    }


def describir(proyecto: str, metrica: str, valores: list[float]) -> dict:
    ordenados = sorted(valores)
    cuartiles = statistics.quantiles(ordenados, n=4, method="inclusive")
    p90 = statistics.quantiles(ordenados, n=10, method="inclusive")[-1]
    return {
        "proyecto": proyecto, "metrica": metrica, "n": len(valores),
        "minimo": ordenados[0], "q1": cuartiles[0], "mediana": cuartiles[1], "q3": cuartiles[2],
        "media": round(statistics.fmean(valores), 3), "p90": p90, "maximo": ordenados[-1],
        "proporcion_ceros": round(sum(v == 0 for v in valores) / len(valores), 4),
    }


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------


def leer_metodos() -> dict[str, list[dict]]:
    """Métodos del release nuevo de cada proyecto, en el orden de corpus.csv."""
    por_proyecto: dict[str, list[dict]] = {}
    for version in leer_corpus():
        if version.orden != 2:
            continue
        ruta = DIR_DATOS / f"extraccion-{version.proyecto}" / "eje2_metodos.csv"
        with ruta.open(encoding="utf-8", newline="") as archivo:
            filas = list(csv.DictReader(archivo))
        for fila in filas:
            fila["proyecto"] = version.proyecto
            fila["version"] = version.version
        por_proyecto[version.proyecto] = filas
        info(f"{version.proyecto} {version.version}: {len(filas)} métodos")
    return por_proyecto


def numero(texto: str) -> float | None:
    return float(texto) if texto not in ("", None) else None


def main() -> None:
    por_proyecto = leer_metodos()
    todos = [f for filas in por_proyecto.values() for f in filas]
    grupos = {**por_proyecto, "corpus": todos}

    descriptivos, correlaciones, acuerdo = [], [], []
    for nombre, filas in grupos.items():
        # Métodos con par en PMD (los que tienen // NOPMD no lo tienen) y cognitiva medida.
        con_par = [f for f in filas if f["ncss_pmd"] != ""]
        medidos = [f for f in con_par if f["cognitiva_origen"] != "no medida"]
        cic = [float(f["ciclomatica_sonar"]) for f in medidos]
        cog = [float(f["cognitiva_sonar"]) for f in medidos]
        tam = [float(f["ncss_pmd"]) for f in medidos]

        for metrica, valores in (("ciclomatica_sonar", cic), ("cognitiva_sonar", cog), ("ncss_pmd", tam)):
            descriptivos.append(describir(nombre, metrica, valores))

        correlaciones.append(fila_correlacion(nombre, "metodo", "medidos", cic, cog, tam))
        # Sensibilidad: sin métodos triviales (ciclomática 1, casi siempre cognitiva 0).
        no_triviales = [i for i, c in enumerate(cic) if c > 1]
        correlaciones.append(fila_correlacion(
            nombre, "metodo", "ciclomatica>1",
            [cic[i] for i in no_triviales], [cog[i] for i in no_triviales], [tam[i] for i in no_triviales]))
        # Como en la vista preliminar de la PT2: los no medidos contados como 0.
        con_ceros = [f for f in con_par]
        correlaciones.append(fila_correlacion(
            nombre, "metodo", "no medidos como 0",
            [float(f["ciclomatica_sonar"]) for f in con_ceros],
            [float(f["cognitiva_sonar"] or 0) for f in con_ceros],
            [float(f["ncss_pmd"]) for f in con_ceros]))

        # Nivel archivo: suma de los métodos medidos de cada archivo.
        archivos: dict[str, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0])
        for f in medidos:
            suma = archivos[(f["proyecto"], f["archivo"])]
            suma[0] += float(f["ciclomatica_sonar"])
            suma[1] += float(f["cognitiva_sonar"])
            suma[2] += float(f["ncss_pmd"])
        valores_archivo = list(archivos.values())
        correlaciones.append(fila_correlacion(
            nombre, "archivo", "suma de medidos",
            [v[0] for v in valores_archivo], [v[1] for v in valores_archivo], [v[2] for v in valores_archivo]))

        # Acuerdo entre implementaciones (solo métodos con par; cognitiva solo medidos).
        for metrica, base in (("ciclomatica", con_par), ("cognitiva", medidos)):
            sonar = [float(f[f"{metrica}_sonar"]) for f in base]
            pmd = [float(f[f"{metrica}_pmd"]) for f in base]
            iguales = sum(a == b for a, b in zip(sonar, pmd))
            acuerdo.append({
                "proyecto": nombre, "metrica": metrica, "n": len(base), "iguales": iguales,
                "proporcion_iguales": round(iguales / len(base), 4),
                "pmd_mayor": sum(b > a for a, b in zip(sonar, pmd)),
                "pmd_menor": sum(b < a for a, b in zip(sonar, pmd)),
                "rho_sonar_pmd": round(spearman(sonar, pmd), 4),
            })

    # No medidos por SonarQube, con lo que dice PMD.
    no_medidos = []
    for f in todos:
        if f["cognitiva_origen"] == "no medida":
            no_medidos.append({k: f[k] for k in ("proyecto", "archivo", "linea", "metodo", "ciclomatica_sonar",
                                                 "ciclomatica_pmd", "cognitiva_pmd", "ncss_pmd")})

    # Discrepancias: diferencia de rango percentil entre las dos métricas (corpus completo).
    medidos = [f for f in todos if f["cognitiva_origen"] != "no medida" and f["ncss_pmd"] != ""]
    n = len(medidos)
    r_cic = rangos([float(f["ciclomatica_sonar"]) for f in medidos])
    r_cog = rangos([float(f["cognitiva_sonar"]) for f in medidos])
    candidatos = []
    for f, a, b in zip(medidos, r_cic, r_cog):
        if max(float(f["ciclomatica_sonar"]), float(f["cognitiva_sonar"])) < MINIMO_COMPLEJIDAD_DISCREPANCIA:
            continue
        candidatos.append((round((b - a) / n, 4), f))
    candidatos.sort(key=lambda par: par[0])
    elegidos = ([("ciclomatica mayor", d, f) for d, f in candidatos[:CANTIDAD_DISCREPANCIAS]]
                + [("cognitiva mayor", d, f) for d, f in reversed(candidatos[-CANTIDAD_DISCREPANCIAS:])])
    discrepancias = [{
        "direccion": direccion, "diferencia_percentil": d, "proyecto": f["proyecto"], "version": f["version"],
        "archivo": f["archivo"], "linea": f["linea"], "metodo": f["metodo"],
        "ciclomatica_sonar": f["ciclomatica_sonar"], "cognitiva_sonar": f["cognitiva_sonar"],
        "ncss_pmd": f["ncss_pmd"],
    } for direccion, d, f in elegidos]

    DIR_RESULTADOS.mkdir(parents=True, exist_ok=True)
    escribir_csv(DIR_RESULTADOS / "descriptivos.csv", descriptivos, list(descriptivos[0]))
    escribir_csv(DIR_RESULTADOS / "correlaciones.csv", correlaciones, list(correlaciones[0]))
    escribir_csv(DIR_RESULTADOS / "acuerdo_herramientas.csv", acuerdo, list(acuerdo[0]))
    escribir_csv(DIR_RESULTADOS / "no_medidos.csv", no_medidos, list(no_medidos[0]))
    escribir_csv(DIR_RESULTADOS / "discrepancias.csv", discrepancias, list(discrepancias[0]))

    for fila in correlaciones:
        info(f"{fila['proyecto']:>20} {fila['nivel']:>7} {fila['subconjunto']:>18}: n={fila['n']:>6} "
             f"rho={fila['rho']:.3f} parcial={fila['rho_parcial_tamano']:.3f}")


if __name__ == "__main__":
    main()
