"""Fig. 6 de la sección 5.2: cognitiva frente a ciclomática, por método y por archivo.

Dos paneles con los datos de ``datos/extraccion-<proyecto>/eje2_metodos.csv``
(release nuevo de cada proyecto, métodos con cognitiva medida):
  (a) un punto por método; como hay miles de puntos repetidos (el 70 % de los
      métodos tiene ciclomática 1 y cognitiva 0), el tono indica cuántos
      métodos caen en cada celda;
  (b) un punto por archivo, con la suma de los métodos.
Los ejes usan escala logarítmica sobre valor + 1, para que entren los ceros.

Estilo de las figuras del artículo: fuente con serifa, escala de grises,
legible en blanco y negro, 800 dpi, ancho de la caja de LNCS (122 mm).

Uso:
    python guiones/figuras/figura_eje2_dispersion.py
Requiere matplotlib (ver requirements-figuras.txt).
"""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "guiones"))
from comun import DIR_DATOS, leer_corpus  # noqa: E402

DESTINO = RAIZ / "resultados" / "figuras" / "fig06_5-2_dispersion_complejidad.png"
ANCHO_MM, ALTO_MM = 122, 58
DPI = 800

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
})


def leer() -> list[dict]:
    filas = []
    for version in leer_corpus():
        if version.orden != 2:
            continue
        with (DIR_DATOS / f"extraccion-{version.proyecto}" / "eje2_metodos.csv").open(encoding="utf-8") as archivo:
            for fila in csv.DictReader(archivo):
                if fila["cognitiva_origen"] != "no medida":
                    fila["proyecto"] = version.proyecto
                    filas.append(fila)
    return filas


def preparar_eje(eje, titulo: str) -> None:
    eje.set_xscale("log")
    eje.set_yscale("log")
    eje.set_xlabel("Complejidad ciclomática + 1")
    eje.set_ylabel("Complejidad cognitiva + 1")
    eje.set_title(titulo, fontsize=8)
    eje.grid(True, which="major", linewidth=0.3, color="0.85")
    eje.set_axisbelow(True)


def main() -> None:
    filas = leer()
    figura, (eje_m, eje_a) = plt.subplots(1, 2, figsize=(ANCHO_MM / 25.4, ALTO_MM / 25.4), constrained_layout=True)

    # (a) Método: cada celda (ciclomática, cognitiva) con su frecuencia.
    celdas = Counter((int(f["ciclomatica_sonar"]), int(f["cognitiva_sonar"])) for f in filas)
    x = [c + 1 for c, _ in celdas]
    y = [g + 1 for _, g in celdas]
    n = list(celdas.values())
    puntos = eje_m.scatter(x, y, c=n, cmap="Greys", norm=LogNorm(vmin=1, vmax=max(n)), s=6,
                           edgecolors="0.15", linewidths=0.2)
    preparar_eje(eje_m, f"(a) Por método (n = {len(filas):,})".replace(",", "."))
    barra = figura.colorbar(puntos, ax=eje_m, pad=0.01, fraction=0.06)
    barra.set_label("Métodos por punto", fontsize=7)
    barra.ax.tick_params(labelsize=6)

    # (b) Archivo: suma de los métodos medidos.
    suma = defaultdict(lambda: [0, 0])
    for f in filas:
        s = suma[(f["proyecto"], f["archivo"])]
        s[0] += int(f["ciclomatica_sonar"])
        s[1] += int(f["cognitiva_sonar"])
    eje_a.scatter([v[0] + 1 for v in suma.values()], [v[1] + 1 for v in suma.values()],
                  s=5, facecolors="0.75", edgecolors="0.15", linewidths=0.25)
    preparar_eje(eje_a, f"(b) Por archivo (n = {len(suma):,})".replace(",", "."))

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    figura.savefig(DESTINO, dpi=DPI)
    print(f"Escrito {DESTINO.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
