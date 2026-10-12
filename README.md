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
| `docs/` | Resultados de las pruebas técnicas y diccionario de datos | Sí |
| `trabajo/` | Checkouts del corpus y logs. Se regenera con los guiones | No |

Las versiones de todo lo que interviene (SonarQube, Maven, JDK, escáner, JaCoCo) están fijadas en [VERSIONES.md](VERSIONES.md).

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

**3. Preparar la instancia.** Espera a que arranque, reemplaza la contraseña de fábrica de `admin` por una aleatoria y genera un token. Las dos quedan en `laboratorio/.env`, que no se sube al repositorio:

```
python guiones/preparar_sonarqube.py
```

SonarQube queda en http://localhost:9000 (usuario `admin`, contraseña en `laboratorio/.env`).

**4. Descargar el corpus.** Trae los ocho commits de `corpus/corpus.csv` y verifica cada hash:

```
python guiones/clonar_corpus.py
```

**5. Compilar el corpus (SCRUM-22).** Compila y corre los tests de las ocho versiones. La primera vez tarda bastante porque descarga las dependencias de Maven; después quedan en caché:

```
python guiones/compilar_corpus.py
```

Resultado en `datos/compilacion.csv`.

**6. Prueba técnica 1 (SCRUM-21).** Analiza jsoup bajo una clave de prueba, exporta las medidas por archivo y los issues, y verifica los supuestos del eje 1:

```
python guiones/analizar.py jsoup 1.23.2 --clave prueba-pt1-jsoup
python guiones/exportar_medidas.py prueba-pt1-jsoup
python guiones/verificar_supuestos.py prueba-pt1-jsoup
```

Resultados en `datos/prueba-pt1-jsoup/`.

Las pruebas técnicas 2, 3 y 4 están descritas en [docs/pruebas-tecnicas.md](docs/pruebas-tecnicas.md).

## Apagar y limpiar

```
docker compose -f laboratorio/docker-compose.yml --env-file laboratorio/.env down      # apaga, conserva los datos
docker compose -f laboratorio/docker-compose.yml --env-file laboratorio/.env down -v   # borra también los análisis
```

## Si algo falla

* **SonarQube no arranca y el log habla de `vm.max_map_count`.** El `docker-compose.yml` ya desactiva el requisito. Si igual aparece, en Windows correr `wsl -d docker-desktop -u root sysctl -w vm.max_map_count=524288` y volver a levantar.
* **SonarQube se reinicia solo o queda muy lento.** Le falta memoria: subirla en Docker Desktop, en Settings, Resources.
* **`preparar_sonarqube.py` no puede autenticarse.** Si cambiaste la contraseña de `admin` a mano, escribila en `SONAR_ADMIN_CLAVE` de `laboratorio/.env`.
* **Un build falla.** El log completo está en `trabajo/logs/`. El guion ya desactiva los plugins de verificación propios de cada proyecto que no tienen que ver con el estudio (licencias, compatibilidad binaria, estilo).

## Reglas del laboratorio

1. Todo número del artículo sale de un guion de este repositorio.
2. Se analiza siempre un commit de `corpus/corpus.csv`, nunca un tag ni una rama.
3. Un único perfil de calidad para todo el análisis principal.
4. Las versiones de las herramientas se cambian solo en `VERSIONES.md` y en el mismo commit donde se usan.
5. Los análisis de prueba van bajo claves `prueba-*`; el análisis definitivo, bajo `corpus-*`.
