# Resultados del eje 2 (sección 5.2): ficha para la redacción

**Generado el 2026-11-18** con `guiones/eje2_correlacion.py` y `guiones/figuras/figura_eje2_dispersion.py`, sobre `datos/extraccion-<proyecto>/eje2_metodos.csv` (release nuevo de cada proyecto: commons-io 2.22.0, commons-collections 4.6.0, jsoup 1.23.2 y jfreechart 1.5.6). Cubre SCRUM-47, 48 y 49. La redacción de la 5.2 (SCRUM-50) la hace Fernando: esta ficha tiene los números, lo que salió de leer el código y las advertencias de interpretación, no el texto.

Todos los números salen de los CSV de `resultados/eje2/`. Si se vuelve a correr el guion, salen iguales.

## 1. Qué se midió

- **Unidad:** el método (D1). 17.782 métodos con par entre SonarQube y PMD; 17.659 con cognitiva medida por SonarQube. Los 123 restantes se informan aparte (sección 4).
- **Variables:** ciclomática y cognitiva de SonarQube (reglas `java:S1541` y `java:S3776` con umbral 0), tamaño = NCSS de PMD 7.26.0 (D1, D5).
- **Estadística (D5):** Spearman; parcial controlando el NCSS (Pearson parcial sobre los rangos); IC del 95 % con la transformación de Fisher y el error 1,03/√(n−3) de Fieller, Hartley y Pearson. Como análisis de sensibilidad, sin los métodos triviales (ciclomática 1) y con los no medidos contados como 0 (como en la vista preliminar de la PT2).

## 2. Distribuciones

Las dos métricas son conteos muy asimétricos: la mediana de la ciclomática es 1 y la de la cognitiva es 0 en los cuatro proyectos, y el 70,7 % de los métodos tiene cognitiva 0. Es lo que justifica Spearman (D5) y lo que hace necesario el análisis sin triviales.

| Proyecto | Métrica | n | Mediana | Q3 | P90 | Máximo | Media | Proporción de ceros |
|---|---|---|---|---|---|---|---|---|
| commons-io | ciclomatica_sonar | 3.076 | 1 | 1 | 2 | 31 | 1,526 | 0,0 % |
| commons-io | cognitiva_sonar | 3.076 | 0 | 0 | 2 | 51 | 0,747 | 75,1 % |
| commons-io | ncss_pmd | 3.076 | 2 | 3 | 6 | 55 | 3,398 | 0,0 % |
| commons-collections | ciclomatica_sonar | 4.692 | 1 | 2 | 3 | 29 | 1,588 | 0,0 % |
| commons-collections | cognitiva_sonar | 4.692 | 0 | 1 | 2 | 50 | 0,822 | 72,4 % |
| commons-collections | ncss_pmd | 4.692 | 2 | 4 | 7 | 124 | 3,713 | 0,0 % |
| jsoup | ciclomatica_sonar | 2.000 | 1 | 2 | 4 | 35 | 2,072 | 0,0 % |
| jsoup | cognitiva_sonar | 2.000 | 0 | 1 | 4 | 47 | 1,437 | 61,5 % |
| jsoup | ncss_pmd | 2.000 | 3 | 5 | 10 | 74 | 4,855 | 0,0 % |
| jfreechart | ciclomatica_sonar | 7.891 | 1 | 2 | 4 | 58 | 2,090 | 0,0 % |
| jfreechart | cognitiva_sonar | 7.891 | 0 | 1 | 4 | 177 | 1,750 | 70,4 % |
| jfreechart | ncss_pmd | 7.891 | 3 | 6 | 13 | 253 | 6,452 | 0,0 % |
| corpus | ciclomatica_sonar | 17.659 | 1 | 2 | 3 | 58 | 1,856 | 0,0 % |
| corpus | cognitiva_sonar | 17.659 | 0 | 1 | 3 | 177 | 1,293 | 70,7 % |
| corpus | ncss_pmd | 17.659 | 2 | 5 | 10 | 253 | 5,011 | 0,0 % |

## 3. Correlación entre ciclomática y cognitiva (Tabla 10 propuesta)

| Proyecto | Nivel | Subconjunto | n | ρ (IC 95 %) | ρ ciclomática-NCSS | ρ cognitiva-NCSS | ρ parcial (NCSS) |
|---|---|---|---|---|---|---|---|
| commons-io | metodo | medidos | 3.076 | 0,930 (0,925 a 0,935) | 0,603 | 0,668 | 0,889 |
| commons-io | metodo | ciclomatica>1 | 673 | 0,922 (0,910 a 0,933) | 0,713 | 0,772 | 0,834 |
| commons-io | metodo | no medidos como 0 | 3.081 | 0,926 (0,920 a 0,931) | 0,605 | 0,665 | 0,880 |
| commons-io | archivo | suma de medidos | 254 | 0,739 (0,676 a 0,792) | 0,977 | 0,737 | 0,133 |
| commons-collections | metodo | medidos | 4.692 | 0,978 (0,977 a 0,979) | 0,749 | 0,756 | 0,950 |
| commons-collections | metodo | ciclomatica>1 | 1.257 | 0,938 (0,931 a 0,945) | 0,730 | 0,755 | 0,864 |
| commons-collections | metodo | no medidos como 0 | 4.720 | 0,965 (0,963 a 0,967) | 0,748 | 0,750 | 0,920 |
| commons-collections | archivo | suma de medidos | 315 | 0,752 (0,698 a 0,798) | 0,983 | 0,759 | 0,050 |
| jsoup | metodo | medidos | 2.000 | 0,975 (0,973 a 0,977) | 0,742 | 0,764 | 0,943 |
| jsoup | metodo | ciclomatica>1 | 744 | 0,906 (0,891 a 0,918) | 0,694 | 0,755 | 0,809 |
| jsoup | metodo | no medidos como 0 | 2.088 | 0,852 (0,839 a 0,864) | 0,774 | 0,660 | 0,717 |
| jsoup | archivo | suma de medidos | 85 | 0,929 (0,891 a 0,954) | 0,990 | 0,923 | 0,273 |
| jfreechart | metodo | medidos | 7.891 | 0,991 (0,991 a 0,992) | 0,772 | 0,780 | 0,978 |
| jfreechart | metodo | ciclomatica>1 | 2.310 | 0,923 (0,917 a 0,929) | 0,795 | 0,814 | 0,784 |
| jfreechart | metodo | no medidos como 0 | 7.893 | 0,991 (0,990 a 0,991) | 0,772 | 0,779 | 0,977 |
| jfreechart | archivo | suma de medidos | 535 | 0,894 (0,875 a 0,910) | 0,976 | 0,886 | 0,289 |
| corpus | metodo | medidos | 17.659 | 0,978 (0,977 a 0,978) | 0,733 | 0,748 | 0,951 |
| corpus | metodo | ciclomatica>1 | 4.984 | 0,923 (0,919 a 0,927) | 0,755 | 0,794 | 0,812 |
| corpus | metodo | no medidos como 0 | 17.782 | 0,958 (0,956 a 0,959) | 0,738 | 0,735 | 0,907 |
| corpus | archivo | suma de medidos | 1.189 | 0,840 (0,822 a 0,856) | 0,975 | 0,849 | 0,105 |

### Lectura

1. **Por método, la correlación es muy alta y sobrevive al control del tamaño.** En el corpus, ρ = 0,978 y la parcial con el NCSS es 0,951. Por proyecto va de 0,930 (commons-io) a 0,991 (jfreechart). El tamaño no explica la asociación: la ciclomática y la cognitiva se parecen entre sí bastante más de lo que cada una se parece al NCSS (0,733 y 0,748).
2. **Los métodos triviales inflan un poco, pero no cambian la conclusión.** Sin los métodos con ciclomática 1 (el 72 % del corpus), ρ baja a 0,923 y la parcial a 0,812. Es la cifra más honesta para decir cuánto se parecen las dos métricas donde hay lógica que medir.
3. **A nivel archivo la correlación no se infla: baja.** Era la hipótesis de SCRUM-48 y los datos dicen lo contrario. En el corpus, ρ por archivo es 0,840 (contra 0,978 por método), y controlando el tamaño cae a 0,105. La razón es aritmética: cada método suma al menos 1 a la ciclomática del archivo, y un método trivial suma 0 a la cognitiva. La ciclomática de un archivo queda casi determinada por cuántos métodos tiene (ρ con el NCSS = 0,975), y la cognitiva no. Sumar métodos convierte a la ciclomática en una medida de tamaño. Es el mismo problema de agregación que la 5.1 vio con la letra de mantenibilidad, y conviene decirlo así en 6.1.
4. **El valor de la PT2 para jsoup (0,852) era efecto de contar los no medidos como 0.** Sin ellos, jsoup da 0,975. La vista preliminar subestimaba la correlación.

**Cómo leerlo (criterio de SCRUM-47).** La correlación sigue muy alta después de controlar el tamaño, así que la cognitiva aporta poca información de orden que la ciclomática no tenga. Las diferencias se concentran en construcciones puntuales (sección 5). Esto no dice cuál de las dos predice mejor la comprensión: eso es lo que discuten [17] y [24], y este trabajo no lo mide.

## 4. Los métodos que SonarQube no mide (123)

Hallazgo nuevo: los "no medidos" no son una sola cosa. Hay dos casos y se comportan distinto.

| Caso | Métodos | Dónde | Qué pasa con su complejidad cognitiva |
|---|---|---|---|
| Métodos de clases anónimas | 36 | commons-collections (28), jsoup (3, en `Attributes`), commons-io (3) y jfreechart (2) | **Se suma al método que contiene la clase anónima.** Ejemplo: `CircularFifoQueue.iterator()` (commons-collections) tiene ciclomática 1 y cognitiva 19, que es la de `hasNext`, `next` y `remove` con el incremento de anidamiento. PMD da lo mismo (19). Es lo que manda la especificación: el flujo de control dentro de métodos anidados y lambdas cuenta para el método que los contiene, con incremento de anidamiento, y sin incremento estructural propio ([7], v1.7, p. 10). |
| Métodos en cuerpos de constantes de enum | 87 | jsoup `TokeniserState` (54) y `HtmlTreeBuilderState` (31); commons-io `FileSystem` (2) | **No se le asigna a ningún método ni al archivo.** No hay método contenedor. La especificación no trata este caso. `HtmlTreeBuilderState.java`, el archivo más complejo de jsoup, tiene cognitiva 6 en SonarQube a nivel archivo (ciclomática 539); PMD le da 790. En total se pierden 918 puntos de cognitiva según PMD. |

Para el artículo: el caso de las clases anónimas es una **decisión de diseño de la métrica**, que además rompe la comparabilidad con la ciclomática, porque la ciclomática sí informa cada método anidado por separado. El caso de los enum es una **omisión del instrumento**, con un efecto directo sobre la validez: el archivo más complejo del proyecto aparece entre los más simples. La ficha de SCRUM-29 hablaba de 88/2/28/5 "no medidos": la corrección es que 36 no se pierden, se reubican.

Los dos casos van a 6.2 (validez de constructo e instrumento). En la correlación quedan fuera, como fijó D5: los de clases anónimas ya están contados en su contenedor (incluirlos sería contar dos veces) y los de enum no tienen valor.

## 5. Dónde se separan las dos métricas (SCRUM-48)

`resultados/eje2/discrepancias.csv` tiene los 15 métodos de cada lado con mayor diferencia de rango percentil, entre los que tienen al menos 5 en alguna de las dos métricas. Leyendo el código salen tres mecanismos:

| Mecanismo | Efecto | Ejemplo |
|---|---|---|
| `switch` con muchos `case` | La ciclomática suma 1 por `case`; la cognitiva, 1 por todo el `switch` ([7], p. 8) | `QueryParser.parsePseudoSelector()` de jsoup: ciclomática 30, cognitiva 1. Un `switch` sobre el nombre de la pseudoclase con un `return` por caso |
| Cadenas del mismo operador lógico | La ciclomática suma 1 por cada `&&` o `\|\|`; la cognitiva, 1 por secuencia ([7], p. 8) | `ItemLabelAnchor.isInternal()` de jfreechart: ciclomática 13, cognitiva 1, NCSS 2. Un `return` con doce comparaciones unidas por `\|\|` |
| Clases anónimas y lambdas | La cognitiva del contenedor incluye la de lo anidado; la ciclomática no | `EnhancedDoubleHasher.indices()` de commons-collections: ciclomática 1, cognitiva 39. Devuelve una clase anónima con dos métodos |

El anidamiento (la diferencia que más defiende [7]) aparece en métodos menos extremos, como `ReadAheadInputStream.readAsync()` de commons-io (ciclomática 3, cognitiva 19), que además tiene una lambda con lógica anidada. Los extremos de la lista los dominan los tres mecanismos de la tabla.

Para el Algoritmo 2 conviene `ItemLabelAnchor.isInternal()` (es corto y muestra la diferencia en una línea), o `parsePseudoSelector()` recortado. Para el caso de las clases anónimas, `CircularFifoQueue.iterator()`.

## 6. Acuerdo entre SonarQube y PMD (confiabilidad entre instrumentos, Tabla 11 propuesta)

| Proyecto | Métrica | n | Valor igual | PMD mayor | PMD menor | ρ SonarQube-PMD |
|---|---|---|---|---|---|---|
| commons-io | ciclomatica | 3.081 | 88,1 % | 314 | 52 | 0,872 |
| commons-io | cognitiva | 3.076 | 99,6 % | 11 | 1 | 0,999 |
| commons-collections | ciclomatica | 4.720 | 85,8 % | 596 | 74 | 0,886 |
| commons-collections | cognitiva | 4.692 | 99,3 % | 24 | 7 | 0,999 |
| jsoup | ciclomatica | 2.088 | 90,9 % | 111 | 79 | 0,927 |
| jsoup | cognitiva | 2.000 | 98,9 % | 13 | 10 | 1,000 |
| jfreechart | ciclomatica | 7.893 | 94,4 % | 392 | 50 | 0,984 |
| jfreechart | cognitiva | 7.891 | 99,0 % | 62 | 18 | 1,000 |
| corpus | ciclomatica | 17.782 | 90,6 % | 1.413 | 255 | 0,935 |
| corpus | cognitiva | 17.659 | 99,2 % | 110 | 36 | 1,000 |

Las dos herramientas coinciden casi siempre en la cognitiva (99,2 % de los métodos medidos; si se miran solo los métodos con cognitiva mayor que 0, los que SonarQube informa por issue, la coincidencia es de 96,6 a 98,6 %, que es la cifra de `docs/corrida-produccion.md`) y bastante menos en la ciclomática (90,6 %). Las diferencias de la ciclomática son sistemáticas y salen de dos reglas de conteo distintas:

- **PMD suma 1 por cada `throw`.** De los 1.413 métodos donde PMD da más, 1.281 tienen un `throw`, y en 1.148 la cantidad de `throw` explica toda la diferencia. Entre los 16.114 métodos donde coinciden, solo 8 tienen un `throw`. La documentación de PMD incluye `throw` entre las sentencias de control que suman a CYCLO.
- **SonarQube suma los `&&` y `||` fuera de las condiciones** (en un `return` o una asignación). En 254 de los 255 métodos donde PMD da menos hay un operador lógico fuera de una condición. PMD solo los cuenta "en la condición de una sentencia de control".

Las dos dicen implementar a McCabe [23]. Que dos implementaciones de la métrica más clásica del programa difieran en el 9,4 % de los métodos es un dato de confiabilidad para 2.3 y 6.2, y conecta con la crítica de Shepperd [28] sobre la definición operativa de la métrica. Pendiente: citar la documentación de la versión instalada de PMD (7.26.0). La verificación se hizo contra la de la serie 6.x y contra los datos.

## 7. Otros datos para 6.2

- 4 métodos no tienen par en PMD por `// NOPMD` y 5 faltan en SonarQube por `// NOSONAR` (SCRUM-29); los dos grupos quedan fuera de `eje2_metodos.csv`. El código medido puede silenciar al instrumento.
- El método con cognitiva más alta del corpus tiene 177 (jfreechart).

## 8. Material listo para la 5.2

| Elemento | Archivo | Numeración sugerida |
|---|---|---|
| Dispersión por método y por archivo | `resultados/figuras/fig6_eje2_dispersion.png` (800 dpi, 122 mm de ancho) | Fig. 6 |
| Correlaciones por proyecto, método y archivo | `resultados/eje2/correlaciones.csv` (tabla de la sección 3) | Tabla 10 |
| Acuerdo SonarQube y PMD | `resultados/eje2/acuerdo_herramientas.csv` (tabla de la sección 6) | Tabla 11 |
| Fragmento de código | `ItemLabelAnchor.isInternal()` o `QueryParser.parsePseudoSelector()` | Algoritmo 2 |
| No medidos | `resultados/eje2/no_medidos.csv` | Texto |

Para la Tabla 10 alcanza con las filas "medidos", "ciclomatica>1" y "archivo" de cada proyecto y del corpus. La fila "no medidos como 0" solo hace falta para explicar la diferencia con la vista preliminar. Referencias del mapa para la 5.2: [6], [7], [17], [23], [24], [28].
