"""Calcula la precisión y el acuerdo entre clasificadores de la sección 5.4 (SCRUM-56).

Lee de ``datos/<clave>/``:
  * ``issues.csv`` (exportar_medidas.py), para el tipo de calidad de cada issue;
  * ``clasificacion-eric.csv`` y ``clasificacion-brenda.csv``: las dos
    clasificaciones independientes, copias completas de la planilla;
  * ``clasificacion-consenso.csv`` (opcional): la categoría acordada después
    de discutir los desacuerdos (columnas ``clave_issue``, ``categoria``,
    ``motivo``). Solo hace falta que traiga los issues en desacuerdo.

Escribe en la misma carpeta:
  * ``desacuerdos-5-4.csv``: los issues en que los clasificadores difieren,
    con las dos categorías y notas, para la reunión de consenso;
  * ``acuerdo-5-4.csv``: acuerdo observado, kappa de Cohen con tres
    categorías y kappa binario (FP frente a no FP), y la matriz de confusión;
  * ``precision-5-4.csv``: precisión estricta R/N y amplia (R+I)/N con
    intervalo de Wilson del 95 %, por clasificador y para el consenso, en total,
    por tipo de calidad y por regla (reglas con al menos 5 issues).

Definiciones en ``docs/protocolo-5-4.md``, sección 6. Solo usa la biblioteca estándar.

Uso:
    python guiones/precision_5_4.py
    python guiones/precision_5_4.py --clave propio-poo2025
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter
from pathlib import Path

from comun import DIR_DATOS, RAIZ, escribir_csv, info, salir, aviso

CATEGORIAS = ("R", "I", "FP")
CLASIFICADORES = ("eric", "brenda")
MINIMO_POR_REGLA = 5
Z_95 = 1.959963984540054  # cuantil 0,975 de la normal estándar


# ---------------------------------------------------------------------------
# Estadística
# ---------------------------------------------------------------------------


def wilson(exitos: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Intervalo de confianza de Wilson para una proporción (Wilson, 1927)."""
    if n == 0:
        return (math.nan, math.nan)
    p = exitos / n
    denominador = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / denominador
    margen = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominador
    return (max(0.0, centro - margen), min(1.0, centro + margen))


def kappa_cohen(a: list[str], b: list[str]) -> tuple[float, float]:
    """Kappa de Cohen entre dos listas de etiquetas. Devuelve (acuerdo observado, kappa)."""
    n = len(a)
    observado = sum(x == y for x, y in zip(a, b)) / n
    frec_a, frec_b = Counter(a), Counter(b)
    esperado = sum(frec_a[c] * frec_b[c] for c in set(a) | set(b)) / (n * n)
    if esperado == 1:
        # Los dos usaron una sola y la misma categoría: kappa no está definido.
        return (observado, math.nan)
    return (observado, (observado - esperado) / (1 - esperado))


# ---------------------------------------------------------------------------
# Lectura y validación
# ---------------------------------------------------------------------------


def leer_clasificacion(ruta: Path, parcial: bool = False) -> dict[str, dict]:
    """Lee una planilla y devuelve sus filas por clave de issue, validando la categoría.

    Con ``parcial`` (planilla de consenso) se ignoran las filas sin categoría.
    """
    if not ruta.exists():
        salir(f"Falta {ruta.relative_to(RAIZ)}")
    with ruta.open(encoding="utf-8-sig", newline="") as archivo:
        texto = archivo.read()
    # Excel en español guarda los CSV con ";" como separador: se detecta solo.
    separador = csv.Sniffer().sniff(texto.splitlines()[0], delimiters=",;").delimiter
    filas = list(csv.DictReader(texto.splitlines(), delimiter=separador))
    resultado: dict[str, dict] = {}
    for fila in filas:
        categoria = (fila.get("categoria") or "").strip().upper()
        if parcial and not categoria:
            continue
        if categoria not in CATEGORIAS:
            salir(f"{ruta.name}, issue {fila.get('n')}: categoría '{fila.get('categoria')}' inválida "
                  f"(tiene que ser una de {', '.join(CATEGORIAS)})")
        fila["categoria"] = categoria
        resultado[fila["clave_issue"]] = fila
    return resultado


def tipo_calidad(impactos: str) -> str:
    """Tipo de calidad del primer impacto (MAINTAINABILITY:HIGH -> MAINTAINABILITY)."""
    primero = impactos.replace("|", ";").split(";")[0]
    return primero.split(":")[0] or "SIN_IMPACTO"


def fila_precision(origen: str, grupo: str, categorias: list[str]) -> dict:
    """Una fila de la tabla de precisión para un conjunto de categorías."""
    n = len(categorias)
    cuenta = Counter(categorias)
    estricta_inf, estricta_sup = wilson(cuenta["R"], n)
    amplia_inf, amplia_sup = wilson(cuenta["R"] + cuenta["I"], n)
    return {
        "origen": origen, "grupo": grupo, "n": n,
        "R": cuenta["R"], "I": cuenta["I"], "FP": cuenta["FP"],
        "precision_estricta": round(cuenta["R"] / n, 4),
        "estricta_ic_inf": round(estricta_inf, 4), "estricta_ic_sup": round(estricta_sup, 4),
        "precision_amplia": round((cuenta["R"] + cuenta["I"]) / n, 4),
        "amplia_ic_inf": round(amplia_inf, 4), "amplia_ic_sup": round(amplia_sup, 4),
    }


def tabla_precision(origen: str, categoria_por_issue: dict[str, str], issues: dict[str, dict]) -> list[dict]:
    """Precisión total, por tipo de calidad y por regla frecuente."""
    claves = list(categoria_por_issue)
    filas = [fila_precision(origen, "total", [categoria_por_issue[k] for k in claves])]
    for agrupador, nombre in ((lambda k: tipo_calidad(issues[k]["impactos"]), "tipo"),
                              (lambda k: issues[k]["regla"], "regla")):
        grupos: dict[str, list[str]] = {}
        for clave in claves:
            grupos.setdefault(agrupador(clave), []).append(categoria_por_issue[clave])
        for valor, categorias in sorted(grupos.items(), key=lambda par: -len(par[1])):
            if nombre == "regla" and len(categorias) < MINIMO_POR_REGLA:
                continue
            filas.append(fila_precision(origen, f"{nombre}={valor}", categorias))
    return filas


# ---------------------------------------------------------------------------
# Principal
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--clave", default="propio-poo2025")
    args = parser.parse_args()
    carpeta = DIR_DATOS / args.clave

    with (carpeta / "issues.csv").open(encoding="utf-8", newline="") as archivo:
        issues = {fila["clave_issue"]: fila for fila in csv.DictReader(archivo)}
    clasificaciones = {c: leer_clasificacion(carpeta / f"clasificacion-{c}.csv") for c in CLASIFICADORES}

    # Las dos planillas tienen que cubrir exactamente los mismos issues que el análisis.
    for nombre, filas in clasificaciones.items():
        faltan, sobran = set(issues) - set(filas), set(filas) - set(issues)
        if faltan or sobran:
            salir(f"clasificacion-{nombre}.csv no coincide con issues.csv: faltan {len(faltan)}, sobran {len(sobran)}")
    claves = sorted(issues, key=lambda k: int(clasificaciones["eric"][k]["n"]))
    eric = [clasificaciones["eric"][k]["categoria"] for k in claves]
    brenda = [clasificaciones["brenda"][k]["categoria"] for k in claves]

    # --- Acuerdo ------------------------------------------------------------
    observado, kappa3 = kappa_cohen(eric, brenda)
    binario = lambda lista: ["FP" if c == "FP" else "no FP" for c in lista]  # noqa: E731
    observado_bin, kappa_bin = kappa_cohen(binario(eric), binario(brenda))
    acuerdo = [
        {"medida": "n", "valor": len(claves)},
        {"medida": "acuerdo_observado_3", "valor": round(observado, 4)},
        {"medida": "kappa_3_categorias", "valor": round(kappa3, 4)},
        {"medida": "acuerdo_observado_binario", "valor": round(observado_bin, 4)},
        {"medida": "kappa_binario_FP", "valor": round(kappa_bin, 4)},
    ]
    matriz = Counter(zip(eric, brenda))
    for ce in CATEGORIAS:
        for cb in CATEGORIAS:
            acuerdo.append({"medida": f"matriz eric={ce} brenda={cb}", "valor": matriz[(ce, cb)]})
    escribir_csv(carpeta / "acuerdo-5-4.csv", acuerdo, ["medida", "valor"])

    # --- Desacuerdos para la reunión de consenso -----------------------------
    desacuerdos = []
    for clave in claves:
        fe, fb = clasificaciones["eric"][clave], clasificaciones["brenda"][clave]
        if fe["categoria"] != fb["categoria"]:
            desacuerdos.append({
                "n": fe["n"], "clave_issue": clave, "regla": fe["regla"], "archivo": fe["archivo"],
                "linea": fe["linea"], "mensaje": fe["mensaje"], "codigo": fe["codigo"],
                "eric": fe["categoria"], "nota_eric": fe.get("nota", ""),
                "brenda": fb["categoria"], "nota_brenda": fb.get("nota", ""),
                "categoria": "", "motivo": "",
            })
    escribir_csv(carpeta / "desacuerdos-5-4.csv", desacuerdos,
                 ["n", "clave_issue", "regla", "archivo", "linea", "mensaje", "codigo",
                  "eric", "nota_eric", "brenda", "nota_brenda", "categoria", "motivo"])

    # --- Precisión -----------------------------------------------------------
    filas = []
    for nombre in CLASIFICADORES:
        filas += tabla_precision(nombre, {k: clasificaciones[nombre][k]["categoria"] for k in claves}, issues)

    ruta_consenso = carpeta / "clasificacion-consenso.csv"
    if ruta_consenso.exists():
        acordadas = {k: f["categoria"] for k, f in leer_clasificacion(ruta_consenso, parcial=True).items()}
        consenso = {}
        for clave, categoria_eric, categoria_brenda in zip(claves, eric, brenda):
            if categoria_eric == categoria_brenda:
                consenso[clave] = categoria_eric
            elif acordadas.get(clave) in CATEGORIAS:
                consenso[clave] = acordadas[clave]
        sin_resolver = len(claves) - len(consenso)
        if sin_resolver:
            aviso(f"Consenso incompleto: {sin_resolver} desacuerdos sin categoría acordada; no se calcula")
        else:
            filas += tabla_precision("consenso", consenso, issues)
    else:
        info("Todavía no hay clasificacion-consenso.csv: se informa solo la precisión de cada clasificador")

    escribir_csv(carpeta / "precision-5-4.csv", filas, list(filas[0]))

    info(f"N = {len(claves)}; acuerdo observado {observado:.1%}; kappa (3 categorías) {kappa3:.3f}; "
         f"kappa binario FP {kappa_bin:.3f}; desacuerdos {len(desacuerdos)}")
    for fila in filas:
        if fila["grupo"] == "total":
            info(f"{fila['origen']}: estricta {fila['precision_estricta']:.1%} "
                 f"[{fila['estricta_ic_inf']:.1%}, {fila['estricta_ic_sup']:.1%}], "
                 f"amplia {fila['precision_amplia']:.1%} [{fila['amplia_ic_inf']:.1%}, {fila['amplia_ic_sup']:.1%}]")


if __name__ == "__main__":
    main()
