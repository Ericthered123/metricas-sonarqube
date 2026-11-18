"""Eje 1 (sección 5.1): del ratio de deuda técnica a la letra de mantenibilidad.

Reemplaza a ``tabla51_calc.py`` (el cálculo que se usó para la muestra de
avances del 2026-10-19 y que no llegó a versionarse) y reproduce sus cifras.
Lee ``datos/corpus-<proyecto>/medidas_archivo.csv`` (perfil principal, D7) y,
como contraste, ``datos/corpus-core-<proyecto>/``; la unidad es el archivo Java
del código principal del release nuevo (D5). Escribe en ``resultados/eje1/``:

* ``archivos.csv``: un archivo por fila, con el ratio calculado como
  ``sqale_index / (30 × ncloc)`` (modelo clásico, D5), la letra que da la grilla,
  la letra publicada por SonarQube y la distancia al umbral más cercano;
* ``resumen.csv``: archivos por letra y por perfil, coincidencia de la grilla con
  la letra publicada (control de S3), coincidencia del modelo clásico con el MQR,
  archivos a ±0,5 y ±1 punto de un umbral, sensibilidad al costo por línea
  (15 y 60 minutos en lugar de 30) y tamaño de los archivos según su letra.

Grilla de Sonar (verificada en la PT1 y el 2026-10-18): A ≤ 5 %, B ≤ 10 %,
C ≤ 20 %, D ≤ 50 %, E > 50 %. Con exactamente 5 % la letra es A.

Solo usa la biblioteca estándar.

Uso:
    python guiones/eje1_calificacion.py
"""

from __future__ import annotations

import csv
import statistics

from comun import DIR_DATOS, RAIZ, escribir_csv, info, leer_corpus, salir

DIR_RESULTADOS = RAIZ / "resultados" / "eje1"
UMBRALES = ((0.05, "A"), (0.10, "B"), (0.20, "C"), (0.50, "D"))
COSTO_POR_LINEA = 30  # minutos, valor por defecto de SonarQube
COSTOS_SENSIBILIDAD = (15, 60)
DISTANCIAS = (0.005, 0.01)  # ±0,5 y ±1 punto porcentual (D5)
PERFILES = (("comprehensive", "corpus"), ("core", "corpus-core"))


def letra(ratio: float) -> str:
    """Letra de mantenibilidad para un ratio de deuda (fracción, no porcentaje)."""
    for umbral, nombre in UMBRALES:
        if ratio <= umbral + 1e-12:  # tolerancia para el borde exacto (5,00 % es A)
            return nombre
    return "E"


def distancia_umbral(ratio: float) -> float:
    return min(abs(ratio - umbral) for umbral, _ in UMBRALES)


def main() -> None:
    filas, resumen = [], []
    for perfil, prefijo in PERFILES:
        archivos = []
        for version in leer_corpus():
            if version.orden != 2:
                continue
            ruta = DIR_DATOS / f"{prefijo}-{version.proyecto}" / "medidas_archivo.csv"
            with ruta.open(encoding="utf-8", newline="") as archivo:
                for f in csv.DictReader(archivo):
                    if f["lenguaje"] != "java":
                        continue
                    ncloc, deuda = int(f["ncloc"]), int(f["sqale_index"])
                    ratio = deuda / (COSTO_POR_LINEA * ncloc)
                    archivos.append({
                        "perfil": perfil, "proyecto": version.proyecto, "archivo": f["archivo"],
                        "ncloc": ncloc, "sqale_index": deuda, "ratio": round(ratio, 6),
                        "letra_grilla": letra(ratio), "letra_sonar": f["sqale_rating_letra"],
                        "letra_mqr": f["software_quality_maintainability_rating_letra"],
                        "distancia_umbral": round(distancia_umbral(ratio), 6),
                        **{f"letra_{c}min": letra(deuda / (c * ncloc)) for c in COSTOS_SENSIBILIDAD},
                    })
        filas += archivos
        n = len(archivos)

        def agregar(medida: str, valor) -> None:
            resumen.append({"perfil": perfil, "medida": medida, "valor": valor})

        agregar("archivos_java", n)
        for nombre in ("A", "B", "C", "D", "E"):
            cantidad = sum(a["letra_grilla"] == nombre for a in archivos)
            agregar(f"letra_{nombre}", cantidad)
            agregar(f"letra_{nombre}_pct", round(100 * cantidad / n, 2))
        agregar("grilla_coincide_con_sonar", sum(a["letra_grilla"] == a["letra_sonar"] for a in archivos))
        agregar("clasico_coincide_con_mqr", sum(a["letra_sonar"] == a["letra_mqr"] for a in archivos))
        agregar("ratio_exactamente_5pct", sum(abs(a["ratio"] - 0.05) < 1e-9 for a in archivos))
        for d in DISTANCIAS:
            cerca = sum(a["distancia_umbral"] <= d + 1e-12 for a in archivos)
            agregar(f"a_menos_de_{d * 100:g}_puntos", cerca)
            agregar(f"a_menos_de_{d * 100:g}_puntos_pct", round(100 * cerca / n, 2))
        for c in COSTOS_SENSIBILIDAD:
            cambian = sum(a[f"letra_{c}min"] != a["letra_grilla"] for a in archivos)
            agregar(f"cambian_letra_con_{c}min", cambian)
            agregar(f"cambian_letra_con_{c}min_pct", round(100 * cambian / n, 2))
        no_a = [a["ncloc"] for a in archivos if a["letra_grilla"] != "A"]
        si_a = [a["ncloc"] for a in archivos if a["letra_grilla"] == "A"]
        if no_a:
            agregar("no_A_mediana_ncloc", statistics.median(no_a))
            agregar("no_A_maximo_ncloc", max(no_a))
            agregar("no_A_con_50_lineas_o_menos", sum(x <= 50 for x in no_a))
        agregar("A_mediana_ncloc", statistics.median(si_a))

        if any(a["letra_grilla"] != a["letra_sonar"] for a in archivos):
            salir(f"{perfil}: la grilla no reproduce la letra publicada en algún archivo (revisar S3)")

    DIR_RESULTADOS.mkdir(parents=True, exist_ok=True)
    escribir_csv(DIR_RESULTADOS / "archivos.csv", filas, list(filas[0]))
    escribir_csv(DIR_RESULTADOS / "resumen.csv", resumen, ["perfil", "medida", "valor"])
    for r in resumen:
        info(f"{r['perfil']:>13} {r['medida']:>32}: {r['valor']}")


if __name__ == "__main__":
    main()
