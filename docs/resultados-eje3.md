# Resultados del eje 3, primera parte (sección 5.3): ficha para la redacción

**Generado el 2026-11-18** con `guiones/eje3_quality_gate.py`, sobre la corrida de producción del 2026-10-13 (`datos/corpus-*` con "Sonar way comprehensive" y `datos/corpus-core-*` con "Sonar way core"; gate "Sonar way"; código nuevo = versión anterior, D2). Cubre SCRUM-52 y deja el material de SCRUM-51. La redacción de la 5.3 (SCRUM-53) la hace Brenda: acá están los números, los mecanismos y de dónde sale cada uno, no el texto.

Son cuatro proyectos: todo es descriptivo. No se generaliza (SCRUM-52).

## 1. Qué decidió el gate (Tabla 12 propuesta)

| Proyecto | Perfil | Líneas nuevas (por cubrir) | Issues nuevos (en test) | Cobertura nueva | Duplicación nueva | Gate | Sin cobertura | Sin issues de test | Sin ambos |
|---|---|---|---|---|---|---|---|---|---|
| commons-io | comprehensive | 7.645 (362) | 57 (34) | 92,5 % | 0,2 % | rechaza | rechaza | rechaza | rechaza |
| commons-io | core | 7.645 (362) | **1 (1)** | 92,5 % | 0,2 % | rechaza | rechaza | **aprueba** | **aprueba** |
| commons-collections | comprehensive | 17.668 (800) | 189 (174) | 85,5 % | **6,1 %** | rechaza | rechaza | rechaza | rechaza |
| commons-collections | core | 17.668 (800) | 4 (3) | 85,5 % | **6,1 %** | rechaza | rechaza | rechaza | rechaza |
| jsoup | comprehensive | 5.325 (1.201) | 79 (21) | 91,7 % | 0,0 % | rechaza | rechaza | rechaza | rechaza |
| jsoup | core | 5.325 (1.201) | 3 (0) | 91,7 % | 0,0 % | rechaza | rechaza | rechaza | rechaza |
| jfreechart | comprehensive | 5.460 (208) | 1 (0) | **30,2 %** | 1,6 % | rechaza | rechaza | rechaza | rechaza |
| jfreechart | core | 5.460 (208) | 1 (0) | **30,2 %** | 1,6 % | rechaza | rechaza | rechaza | rechaza |

En negrita, los valores que hacen fallar una condición distinta de `new_violations`, y los cambios de decisión. Umbrales de "Sonar way": `new_violations` > 0, `new_coverage` < 80 %, `new_duplicated_lines_density` > 3 %. La condición de *hotspots* revisados no aparece en ningún proyecto (no hubo *hotspots* nuevos). El guion vuelve a evaluar el gate con los umbrales exportados de la instancia y controla que el escenario real coincida con el de SonarQube (coincide en los ocho).

"Sin issues de test" cuenta en `new_violations` solo los issues nuevos de `src/main`. No es una opción de SonarQube: es un contrafáctico para ver cuánto del rechazo viene del código de test.

## 2. Lo que muestra la tabla

1. **Los ocho gates se rechazan, y `new_violations` rechaza en los ocho.** La duplicación rechaza en commons-collections (los dos perfiles) y la cobertura en jfreechart (los dos perfiles).
2. **Sacar la cobertura no cambia nada** (pedido de SCRUM-52): ningún proyecto se rechaza solo por cobertura, porque en todos hay al menos un issue nuevo.
3. **El umbral cero satura el indicador.** Con comprehensive, commons-collections tiene 189 issues nuevos; con core, jfreechart tiene 1. La decisión es la misma. Cambiar de perfil reduce los issues nuevos entre un 96 y un 98 % en tres proyectos (79 a 3, 189 a 4, 57 a 1) y no cambia ninguna decisión. Leído con 2.1 y 2.2: un conteo en escala de razón se convierte en una decisión binaria con el umbral en el valor mínimo posible, así que el indicador no distingue un issue de doscientos. Material para 6.1.
4. **El código de test pesa mucho en la decisión.** En commons-collections, 174 de los 189 issues nuevos (92 %) están en tests; en commons-io, 34 de 57; en jsoup, 21 de 79. Con core, el único issue nuevo de commons-io es un test sin aserciones (`java:S2699`): si no contaran los tests, ese gate aprobaría. En cambio, la cobertura y la duplicación se miden solo sobre el código principal (`new_lines_to_cover` es 362 en commons-io, con 7.645 líneas nuevas que incluyen tests y archivos que no son Java).
5. **jfreechart: el gate juzga un cambio de licencia.** Entre 1.5.5 y 1.5.6 cambió el encabezado de 652 de los 658 archivos (`docs/corrida-produccion.md`). SonarQube marca 5.460 líneas nuevas, de las que 208 se pueden cubrir; con 30,2 % de cobertura sobre esas 208, el gate rechaza. El único issue nuevo es `java:S3518` (posible división por cero), de fiabilidad. La "calidad del código nuevo" de esa versión es, en su mayor parte, la de un comentario.
6. **commons-collections: la duplicación nueva está en decoradores.** De los 54 archivos con duplicación en el código nuevo, 20 son clases `Unmodifiable*` (por ejemplo `UnmodifiableMultiSet` y `UnmodifiableSortedSet`, con 80 % de líneas nuevas duplicadas): código de delegación que se repite por diseño. Lista completa en `resultados/eje3/duplicacion_codigo_nuevo.csv`.

## 3. Qué issues rechazan (reglas más frecuentes del código nuevo)

Detalle en `resultados/eje3/issues_nuevos_por_regla.csv`. Las descripciones son las de rules.sonarsource.com: conviene verificarlas con el enlace antes de citarlas.

| Proyecto | Perfil | Reglas más frecuentes (issues nuevos, en test) |
|---|---|---|
| commons-io | comprehensive | `S1130` excepciones declaradas que no se lanzan (11, 11); `S5778` más de una invocación dentro de `assertThrows` (9, 9); `S110` jerarquía de herencia profunda (5, 0); `S1133` código obsoleto que hay que quitar (4, 0) |
| commons-io | core | `S2699` test sin aserciones (1, 1) |
| commons-collections | comprehensive | `S125` código comentado (47, 47); `S1130` (39, 39); `S5778` (26, 26); `S5961` demasiadas aserciones en un test (15, 15) |
| commons-collections | core | `S2699` (2, 2); `S2118` escritura de objetos no serializables (1, 0); `S5863` aserción que compara un objeto consigo mismo (1, 1) |
| jsoup | comprehensive | `S115` nombre de constante (28, 8); `S5778` (8, 8); `S1192` literal repetido (7, 0); `S1117` variable que oculta un campo (4, 0) |
| jsoup | core | `S2259` posible desreferencia de `null` (2, 0); `S8786` expresión regular con *backtracking* costoso (1, 0) |
| jfreechart | ambos | `S3518` posible división por cero (1, 0) |

Con comprehensive, el gate se rechaza sobre todo por convenciones de nombres y de estilo de tests; con core, por posibles defectos de fiabilidad y por tests sin aserciones. La decisión es la misma, pero el motivo no.

## 4. Formas de aprobar el gate sin mejorar el código (SCRUM-51)

Cada mecanismo con su fuente. "Lab" = verificado en este laboratorio. "Doc" = según la documentación de Community Build 26.10 ([31]); si se cita, verificar la página el día del cierre y archivarla (pendiente de `tp-referencias.md`).

| Mecanismo | Cómo funciona | Fuente |
|---|---|---|
| Entregar en partes de menos de 20 líneas | Con menos de 20 líneas nuevas, las condiciones de cobertura y duplicación no se evalúan (`sonar.qualitygate.ignoreSmallChanges`) | Lab (PT3) y Doc |
| Primer análisis | Sin análisis anterior no hay código nuevo y el gate aprueba sin evaluar ninguna condición | Lab (PT1) |
| Elegir un perfil más laxo | Con core, los issues nuevos bajan entre 96 y 98 % en tres proyectos. Acá no alcanzó para aprobar, pero con umbral 0 alcanza con que el perfil no tenga la regla | Lab (corrida de producción, D7) |
| Comentarios `// NOSONAR` | La línea deja de generar issues; en commons-io hay 5 | Lab (SCRUM-29) |
| Marcar issues como aceptados o falsos positivos | `new_violations` cuenta issues abiertos; quien tenga el permiso *Administer Issues* puede cerrarlos sin tocar el código. En la instancia del grupo ese permiso lo tenía cualquier usuario por defecto hasta el 17/10 | Lab (configuración de permisos, plan sección 14) y Doc |
| Excluir archivos del análisis | `sonar.exclusions`, `sonar.test.exclusions`, `sonar.coverage.exclusions`, `sonar.cpd.exclusions` | Doc (el laboratorio no usa exclusiones, D7) |
| Tests sin aserciones | Suben la cobertura sin verificar nada. La regla `S2699` lo detecta, pero sus issues van a `new_violations`, no a la cobertura | Lab (aparece en commons-io y commons-collections con core) |
| Cambiar la definición de código nuevo | Versión anterior, cantidad de días, fecha o rama de referencia: el mismo cambio puede entrar o no en el período | Doc |
| Cambios que son solo de espacios | No cuentan como código nuevo | Lab (PT3) |

Encuadre teórico: ley de Goodhart en la formulación de Strathern [33] y medición motivacional frente a informativa de Austin [1]. Todas las condiciones son umbrales binarios sobre métricas continuas: optimizar la métrica no requiere mejorar el atributo. [36] da el contexto de uso de estas herramientas en integración continua.

## 5. Para 6.2 (amenazas)

- Cuatro proyectos y un solo par de versiones por proyecto.
- El resultado depende del perfil (D7) y de la definición de código nuevo (D2). La conclusión del punto 3 de la sección 2 se mantiene con los dos perfiles.
- En la API, `new_lines` incluye tests y archivos que no son Java, y `new_lines_to_cover` solo el código principal: dos poblaciones distintas en el mismo gate.
- La condición de *hotspots* figura en la documentación de "Sonar way" pero no se evaluó en ningún caso (plan, D2).

## 6. Material listo

| Elemento | Archivo | Numeración sugerida |
|---|---|---|
| Resultado del gate y contrafácticos | `resultados/eje3/gate_por_proyecto.csv` (tabla de la sección 1) | Tabla 12 |
| Mecanismos de elusión | Tabla de la sección 4 | Tabla 13 |
| Efecto del perfil sobre los issues nuevos | Ya está en la Fig. 1 de la muestra de avances: remitir a esa figura (SCRUM-53) | Fig. 1 |
