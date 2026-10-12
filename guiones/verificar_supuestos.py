"""Prueba técnica 1: confirma o refuta los supuestos que dan forma al eje 1.

Supuestos (ver SCRUM-21 y la decisión D5):
  S1. El ratio de deuda y la calificación de mantenibilidad existen por archivo,
      no solo por proyecto.
  S2. El costo de desarrollo por línea vale 30 minutos en la versión instalada.
  S3. La grilla de la calificación es 5 %, 10 %, 20 % y 50 % (A a E).
  S4. El ratio publicado por archivo coincide con la fórmula documentada:
      deuda / (costo por línea x líneas de código).

Lee ``datos/<clave>/medidas_archivo.csv`` (generado por exportar_medidas.py)
y la configuración del servidor, y escribe ``datos/<clave>/supuestos.md``.

Uso:
    python guiones/verificar_supuestos.py prueba-pt1-jsoup
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime

from comun import DIR_DATOS, RAIZ, ClienteSonar, info, salir

COSTO_ESPERADO = "30"
GRILLA_ESPERADA = "0.05,0.1,0.2,0.5"


def valor_ajuste(cliente: ClienteSonar, clave: str) -> tuple[str, str]:
    """Valor efectivo de un ajuste del servidor y si es el de fábrica."""
    respuesta = cliente.get("/api/settings/values", keys=clave)
    ajustes = respuesta.get("settings", [])
    if ajustes:
        ajuste = ajustes[0]
        origen = "valor de fábrica" if ajuste.get("inherited") else "configurado en la instancia"
        return ajuste.get("value", ""), origen
    # Si el ajuste no figura, rige el valor por defecto declarado en su definición.
    definiciones = cliente.get("/api/settings/list_definitions").get("definitions", [])
    for definicion in definiciones:
        if definicion["key"] == clave:
            return definicion.get("defaultValue", ""), "valor de fábrica, según la definición"
    return "", "no encontrado"


def a_float(texto: str) -> float | None:
    try:
        return float(texto)
    except (TypeError, ValueError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("clave", help="clave del proyecto ya exportado con exportar_medidas.py")
    args = parser.parse_args()

    ruta_medidas = DIR_DATOS / args.clave / "medidas_archivo.csv"
    if not ruta_medidas.exists():
        salir(f"Falta {ruta_medidas.relative_to(RAIZ)}. Corré antes exportar_medidas.py {args.clave}")
    with ruta_medidas.open(encoding="utf-8", newline="") as archivo:
        filas = list(csv.DictReader(archivo))

    cliente = ClienteSonar.desde_config()
    version = cliente.get("/api/system/status").get("version", "desconocida")
    costo, origen_costo = valor_ajuste(cliente, "sonar.technicalDebt.developmentCost")
    grilla, origen_grilla = valor_ajuste(cliente, "sonar.technicalDebt.ratingGrid")

    # S1: ¿cuántos archivos traen ratio y calificación?
    con_ratio = [f for f in filas if f.get("sqale_debt_ratio")]
    con_letra = [f for f in filas if f.get("sqale_rating_letra")]
    distribucion: dict[str, int] = {}
    for fila in con_letra:
        distribucion[fila["sqale_rating_letra"]] = distribucion.get(fila["sqale_rating_letra"], 0) + 1

    # S4: recalcula el ratio con la fórmula documentada y lo compara con el publicado.
    costo_min = a_float(costo) or 30.0
    diferencias = []
    for fila in filas:
        deuda = a_float(fila.get("sqale_index", ""))
        lineas = a_float(fila.get("ncloc", ""))
        publicado = a_float(fila.get("sqale_debt_ratio", ""))
        if deuda is None or not lineas or publicado is None:
            continue
        calculado = 100 * deuda / (costo_min * lineas)
        diferencias.append(abs(calculado - publicado))
    coincide = bool(diferencias) and max(diferencias) < 0.1  # el ratio viene redondeado a un decimal

    def veredicto(cumple: bool) -> str:
        return "confirmado" if cumple else "refutado"

    informe = f"""# Prueba técnica 1: supuestos del eje 1

Proyecto `{args.clave}`, SonarQube {version}. Generado por `guiones/verificar_supuestos.py` el {datetime.now():%Y-%m-%d %H:%M}.

| Supuesto | Resultado | Evidencia |
| --- | --- | --- |
| S1. Ratio y calificación existen por archivo | {veredicto(bool(con_ratio) and bool(con_letra))} | {len(con_ratio)} de {len(filas)} archivos con ratio; {len(con_letra)} con calificación |
| S2. Costo por línea = 30 min | {veredicto(costo == COSTO_ESPERADO)} | `sonar.technicalDebt.developmentCost` = {costo or '(vacío)'} ({origen_costo}) |
| S3. Grilla 5/10/20/50 % | {veredicto(grilla.replace(' ', '') == GRILLA_ESPERADA)} | `sonar.technicalDebt.ratingGrid` = {grilla or '(vacío)'} ({origen_grilla}) |
| S4. Ratio = deuda / (costo x líneas) | {veredicto(coincide)} | {len(diferencias)} archivos comparados; diferencia máxima {max(diferencias) if diferencias else 0:.3f} puntos |

## Distribución de archivos por calificación

| Letra | Archivos |
| --- | --- |
""" + "".join(f"| {letra} | {distribucion.get(letra, 0)} |\n" for letra in "ABCDE")

    destino = DIR_DATOS / args.clave / "supuestos.md"
    destino.write_text(informe, encoding="utf-8")
    print(informe)
    info(f"Escrito {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
