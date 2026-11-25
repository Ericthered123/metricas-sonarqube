"""Fig. 7 de la sección 5.2: complejidad de los archivos más complejos de jsoup.

Para los diez archivos de jsoup 1.23.2 con mayor complejidad ciclomática según
SonarQube, muestra la ciclomática y la cognitiva por archivo según SonarQube
(``datos/corpus-jsoup/medidas_archivo.csv``) y la cognitiva según PMD, sumada
por archivo desde ``datos/extraccion-jsoup/eje2_metodos.csv``.

En la suma de PMD se excluyen los métodos de clases anónimas que SonarQube no
mide, porque su complejidad ya está incluida en el método que los contiene
(especificación de Campbell; sección 5.2). Los métodos dentro de constantes de
enumeración sí se suman: no tienen método contenedor y SonarQube no los cuenta
en ningún lado. Los dos archivos de ese tipo se marcan en el eje.

Uso:
    python guiones/figuras/figura_eje2_enum.py
"""

import csv
from collections import defaultdict

from estilo import BORDE, GRIS_MEDIO, GRIS_OSCURO, RAIZ, guardar, plt, tamano

ARCHIVOS_ENUM = {"src/main/java/org/jsoup/parser/TokeniserState.java",
                 "src/main/java/org/jsoup/parser/HtmlTreeBuilderState.java"}
CANTIDAD = 10


def main() -> None:
    with (RAIZ / "datos" / "extraccion-jsoup" / "eje2_metodos.csv").open(encoding="utf-8") as archivo:
        metodos = list(csv.DictReader(archivo))
    cognitiva_pmd = defaultdict(int)
    for m in metodos:
        if m["cognitiva_origen"] == "no medida" and m["archivo"] not in ARCHIVOS_ENUM:
            continue  # método de clase anónima: ya contado en su contenedor
        cognitiva_pmd[m["archivo"]] += int(m["cognitiva_pmd"])

    with (RAIZ / "datos" / "corpus-jsoup" / "medidas_archivo.csv").open(encoding="utf-8") as archivo:
        medidas = {f["archivo"]: f for f in csv.DictReader(archivo) if f["lenguaje"] == "java"}
    top = sorted(medidas, key=lambda a: -int(medidas[a]["complexity"]))[:CANTIDAD]

    figura, eje = plt.subplots(figsize=tamano(68), constrained_layout=True)
    etiquetas = []
    for i, ruta in enumerate(reversed(top)):
        ciclomatica = int(medidas[ruta]["complexity"])
        cog_sonar = int(medidas[ruta]["cognitive_complexity"])
        cog_pmd = cognitiva_pmd[ruta]
        eje.plot([cog_sonar, cog_pmd], [i, i], color="0.6", linewidth=0.8, zorder=1)
        eje.scatter([ciclomatica], [i], s=16, marker="s", color=GRIS_MEDIO, edgecolors=BORDE, linewidths=0.4, zorder=2)
        eje.scatter([cog_pmd], [i], s=34, facecolors="white", edgecolors=BORDE, linewidths=0.6, zorder=3)
        eje.scatter([cog_sonar], [i], s=18, color=GRIS_OSCURO, edgecolors=BORDE, linewidths=0.4, zorder=4)
        nombre = ruta.split("/")[-1].removesuffix(".java")
        etiquetas.append(f"{nombre} (enum)" if ruta in ARCHIVOS_ENUM else nombre)

    eje.set_yticks(range(len(etiquetas)), etiquetas, fontsize=7)
    eje.set_xlim(0, 820)
    eje.set_xlabel("Complejidad por archivo")
    eje.grid(True, axis="x", linewidth=0.3, color="0.85")
    eje.set_axisbelow(True)
    eje.scatter([], [], s=16, marker="s", color=GRIS_MEDIO, edgecolors=BORDE, label="Ciclomática (SonarQube)")
    eje.scatter([], [], s=18, color=GRIS_OSCURO, edgecolors=BORDE, label="Cognitiva (SonarQube)")
    eje.scatter([], [], s=34, facecolors="white", edgecolors=BORDE, label="Cognitiva (PMD)")
    figura.legend(loc="outside lower center", ncol=3, fontsize=7, frameon=False)
    guardar(figura, "fig07_5-2_archivos_jsoup_enum.png")


if __name__ == "__main__":
    main()
