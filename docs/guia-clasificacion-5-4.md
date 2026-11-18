# Guía de clasificación de la 5.4 (igual para los dos clasificadores)

**2026-11-18.** Ayuda para aplicar `docs/protocolo-5-4.md`. La pidió Eric y se la entrega igual a Brenda: los dos clasifican con la misma información. Explica **qué mira cada regla y qué conviene verificar en el código**. No dice qué categoría corresponde a ningún issue: eso lo decide cada clasificador. Se registra como enmienda 1 del protocolo.

## 1. Cómo trabajar

- La planilla está ordenada por archivo y línea: abrí cada archivo una sola vez en GitHub (enlace de la columna `codigo`) y clasificá todos sus issues juntos.
- Para cada issue, las dos preguntas del protocolo, **en orden**:
  1. **¿Es cierto lo que dice el mensaje sobre este código?** Es una pregunta sobre el código, no sobre si la regla te parece buena. Si no es cierto: `FP`.
  2. **¿Corregirlo mejoraría, en este proyecto, el atributo que la regla dice proteger?** Si sí: `R`. Si no: `I`.
- La pregunta 2 no es "¿me molesta arreglarlo?" ni "¿es un TP de la facultad?". Es: si un equipo mantuviera este código, ¿el cambio lo haría más fácil de mantener, más confiable o más seguro?
- Si dudás entre dos categorías, elegí una, poné `baja` en `confianza` y explicá la duda en `nota`. Las dudas también son datos.
- La `nota` es una frase con el motivo, por ejemplo: "el import no se usa en ningún lado del archivo" o "el campo lo lee el código generado por Lombok". Es obligatoria en `FP` e `I`.
- Si una regla se repite muchas veces, decidí cada issue por separado: dos issues de la misma regla pueden tener categorías distintas.
- Tiempo estimado: una hora a una hora y media.

## 2. Las 13 reglas que aparecieron

Entre paréntesis, cuántos issues hay. La descripción oficial de cada regla está en el enlace de la columna `descripcion_regla`; ante cualquier diferencia con esta guía, vale la oficial.

| Regla | Qué detecta | Para la pregunta 1 (¿es cierto?) | Para la pregunta 2 (¿mejoraría?) |
|---|---|---|---|
| `S8688` (19) | Llamadas a `.now()` de `java.time` (por ejemplo `LocalDateTime.now()`) sin indicar zona horaria ni `Clock`: se usa la zona del sistema donde corre | ¿La llamada efectivamente no recibe `ZoneId` ni `Clock`? | ¿Importa en qué zona horaria corre el servidor para lo que hace ese código (fechas de torneos, comparaciones, lo que se guarda)? ¿Hace falta controlar el reloj para testear? SonarQube la marca como de **fiabilidad** |
| `S1128` (16) | `import` que no se usa en el archivo | ¿El nombre importado aparece en algún lugar del archivo, incluidas anotaciones, genéricos y Javadoc? | ¿Sacar el import mejoraría la mantenibilidad (lectura, dependencias aparentes entre clases)? |
| `S125` (5) | Bloques de código comentado | ¿Lo marcado es código comentado, o es un comentario en prosa que se parece a código? | ¿Ese código comentado cumple alguna función hoy (documentación, alternativa explicada) o es un resto? |
| `S106` (3) | Uso de `System.out` o `System.err` en lugar de un *logger* | ¿Es `System.out` o `System.err`? | ¿En el contexto de ese código (aplicación Spring Boot que corre en un servidor) importa poder filtrar, ubicar o apagar esos mensajes? |
| `S6204` (3) | `stream.collect(Collectors.toList())` que se podría escribir `stream.toList()` (Java 16+) | ¿Es esa construcción? ¿El proyecto compila con Java 16 o más? (`pom.xml`: Java 17) | Ojo: `toList()` devuelve una lista **inmodificable** y `Collectors.toList()` no lo garantiza. ¿Algún código modifica después esa lista? |
| `S1192` (3) | Un mismo literal de texto repetido 3 veces o más | ¿Está realmente repetido el literal, con el mismo texto? | ¿Una constante evitaría inconsistencias o facilitaría cambiarlo (por ejemplo, un estado como `"NO_PUBLICADO"`), o los usos son independientes entre sí? |
| `S1068` (3) | Campo `private` que no se usa | ¿El campo se lee o se usa en algún lado? Tené en cuenta el código que generan Lombok o MapStruct y lo que hace Spring con los campos. Distinguí entre que el framework **asigne** el campo y que el código lo **use** | Si es cierto que no se usa: ¿sacarlo mejoraría la mantenibilidad (dependencias que parecen existir y no existen)? |
| `S6353` (3) | Expresión regular con `[0-9]` que se puede escribir `\d` | ¿Es esa construcción? | ¿El cambio hace la expresión más clara o es indiferente para quien la lee? |
| `S4502` (1) | Protección CSRF de Spring Security desactivada | ¿Se desactiva efectivamente CSRF en esa configuración? | La pregunta es de **seguridad**: ¿esta API la consumen navegadores con sesiones o *cookies* (donde CSRF es un riesgo), o se autentica de otra forma (por ejemplo, *tokens* en encabezados)? Mirá cómo se autentica el frontend |
| `S5993` (1) | Constructor `public` en una clase abstracta (debería ser `protected`) | ¿La clase es abstracta y el constructor es `public`? | ¿Cambiar la visibilidad comunica mejor el diseño, o es indiferente? |
| `S112` (1) | Se lanza una excepción genérica (`RuntimeException`, `Exception`, etc.) | ¿Es una excepción genérica? | ¿Quien llama necesita distinguir ese error de otros (por ejemplo, para responder un código HTTP distinto)? |
| `S2143` (1) | Uso de la API vieja de fechas (`Date`, `Calendar`) en lugar de `java.time` | ¿Se usa `java.util.Date`, `Calendar` u otra clase de la API vieja? | ¿Esa parte del código convive con `java.time` y mezclar las dos API complica, o está aislada? |
| `S1948` (1) | Campo no `transient` de un tipo no serializable dentro de una clase `Serializable` | ¿La clase es `Serializable` (directa o heredada) y el tipo del campo no lo es? | ¿Esa clase se serializa de verdad con la serialización de Java (sesiones, caché), o el `Serializable` está por otro motivo? |

## 3. Qué no hacer

- No mirar la severidad ni el esfuerzo en SonarQube, ni abrir los issues en la interfaz.
- No consultar al otro clasificador sobre issues puntuales hasta que los dos entregaron. Brenda sí puede preguntarle a Eric **cómo funciona** el código.
- No pedirle a Claude, ni a otra herramienta, que decida la categoría.
