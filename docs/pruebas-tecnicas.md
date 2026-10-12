# Pruebas técnicas

Las cuatro pruebas confirman, antes de comprometernos con un diseño, que el laboratorio puede producir los datos que necesita cada eje. Cada una tiene su tarea en Jira. Cuando una prueba se corre, sus resultados se escriben acá, debajo de su sección, con la fecha.

Estado al 2026-10-12: el laboratorio y los guiones están listos; ninguna prueba se corrió todavía.

**Cuándo se corren los tests (decidido el 2026-10-12).** `analizar.py` compila de nuevo en cada análisis y, por defecto, corre todos los tests. Los tests solo hacen falta para medir cobertura, así que se usa `--sin-tests` en las pruebas 1, 2 y 3 y en los análisis `extraccion-*`. La prueba 4 y los análisis principales `corpus-*` se corren con tests y `--jacoco` (decisión D2 bis). `--sin-tests` pasa `-DskipTests=true`, que compila los tests pero no los ejecuta: SonarQube sigue analizando el código de test con sus clases compiladas, y lo único que falta es la cobertura. En commons-io los tests tardan unos 11 minutos.

## Prueba técnica 1: punta a punta y medidas por archivo (SCRUM-21)

**Qué confirma.** Que SonarQube levanta, que un proyecto del corpus se analiza completo y que se pueden exportar por la API, para cada archivo, las medidas del eje 1. Además verifica cuatro supuestos:

| Supuesto | Por qué importa |
| --- | --- |
| S1. El ratio de deuda y la letra existen por archivo | El eje 1 usa el archivo como unidad de análisis (D5). Si solo existen por proyecto, hay que rediseñar el eje |
| S2. El costo de desarrollo por línea es 30 minutos | Es la constante del modelo de estimación que critica el eje 1 |
| S3. La grilla es 5, 10, 20 y 50 % | Define dónde están los bordes entre letras |
| S4. El ratio publicado coincide con deuda / (costo x líneas) | Confirma que la fórmula documentada es la que efectivamente aplica la herramienta |

**Cómo se corre.** Pasos 1 a 6 del README.

**Hecho cuando.** Existen `datos/prueba-pt1-jsoup/medidas_archivo.csv`, `issues.csv` y `supuestos.md`, y los cuatro supuestos están confirmados o refutados.

**Resultados.** Pendiente.

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
* Cómo obtener el tamaño de cada método: la ubicación del issue es el nombre del método, no su cuerpo, así que no sale de acá.

**Plan B.** Calcular ambas métricas con una herramienta externa.

**Resultados.** Pendiente.

## Prueba técnica 3: Quality Gate sobre código nuevo entre dos releases (SCRUM-24)

**Qué confirma.** Que, analizando dos releases seguidos bajo la misma clave, SonarQube toma como código nuevo la diferencia entre ambos, que es lo que evalúa el Quality Gate por defecto (decisión D2).

**Cómo se corre.** Primero el release viejo y después el nuevo, bajo una clave de prueba:

```
python guiones/analizar.py jsoup 1.22.2 --clave prueba-pt3-jsoup --sin-tests
python guiones/analizar.py jsoup 1.23.2 --clave prueba-pt3-jsoup --sin-tests
python guiones/exportar_medidas.py prueba-pt3-jsoup
```

Luego comparar las métricas de código nuevo (`new_lines`, `new_violations`) con el cambio real entre los dos tags. Si no lo reflejan, repetir con una clave nueva fechando el primer análisis hacia atrás con `--fecha`.

**A tener en cuenta.** Al correr sin tests no hay cobertura, así que la condición "cobertura del código nuevo de al menos 80 %" va a fallar o quedar sin evaluar. No es un resultado: esta prueba mira si se detecta el código nuevo, no si el gate aprueba. La cobertura se prueba en la 4.

La definición de código nuevo por defecto es "versión anterior", que se apoya en `sonar.projectVersion`; el guion la completa con la versión del corpus. Desde la versión 26.9, SonarQube fecha cada issue según el último cambio de la línea en git: como los checkouts no traen historia (`--depth 1`), hay que ver cómo afecta eso a la detección de código nuevo.

**Plan B.** Un solo commit por proyecto y un gate propio con las mismas condiciones aplicadas a todo el código, declarado como limitación.

**Resultados.** Pendiente.

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

En commons-io 2.21.0 son 13 de 6.106 tests (0,2 %); además hay 26 omitidos por el propio proyecto. Las demás versiones se agregan cuando termine la corrida.

**Otros hallazgos.** commons-io 2.21.0 compiló en 12:37 min, de los cuales unos 11 fueron tests. Usa JaCoCo 0.8.14, la que fija su POM padre, no la 0.8.15 de `VERSIONES.md`. Revisar en la prueba 4 si `--jacoco` impone la 0.8.15.

**Resultados.** Corrida iniciada el 2026-10-12; pendiente el CSV completo.
