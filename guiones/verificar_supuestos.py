"""Prueba técnica 1: confirma o refuta los supuestos que dan forma al eje 1.

Supuestos (ver SCRUM-21 y la decisión D5):
  S1. El ratio de deuda y la calificación de mantenibilidad existen por archivo,
      no solo por proyecto.
  S2. El costo de desarrollo por línea vale 30 minutos en la versión instalada.
  S3. La grilla de la calificación es 5 %, 10 %, 20 % y 50 % (A a E).
  S4. El ratio publicado por archivo coincide con la fórmula documentada:
      deuda / (costo por línea x líneas de código).
  S5. Modo de la instancia: estándar (tipos y severidades) o MQR (impactos
      sobre cualidades del software). Es informativo: define qué deuda y qué
      calificación muestra la interfaz.
  S6. La deuda del proyecto es la suma de la deuda de sus archivos de código,
      es decir, no incluye la del código de test.

Lee ``datos/<clave>/medidas_archivo.csv``, ``medidas_proyecto.csv`` e
``issues.csv`` (generados por exportar_medidas.py) y la configuración del
servidor, y escribe ``datos/<clave>/supuestos.md``.

Uso:
    python guiones/verificar_supuestos.py prueba-pt1-jsoup
"""

from __future__ import annotations

import argparse
import csv
import re
from datetime import datetime
from pathlib import Path

from comun import DIR_DATOS, RAIZ, ClienteSonar, info, salir

COSTO_ESPERADO = "30"
GRILLA_ESPERADA = "0.05,0.1,0.2,0.5"
# Ajuste que activa el modo MQR (Multi-Quality Rule) desde SonarQube 10.8.
AJUSTE_MODO = "sonar.multi-quality-mode.enabled"
# Jornada que usa SonarQube para expresar el esfuerzo en días.
MINUTOS_POR_DIA = 8 * 60


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


def minutos(esfuerzo: str) -> int:
    """Convierte un esfuerzo de la API ("5min", "1h30min", "2d") a minutos."""
    total = 0
    for cantidad, unidad in re.findall(r"(\d+)\s*(d|h|min)", esfuerzo or ""):
        total += int(cantidad) * {"d": MINUTOS_POR_DIA, "h": 60, "min": 1}[unidad]
    return total


def leer_csv(ruta: Path) -> list[dict]:
    if not ruta.exists():
        salir(f"Falta {ruta.relative_to(RAIZ)}. Corré antes exportar_medidas.py")
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("clave", help="clave del proyecto ya exportado con exportar_medidas.py")
    args = parser.parse_args()

    carpeta = DIR_DATOS / args.clave
    filas = leer_csv(carpeta / "medidas_archivo.csv")
    proyecto = leer_csv(carpeta / "medidas_proyecto.csv")[0]
    issues = leer_csv(carpeta / "issues.csv")

    cliente = ClienteSonar.desde_config()
    version = cliente.get("/api/system/status").get("version", "desconocida")
    costo, origen_costo = valor_ajuste(cliente, "sonar.technicalDebt.developmentCost")
    grilla, origen_grilla = valor_ajuste(cliente, "sonar.technicalDebt.ratingGrid")
    modo, origen_modo = valor_ajuste(cliente, AJUSTE_MODO)

    def publicado(fila: dict, metrica: str) -> bool:
        """La medida vino de SonarQube y no fue completada con el mejor valor."""
        return fila.get(metrica, "") != "" and metrica not in fila.get("imputadas", "").split(";")

    # S1: ¿cuántos archivos traen ratio y calificación publicados por SonarQube?
    con_ratio = [f for f in filas if publicado(f, "sqale_debt_ratio")]
    ratio_imputado = [f for f in filas if f.get("sqale_debt_ratio") and not publicado(f, "sqale_debt_ratio")]
    con_letra = [f for f in filas if f.get("sqale_rating_letra")]
    distribucion: dict[str, int] = {}
    for fila in con_letra:
        distribucion[fila["sqale_rating_letra"]] = distribucion.get(fila["sqale_rating_letra"], 0) + 1

    # S4: recalcula el ratio con la fórmula documentada y lo compara con el publicado.
    # Solo se usan los ratios publicados: los completados con 0 no son mediciones.
    costo_min = a_float(costo) or 30.0
    diferencias = []
    for fila in con_ratio:
        deuda = a_float(fila.get("sqale_index", ""))
        lineas = a_float(fila.get("ncloc", ""))
        ratio = a_float(fila.get("sqale_debt_ratio", ""))
        if deuda is None or not lineas or ratio is None:
            continue
        diferencias.append(abs(100 * deuda / (costo_min * lineas) - ratio))
    coincide = bool(diferencias) and max(diferencias) < 0.1  # el ratio viene redondeado a un decimal

    # S5: modo de la instancia.
    if modo == "true":
        texto_modo = "MQR (impactos sobre cualidades del software)"
    elif modo == "false":
        texto_modo = "estándar (tipos y severidades)"
    else:
        texto_modo = "no determinado"

    # S6: deuda del proyecto contra la suma de la de sus archivos de código.
    deuda_proyecto = a_float(proyecto.get("sqale_index", "")) or 0.0
    deuda_archivos = sum(a_float(f.get("sqale_index", "")) or 0.0 for f in filas)
    rutas_codigo = {f["archivo"] for f in filas}
    deuda_fuera = sum(
        minutos(i["esfuerzo"]) for i in issues
        if i.get("tipo") == "CODE_SMELL" and i.get("archivo") not in rutas_codigo
    )
    s6 = abs(deuda_proyecto - deuda_archivos) < 1

    def veredicto(cumple: bool) -> str:
        return "confirmado" if cumple else "refutado"

    informe = f"""# Prueba técnica 1: supuestos del eje 1

Proyecto `{args.clave}`, SonarQube {version}. Generado por `guiones/verificar_supuestos.py` el {datetime.now():%Y-%m-%d %H:%M}.

| Supuesto | Resultado | Evidencia |
| --- | --- | --- |
| S1. Ratio y calificación existen por archivo | {veredicto(bool(con_ratio) and bool(con_letra))} | {len(con_ratio)} de {len(filas)} archivos con ratio publicado y {len(ratio_imputado)} completados con el mejor valor; {len(con_letra)} con calificación |
| S2. Costo por línea = 30 min | {veredicto(costo == COSTO_ESPERADO)} | `sonar.technicalDebt.developmentCost` = {costo or '(vacío)'} ({origen_costo}) |
| S3. Grilla 5/10/20/50 % | {veredicto(grilla.replace(' ', '') == GRILLA_ESPERADA)} | `sonar.technicalDebt.ratingGrid` = {grilla or '(vacío)'} ({origen_grilla}) |
| S4. Ratio = deuda / (costo x líneas) | {veredicto(coincide)} | {len(diferencias)} archivos con ratio publicado comparados; diferencia máxima {max(diferencias) if diferencias else 0:.3f} puntos |
| S5. Modo de la instancia | {texto_modo} | `{AJUSTE_MODO}` = {modo or '(vacío)'} ({origen_modo}) |
| S6. Deuda del proyecto = suma de los archivos de código | {veredicto(s6)} | Proyecto {deuda_proyecto:.0f} min; archivos de código {deuda_archivos:.0f} min; code smells en archivos que no están en las medidas (tests) {deuda_fuera} min |

## Distribución de archivos por calificación

| Letra | Archivos |
| --- | --- |
""" + "".join(f"| {letra} | {distribucion.get(letra, 0)} |\n" for letra in "ABCDE")

    destino = carpeta / "supuestos.md"
    destino.write_text(informe, encoding="utf-8")
    print(informe)
    info(f"Escrito {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
