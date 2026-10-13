# Prueba técnica 1: supuestos del eje 1

Proyecto `prueba-comp-jsoup`, SonarQube 26.10.0.133078. Generado por `guiones/verificar_supuestos.py` el 2026-10-13 14:19.

| Supuesto | Resultado | Evidencia |
| --- | --- | --- |
| S1. Ratio y calificación existen por archivo | confirmado | 72 de 96 archivos con ratio publicado y 23 completados con el mejor valor; 96 con calificación |
| S2. Costo por línea = 30 min | confirmado | `sonar.technicalDebt.developmentCost` = 30 (valor de fábrica) |
| S3. Grilla 5/10/20/50 % | confirmado | `sonar.technicalDebt.ratingGrid` = 0.05,0.1,0.2,0.5 (valor de fábrica) |
| S4. Ratio = deuda / (costo x líneas) | confirmado | 72 archivos con ratio publicado comparados; diferencia máxima 0.047 puntos |
| S5. Modo de la instancia | MQR (impactos sobre cualidades del software) | `sonar.multi-quality-mode.enabled` = true (configurado en la instancia) |
| S6. Deuda del proyecto = suma de los archivos de código | refutado | Proyecto 5778 min; archivos de código 4451 min; code smells en archivos que no están en las medidas (tests) 1327 min |

## Distribución de archivos por calificación

| Letra | Archivos |
| --- | --- |
| A | 92 |
| B | 3 |
| C | 1 |
| D | 0 |
| E | 0 |
