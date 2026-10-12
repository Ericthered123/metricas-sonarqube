"""Utilidades compartidas por todos los guiones del laboratorio.

Reúne en un solo lugar lo que cada guion necesita:

* las rutas del repositorio (raíz, corpus, datos, área de trabajo);
* la lectura de la configuración local (``laboratorio/.env``);
* la lectura del corpus congelado (``corpus/corpus.csv``);
* un cliente mínimo de la API web de SonarQube, con paginado;
* la ejecución de comandos de Maven dentro del contenedor de herramientas.

Solo usa la biblioteca estándar de Python (3.10 o superior), para que
cualquier integrante pueda correr los guiones sin instalar dependencias.
"""

from __future__ import annotations

import base64
import csv
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

# ---------------------------------------------------------------------------
# Rutas del repositorio
# ---------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parent.parent
"""Carpeta raíz del repositorio, calculada desde la ubicación de este archivo."""

DIR_LABORATORIO = RAIZ / "laboratorio"
ARCHIVO_COMPOSE = DIR_LABORATORIO / "docker-compose.yml"
ARCHIVO_ENV = DIR_LABORATORIO / ".env"
ARCHIVO_CORPUS = RAIZ / "corpus" / "corpus.csv"
DIR_DATOS = RAIZ / "datos"

DIR_TRABAJO = RAIZ / "trabajo"
"""Checkouts del corpus y logs de compilación. No se versiona (ver .gitignore)."""

DIR_LOGS = DIR_TRABAJO / "logs"

# Dentro del contenedor de herramientas, ``trabajo/`` se monta en esta ruta.
DIR_TRABAJO_CONTENEDOR = "/trabajo"

# Desde el contenedor de herramientas, SonarQube se alcanza por el nombre del
# servicio en la red de Docker Compose; desde la máquina anfitriona, por localhost.
URL_SONAR_DESDE_CONTENEDOR = "http://sonarqube:9000"

# ---------------------------------------------------------------------------
# Configuración local
# ---------------------------------------------------------------------------


def leer_env(ruta: Path = ARCHIVO_ENV) -> dict[str, str]:
    """Lee un archivo ``.env`` simple (líneas ``CLAVE=valor``).

    Ignora líneas vacías y comentarios. No interpreta comillas ni variables:
    alcanza para la configuración del laboratorio y evita una dependencia.
    """
    valores: dict[str, str] = {}
    if not ruta.exists():
        return valores
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        valores[clave.strip()] = valor.strip()
    return valores


def escribir_valor_env(clave: str, valor: str, ruta: Path = ARCHIVO_ENV) -> None:
    """Agrega o reemplaza una línea ``CLAVE=valor`` en el ``.env`` local."""
    lineas = ruta.read_text(encoding="utf-8").splitlines() if ruta.exists() else []
    nuevas: list[str] = []
    reemplazada = False
    for linea in lineas:
        if linea.split("=", 1)[0].strip() == clave:
            nuevas.append(f"{clave}={valor}")
            reemplazada = True
        else:
            nuevas.append(linea)
    if not reemplazada:
        nuevas.append(f"{clave}={valor}")
    ruta.write_text("\n".join(nuevas) + "\n", encoding="utf-8")


def config() -> dict[str, str]:
    """Configuración efectiva: el ``.env`` local, con valores por defecto."""
    env = leer_env()
    env.setdefault("SONAR_PUERTO", "9000")
    env.setdefault("SONAR_URL", f"http://localhost:{env['SONAR_PUERTO']}")
    return env


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VersionCorpus:
    """Una versión congelada de un proyecto del corpus (una fila de corpus.csv)."""

    proyecto: str
    version: str
    orden: int  # 1 = release viejo, 2 = release nuevo (el par se usa en el eje 3)
    repositorio: str
    tag: str
    commit: str

    @property
    def directorio(self) -> Path:
        """Carpeta del checkout en la máquina anfitriona."""
        return DIR_TRABAJO / self.proyecto / self.version

    @property
    def directorio_contenedor(self) -> str:
        """La misma carpeta, vista desde el contenedor de herramientas."""
        return f"{DIR_TRABAJO_CONTENEDOR}/{self.proyecto}/{self.version}"

    @property
    def url_git(self) -> str:
        return f"https://github.com/{self.repositorio}.git"


def leer_corpus(ruta: Path = ARCHIVO_CORPUS) -> list[VersionCorpus]:
    """Devuelve las versiones del corpus en el orden del archivo."""
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return [
            VersionCorpus(
                proyecto=fila["proyecto"],
                version=fila["version"],
                orden=int(fila["orden"]),
                repositorio=fila["repositorio"],
                tag=fila["tag"],
                commit=fila["commit"],
            )
            for fila in csv.DictReader(archivo)
        ]


def buscar_version(proyecto: str, version: str) -> VersionCorpus:
    """Busca una versión del corpus o termina con un mensaje claro."""
    for item in leer_corpus():
        if item.proyecto == proyecto and item.version == version:
            return item
    disponibles = ", ".join(f"{v.proyecto} {v.version}" for v in leer_corpus())
    salir(f"No existe '{proyecto} {version}' en el corpus. Disponibles: {disponibles}")
    raise AssertionError  # inalcanzable: salir() termina el proceso


def filtrar_corpus(proyecto: str | None, version: str | None) -> list[VersionCorpus]:
    """Filtra el corpus por proyecto y versión (ambos opcionales)."""
    return [
        v
        for v in leer_corpus()
        if (proyecto is None or v.proyecto == proyecto)
        and (version is None or v.version == version)
    ]


# ---------------------------------------------------------------------------
# Mensajes y salida
# ---------------------------------------------------------------------------


def info(mensaje: str) -> None:
    print(f"[info] {mensaje}", flush=True)


def aviso(mensaje: str) -> None:
    print(f"[aviso] {mensaje}", file=sys.stderr, flush=True)


def salir(mensaje: str, codigo: int = 1) -> None:
    print(f"[error] {mensaje}", file=sys.stderr, flush=True)
    sys.exit(codigo)


def escribir_csv(ruta: Path, filas: list[dict[str, Any]], columnas: list[str]) -> None:
    """Escribe un CSV en UTF-8 con las columnas en el orden dado."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(filas)
    info(f"Escrito {ruta.relative_to(RAIZ)} ({len(filas)} filas)")


def agregar_fila_csv(ruta: Path, fila: dict[str, Any], columnas: list[str]) -> None:
    """Agrega una fila a un CSV de registro, creando el encabezado si hace falta."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not ruta.exists()
    with ruta.open("a", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas, extrasaction="ignore")
        if nuevo:
            escritor.writeheader()
        escritor.writerow(fila)


# ---------------------------------------------------------------------------
# Cliente de la API web de SonarQube
# ---------------------------------------------------------------------------


class ErrorSonar(RuntimeError):
    """Error devuelto por la API de SonarQube, con el código HTTP y el cuerpo."""

    def __init__(self, codigo: int, cuerpo: str, url: str) -> None:
        super().__init__(f"HTTP {codigo} en {url}: {cuerpo[:300]}")
        self.codigo = codigo
        self.cuerpo = cuerpo


class ClienteSonar:
    """Cliente mínimo de la API web de SonarQube.

    Autentica con un token de usuario (cabecera ``Authorization: Bearer``) o,
    solo para la preparación inicial, con usuario y contraseña (Basic).
    """

    # Tope de la API de búsqueda de issues: no devuelve más allá del resultado 10.000.
    LIMITE_ISSUES = 10_000

    def __init__(
        self,
        url: str,
        token: str | None = None,
        usuario: str | None = None,
        clave: str | None = None,
    ) -> None:
        self.url = url.rstrip("/")
        self._cabeceras: dict[str, str] = {"Accept": "application/json"}
        if token:
            self._cabeceras["Authorization"] = f"Bearer {token}"
        elif usuario is not None:
            credencial = base64.b64encode(f"{usuario}:{clave or ''}".encode()).decode()
            self._cabeceras["Authorization"] = f"Basic {credencial}"

    @classmethod
    def desde_config(cls) -> "ClienteSonar":
        """Crea el cliente con la URL y el token del ``.env`` local."""
        cfg = config()
        token = cfg.get("SONAR_TOKEN")
        if not token:
            salir("Falta SONAR_TOKEN en laboratorio/.env. Corré antes preparar_sonarqube.py.")
        return cls(cfg["SONAR_URL"], token=token)

    def _pedir(self, metodo: str, ruta: str, params: dict[str, Any] | None) -> Any:
        params = {k: v for k, v in (params or {}).items() if v is not None}
        codificados = urllib.parse.urlencode(params, doseq=True)
        url = f"{self.url}{ruta}"
        datos = None
        if metodo == "GET" and codificados:
            url = f"{url}?{codificados}"
        elif metodo == "POST":
            datos = codificados.encode()
        pedido = urllib.request.Request(url, data=datos, method=metodo, headers=self._cabeceras)
        if datos is not None:
            pedido.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
            with urllib.request.urlopen(pedido, timeout=60) as respuesta:
                cuerpo = respuesta.read().decode("utf-8")
        except urllib.error.HTTPError as error:
            raise ErrorSonar(error.code, error.read().decode("utf-8", "replace"), url) from None
        return json.loads(cuerpo) if cuerpo.strip() else {}

    def get(self, ruta: str, **params: Any) -> Any:
        return self._pedir("GET", ruta, params)

    def post(self, ruta: str, **params: Any) -> Any:
        return self._pedir("POST", ruta, params)

    def paginar(self, ruta: str, clave_lista: str, tam_pagina: int = 500, **params: Any) -> Iterator[dict]:
        """Recorre todas las páginas de un recurso paginado de la API.

        La API informa el total en ``paging.total`` (o ``total`` en algunos
        recursos viejos). Corta cuando ya se recibió todo o la página vino vacía.
        """
        pagina = 1
        recibidos = 0
        while True:
            respuesta = self.get(ruta, p=pagina, ps=tam_pagina, **params)
            elementos = respuesta.get(clave_lista, [])
            yield from elementos
            recibidos += len(elementos)
            total = respuesta.get("paging", {}).get("total", respuesta.get("total", 0))
            if not elementos or recibidos >= total:
                return
            pagina += 1

    def esperar_disponible(self, espera_maxima_s: int = 600) -> str:
        """Espera hasta que el servidor informe estado UP y devuelve la versión."""
        limite = time.monotonic() + espera_maxima_s
        ultimo_estado = "sin respuesta"
        while time.monotonic() < limite:
            try:
                estado = self.get("/api/system/status")
                ultimo_estado = estado.get("status", "desconocido")
                if ultimo_estado == "UP":
                    return estado.get("version", "desconocida")
            except (urllib.error.URLError, ConnectionError, ErrorSonar, TimeoutError):
                pass
            time.sleep(5)
        salir(f"SonarQube no quedó disponible en {espera_maxima_s} s (último estado: {ultimo_estado}).")
        raise AssertionError  # inalcanzable


# ---------------------------------------------------------------------------
# Docker Compose y Maven
# ---------------------------------------------------------------------------


def comando_compose(*argumentos: str) -> list[str]:
    """Arma un comando ``docker compose`` apuntado al archivo del laboratorio."""
    base = ["docker", "compose", "-f", str(ARCHIVO_COMPOSE)]
    if ARCHIVO_ENV.exists():
        base += ["--env-file", str(ARCHIVO_ENV)]
    return base + list(argumentos)


def correr_en_herramientas(
    comando: list[str],
    directorio: str,
    ruta_log: Path,
    variables: dict[str, str] | None = None,
) -> tuple[int, float]:
    """Ejecuta un comando dentro del contenedor de herramientas (Maven y JDK fijos).

    La salida completa se guarda en ``ruta_log`` y se muestra resumida en consola.
    Devuelve el código de salida y la duración en segundos.
    """
    argumentos = ["run", "--rm", "-T", "-w", directorio]
    for clave, valor in (variables or {}).items():
        # Se pasa solo el nombre: Docker toma el valor del entorno del proceso,
        # así el token no aparece en la línea de comandos.
        argumentos += ["-e", clave]
    argumentos += ["herramientas", *comando]

    entorno = os.environ.copy()
    entorno.update(variables or {})

    ruta_log.parent.mkdir(parents=True, exist_ok=True)
    inicio = time.monotonic()
    # buffering=1: el log se vuelca línea por línea, así se puede seguir en vivo
    # (con el buffer por defecto de 8 KB quedaba atrasado respecto de la consola).
    with ruta_log.open("w", encoding="utf-8", buffering=1) as log:
        proceso = subprocess.Popen(
            comando_compose(*argumentos),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=entorno,
        )
        assert proceso.stdout is not None
        for linea in proceso.stdout:
            log.write(linea)
            # En consola solo se muestran las líneas que marcan el avance del build.
            if linea.startswith(("[INFO] Building ", "[INFO] BUILD", "[ERROR]", "[INFO] ANALYSIS SUCCESSFUL")):
                print("    " + linea.rstrip(), flush=True)
        codigo = proceso.wait()
    return codigo, time.monotonic() - inicio


# Plugins de verificación que algunos proyectos corren en ``verify`` y que no
# tienen relación con el estudio: auditoría de licencias (RAT), compatibilidad
# binaria (japicmp, revapi, animal-sniffer), estilo y análisis estático propios
# del proyecto, firma y SBOM. Si se dejan activos, un incumplimiento de esas
# reglas internas hace fallar el build aunque el código compile y los tests pasen.
OMITIR_PLUGINS_AJENOS = [
    "-Drat.skip=true",
    "-Djapicmp.skip=true",
    "-Drevapi.skip=true",
    "-Danimal.sniffer.skip=true",
    "-Dcheckstyle.skip=true",
    "-Dpmd.skip=true",
    "-Dcpd.skip=true",
    "-Dspotbugs.skip=true",
    "-Dgpg.skip=true",
    "-Dcyclonedx.skip=true",
    "-Dspdx.skip=true",
    "-Dmaven.javadoc.skip=true",
    "-Dmaven.source.skip=true",
]
