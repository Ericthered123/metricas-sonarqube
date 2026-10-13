# Configuración del análisis (SCRUM-26)

Qué reglas, qué gate y qué parámetros se usan para analizar el corpus. Es la fuente de la sección 4.3 del artículo. Los valores salen de `laboratorio/configuracion/`, que genera `guiones/exportar_configuracion.py` a partir de la instancia; si este documento y esos archivos no coinciden, valen los archivos.

## Instancia

SonarQube Community Build 26.10.0.133078, en modo MQR (`sonar.multi-quality-mode.enabled = true`). Detalle de versiones en `VERSIONES.md`.

## Perfil de calidad

**Hallazgo (2026-10-13).** Desde la 26.10 hay tres perfiles predefinidos "Sonar way" por lenguaje, y en una instalación nueva el predeterminado es "Sonar way core". Según las notas de versión de Community Build: *"Sonar way core activates all security rules and the most impactful reliability and maintainability rules. Sonar way extended adds more reliability and maintainability rules. Sonar way comprehensive activates all recommended rules"* y *"On new installations, Sonar way core is the default profile for each language"*. SonarSource aclara en su herramienta de migración que *"What was Sonar way before, is now Sonar way comprehensive"*.

Perfiles de Java de la instancia (`laboratorio/configuracion/perfiles-java.csv`):

| Perfil | Reglas activas |
| --- | --- |
| Sonar way core | 274 |
| Sonar way extended | 337 |
| Sonar way comprehensive | 618 |
| Sonar agentic AI | 464 |

Composición de "Sonar way core": de las 274 reglas, 179 son de tipo BUG, 63 VULNERABILITY y 32 CODE_SMELL. Por cualidad (modo MQR, una regla puede afectar a más de una): 196 de confiabilidad, 71 de seguridad y 45 de mantenibilidad. No incluye `java:S3776` (complejidad cognitiva).

**Decisión (2026-10-13).**

* **Análisis principal: "Sonar way comprehensive"** (claves `corpus-<proyecto>`). Es el "Sonar way" histórico, el que usan los estudios con los que se contrastan los resultados, y el que siguen teniendo las instalaciones que se actualizaron.
* **Contraste: "Sonar way core"** (claves `corpus-core-<proyecto>`), para el eje 1: la deuda, el ratio y la letra dependen de qué reglas están activas, y el predeterminado cambió justo en la versión fijada.
* El perfil se asigna explícitamente a cada proyecto en cada análisis (`analizar.py`, función `asignar_perfil` de `comun.py`), y además `preparar_sonarqube.py` pone comprehensive como predeterminado de Java. Así el resultado no depende del predeterminado de la instancia.
* Los perfiles se usan sin modificar. Copias de respaldo en `perfil-java-comprehensive.xml` y `perfil-java-core.xml`, y las reglas en los CSV `reglas-perfil-java-*.csv`.

**Consecuencia para lo ya hecho.** Las pruebas técnicas 1, 3 y 4 se corrieron con "Sonar way core", el predeterminado de la instalación nueva (registrado en la columna `perfil` de `datos/registro_analisis.csv`). Sus conclusiones técnicas siguen valiendo; sus cifras de deuda e issues no son las del análisis principal. En particular, el "todo A" de jsoup (D5) hay que volver a mirarlo con comprehensive. La prueba técnica 2 usó su propio perfil de extracción y no se ve afectada.

**Primer contraste (jsoup 1.23.2, sin tests, 2026-10-13).** El mismo commit analizado con cada perfil (`prueba-pt3-jsoup` con core y `prueba-comp-jsoup` con comprehensive):

| | core | comprehensive |
| --- | --- | --- |
| Issues abiertos | 55 (13 reglas) | 1.003 (90 reglas) |
| Issues de mantenibilidad (MQR) | 30 | 952 |
| Deuda de los archivos de código | 620 min | 4.451 min |
| Archivos con ratio distinto de 0 | 21 de 96 | 72 de 96 |
| Letras | 96 A | 92 A, 3 B, 1 C |

* La regla con más issues en comprehensive es `java:S115` (nombres de constantes), con 287 issues, el 29 % del total.
* Los cuatro archivos que no son A son de los más chicos del proyecto: `Progress.java` (5 líneas de código, B), `SharedConstants.java` (17, C), `ParseErrorList.java` (31, B) y `FormElement.java` (87, B). Con la grilla del 5 %, en un archivo chico alcanzan unos pocos issues para cambiar de letra. Es la primera evidencia a favor de la hipótesis del eje 1 de que la letra por archivo mide en buena parte el tamaño. Falta confirmarla con todo el corpus.
* El "todo A" de D5 era en buena parte efecto del perfil: con comprehensive deja de valer, aunque el 96 % de los archivos sigue en A.

## Quality Gate

"Sonar way", predefinido, sin modificar (`laboratorio/configuracion/quality-gate.json`). Las cuatro condiciones aplican solo al código nuevo:

| Métrica | Condición de rechazo |
| --- | --- |
| `new_violations` | mayor que 0 |
| `new_coverage` | menor que 80 % |
| `new_duplicated_lines_density` | mayor que 3 % |
| `new_security_hotspots_reviewed` | menor que 100 % |

* `sonar.qualitygate.ignoreSmallChanges = true` (valor de fábrica): con menos de 20 líneas nuevas, las condiciones de cobertura y duplicación no se evalúan.
* En los resultados de las pruebas 3 y 4 aparecen solo tres condiciones: la de hotspots no se informa cuando no hay hotspots en el código nuevo. Con el retiro de los hotspots en Community Build (anotado el 2026-10-12), es probable que no se evalúe en ningún proyecto. A verificar en la corrida de producción.
* En el primer análisis de una clave no hay código nuevo y el gate aprueba sin evaluar ninguna condición (prueba técnica 1).

## Código nuevo

"Versión anterior" (`PREVIOUS_VERSION`), el valor de fábrica. Los dos releases de cada proyecto se analizan bajo la misma clave, el viejo primero, con `sonar.projectVersion` igual a la versión del corpus. Aunque los checkouts no tienen historia de git, el código nuevo coincide con el diff real entre releases (prueba técnica 3).

## Parámetros que afectan las medidas

Todos con el valor de fábrica (`laboratorio/configuracion/ajustes.json`):

| Parámetro | Valor | Eje |
| --- | --- | --- |
| `sonar.technicalDebt.developmentCost` | 30 min por línea | 1 (ratio de deuda) |
| `sonar.technicalDebt.ratingGrid` | 0.05, 0.1, 0.2, 0.5 | 1 (letra) |
| `sonar.qualitygate.ignoreSmallChanges` | true | 3 |

## Qué se analiza

* **Sin exclusiones** (decisión del 2026-10-13): `sonar.exclusions`, `sonar.test.exclusions`, `sonar.coverage.exclusions` y `sonar.cpd.exclusions` vacíos, y ningún pom del corpus define propiedades `sonar.*`. Se analiza lo que ve cualquier usuario con la configuración por defecto. El único código no productivo del corpus es `org.jsoup.examples` (código de ejemplo, 0 % de cobertura), que entra en el análisis y se declara.
* **Código principal y tests** los separa el escáner de Maven a partir del pom (`src/main/java` y `src/test/java`). Las medidas por archivo del eje 1 son solo de código principal; la deuda del proyecto incluye la de los tests (prueba técnica 1).
* **Codificación y versión de Java** las toma el escáner del pom de cada proyecto (`project.build.sourceEncoding`, nivel de compilación). No se fijan aparte.
* **Variantes de Java 11 de jsoup** (`src/main/java11`): no se analizan, porque el pom las compila en una ejecución aparte que el escáner no ve. Pasa igual en los dos releases.
* **Cobertura**: agente de JaCoCo 0.8.15 por variable de entorno, igual en los cuatro proyectos (prueba técnica 4).

## Cómo se verifica

```
python guiones/exportar_configuracion.py --verificar corpus-jsoup corpus-core-jsoup ...
```

Exporta la configuración y comprueba que cada clave usa el perfil que le corresponde y el gate "Sonar way". Termina con error si alguna no.
