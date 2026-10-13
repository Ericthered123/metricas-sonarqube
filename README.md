# Auditoría metrológica de SonarQube: laboratorio

Repositorio del trabajo integrador de Métricas de Software (UNNOBA, 2.º cuatrimestre de 2026). Acá están el laboratorio, los guiones y los datos. La documentación del trabajo (ejes, decisiones, reparto, referencias) está en Confluence, y las tareas en Jira.

El estudio trata a SonarQube como un instrumento de medición y examina qué mide, con qué escala y con qué validez. Todo lo que produce un número para el artículo tiene que salir de un guion de este repositorio: nada de capturas de pantalla ni números copiados a mano.

## Qué hay en cada carpeta

| Carpeta | Contenido | ¿Se versiona? |
| --- | --- | --- |
| `laboratorio/` | `docker-compose.yml` con SonarQube, PostgreSQL y el contenedor de herramientas (Maven y JDK) | Sí, salvo `.env` |
| `corpus/` | `corpus.csv`: los commits exactos que se analizan | Sí |
| `guiones/` | Los guiones en Python que clonan, compilan, analizan y exportan | Sí |
| `datos/` | Los CSV que producen los guiones. Es lo que se analiza en cada eje | Sí |
| `docs/` | Configuración del análisis, resultados de las pruebas técnicas y de la corrida de producción, y diccionario de datos | Sí |
| `trabajo/` | Checkouts del corpus y logs. Se regenera con los guiones | No |

Las versiones de todo lo que interviene (SonarQube, Maven, JDK, escáner, JaCoCo) están fijadas en [VERSIONES.md](VERSIONES.md).

## Si sos del grupo y querés trabajar con los datos

Para analizar no hace falta levantar SonarQube ni correr nada: los resultados están en `datos/` como CSV. Alcanza con clonar el repositorio (o mirarlo en GitHub) y abrirlos con Python, R o una planilla.

Por dónde empezar:

1. [docs/corrida-produccion.md](docs/corrida-produccion.md): qué se corrió sobre el corpus y una primera lectura de los resultados.
2. [docs/configuracion-analisis.md](docs/configuracion-analisis.md): con qué perfil, gate y parámetros se analizó (fuente de la sección 4.3).
3. [docs/diccionario-de-datos.md](docs/diccionario-de-datos.md): qué significa cada columna de cada CSV.

Qué carpeta usa cada eje:

| Eje | Carpetas | Archivos |
| --- | --- | --- |
| 1 (5.1), deuda y calificación | `datos/corpus-<proyecto>/` (perfil principal) y `datos/corpus-core-<proyecto>/` (contraste) | `medidas_archivo.csv`, `medidas_proyecto.csv`, `issues.csv` |
| 2 (5.2), complejidad por método | `datos/extraccion-<proyecto>/` | `eje2_metodos.csv` (por ahora solo jsoup; el resto sale de SCRUM-29) |
| 3 (5.3), Quality Gate | `datos/corpus-<proyecto>/` y `datos/corpus-core-<proyecto>/` | `quality_gate.csv`, `codigo_nuevo_archivo.csv`, `comparacion_codigo_nuevo.csv`, `issues.csv` |

Las medidas por archivo son del release nuevo de cada proyecto. Las carpetas `datos/prueba-*` son de las pruebas técnicas: sirven como evidencia de cómo se validó el laboratorio, pero **no** se usan para los resultados (varias se corrieron con otro perfil). `datos/registro_analisis.csv` dice cuándo, con qué commit y con qué perfil se hizo cada análisis.

El avance de las tareas está en Jira y las decisiones del diseño en Confluence (página "3. Decisiones de diseño").

## Requisitos

* Docker Desktop (Windows o macOS) o Docker Engine con el plugin Compose (Linux), con al menos 6 GB de memoria asignados a Docker.
* Python 3.10 o posterior. No hace falta instalar paquetes.
* Git.

No hace falta tener Java ni Maven instalados: se usan los del contenedor `herramientas`, así todos compilamos y analizamos con exactamente las mismas versiones.

## Reproducir desde cero

Todos los comandos se corren desde la raíz del repositorio. En Windows, desde PowerShell; donde dice `python` puede ser `py`.

**1. Configuración local.** Copiar la plantilla:

```powershell
copy laboratorio\.env.example laboratorio\.env      # Windows
cp laboratorio/.env.example laboratorio/.env        # Linux o macOS
```

**2. Levantar SonarQube.** La primera vez descarga las imágenes (unos 2 GB):

```
docker compose -f laboratorio/docker-compose.yml --env-file laboratorio/.env up -d
```

**3. Preparar la instancia.** Espera a que arranque, reemplaza la contraseña de fábrica de `admin` por una aleatoria, genera un token y pone "Sonar way comprehensive" como perfil predeterminado de Java (ver [docs/configuracion-analisis.md](docs/configuracion-analisis.md)). La contraseña y el token quedan en `laboratorio/.env`, que no se sube al repositorio:

```
python guiones/preparar_sonarqube.py
```

SonarQube queda en http://localhost:9000 (usuario `admin`, contraseña en `laboratorio/.env`).

Para comprobar que tu instancia tiene la misma configuración que la del estudio, exportala y compará con lo versionado en `laboratorio/configuracion/` (`git diff` no tendría que mostrar cambios salvo la fecha de exportación):

```
python guiones/exportar_configuracion.py
```

**4. Descargar el corpus.** Trae los ocho commits de `corpus/corpus.csv` y verifica cada hash:

```
python guiones/clonar_corpus.py
```

**5. Compilar el corpus (SCRUM-22).** Compila y corre los tests de las ocho versiones. La primera vez tarda bastante porque descarga las dependencias de Maven; después quedan en caché:

```
python guiones/compilar_corpus.py
```

Resultado en `datos/compilacion.csv`, que se actualiza al terminar cada versión. Algunos tests fallan por el entorno y no por el código (ver la sección de SCRUM-22 en [docs/pruebas-tecnicas.md](docs/pruebas-tecnicas.md)). No lances análisis mientras corre: `analizar.py` hace `mvn clean` sobre los mismos checkouts y comparte la caché de Maven.

**6. Prueba técnica 1 (SCRUM-21).** Analiza jsoup bajo una clave de prueba, exporta las medidas por archivo y los issues, y verifica los supuestos del eje 1:

```
python guiones/analizar.py jsoup 1.23.2 --clave prueba-pt1-jsoup --sin-tests
python guiones/exportar_medidas.py prueba-pt1-jsoup
python guiones/verificar_supuestos.py prueba-pt1-jsoup
```

Resultados en `datos/prueba-pt1-jsoup/`.

Las pruebas técnicas 2, 3 y 4 están descritas en [docs/pruebas-tecnicas.md](docs/pruebas-tecnicas.md).

**7. Corrida de producción (SCRUM-27 y 28).** Analiza los cuatro proyectos, en sus dos releases y con los dos perfiles (16 análisis con tests y cobertura, unas dos horas y media), exporta los datos a `datos/corpus-*/` y verifica la configuración de cada clave. Se puede cortar y volver a lanzar: lo que ya terminó bien no se repite.

```
python guiones/correr_corpus.py
```

**8. Extracción del eje 2 (SCRUM-29).** Para el release nuevo de cada proyecto: análisis aparte con el perfil de extracción de complejidad, exportación por método y PMD como segunda implementación. Necesita la corrida del paso 7 (o al menos las versiones compiladas) y PMD instalado (`python guiones/pmd_metodos.py instalar`).

```
python guiones/extraer_eje2.py
```

## Apagar y limpiar

```
docker compose -f laboratorio/docker-compose.yml --env-file laboratorio/.env down      # apaga, conserva los datos
docker compose -f laboratorio/docker-compose.yml --env-file laboratorio/.env down -v   # borra también los análisis
```

## Si algo falla

* **SonarQube no arranca y el log habla de `vm.max_map_count`.** El `docker-compose.yml` ya desactiva el requisito. Si igual aparece, en Windows correr `wsl -d docker-desktop -u root sysctl -w vm.max_map_count=524288` y volver a levantar.
* **SonarQube se reinicia solo o queda muy lento.** Le falta memoria: subirla en Docker Desktop, en Settings, Resources.
* **Después de un `down` y un `up` desaparecen los análisis y `preparar_sonarqube.py` dice que reemplazó la contraseña de fábrica.** La base no está persistiendo. Pasaba con el `docker-compose.yml` anterior al 2026-10-13, que no montaba el volumen `postgresql_data` (ver el comentario en el servicio `db`). Para comprobarlo: `docker inspect tp-metricas-postgres --format "{{range .Mounts}}{{.Name}} -> {{.Destination}}{{println}}{{end}}"` tiene que mostrar `tp-metricas_postgresql_data` en `/var/lib/postgresql/data`, y no un nombre con forma de hash.
* **`preparar_sonarqube.py` no puede autenticarse.** Si cambiaste la contraseña de `admin` a mano, escribila en `SONAR_ADMIN_CLAVE` de `laboratorio/.env`.
* **Fallan tests de permisos o de red.** Es esperable: el contenedor de herramientas corre como root, que ignora los permisos de archivo, y algunos tests dependen de sitios externos. No afecta el análisis estático. Detalle en la sección de SCRUM-22 de [docs/pruebas-tecnicas.md](docs/pruebas-tecnicas.md).
* **Un guion no hace lo que se espera con la API.** Consultá la API directamente y guardá la respuesta: `python guiones/consultar_api.py /api/system/status` (más ejemplos en el propio guion). Solo hace pedidos de lectura, toma el token de `laboratorio/.env` y escribe en `trabajo/api/`, que no se versiona. Así la respuesta real queda en un archivo que cualquiera del grupo puede revisar.
* **Un build falla.** El log completo está en `trabajo/logs/`. El guion ya desactiva los plugins de verificación propios de cada proyecto que no tienen que ver con el estudio (licencias, compatibilidad binaria, estilo).

## Reglas del laboratorio

1. Todo número del artículo sale de un guion de este repositorio.
2. Se analiza siempre un commit de `corpus/corpus.csv`, nunca un tag ni una rama.
3. Un único perfil de calidad para todo el análisis principal ("Sonar way comprehensive", claves `corpus-*`). El contraste del eje 1 con "Sonar way core" va bajo `corpus-core-*`. `analizar.py` asigna el perfil en cada análisis.
4. Las versiones de las herramientas se cambian solo en `VERSIONES.md` y en el mismo commit donde se usan.
5. Los análisis de prueba van bajo claves `prueba-*`; el análisis definitivo, bajo `corpus-*`.
