# Versiones fijadas

Todo lo que puede cambiar una medición está fijado acá. Si alguien actualiza una versión, la actualiza en este archivo y en el lugar donde se usa, en el mismo commit, y lo anota en el historial de abajo. Nunca se usan etiquetas móviles como `latest` o `community`.

| Componente | Versión | Dónde se fija | Por qué esta |
| --- | --- | --- | --- |
| SonarQube Community Build | 26.10.0.133078 (imagen `sonarqube:26.10.0.133078-community`) | `laboratorio/docker-compose.yml` | La vigente al montar el laboratorio. La documentación online de Sonar describe siempre la última versión, así que con esta la documentación que se cita coincide con lo instalado |
| PostgreSQL | 17.11 (imagen `postgres:17.11`) | `laboratorio/docker-compose.yml` | Base de datos que usa el ejemplo oficial de SonarSource |
| Maven | 3.10.0 | `laboratorio/docker-compose.yml` (imagen `maven:3.10.0-eclipse-temurin-21`) | Imagen oficial vigente |
| JDK de compilación y análisis | Eclipse Temurin 21 | ídem | Desde la versión 26.8, el escáner de SonarQube necesita Java 21. Los cuatro proyectos compilan con un JDK posterior al que exigen (8 u 11) |
| Escáner de Maven (`sonar-maven-plugin`) | 5.8.0.7211 | `guiones/analizar.py` | Última versión publicada al montar el laboratorio |
| JaCoCo (agente `org.jacoco.agent:runtime` y CLI `org.jacoco.cli:nodeps`) | 0.8.15 | `guiones/analizar.py` | Última versión publicada; soporta Java 21. Desde la PT4 se usan el agente y la CLI en lugar del plugin de Maven (ver el docstring de `analizar.py`) |
| `maven-dependency-plugin` | 3.8.1 | `guiones/analizar.py` | Descarga el agente y la CLI de JaCoCo al repositorio de Maven del contenedor |
| Python (guiones) | 3.10 o posterior, solo biblioteca estándar | — | Sin dependencias que instalar |
| PMD | 7.26.0 (`pmd-dist-7.26.0-bin.zip`, SHA-256 `9f55cb7ff0e9f9a66dd2f005eaa370e84c8a4cd971b134aa14a930c4a283ebc9`) | `guiones/pmd_metodos.py` | Estable vigente al 2026-10-13. Segunda implementación de la ciclomática y la cognitiva, y fuente del tamaño de cada método (eje 2). Corre en el contenedor de herramientas con su Java 21 |

Las versiones se verificaron el 2026-10-12 contra las etiquetas de los repositorios oficiales (`SonarSource/docker-sonarqube`, `docker-library/official-images`, `SonarSource/sonar-scanner-maven`, `jacoco/jacoco`).

## Parámetros de SonarQube que afectan las mediciones

Se usan los valores de fábrica y no se modifican. `guiones/verificar_supuestos.py` registra los valores efectivos en cada prueba. El perfil y el Quality Gate son la propuesta de SCRUM-26: se confirman o se cambian en esa tarea.

| Parámetro | Valor de fábrica | Qué afecta |
| --- | --- | --- |
| `sonar.technicalDebt.developmentCost` | 30 (minutos por línea) | Denominador del ratio de deuda (eje 1) |
| `sonar.technicalDebt.ratingGrid` | 0.05,0.1,0.2,0.5 | Umbrales de la letra de mantenibilidad (eje 1) |
| Perfil de calidad de Java | Sonar way, sin modificar | Qué reglas generan issues (todos los ejes) |
| Quality Gate | Sonar way, sin modificar | Eje 3 |

## Historial

| Fecha | Cambio |
| --- | --- |
| 2026-10-12 | Versiones iniciales del laboratorio |
| 2026-10-13 | Se agrega PMD 7.26.0 para el eje 2 (huella verificada con dos descargas independientes) |
