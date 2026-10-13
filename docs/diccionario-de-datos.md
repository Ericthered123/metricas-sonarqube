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
| `tests`, `fallas`, `errores`, `omitidos` | Tests unitarios (Surefire), sumando los resúmenes que imprime Maven al final de cada ejecución. No se usan los reportes XML porque no incluyen las clases de test anidadas definidas en clases abstractas. Describen el build en este entorno, no la calidad del proyecto: algunos tests fallan por el entorno (contenedor como root, sitios externos). Ver la sección de SCRUM-22 en `docs/pruebas-tecnicas.md` |
| `tests_integracion`, `fallas_integracion` | Tests de integración (Failsafe) y cuántos fallaron, con o sin error. Solo jsoup los tiene |
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
| `coverage` | Cobertura de tests en %. Vacía si el archivo no tiene líneas para cubrir o si el análisis se corrió sin tests: en ese caso SonarQube informa 0,0 %, que no es una medición, y el guion lo borra | Razón |
| `violations` | Cantidad total de issues | Absoluta |
| `imputadas` | Métricas de la fila que el guion completó con su mejor valor, separadas por `;` | Nominal |

**Celdas vacías y mejor valor.** SonarQube no guarda, por archivo, las medidas que valen su mejor valor (por ejemplo deuda 0), y la API las devuelve vacías. En los archivos Java el guion completa con 0 las métricas de la lista `CERO_SI_VACIO` de `exportar_medidas.py` (deuda, ratio, code smells, issues de mantenibilidad, violaciones, complejidad cognitiva y duplicación) y lo anota en `imputadas`. La lista es explícita porque la API de métricas no informa el mejor valor de cada una. En la prueba 1 se verificó contra `issues.csv` que ningún archivo con deuda, ratio, code smells o violaciones vacías tiene issues que debieran haberlas sumado. Ejemplo de la prueba 1: `TokeniserState.java` tiene 10 min de deuda sobre 1.759 líneas, un ratio de 0,019 % que redondea a 0,0 y que la API no devuelve. La cobertura nunca se completa. En los archivos que no son Java (por ejemplo `pom.xml`), una celda vacía significa que SonarQube no informó esa medida.

**Resolución del ratio.** `sqale_debt_ratio` viene redondeado a un decimal. Para el eje 1 conviene calcularlo como `sqale_index / (30 x ncloc)` y usar el publicado como control.

## `datos/<clave>/medidas_proyecto.csv`

Una sola fila con las mismas medidas para el proyecto completo. Sirve para comparar con la suma de los archivos (supuesto S6 de la prueba 1) y para el análisis por proyecto del eje 3. No lleva `imputadas`: a nivel proyecto SonarQube informa todas las medidas.

Si la clave tiene período de código nuevo (desde su segundo análisis), la fila suma la definición del período y las medidas de código nuevo del proyecto:

| Columna | Descripción |
| --- | --- |
| `periodo_modo` | Criterio de código nuevo con que se calculó el último análisis (por ejemplo `PREVIOUS_VERSION`) |
| `periodo_parametro` | Referencia del criterio: con `PREVIOUS_VERSION`, la versión anterior |
| `periodo_fecha` | Comienzo del período: fecha del análisis de referencia |
| `new_*` | Las mismas columnas de `codigo_nuevo_archivo.csv`, para el proyecto completo |

## `datos/<clave>/issues.csv`

Una fila por issue abierto. `regla` es la clave de la regla (por ejemplo `java:S3776`), `tipo` y `severidad` son de la taxonomía estándar, `impactos` y `atributo_clean_code` de la taxonomía Clean Code, y `esfuerzo` es el tiempo de remediación que asigna la regla (por ejemplo `5min`).

`fecha_creacion` es la fecha que SonarQube le asigna al issue. Con historia de git sería la del último cambio de la línea; como los checkouts no la traen, es la del primer análisis de la clave que lo detectó. `codigo_nuevo` vale `sí` si el issue está en el período de código nuevo (filtro `inNewCodePeriod` de la API, el mismo criterio de `new_violations`), `no` si no, y queda vacía si la clave tiene un solo análisis.

## `datos/<clave>/codigo_nuevo_archivo.csv`

Una fila por archivo con las medidas de código nuevo. Solo existe si la clave tiene período de código nuevo. La API las devuelve en el campo `period` de cada medida y no en `value`.

| Columna | Descripción |
| --- | --- |
| `new_lines`, `new_lines_to_cover` | Líneas nuevas y líneas nuevas que se podrían cubrir con tests |
| `new_violations`, `new_code_smells` | Issues nuevos (todos, y solo los de mantenibilidad en la taxonomía estándar) |
| `new_technical_debt`, `new_sqale_debt_ratio`, `new_maintainability_rating` | Deuda, ratio y calificación del código nuevo, modo estándar (la calificación con su `_letra`) |
| `new_software_quality_maintainability_*` | Lo mismo en modo MQR |
| `new_duplicated_lines_density`, `new_coverage` | Las otras dos condiciones del gate por defecto. `new_coverage` queda vacía si el análisis se corrió sin tests |

No se imputa nada: una celda vacía puede significar que el archivo no tiene código nuevo o que SonarQube omitió el mejor valor. Como `medidas_archivo.csv`, solo trae archivos principales (calificador `FIL`): los de test no aparecen, aunque sí cuentan en el `new_lines` del proyecto (ver los resultados de la prueba técnica 3). `new_lines` cuenta líneas físicas, incluidas las vacías y los comentarios. Las métricas que la instancia no tiene se omiten con un aviso.

## `datos/diff-<proyecto>/archivos.csv`

Lo genera `diff_releases.py` con `git diff --no-index` entre los checkouts de los dos releases. Es la referencia independiente de SonarQube para la prueba técnica 3. Una fila por archivo `.java` que cambió.

| Columna | Descripción |
| --- | --- |
| `ambito` | `main` (`src/main/`), `test` (`src/test/`) u `otro` |
| `estado` | `agregado`, `modificado` o `borrado`. Un renombrado aparece como borrado más agregado |
| `agregadas`, `borradas` | Líneas agregadas y borradas según git. Una línea modificada cuenta como una borrada y una agregada |
| `agregadas_codigo` | Aproximación de las agregadas que son código: sin las vacías ni las que empiezan como comentario (`//`, `/*`, `*`) |

## `datos/<clave>/comparacion_codigo_nuevo.csv`

Lo genera `diff_releases.py <proyecto> --comparar <clave>`. Una fila por archivo `.java` presente en el release nuevo, con lo que cambió de verdad (`estado_real`, que puede ser `sin cambios`, `agregadas`, `agregadas_codigo`) al lado de lo que informó SonarQube (`new_lines`, `new_violations`, y `issues_nuevos`, que cuenta los issues con `codigo_nuevo = sí`). En las columnas de SonarQube, un vacío por archivo se toma como 0; si el archivo no figura en la exportación, quedan vacías.

## `datos/<clave>/quality_gate.csv`

Primera fila: el estado global del gate (`OK` o `ERROR`). Las siguientes: una por condición, con la métrica, el comparador, el umbral y el valor medido.

## `datos/extraccion-<proyecto>/complejidad_metodo.csv`

Una fila por método. `ciclomatica` sale del mensaje de `java:S1541` y `cognitiva` del de `java:S3776`. `cognitiva_origen` dice de dónde sale la cognitiva:

| Valor | Significado |
| --- | --- |
| `issue` | Leída del mensaje de `S3776` |
| `cero` | El método no generó issue de `S3776` y su ciclomática es 1 (ningún punto de decisión): la cognitiva es 0 |
| `no medida` | El método no generó issue de `S3776` pero su ciclomática es mayor que 1. Todo punto de decisión suma al menos 1 a la cognitiva, así que no puede ser 0: SonarQube no la calculó. En jsoup son los métodos declarados dentro de constantes de enum y de clases anónimas. La celda `cognitiva` queda vacía y el método no entra en la correlación |

No aparecen los métodos sin cuerpo (abstractos o de interfaces) ni `equals` y `hashCode`, que ninguna de las dos reglas informa. Por eso la cantidad de filas es menor que la medida `functions`.

## `datos/pmd-<proyecto>-<version>/metodos.csv`

Una fila por método o constructor según PMD 7.26.0. Lo genera `pmd_metodos.py exportar` a partir del reporte XML de `pmd_metodos.py correr`.

| Columna | Descripción | Escala |
| --- | --- | --- |
| `archivo`, `linea` | Ruta del archivo y línea del nombre del método (la misma que usa SonarQube) | Nominal |
| `metodo`, `tipo` | Nombre, y si es `method` o `constructor` | Nominal |
| `ciclomatica_pmd` | Complejidad ciclomática según la regla `CyclomaticComplexity` | Absoluta |
| `cognitiva_pmd` | Complejidad cognitiva según `CognitiveComplexity`. Con umbral 1 la regla calla cuando el valor es 0, así que un método sin informe de esta regla tiene 0 | Absoluta |
| `ncss_pmd` | Tamaño del método en sentencias (NCSS: sin comentarios ni líneas en blanco), según `NcssCount`. Es la medida de tamaño del eje 2, porque PMD no informa la línea final del método | Absoluta |

A diferencia de SonarQube, PMD informa también `equals`, `hashCode` y los métodos sin cuerpo.

## `datos/extraccion-<proyecto>/eje2_metodos.csv`

La tabla del eje 2: los métodos de `complejidad_metodo.csv` (SonarQube) cruzados con los de PMD por archivo y línea. Solo se arma si las dos fuentes son de la misma versión.

| Columna | Origen |
| --- | --- |
| `archivo`, `linea`, `metodo` | SonarQube |
| `ciclomatica_sonar`, `cognitiva_sonar`, `cognitiva_origen` | `complejidad_metodo.csv` (ver arriba) |
| `ciclomatica_pmd`, `cognitiva_pmd`, `ncss_pmd` | `metodos.csv` de PMD |
