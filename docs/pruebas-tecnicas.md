# Pruebas técnicas

Las cuatro pruebas confirman, antes de comprometernos con un diseño, que el laboratorio puede producir los datos que necesita cada eje. Cada una tiene su tarea en Jira. Cuando una prueba se corre, sus resultados se escriben acá, debajo de su sección, con la fecha.

Estado al 2026-10-13: compilación del corpus (SCRUM-22) y pruebas técnicas 1 y 2 corridas; la 3 y la 4 todavía no.

**Cuándo se corren los tests (decidido el 2026-10-12).** `analizar.py` compila de nuevo en cada análisis y, por defecto, corre todos los tests. Los tests solo hacen falta para medir cobertura, así que se usa `--sin-tests` en las pruebas 1, 2 y 3 y en los análisis `extraccion-*`. La prueba 4 y los análisis principales `corpus-*` se corren con tests y `--jacoco` (decisión D2 bis). `--sin-tests` pasa `-DskipTests=true`, que compila los tests pero no los ejecuta: SonarQube sigue analizando el código de test con sus clases compiladas, y lo único que falta es la cobertura. En commons-io los tests tardan unos 11 minutos.

## Prueba técnica 1: punta a punta y medidas por archivo (SCRUM-21)

**Qué confirma.** Que SonarQube levanta, que un proyecto del corpus se analiza completo y que se pueden exportar por la API, para cada archivo, las medidas del eje 1. Además verifica cuatro supuestos, y desde el 2026-10-12 informa dos más (S5 y S6, ver los resultados):

| Supuesto | Por qué importa |
| --- | --- |
| S1. El ratio de deuda y la letra existen por archivo | El eje 1 usa el archivo como unidad de análisis (D5). Si solo existen por proyecto, hay que rediseñar el eje |
| S2. El costo de desarrollo por línea es 30 minutos | Es la constante del modelo de estimación que critica el eje 1 |
| S3. La grilla es 5, 10, 20 y 50 % | Define dónde están los bordes entre letras |
| S4. El ratio publicado coincide con deuda / (costo x líneas) | Confirma que la fórmula documentada es la que efectivamente aplica la herramienta |

**Cómo se corre.** Pasos 1 a 6 del README.

**Hecho cuando.** Existen `datos/prueba-pt1-jsoup/medidas_archivo.csv`, `issues.csv` y `supuestos.md`, y los cuatro supuestos están confirmados o refutados.

**Resultados (2026-10-12).** Corrida con `--sin-tests`; el análisis tardó 174 s. Los cuatro supuestos se confirman, pero con matices que cambian cómo hay que leer los datos.

| Supuesto | Resultado |
| --- | --- |
| S1 | Confirmado con un matiz. El ratio y la letra existen por archivo, pero la API no devuelve la deuda ni el ratio cuando valen su mejor valor (0). De los 96 archivos, 74 no traen ninguno de los dos (deuda 0) y `TokeniserState.java` trae deuda (10 min sobre 1.759 líneas) pero no ratio, porque 0,019 % redondea a 0,0. Un vacío en esas columnas significa 0, no falta de dato |
| S2 | Confirmado: 30 min por línea, valor de fábrica |
| S3 | Confirmado: 0.05, 0.1, 0.2 y 0.5, valor de fábrica |
| S4 | Confirmado en los 21 archivos con ratio. La diferencia máxima, 0,049 puntos, es el redondeo: el ratio publicado tiene un solo decimal |

Lo que dejó la prueba, además de los supuestos:

1. **Todo jsoup es A.** Los 96 archivos tienen A; el ratio más alto es 3,8 % y el del proyecto, 0,11 % (620 min sobre 18.941 líneas). En jsoup no hay ningún archivo cerca de un borde entre letras. Antes de cerrar D5 conviene ver cómo se distribuye el resto del corpus.
2. **El ratio publicado tiene resolución de 0,1 puntos.** Lo confirma la definición de la métrica en la API: `sqale_debt_ratio` tiene `decimalScale` 1 (respuesta guardada con `consultar_api.py /api/metrics/search --paginar metrics`). Para el eje 1 conviene calcular el ratio a partir de la deuda y las líneas (S4 confirma la fórmula) y usar el publicado como control. Queda por ver qué valor usa la herramienta para decidir la letra en el borde de 5 %: el redondeado o el exacto.
3. **Dos modelos, dos deudas.** El CSV trae las columnas del modelo clásico (`sqale_*`, por tipo de issue) y las del modelo por impactos (`software_quality_maintainability_*`). En jsoup no coinciden: 620 min contra 580 min en el código principal. La diferencia es la regla `java:S8786` (expresión regular con tiempo de ejecución excesivo), que en el modelo clásico es CODE_SMELL y en el nuevo tiene impacto RELIABILITY: suma 20 min de deuda en `HttpConnection.java` y en `Safelist.java` en un modelo y nada en el otro. Sirve para 3.2 y para la extensión del cambio de taxonomía. Además, en la API las dos calificaciones se llaman igual, "Maintainability Rating" (`sqale_rating` y `software_quality_maintainability_rating`): solo la clave dice de qué modelo es cada una. La instancia está en modo MQR (S5), así que la interfaz muestra la deuda y la letra del modelo por impactos.
4. **La deuda del proyecto incluye la del código de test, pero las líneas no.** `exportar_medidas.py` pide archivos con calificador `FIL`, y los de test tienen `UTS`, así que no están en las medidas por archivo. Hay 7 issues en código de test que suman 55 min. La deuda del proyecto es 675 min en el modelo clásico (620 de código principal más 55 de tests) y 635 en el de impactos (580 más 55), mientras que las líneas del proyecto (18.941) son solo las del código principal. El ratio del proyecto divide entonces una deuda de dos poblaciones por el tamaño de una sola (S6 refutado). En jsoup el efecto es chico, pero es un problema de validez de la medida para 5.1.
5. **Sin tests, la cobertura sale 0,0 y no vacía.** En 86 archivos figura 0,0 % (en 10 está vacía). No hay que usar la cobertura de ningún análisis corrido con `--sin-tests`.
6. **El gate aprueba en un primer análisis.** Sin un análisis anterior no hay código nuevo, y las cuatro condiciones de Sonar way no se evalúan. Para el eje 3 y la prueba 3.

Issues: 55 en total (32 code smells, 22 bugs y 1 vulnerabilidad).

**Supuestos agregados (corridos el 2026-10-12, 23:43).**

| Supuesto | Resultado |
| --- | --- |
| S5. Modo de la instancia | MQR: `sonar.multi-quality-mode.enabled` = true. No lo configuró ningún guion del laboratorio |
| S6. Deuda del proyecto = suma de los archivos de código | Refutado: incluye los 55 min del código de test (ver el hallazgo 4) |

**Cambios en los guiones a partir de la prueba (2026-10-12).** Para los hallazgos 1, 3, 4 y 5:

* `exportar_medidas.py` completa con 0 las medidas omitidas de los archivos Java (lista explícita, porque la API de métricas no informa el mejor valor: en la 26.10, `/api/metrics/search` solo trae clave, nombre, descripción, dominio, tipo, dirección, `qualitative`, `hidden` y `decimalScale`) y lo anota en la columna `imputadas`; deja vacía la cobertura si el análisis se corrió sin tests; y exporta también `medidas_proyecto.csv`.
* `verificar_supuestos.py` cuenta en S1 y S4 solo los ratios publicados, y agrega S5 (modo de la instancia, leído del ajuste `sonar.multi-quality-mode.enabled`) y S6 (si la deuda del proyecto es la suma de la de sus archivos de código o incluye la de los tests).

Hay que volver a correr `exportar_medidas.py` y `verificar_supuestos.py` sobre `prueba-pt1-jsoup`; no hace falta repetir el análisis.

## Prueba técnica 2: complejidad por método (SCRUM-23)

**Qué confirma.** Que se puede obtener la complejidad ciclomática y la cognitiva de cada método a partir de los mensajes de las reglas `java:S1541` y `java:S3776`, con un perfil de extracción y una clave de proyecto aparte (decisión D1).

**Cómo se corre.**

```
python guiones/complejidad_por_metodo.py perfil jsoup
python guiones/analizar.py jsoup 1.23.2 --clave extraccion-jsoup --sin-tests
python guiones/complejidad_por_metodo.py exportar jsoup
```

**A verificar en esta prueba.**

* Que las dos reglas existen en la versión instalada y cómo se llama su parámetro de umbral (el guion lo lee de la definición de cada regla y lo informa).
* Que los patrones de los mensajes coinciden: el guion avisa si algún mensaje no se pudo leer.
* Cuántos métodos aparecen solo en una de las dos reglas. Los que tienen cognitiva 0 no generan issue de `S3776` y se imputan como 0.
* Cómo obtener el tamaño de cada método: la ubicación del issue es el nombre del método, no su cuerpo, así que no sale de acá. D5 lo necesita para la correlación controlada por tamaño.
* Los controles que informa `exportar` (agregados el 2026-10-12): issues de `S3776` sin su par de `S1541` en la misma línea (tienen que ser 0), métodos extraídos contra la medida `functions` del proyecto (la diferencia esperable son los métodos sin cuerpo, de interfaces o abstractos) y métodos en archivos de test.

**Hecho cuando.** Existe `datos/extraccion-jsoup/complejidad_metodo.csv`, los patrones leen todos los mensajes, el cruce entre reglas no deja huérfanos (o se explica por qué), y está decidido cómo se obtiene el tamaño del método.

**Cambios previos a la corrida (2026-10-12).** El guion solo lee issues abiertos (`resolved=false`), consulta archivo por archivo si una regla supera el tope de 10.000 resultados de la API (jfreechart puede pasarlo) y no crea filas para mensajes que no reconoce. El mismo filtro de issues abiertos se agregó a `exportar_medidas.py`: sin él, en las claves `corpus-*` aparecerían los issues que se arreglaron entre un release y el otro.

**Plan B.** Calcular ambas métricas con una herramienta externa.

**Resultados (2026-10-13).** El perfil de extracción funciona con umbral 0 en las dos reglas, los patrones leyeron todos los mensajes y el cruce entre reglas no dejó huérfanos. SonarQube procesó el análisis en 7 s (2.858 issues: 2.088 de `S1541` y 770 de `S3776`). El comando tardó 1.116 s, pero no por el análisis: Maven terminó a los 2:44 min y el resto fue la consola de Windows bloqueada en modo selección (ver más abajo).

| Control | Resultado |
| --- | --- |
| Métodos extraídos | 2.088 en 85 archivos, ninguno de test |
| Medida `functions` del proyecto | 2.130. La diferencia (42) son `equals` y `hashCode` (17 en el código, 0 en la extracción: ninguna de las dos reglas los informa) y métodos sin cuerpo |
| Issues de `S3776` sin par de `S1541` | 0 |
| Suma por archivo contra la medida del archivo | Ciclomática igual en 67 de 85 archivos, cognitiva en 76. En esos archivos la suma es menor que la medida: al menos parte de la diferencia son `equals` y `hashCode`, que las reglas no informan pero la medida del archivo sí cuenta. No se verificó método por método |

**Hallazgo: SonarQube no calcula la complejidad cognitiva de los métodos declarados dentro de constantes de enum ni de clases anónimas.** Al clasificar cada método por el bloque que lo contiene, los 731 métodos de clases con nombre que tienen ciclomática mayor que 1 tienen todos cognitiva mayor que 0; en cambio, los 85 de constantes de enum y los 3 de clases anónimas con ciclomática mayor que 1 no generaron issue de `S3776`. No es que valgan 0: todo punto de decisión que cuenta la ciclomática suma al menos 1 a la cognitiva. La medida por archivo tampoco los cuenta: `HtmlTreeBuilderState.java` (la máquina de estados del parser, hecha con un enum) tiene ciclomática 539 y cognitiva 6, y su método `inBodyStartTag` tiene ciclomática 119 y ninguna cognitiva. Es un problema de cobertura del instrumento para el eje 2 (5.2) y para 6.2: el archivo más complejo de jsoup parece trivial según la cognitiva. Falta contrastarlo con la especificación de la métrica (Campbell, 2018), para saber si es una decisión de la especificación o de la implementación.

**Consecuencia en el guion.** La primera versión imputaba 0 a todo método sin issue de `S3776`, lo que metía 88 ceros falsos. Ahora imputa 0 solo si la ciclomática es 1 y deja la cognitiva vacía (`no medida`) en los demás casos (ver el diccionario de datos).

**Vista preliminar de la correlación** (Spearman, sin controlar el tamaño, solo para dimensionar; el análisis de 5.2 lo hace el integrante 3). Con los 88 ceros falsos: 0,852. Sin ellos (2.000 métodos): 0,975. Solo métodos con ciclomática mayor que 1 (744): 0,906. El error de imputación bajaba la correlación de forma notable, así que el tratamiento de los no medidos importa para el resultado.

**Tamaño del método y segunda implementación: PMD (2026-10-13).** Se eligió PMD 7.26.0 en lugar de medir el tamaño con un guion propio: además del tamaño da una implementación independiente de las dos complejidades. Corre en el contenedor de herramientas sobre el código fuente (jsoup tardó 573 s, lento; antes de la corrida de producción conviene probar `--aux-classpath` con las clases compiladas):

```
python guiones/pmd_metodos.py instalar
python guiones/pmd_metodos.py correr jsoup 1.23.2
python guiones/pmd_metodos.py exportar jsoup 1.23.2
```

| Control | Resultado |
| --- | --- |
| Métodos de SonarQube con par en PMD (por archivo y línea) | 2.088 de 2.088. PMD informa 155 más: `equals`, `hashCode` y métodos sin cuerpo |
| Mensajes de PMD no leídos | 0 |
| Cognitiva 0 en SonarQube (imputada por ciclomática 1) | 0 también en PMD en los 1.230 |
| Cognitiva no medida por SonarQube | Mayor que 0 en PMD en los 88. `HtmlTreeBuilderState.java`: 6 en SonarQube, 790 en PMD; `inBodyStartTag`: 119 |
| Cognitiva igual entre herramientas (métodos medidos por SonarQube) | 747 de 770 (97 %) |
| Ciclomática igual entre herramientas | 1.898 de 2.088 (91 %); en 111 PMD da más y en 79 da menos |

Tres conclusiones. La primera: el hallazgo de la cognitiva no medida queda confirmado por una implementación independiente; el problema es de SonarQube, no de la extracción. La segunda: la imputación de ceros era correcta. La tercera, que es otro hallazgo: dos implementaciones de la ciclomática de McCabe no coinciden en uno de cada once métodos. Para 2.4 y 6.2 hay que mirar qué construcciones cuenta distinto cada una (ejemplos: `readByteDataUnchecked` da 1 en SonarQube y 3 en PMD; `consumeCharacterReference`, 27 y 26).

**Tamaño.** PMD informa en la línea del nombre del método (`beginline` igual a `endline`), así que tampoco da el tamaño en líneas. El tamaño del eje 2 es el NCSS de PMD (sentencias, sin comentarios ni líneas en blanco), disponible para los 2.088 métodos.

**Hecho.** La tabla `datos/extraccion-jsoup/eje2_metodos.csv` tiene una fila por método con las dos complejidades de las dos herramientas y el tamaño. Con eso la prueba técnica 2 queda cerrada.

**La consola de Windows.** En la consola clásica de Windows, hacer clic o seleccionar texto la pone en modo selección, y cualquier programa que quiera escribir en ella se bloquea hasta que se sale de ese modo (Enter, Esc o Ctrl+C con texto seleccionado, que copia en lugar de interrumpir). El análisis quedó así 15 minutos después de terminar. Si un comando parece colgado, conviene apretar Esc en su ventana antes de cortarlo.

## Prueba técnica 3: Quality Gate sobre código nuevo entre dos releases (SCRUM-24)

**Qué confirma.** Que, analizando dos releases seguidos bajo la misma clave, SonarQube toma como código nuevo la diferencia entre ambos, que es lo que evalúa el Quality Gate por defecto (decisión D2).

**Cómo se corre.** Primero el release viejo y después el nuevo, bajo una clave de prueba:

```
python guiones/analizar.py jsoup 1.22.2 --clave prueba-pt3-jsoup --sin-tests
python guiones/analizar.py jsoup 1.23.2 --clave prueba-pt3-jsoup --sin-tests
python guiones/exportar_medidas.py prueba-pt3-jsoup
python guiones/diff_releases.py jsoup --comparar prueba-pt3-jsoup
```

`exportar_medidas.py` exporta las métricas de código nuevo (`codigo_nuevo_archivo.csv`) y marca qué issues están en código nuevo. `diff_releases.py` calcula el cambio real entre los dos tags con `git diff --no-index` y lo cruza con lo que informó SonarQube. Las dos cosas se agregaron para esta prueba (ver el diccionario de datos). Si no lo reflejan, repetir con una clave nueva fechando el primer análisis hacia atrás con `--fecha`.

**A tener en cuenta.** Al correr sin tests no hay cobertura, así que la condición "cobertura del código nuevo de al menos 80 %" va a fallar o quedar sin evaluar. No es un resultado: esta prueba mira si se detecta el código nuevo, no si el gate aprueba. La cobertura se prueba en la 4.

La definición de código nuevo por defecto es "versión anterior", que se apoya en `sonar.projectVersion`; el guion la completa con la versión del corpus. Desde la versión 26.9, SonarQube fecha cada issue según el último cambio de la línea en git: como los checkouts no traen historia (`--depth 1`), hay que ver cómo afecta eso a la detección de código nuevo. La PT2 ya lo mostró: el análisis advierte "Shallow clone detected, no blame information will be provided" y "Missing blame information for 195 files" (todos los de jsoup), además de dos archivos de test con caracteres que no son UTF-8 (`HtmlParserTest.java` y `TokeniserStateTest.java`).

**Plan B.** Un solo commit por proyecto y un gate propio con las mismas condiciones aplicadas a todo el código, declarado como limitación.

**Resultados (2026-10-13).** D2 confirmada: el código nuevo es la diferencia entre los dos releases, aun sin historia de git. No hace falta el plan B ni fechar análisis con `--fecha`.

Corrida: jsoup 1.22.2 y 1.23.2 bajo `prueba-pt3-jsoup`, sin tests. Período informado por la API: `PREVIOUS_VERSION`, parámetro `1.22.2`, desde la fecha del primer análisis (también es el criterio por defecto de la instancia). Referencia independiente: `diff_releases.py`, con `git diff --no-index` entre los checkouts. Datos en `datos/prueba-pt3-jsoup/` y `datos/diff-jsoup/`.

1. **Archivos.** De los 95 archivos Java principales que informa SonarQube, los 44 que cambiaron según git tienen `new_lines > 0` y los 51 que no cambiaron tienen 0. Ningún falso positivo ni falso negativo.
2. **Líneas.** `new_lines` suma 2.455 en el código principal; git da 2.485 líneas agregadas. La diferencia se explica por dos cosas:
   * SonarQube compara las líneas sin tener en cuenta los espacios. Con `git diff -w`, 39 de los 40 archivos modificados que informa coinciden exactamente (2.127 contra 2.126 líneas). La excepción es `W3CDom.java` (215 contra 214), atribuible a que los dos algoritmos de diff alinean distinto un bloque.
   * En los 4 archivos nuevos SonarQube cuenta una línea más que git: cuenta como línea lo que sigue al último salto de línea, igual que en la métrica `lines`.
   * Como `new_lines` incluye líneas en blanco y comentarios (2.455, contra unas 1.943 líneas de código según la aproximación de `agregadas_codigo`), mide líneas físicas y no `ncloc`.
3. **Mecanismo (inferido, no documentado).** El análisis advierte "Shallow clone detected, no blame information will be provided". Sin blame, la coincidencia con `git diff -w` indica que SonarQube detecta las líneas cambiadas comparando cada archivo con el que guardó en el análisis anterior, línea por línea y sin espacios. No encontramos documentación oficial que lo describa; queda como inferencia apoyada en estos datos.
4. **Issues.** 55 issues abiertos: 52 con fecha del primer análisis y 3 con fecha del segundo, que son los 3 de `new_violations` (`codigo_nuevo = sí` en `issues.csv`). Sin blame, la fecha de un issue es la del análisis que lo detectó por primera vez, y el seguimiento entre análisis no confundió issues viejos con nuevos. Los 3: `java:S8786` en `HttpConnection.java` y dos `java:S2259` en `HtmlTreeBuilder.java`.
5. **Gate.** Rechazado por `new_violations` = 3 (umbral 0) y `new_coverage` = 0,0 (umbral 80, esperable sin tests). `new_duplicated_lines_density` = 0,0, aprobado.

**Hallazgos laterales que afectan a otras decisiones.**

* **Taxonomías distintas en el código nuevo (eje 1).** `java:S8786` es `CODE_SMELL` en el modo estándar y tiene impacto `RELIABILITY` en el modo MQR. Por eso el código nuevo tiene 1 code smell y 20 min de deuda en el modo estándar, y 0 issues y 0 min de mantenibilidad en el modo MQR. Hay que tenerlo en cuenta al decidir el modelo de deuda del eje 1.
* **`new_lines` del proyecto no es la suma de los archivos principales.** El proyecto informa 5.325: incluye los tests y el `pom.xml` (87 líneas, que coinciden con git). `codigo_nuevo_archivo.csv`, igual que `medidas_archivo.csv`, solo trae archivos principales (calificador `FIL`), así que lo de los tests no se puede verificar archivo por archivo. La estimación con git (unas 2.842 líneas) no cierra exacto contra el resto (2.783). Para el eje 3 conviene usar las medidas por archivo o las condiciones del gate, no `new_lines` del proyecto.
* **`src/main/java11/` no se analiza.** jsoup tiene ahí una variante de `HttpClientExecutor.java` para Java 11 (cambió entre los releases) y SonarQube no la informa. Pasa igual en los dos análisis, así que no sesga la comparación: se declara como alcance.
* **Dos defectos de los guiones, corregidos.** `analizar.py` marcaba como falla un análisis publicado con el gate rechazado, porque buscaba un mensaje que el escáner de Maven 5.x ya no imprime. `exportar_medidas.py` no exportaba ninguna métrica de código nuevo, porque la API las devuelve en `period` y no en `value`.
* **Persistencia del laboratorio, corregida.** El `docker-compose.yml` no montaba el volumen de datos de PostgreSQL: cada `down` + `up` arrancaba con una base vacía. Corregido y verificado con un reinicio (ver el comentario en el servicio `db` y el README).

## Prueba técnica 4: cobertura con JaCoCo (SCRUM-25)

**Qué confirma.** Que se puede medir la cobertura, una de las cuatro condiciones del gate, en un proyecto que ya trae JaCoCo configurado (Commons IO) y en uno que no (jsoup), sin modificar los proyectos (decisión D2 bis).

**Cómo se corre.**

```
python guiones/analizar.py commons-io 2.22.0 --clave prueba-pt4-commons-io --jacoco
python guiones/analizar.py jsoup 1.23.2 --clave prueba-pt4-jsoup --jacoco
python guiones/exportar_medidas.py prueba-pt4-commons-io
python guiones/exportar_medidas.py prueba-pt4-jsoup
```

La opción `--jacoco` agrega el agente de JaCoCo y el reporte XML desde la línea de comandos. Verificar que la columna `coverage` de `medidas_archivo.csv` tiene valores. En Commons IO, revisar en el log que el agente no quede declarado dos veces (el proyecto ya lo configura).

**Resultados.** Pendiente.

## Compilación del corpus (SCRUM-22)

**Qué confirma.** Que las ocho versiones del corpus compilan sin intervención manual (criterio 2 de D3) y cuántos tests tiene cada una. Se corre una sola vez, salvo que cambie el corpus o la versión de Maven o del JDK.

**Cómo se corre.** Paso 5 del README. Resultado en `datos/compilacion.csv` y logs en `trabajo/logs/`.

**Fallas de tests por el entorno.** Algunos tests fallan en el laboratorio por cómo está armado el entorno, no por el código del proyecto. No afectan el análisis estático, que es lo que usan los tres ejes, y casi no mueven la cobertura (un test que falla en una aserción igual ejecutó el código hasta ese punto). Se decidió documentarlas y no cambiar el contenedor (2026-10-12). Al revisar `compilacion.csv`, cada falla se clasifica como "de entorno" o "a investigar".

| Proyecto y versión | Tests que fallan | Causa |
| --- | --- | --- |
| commons-io 2.21.0 | `FileFilterTest.testCanRead`, `testCanWrite`; `FileUtilsCleanDirectoryTest.testThrowsOnNullList`; `FileUtilsDeleteDirectoryLinuxTest.testThrowsOnNullList`, `testThrowsOnCannotDeleteFile`; `FileUtilsTest.testForceDeleteReadOnlyFile`, `testCopyFileToReadOnlyDirectory`, `testForceDeleteUnwritableFile` y los tres `*_IOExceptionOnPosixFileSystem` (11 fallas) | Permisos. Los tests le quitan un permiso a un archivo y esperan que la operación falle, pero la imagen `maven:3.10.0-eclipse-temurin-21` corre como root, que ignora los permisos. No es el montaje de Windows: esos archivos están en `/tmp` del contenedor |
| commons-io 2.21.0 | `URIOriginTest.testGetInputStream` [1] y [2] (2 errores) | Red. El test descarga `http://www.apache.com/`, un sitio externo que no es de Apache y que respondió HTTP 500 por http y un certificado que no coincide por https |
| commons-io 2.22.0 | Los mismos 11 tests de permisos (comparados uno por uno) | Permisos, igual que en 2.21.0. `URIOriginTest` pasó, pero el test cambió entre releases (28 casos en 2.21.0, 33 en 2.22.0), así que no alcanza para hablar de inestabilidad |

En commons-io 2.21.0 son 13 de 6.106 tests (0,2 %) y en 2.22.0, 11 de 6.301; en las dos hay además 26 omitidos por el propio proyecto. Los otros tres proyectos no tienen fallas.

**Resultados (2026-10-12).** Las ocho versiones terminan con BUILD SUCCESS: el criterio 2 de D3 se cumple en todo el corpus. Los tests de la tabla son los que informa Maven en su resumen.

| Versión | Duración | Tests unitarios | Tests de integración | Fallas de entorno |
| --- | --- | --- | --- | --- |
| commons-io 2.21.0 | 12:37 | 6.106 | | 11 de permisos y 2 de red |
| commons-io 2.22.0 | 21:39 | 6.301 | | 11 de permisos |
| commons-collections 4.5.0 | 3:18 | 8.399 | | 0 |
| commons-collections 4.6.0 | 7:21 | 18.024 | | 0 |
| jsoup 1.22.2 | 2:46 | 1.952 | 48 | 0 |
| jsoup 1.23.2 | 1:28 | 2.165 | 46 | 0 |
| jfreechart 1.5.5 | 2:12 | 2.350 | | 0 |
| jfreechart 1.5.6 | 2:12 | 2.351 | | 0 |

**El CSV contaba mal en dos casos** (corregido el 2026-10-12). `compilar_corpus.py` sumaba los reportes XML de Surefire, y eso no coincidía con lo que ejecuta Maven:

* En commons-collections 4.6.0 faltan 6.507 tests (el CSV dice 11.517). En esa versión el proyecto usa clases de test anidadas (`@Nested`) definidas en clases abstractas, por ejemplo `AbstractMapTest$MapEntrySetTest`, que se ejecutan una vez por cada subclase y no dejan un XML propio: 275 clases en la consola contra 252 archivos XML. En 4.5.0 los dos conteos coinciden.
* En jsoup no se cuentan los tests de integración de Failsafe.

El guion medía "reportes XML" en lugar de "tests ejecutados": la definición operacional se apartó del concepto. Ahora cuenta desde los resúmenes de Maven, separa los de integración en `tests_integracion` y `fallas_integracion`, y con `--recontar` recalcula el CSV desde los logs sin volver a compilar. Probado contra los ocho logs: coincide con Maven en todos.

**Duraciones.** No son comparables entre corridas: commons-io 2.22.0 tardó casi el doble que 2.21.0 con una suma de tiempos por clase parecida (365 s contra 300 s), y no se controló la carga de la máquina. No se usan en ningún eje.

**JaCoCo propio de cada proyecto.** commons-collections 4.5.0 usa 0.8.12, commons-io 0.8.14 y commons-collections 4.6.0 0.8.15; jsoup y jfreechart no lo traen. A revisar en la prueba 4.
