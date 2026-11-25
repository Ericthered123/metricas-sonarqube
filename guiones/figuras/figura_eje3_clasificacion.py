"""Fig. 9 de la sección 5.4: clasificación de los hallazgos por regla y por clasificador.

Lee ``datos/propio-poo2025/clasificacion-eric.csv``, ``clasificacion-brenda.csv`` y
``clasificacion-consenso.csv``. Para las reglas con más hallazgos, y el resto
agrupado, muestra cuántos hallazgos clasificó como R e I cada clasificador y el
consenso. Ningún clasificador usó FP. El desacuerdo es sistemático por regla:
bloques enteros cambian de categoría según quién clasifica.

Uso:
    python guiones/figuras/figura_eje3_clasificacion.py
"""

import csv
from collections import Counter

from matplotlib.patches import Patch

from estilo import BORDE, RAIZ, guardar, plt, tamano

plt.rcParams["hatch.color"] = "#B08A3E"   # rayado suave, del mismo tono que I
plt.rcParams["hatch.linewidth"] = 0.5

# Colores suaves con contorno oscuro (pauta de SCRUM-49). Las luminosidades son
# bien distintas (azul medio contra ámbar claro) y la categoría I lleva además un
# rayado, así que la figura se sigue leyendo impresa en blanco y negro.
COLOR_R = "#4C78A8"
COLOR_I = "#F2CF8A"
RAYADO_I = "////"

CARPETA = RAIZ / "datos" / "propio-poo2025"
REGLAS = [("java:S8688", "S8688\n.now() sin zona"), ("java:S1128", "S1128\nimport sin usar"),
          ("java:S125", "S125\ncódigo comentado"), ("java:S106", "S106\nSystem.out")]
CLASIFICADORES = [("eric", "Autor"), ("brenda", "Segunda"), ("consenso", "Consenso")]


def leer(nombre: str) -> dict[str, dict]:
    ruta = CARPETA / f"clasificacion-{nombre}.csv"
    texto = ruta.read_text(encoding="utf-8-sig")
    separador = csv.Sniffer().sniff(texto.splitlines()[0], delimiters=",;").delimiter
    return {f["clave_issue"]: f for f in csv.DictReader(texto.splitlines(), delimiter=separador)}


def main() -> None:
    eric, brenda = leer("eric"), leer("brenda")
    acordadas = {k: f["categoria"].strip().upper() for k, f in leer("consenso").items()}
    consenso = {k: (acordadas.get(k) or eric[k]["categoria"].strip().upper()) for k in eric}
    categorias = {
        "eric": {k: f["categoria"].strip().upper() for k, f in eric.items()},
        "brenda": {k: f["categoria"].strip().upper() for k, f in brenda.items()},
        "consenso": consenso,
    }
    regla_de = {k: f["regla"] for k, f in eric.items()}
    grupos = REGLAS + [("otras", "Otras\n9 reglas")]

    figura, ejes = plt.subplots(1, len(grupos), figsize=tamano(62), sharey=True, constrained_layout=True)
    for eje, (regla, titulo) in zip(ejes, grupos):
        claves = [k for k in regla_de if (regla_de[k] == regla) or (regla == "otras" and regla_de[k] not in dict(REGLAS))]
        for j, (nombre, etiqueta) in enumerate(CLASIFICADORES):
            cuenta = Counter(categorias[nombre][k] for k in claves)
            eje.bar(j, cuenta["R"], color=COLOR_R, edgecolor=BORDE, linewidth=0.4, width=0.7)
            eje.bar(j, cuenta["I"], bottom=cuenta["R"], color=COLOR_I, edgecolor=BORDE, linewidth=0.4, width=0.7,
                    hatch=RAYADO_I)
        eje.set_xticks(range(len(CLASIFICADORES)), [e for _, e in CLASIFICADORES], rotation=90, fontsize=7)
        eje.set_title(f"{titulo}\n(n = {len(claves)})", fontsize=7)
        eje.tick_params(axis="y", labelsize=7)
    ejes[0].set_ylabel("Hallazgos")
    figura.legend(handles=[Patch(facecolor=COLOR_R, edgecolor=BORDE, label="R: problema real"),
                           Patch(facecolor=COLOR_I, edgecolor=BORDE, hatch=RAYADO_I, label="I: real pero irrelevante")],
                  loc="outside lower center", ncol=2, fontsize=7, frameon=False)
    guardar(figura, "fig09_5-4_clasificacion_por_regla.png")


if __name__ == "__main__":
    main()
