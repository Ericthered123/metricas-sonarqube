# Corrida de producción (SCRUM-27 y SCRUM-28)

Lanzada el 2026-10-13 a las 15:01 con `python guiones/correr_corpus.py` y terminada a las 18:27 (205 minutos). Los 16 análisis terminaron bien: los cuatro proyectos, en sus dos releases, con "Sonar way comprehensive" (`corpus-*`) y con "Sonar way core" (`corpus-core-*`), todos con tests y cobertura. La verificación final confirmó que las ocho claves usan el perfil que les corresponde y el gate "Sonar way". Datos en `datos/corpus-*/` y `datos/corpus-core-*/`; detalle de cada análisis en `datos/registro_analisis.csv`.

Esta página registra la corrida y una primera lectura. El análisis de cada eje se hace sobre estos CSV.

## Tests y cobertura

| Proyecto | Tests (viejo / nuevo) | Fallas | Sesiones de JaCoCo | Líneas cubiertas según JaCoCo (release nuevo) |
| --- | --- | --- | --- | --- |
| jsoup | 1.952 + 48 / 2.165 + 46 | 1 en `corpus-jsoup` 1.23.2 | 4 | 9.764 de 10.777 (90,6 %) |
| jfreechart | 2.350 / 2.351 | 0 | 3 | 31.380 de 54.429 (57,7 %) |
| commons-collections | 8.399 / 18.024 | 0 | 3 | 13.569 de 15.185 (89,4 %) |
| commons-io | 6.106 / 6.301 | 11 de permisos (+2 de red en 2.21.0) | 259 / 277 | 8.560 de 9.408 (91,0 %) |

* Las fallas de commons-io son las de entorno ya conocidas (SCRUM-22). La de jsoup es `HttpClientConnectIT.totalTimeout`, un test de tiempos que pasó en la clave de contraste con el mismo commit: inestable, como el `ConnectIT` de la PT4.
* Cada release se midió dos veces (una por perfil, mismo commit), lo que da una repetición del procedimiento de cobertura. En jsoup, jfreechart y commons-collections las líneas cubiertas son idénticas. En commons-io varían en hasta 2 líneas: 8.403 y 8.401 en 2.21.0, y 8.560 en las dos claves de 2.22.0 contra 8.562 en la PT4. Probablemente son tests que dependen de tiempos o de hilos. Es evidencia de confiabilidad alta pero no perfecta, para 6.2.

## Quality Gate (release nuevo)

| Clave | Gate | `new_violations` | `new_coverage` | `new_duplicated_lines_density` | Líneas nuevas por cubrir |
| --- | --- | --- | --- | --- | --- |
| corpus-jsoup | rechazado | 79 | 91,7 | 0,0 | 1.201 |
| corpus-core-jsoup | rechazado | 3 | 91,7 | 0,0 | 1.201 |
| corpus-jfreechart | rechazado | 1 | 30,2 (rechaza) | 1,6 | 208 |
| corpus-core-jfreechart | rechazado | 1 | 30,2 (rechaza) | 1,6 | 208 |
| corpus-commons-collections | rechazado | 189 | 85,5 | 6,1 (rechaza) | 800 |
| corpus-core-commons-collections | rechazado | 4 | 85,5 | 6,1 (rechaza) | 800 |
| corpus-commons-io | rechazado | 57 | 92,5 | 0,2 | 362 |
| corpus-core-commons-io | rechazado | 1 | 92,5 | 0,2 | 362 |

* Los ocho gates se rechazan, con los dos perfiles. Con core, alcanza un solo issue nuevo para rechazar (jfreechart y commons-io).
* La condición de hotspots no aparece en ningún proyecto.
* **jfreechart: el "código nuevo" es casi todo comentarios.** Entre 1.5.5 y 1.5.6 cambió el encabezado de licencia de 652 de los 658 archivos (por ejemplo, `http://` por `https://` en la URL del proyecto). SonarQube marca 5.460 líneas nuevas, pero solo 208 se pueden cubrir con tests, y la cobertura de esas 208 (30,2 %) rechaza el gate. Para el eje 3: un cambio de licencia convierte a casi todo el proyecto en código nuevo.

## Calificación de mantenibilidad por archivo (release nuevo, archivos Java)

| Proyecto | comprehensive | core |
| --- | --- | --- |
| jsoup | 91 A, 3 B, 1 C | 95 A |
| jfreechart | 648 A, 8 B, 1 C, 1 D | 657 A, 1 D |
| commons-collections | 345 A, 17 B, 5 C | 367 A |
| commons-io | 264 A, 6 B, 2 C, 4 D | 276 A |

* Con core, salvo un archivo de jfreechart, todo el corpus es A. Con comprehensive quedan 48 archivos fuera de A de 1.396 (3,4 %).
* La calificación del modo estándar y la del modo MQR coinciden archivo por archivo en los ocho análisis.
* Queda por ver en el eje 1 si los archivos fuera de A son los chicos, como en jsoup.

## Comparación con el diff real

`diff_releases.py --comparar` coincide archivo por archivo en jsoup, jfreechart y commons-collections. En commons-io hay un archivo modificado sin `new_lines`: `BrokenInputStream.java`, con un cambio que git cuenta como una línea agregada y SonarQube no. Es consistente con lo que mostró la PT3: SonarQube ignora los cambios que son solo de espacios.
