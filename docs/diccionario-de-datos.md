# Diccionario de datos

Qué contiene cada archivo de `datos/` y de dónde sale cada columna. Los nombres de las métricas son las claves de la API de SonarQube; su definición oficial está en la página "Understanding measures and metrics" de la documentación de SonarQube Community Build (ver la referencia [30] del artículo).

## `datos/compilacion.csv`

Una fila por versión del corpus. Lo genera `compilar_corpus.py`.

| Columna | Descripción |
| --- | --- |
| `proyecto`, `version`, `tag`, `commit` | Identificación de la versión, copiada de `corpus/corpus.csv` |
| `jdk`, `maven` | Versiones usadas por el contenedor de herramientas |
| `resultado` | `ok` si `mvn verify` terminó bien; si no, el código de salida |
| `duracion_s` | Duración del build en segundos |
| `tests`, `fallas`, `errores`, `omitidos` | Totales de los reportes de Surefire. Describen el build en este entorno, no la calidad del proyecto: algunos tests fallan por el entorno (contenedor como root, sitios externos). Ver la sección de SCRUM-22 en `docs/pruebas-tecnicas.md` |
| `fecha`, `log` | Momento de la corrida y nombre del log en `trabajo/logs/` |

## `datos/registro_analisis.csv`

Una fila por cada análisis lanzado con `analizar.py`: fecha, clave de SonarQube, versión, commit, opciones (tests, JaCoCo, fecha forzada), resultado y log. Sirve para reconstruir en qué orden se hizo cada análisis, que importa para el código nuevo del eje 3.

## `datos/<clave>/medidas_archivo.csv`

Una fila por archivo de código. Lo genera `exportar_medidas.py`.

| Columna | Descripción | Escala |
| --- | --- | --- |
| `archivo` | Ruta dentro del proyecto | Nominal |
| `ncloc` | Líneas de código sin comentarios ni líneas en blanco | Razón |
| `lines`, `statements`, `functions`, `classes` | Otras medidas de tamaño | Razón |
| `complexity` | Complejidad ciclomática del archivo (suma de la de sus métodos) | Razón |
| `cognitive_complexity` | Complejidad cognitiva del archivo | Razón |
| `sqale_index` | Deuda técnica en minutos (modo estándar) | Razón |
| `sqale_debt_ratio` | Ratio de deuda en %: deuda / (costo por línea x `ncloc`) | Razón |
| `sqale_rating`, `sqale_rating_letra` | Calificación de mantenibilidad, como número (1 a 5) y como letra (A a E) | Ordinal |
| `code_smells` | Cantidad de issues de mantenibilidad (modo estándar) | Absoluta |
| `software_quality_maintainability_*` | Las mismas medidas en modo MQR (taxonomía Clean Code) | Ídem |
| `duplicated_lines_density` | Porcentaje de líneas duplicadas | Razón |
| `coverage` | Cobertura de tests en % (vacía si no se midió) | Razón |
| `violations` | Cantidad total de issues | Absoluta |

Una celda vacía significa que SonarQube no informó esa medida para ese archivo.

## `datos/<clave>/issues.csv`

Una fila por issue abierto. `regla` es la clave de la regla (por ejemplo `java:S3776`), `tipo` y `severidad` son de la taxonomía estándar, `impactos` y `atributo_clean_code` de la taxonomía Clean Code, y `esfuerzo` es el tiempo de remediación que asigna la regla (por ejemplo `5min`).

## `datos/<clave>/quality_gate.csv`

Primera fila: el estado global del gate (`OK` o `ERROR`). Las siguientes: una por condición, con la métrica, el comparador, el umbral y el valor medido.

## `datos/extraccion-<proyecto>/complejidad_metodo.csv`

Una fila por método. `ciclomatica` sale del mensaje de `java:S1541` y `cognitiva` del de `java:S3776`. `cognitiva_imputada` vale `sí` cuando el método no generó issue de `S3776`, lo que significa complejidad cognitiva 0.
