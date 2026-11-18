# Protocolo de clasificación de hallazgos (sección 5.4, SCRUM-54)

**Fecha de fijación:** 2026-11-18, antes de exportar y de ver los hallazgos del proyecto propio.
**Estado:** borrador de Claude para que lo apruebe Brenda (integrante-4, responsable de SCRUM-54). Se considera fijado cuando Brenda lo aprueba y se versiona en el repositorio. Desde ese commit no se cambia: si hace falta un ajuste, se agrega al final como enmienda con fecha y motivo, y se declara en 6.2.

## 1. Qué se mide

La **precisión** de SonarQube sobre un código del que el grupo tiene criterio de verdad: qué proporción de los hallazgos que informa la herramienta son problemas reales. No se mide la exhaustividad (recall) ni F1, porque haría falta un inventario completo de los problemas reales del proyecto (4.4).

## 2. Objeto

| Aspecto | Valor |
|---|---|
| Proyecto | `poo2025-Junin-grupo-Doyle-Olano-Uribe`, módulo `poo2025/` (backend Java 17, Spring Boot 3.5.6) |
| Commit | `cbccd2676cc7335dd0c863dced2d9af3c3ba253a` (rama `main`, 2026-03-13), en `corpus/proyecto-propio.csv` |
| Análisis | Clave `propio-poo2025`, SonarQube Community Build 26.10.0.133078, perfil "Sonar way comprehensive", sin exclusiones (igual que el corpus, D7) |
| Unidad de análisis | El issue abierto, tal como aparece en `datos/propio-poo2025/issues.csv` |
| Qué se clasifica | **Todos** los issues abiertos, de mantenibilidad, fiabilidad y seguridad (decisión de Eric del 2026-11-18). Los *security hotspots* quedan fuera: no son issues y Community Build los está retirando |

## 3. Categorías

Cada issue recibe exactamente una de estas tres categorías.

| Código | Categoría | Definición operativa |
|---|---|---|
| `R` | Problema real | Lo que el mensaje afirma sobre el código es cierto **y** corregirlo mejoraría, en este proyecto, el atributo de calidad que la regla dice proteger (mantenibilidad, fiabilidad o seguridad). Un revisor razonable pediría el cambio. |
| `FP` | Falso positivo | Lo que el mensaje afirma sobre el código **no es cierto**: la condición de la regla no se cumple en realidad. Es un error del detector. |
| `I` | Real pero irrelevante | Lo que el mensaje afirma es cierto, pero corregirlo no aporta nada en este contexto, o contradice una convención deliberada o un requisito del framework. |

### Regla de decisión (se aplica en este orden)

1. **¿Es cierto lo que el mensaje dice del código?** Se lee la línea señalada y lo que haga falta alrededor. Si no es cierto, `FP`.
2. **¿Corregirlo mejoraría el atributo de calidad en este proyecto?** Si sí, `R`. Si no, `I`.
3. **Si quedan dudas,** igual se elige una categoría y se escribe `baja` en la columna `confianza`. No hay categoría "no sé".

La pregunta 1 es sobre el código, no sobre la regla. La 2 es sobre este proyecto, no sobre el código Java en general: que el proyecto sea académico no vuelve irrelevante un hallazgo por sí solo, porque el estudio pregunta qué haría un equipo con ese código.

### Ejemplos genéricos

Estos ejemplos se escribieron sin conocer los hallazgos del proyecto, para fijar el criterio. No anticipan qué reglas van a aparecer.

| Categoría | Ejemplo |
|---|---|
| `R` | "Remove this unused private field": el campo no se usa en ningún lado y no lo lee ningún framework. |
| `R` | Un `Optional.get()` sin `isPresent()` en un camino donde el repositorio puede devolver vacío. |
| `FP` | "Remove this unused private field" sobre un campo que Lombok expone con `@Getter`, o que JPA lee por reflexión. |
| `FP` | Una posible desreferencia de `null` sobre una variable que, por cómo está escrito el método, nunca puede ser `null` en esa línea. |
| `I` | Nombre de campo que no sigue la convención de la regla, pero que tiene que llamarse así porque se mapea a JSON o a una columna. |
| `I` | Un literal repetido tres veces en mensajes de error distintos, donde una constante no haría el código más claro. |

## 4. Quiénes clasifican y con qué información

- **Eric Doyle**, autor del código, y **Brenda Martin**, segunda clasificadora (D4, reunión del 2026-10-17).
- Antes de clasificar, Brenda recorre el código del módulo (paquetes, entidades, servicios, controladores y DTO) para entender la arquitectura. Puede consultarle a Eric **cómo funciona el código**, pero no **cómo clasificó** un issue.
- Cada clasificador trabaja sobre su propia copia de la planilla (`planilla-clasificacion.csv`), guardada como `clasificacion-eric.csv` y `clasificacion-brenda.csv`. No se muestran las respuestas ni hablan de issues puntuales hasta que los dos entregaron.
- La planilla trae la regla, el mensaje, el archivo, la línea, un enlace a la línea en GitHub (en el commit fijado) y un enlace a la descripción de la regla. **No trae la severidad ni el esfuerzo de remediación**, para que la categoría no se ancle en lo que opina la herramienta. Los clasificadores no abren los issues en la interfaz de SonarQube mientras clasifican, por la misma razón.
- Para cada issue se completan `categoria` (`R`, `FP` o `I`), `confianza` (`alta` o `baja`) y `nota` (una frase con el motivo; obligatoria en `FP` e `I`).

## 5. Desacuerdos

1. El acuerdo se calcula sobre las dos clasificaciones **independientes**, antes de cualquier discusión.
2. Después, Eric y Brenda revisan juntos solo los issues en desacuerdo y acuerdan una categoría, registrando el motivo en `clasificacion-consenso.csv`.
3. Si no llegan a un acuerdo, decide un tercer integrante (Alejo o Fernando) leyendo las dos notas.
4. La precisión que se informa como resultado principal es la del consenso. También se informa la de cada clasificador por separado, para mostrar cuánto depende del evaluador.

## 6. Medidas que se calculan (`guiones/precision_5_4.py`)

| Medida | Definición |
|---|---|
| Precisión estricta | `R / N` |
| Precisión amplia | `(R + I) / N`: proporción de hallazgos en que la herramienta dice algo cierto del código |
| Tasa de falsos positivos | `FP / N` = 1 menos la precisión amplia |
| Intervalo de confianza | 95 %, método de Wilson (se comporta bien con proporciones cercanas a 0 o a 1 y con N chico) |
| Acuerdo | Kappa de Cohen con las tres categorías, y kappa binario `FP` frente a no `FP`. Se informa también la matriz de confusión entre clasificadores y el acuerdo observado |
| Desglose | Por tipo de calidad (mantenibilidad, fiabilidad, seguridad) y por regla, para las reglas con al menos 5 issues |

Los issues no se agrupan: si una regla aparece 40 veces, son 40 decisiones. Se informa cuántos issues aporta cada regla, porque una sola regla frecuente puede dominar la precisión (en jsoup, `java:S115` es el 29 % de los issues).

## 7. Amenazas que se declaran en 6.2

- **Sesgo del autor.** Eric puede tender a defender su código y marcar `FP` o `I` de más.
- **Asimetría de conocimiento.** Brenda conoce el código menos que el autor; el kappa mide también esa diferencia.
- **Un solo proyecto, académico, chico y con Lombok y MapStruct.** La precisión no se generaliza al corpus; el proyecto se eligió porque es el único con criterio de verdad (4.2).
- **Categoría `I`.** Es la más subjetiva de las tres. Por eso se informan las dos precisiones y el kappa binario.

## 8. Enmiendas

1. **2026-11-18, antes de que empiece la clasificación.** Se agrega `docs/guia-clasificacion-5-4.md`: qué detecta cada una de las 13 reglas presentes y qué verificar en el código para responder las dos preguntas de la sección 3, sin indicar categorías. La pidió Eric y la reciben los dos clasificadores por igual, así que no cambia el criterio ni la independencia. Las reglas presentes se conocían porque `planilla_5_4.py` ya se había corrido; la guía se escribió sin mirar el código señalado por los issues.
