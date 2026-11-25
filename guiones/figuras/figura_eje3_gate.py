"""Fig. 8 de la sección 5.3: issues nuevos que deciden el Quality Gate, por proyecto y perfil.

Lee ``resultados/eje3/gate_por_proyecto.csv`` (guiones/eje3_quality_gate.py). Para
cada proyecto y perfil muestra, en escala logarítmica, los issues nuevos totales
(cuadrado lleno) y los del código principal solamente (círculo vacío). La zona
sombreada es la de rechazo del Quality Gate Sonar way (más de 0 issues nuevos):
todos los análisis caen en ella, aunque los valores van de 1 a 189. El valor 0,
que el eje logarítmico no admite, se dibuja en una posición propia separada del
resto del eje.

Uso:
    python guiones/figuras/figura_eje3_gate.py
"""

import csv

from matplotlib.ticker import FixedLocator, NullLocator

from estilo import BORDE, GRIS_OSCURO, RAIZ, guardar, plt, tamano

NOMBRES = {"commons-io": "commons-io", "commons-collections": "commons-collections",
           "jsoup": "jsoup", "jfreechart": "JFreeChart"}
X_CERO = 0.5        # posición de dibujo del valor 0
X_MIN, X_MAX = 0.38, 320
MARCAS = [1, 3, 10, 30, 100]


def main() -> None:
    with (RAIZ / "resultados" / "eje3" / "gate_por_proyecto.csv").open(encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))

    figura, eje = plt.subplots(figsize=tamano(70))
    figura.subplots_adjust(left=0.27, right=0.86, top=0.88, bottom=0.2)

    # Zona de rechazo: 1 o más issues nuevos.
    eje.axvspan(0.75, X_MAX, color="0.93", zorder=0)
    eje.text(14, -0.95, "Zona de rechazo de Sonar way (1 o más issues nuevos)",
             ha="center", va="center", fontsize=6.5, style="italic", color="0.3")

    n = len(filas)
    proyecto_anterior = None
    for i, f in enumerate(filas):
        y = n - 1 - i
        total = int(f["issues_nuevos"])
        principal = total - int(f["issues_nuevos_en_test"])
        x_principal = principal if principal > 0 else X_CERO
        eje.plot([x_principal, total], [y, y], color="0.55", linewidth=0.8, zorder=1)
        # Círculo vacío grande (solo principal) y cuadrado lleno chico (total) encima.
        eje.scatter([x_principal], [y], s=40, facecolors="white", edgecolors=BORDE, linewidths=0.6, zorder=3)
        eje.scatter([total], [y], s=13, marker="s", color=GRIS_OSCURO, edgecolors=BORDE, linewidths=0.4, zorder=4)

        # Etiquetas: proyecto (una vez por par) y perfil.
        if f["proyecto"] != proyecto_anterior:
            eje.text(-0.40, y - 0.5, NOMBRES[f["proyecto"]], transform=eje.get_yaxis_transform(),
                     ha="left", va="center", fontsize=7.5)
            if proyecto_anterior is not None:
                eje.axhline(y + 0.5, color="0.75", linewidth=0.4, xmin=-0.41, clip_on=False)
            proyecto_anterior = f["proyecto"]
        eje.text(-0.02, y, "comp." if f["perfil"] == "comprehensive" else "core",
                 transform=eje.get_yaxis_transform(), ha="right", va="center", fontsize=7, color="0.25")

        # Decisión: un asterisco si sin los issues de test cambiaría.
        decision = "Rechaza" if f["gate_real"] == "rechaza" else "Aprueba"
        if f["gate_sin_issues_de_test"] != f["gate_real"]:
            decision += "*"
        eje.text(1.02, y, decision, transform=eje.get_yaxis_transform(), ha="left", va="center", fontsize=7)

    eje.text(1.02, n - 0.35, "Gate", transform=eje.get_yaxis_transform(), ha="left", va="bottom",
             fontsize=7, style="italic")
    eje.set_xscale("log")
    eje.set_xlim(X_MIN, X_MAX)
    eje.set_ylim(-1.3, n - 0.4)
    eje.xaxis.set_major_locator(FixedLocator([X_CERO] + MARCAS))
    eje.xaxis.set_minor_locator(NullLocator())
    eje.set_xticklabels(["0"] + [str(m) for m in MARCAS])
    eje.set_yticks([])
    eje.spines["left"].set_visible(False)
    eje.grid(True, axis="x", linewidth=0.3, color="0.82")
    eje.set_axisbelow(True)
    # Corte del eje entre el 0 y el 1 (el 0 no existe en escala logarítmica).
    for x in (0.62, 0.66):
        eje.plot([x, x], [-1.3, -1.05], color=BORDE, linewidth=0.6, clip_on=False, zorder=5)
    eje.set_xlabel("Issues nuevos en el código nuevo (escala logarítmica)")

    eje.scatter([], [], s=13, marker="s", color=GRIS_OSCURO, edgecolors=BORDE, label="Total")
    eje.scatter([], [], s=40, facecolors="white", edgecolors=BORDE, label="Solo código principal")
    figura.legend(loc="upper center", ncol=2, fontsize=7, frameon=False, bbox_to_anchor=(0.56, 1.0))
    figura.text(0.27, 0.025, "* Aprobaría si no se contaran los issues del código de test.",
                fontsize=6.5, style="italic")
    guardar(figura, "fig08_5-3_quality_gate.png")


if __name__ == "__main__":
    main()
