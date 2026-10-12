# Corpus congelado

`corpus.csv` es la única fuente de verdad sobre qué código se analiza. Todos los guiones lo leen; nadie analiza un commit que no esté acá.

| Columna | Significado |
| --- | --- |
| `proyecto` | Nombre corto, se usa en carpetas y claves de SonarQube |
| `version` | Versión publicada del proyecto |
| `orden` | 1 para el release viejo y 2 para el nuevo. Los ejes 1 y 2 usan el 2; el eje 3 usa el par |
| `repositorio` | `dueño/nombre` en GitHub |
| `tag` | Etiqueta de git del release |
| `commit` | Hash del commit al que apunta el tag. Es lo que se analiza, no el tag |

## Por qué el commit y no el tag

Un tag se puede mover o borrar; un hash de commit no. En los tags anotados (todos los de este corpus salvo JFreeChart) el objeto tag tiene su propio hash, distinto del commit al que apunta: acá se registra el del commit.

Los hashes se obtuvieron el 2026-10-12 con:

```
git ls-remote --tags https://github.com/<repositorio>
```

tomando la línea terminada en `^{}` cuando el tag es anotado. `guiones/clonar_corpus.py` verifica que cada checkout quede exactamente en ese commit.

## Aprobación

El grupo aprobó estos cuatro proyectos y sus pares de releases el 2026-10-12 (SCRUM-14). Los criterios de selección están en la decisión D3 de Confluence. Suplentes, si alguno no compila: Apache Commons Lang y Gson.

## Proyecto propio

El proyecto propio de la sección 5.4 todavía es provisorio (SCRUM-18) y no está en este archivo. Se agrega cuando el grupo lo confirme, con el commit exacto que se analiza.
