"""Estilo común de las figuras del artículo (plantilla del Simposio, basada en LNCS).

Fuente con serifa, escala de grises legible en blanco y negro, 800 dpi y ancho
de la caja de impresión de LNCS (122 mm).
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
DIR_FIGURAS = RAIZ / "resultados" / "figuras"
ANCHO_MM = 122
DPI = 800
GRIS_OSCURO, GRIS_MEDIO, GRIS_CLARO, BORDE = "0.25", "0.55", "0.85", "0.1"

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 8, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
})


def tamano(alto_mm: float) -> tuple[float, float]:
    """Tamaño de figura en pulgadas para el ancho de la caja y el alto dado."""
    return (ANCHO_MM / 25.4, alto_mm / 25.4)


def guardar(figura, nombre: str) -> None:
    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    destino = DIR_FIGURAS / nombre
    figura.savefig(destino, dpi=DPI)
    print(f"Escrito {destino.relative_to(RAIZ)}")
