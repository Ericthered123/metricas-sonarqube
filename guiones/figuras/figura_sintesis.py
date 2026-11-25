"""Fig. 10 de la sección 6.1: el recorrido del dato con el hallazgo principal de cada eje.

Retoma la cadena de la Fig. 2 (regla violada, issue, métrica, calificación,
Quality Gate, decisión) y ubica debajo de cada estación lo que mostró el
estudio. El tono de cada estación va de oscuro (medición confiable) a claro
(validez débil), que es la lectura de conjunto de la sección 6.1. Las cifras
están tomadas de resultados/ y datos/propio-poo2025/ (secciones 5.1 a 5.4).

Uso:
    python guiones/figuras/figura_sintesis.py
"""

from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from matplotlib.colors import LinearSegmentedColormap, to_hex

from estilo import BORDE, guardar, plt, tamano

# Escala de lectura: azul (medición confiable) a ámbar (validez débil).
ESCALA = LinearSegmentedColormap.from_list("confiabilidad", ["#2F5F8A", "#7FA6C9", "#F2CF8A", "#F6E3B8"])

ESTACIONES = ["Regla violada", "Issue", "Métrica", "Calificación\n(A a E)", "Quality Gate", "Decisión"]
# Tono de gris de cada estación: oscuro = confiable, claro = validez débil.
POSICIONES = [0.0, 0.0, 0.3, 0.62, 0.95, 0.95]   # lugar de cada estación en la escala
TONOS = [to_hex(ESCALA(p)) for p in POSICIONES]
# Hallazgo principal de cada estación (sección del artículo, texto).
HALLAZGOS = {
    1: ("5.4", "Los 60 hallazgos del proyecto propio son ciertos\n"
               "(0 falsos positivos), pero si conviene corregirlos\n"
               "depende de quién evalúa: κ = −0,30."),
    2: ("5.2", "La cognitiva ordena los métodos casi igual que la\n"
               "ciclomática (ρ parcial = 0,95); 87 métodos dentro\n"
               "de enumeraciones quedan sin medir."),
    3: ("5.1", "El 96,6 % de los archivos recibe la letra A, que\n"
               "refleja sobre todo el tamaño: 40 de los 48 archivos\n"
               "fuera de A tienen 50 líneas de código o menos."),
    4: ("5.3", "Con el umbral en cero, 1 o 189 issues nuevos dan\n"
               "la misma decisión; en un proyecto, el 92 % de esos\n"
               "issues está en el código de test."),
}


def main() -> None:
    figura, eje = plt.subplots(figsize=tamano(82))
    eje.set_xlim(0, 12.2)
    eje.set_ylim(-1.0, 6.2)
    eje.axis("off")

    x_caja, ancho, alto = 0.05, 2.35, 0.74
    paso = 1.05
    for i, (nombre, tono) in enumerate(zip(ESTACIONES, TONOS)):
        y = 5.6 - i * paso
        texto_color = "white" if POSICIONES[i] < 0.2 else "black"
        eje.add_patch(FancyBboxPatch((x_caja, y - alto / 2), ancho, alto, boxstyle="round,pad=0.03",
                                     facecolor=tono, edgecolor=BORDE, linewidth=0.6))
        eje.text(x_caja + ancho / 2, y, nombre, ha="center", va="center", fontsize=7, color=texto_color, linespacing=1.1)
        if i < len(ESTACIONES) - 1:
            eje.add_patch(FancyArrowPatch((x_caja + ancho / 2, y - alto / 2 - 0.02),
                                          (x_caja + ancho / 2, y - paso + alto / 2 + 0.02),
                                          arrowstyle="-|>", mutation_scale=7, linewidth=0.6, color=BORDE))
        if i in HALLAZGOS:
            seccion, texto = HALLAZGOS[i]
            eje.plot([x_caja + ancho + 0.05, 2.75], [y, y], color="0.4", linewidth=0.5, linestyle=":")
            eje.text(2.8, y, f"{seccion}", ha="left", va="center", fontsize=7, style="italic")
            eje.text(3.3, y, texto, ha="left", va="center", fontsize=6.6, linespacing=1.15)

    # Escala de lectura: de medición confiable a validez débil.
    pasos = 60
    for k in range(pasos):
        eje.add_patch(plt.Rectangle((3.3 + k * 8.5 / pasos, -0.75), 8.5 / pasos, 0.22,
                                    facecolor=ESCALA(k / (pasos - 1)), edgecolor="none"))
    eje.add_patch(plt.Rectangle((3.3, -0.75), 8.5, 0.22, facecolor="none", edgecolor=BORDE, linewidth=0.5))
    eje.text(3.3, -0.35, "Medición confiable", ha="left", va="center", fontsize=6.5)
    eje.text(11.8, -0.35, "Validez débil", ha="right", va="center", fontsize=6.5)

    figura.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    guardar(figura, "fig10_6-1_sintesis.png")


if __name__ == "__main__":
    main()
