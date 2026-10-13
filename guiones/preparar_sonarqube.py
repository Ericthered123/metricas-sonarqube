"""Deja lista una instancia nueva de SonarQube para los guiones.

Pasos, todos idempotentes:
  1. Espera a que el servidor informe estado UP.
  2. Si el usuario admin todavía tiene la contraseña de fábrica (admin/admin),
     la cambia por una aleatoria y la guarda en ``laboratorio/.env``.
  3. Si no hay token en ``laboratorio/.env``, genera uno de usuario para admin
     y lo guarda ahí. Los demás guiones lo usan para la API y el escáner.
  4. Pone "Sonar way comprehensive" como perfil predeterminado de Java (en una
     instalación nueva de la 26.10 es "Sonar way core"; ver comun.PERFIL_PRINCIPAL).
     analizar.py igual asigna el perfil a cada proyecto: esto evita sorpresas
     si alguien analiza a mano.
  5. Muestra la versión instalada y los dos parámetros que el eje 1 necesita
     verificar (costo de desarrollo por línea y grilla de la calificación).

``laboratorio/.env`` no se versiona: las credenciales son de tu instancia local.

Uso:
    python guiones/preparar_sonarqube.py
"""

from __future__ import annotations

import secrets
import string
from datetime import datetime

from comun import (
    ARCHIVO_ENV,
    PERFIL_PRINCIPAL,
    ClienteSonar,
    ErrorSonar,
    config,
    escribir_valor_env,
    info,
    salir,
)

CLAVE_DE_FABRICA = "admin"


def generar_clave(largo: int = 24) -> str:
    """Contraseña aleatoria que cumple la política de SonarQube (mayúscula, minúscula, dígito y símbolo)."""
    simbolos = "!#%+-_="
    alfabeto = string.ascii_letters + string.digits + simbolos
    while True:
        clave = "".join(secrets.choice(alfabeto) for _ in range(largo))
        if (
            any(c.islower() for c in clave)
            and any(c.isupper() for c in clave)
            and any(c.isdigit() for c in clave)
            and any(c in simbolos for c in clave)
        ):
            return clave


def asegurar_clave_admin(url: str) -> str:
    """Devuelve una contraseña de admin válida, cambiando la de fábrica si sigue activa."""
    cfg = config()
    guardada = cfg.get("SONAR_ADMIN_CLAVE", "")

    # /api/authentication/validate responde 200 con {"valid": false} si las
    # credenciales no sirven, así que basta con mirar ese campo.
    if guardada:
        try:
            if ClienteSonar(url, usuario="admin", clave=guardada).get("/api/authentication/validate").get("valid"):
                return guardada
        except ErrorSonar:
            pass

    de_fabrica = ClienteSonar(url, usuario="admin", clave=CLAVE_DE_FABRICA)
    if not de_fabrica.get("/api/authentication/validate").get("valid"):
        salir(
            "No se pudo autenticar como admin ni con la contraseña guardada ni con la de fábrica. "
            "Si la cambiaste a mano, escribila en SONAR_ADMIN_CLAVE de laboratorio/.env."
        )

    nueva = generar_clave()
    de_fabrica.post(
        "/api/users/change_password",
        login="admin",
        previousPassword=CLAVE_DE_FABRICA,
        password=nueva,
    )
    escribir_valor_env("SONAR_ADMIN_CLAVE", nueva)
    info("Se reemplazó la contraseña de fábrica de admin; quedó guardada en laboratorio/.env")
    return nueva


def asegurar_token(url: str, clave_admin: str) -> str:
    """Devuelve un token válido, generándolo si no hay uno guardado."""
    guardado = config().get("SONAR_TOKEN", "")
    if guardado:
        try:
            if ClienteSonar(url, token=guardado).get("/api/authentication/validate").get("valid"):
                return guardado
        except ErrorSonar:
            pass

    admin = ClienteSonar(url, usuario="admin", clave=clave_admin)
    nombre = f"guiones-tp-{datetime.now():%Y%m%d-%H%M%S}"
    respuesta = admin.post("/api/user_tokens/generate", name=nombre, type="USER_TOKEN")
    token = respuesta["token"]
    escribir_valor_env("SONAR_TOKEN", token)
    info(f"Token '{nombre}' generado y guardado en laboratorio/.env")
    return token


def main() -> None:
    if not ARCHIVO_ENV.exists():
        salir("Falta laboratorio/.env. Copiá laboratorio/.env.example a laboratorio/.env y volvé a correr.")

    url = config()["SONAR_URL"]
    info(f"Esperando a SonarQube en {url} (la primera vez tarda uno o dos minutos)...")
    version = ClienteSonar(url).esperar_disponible()
    info(f"SonarQube {version} está UP")

    clave = asegurar_clave_admin(url)
    token = asegurar_token(url, clave)

    cliente = ClienteSonar(url, token=token)
    cliente.post("/api/qualityprofiles/set_default", language="java", qualityProfile=PERFIL_PRINCIPAL)
    info(f"Perfil predeterminado de Java: '{PERFIL_PRINCIPAL}'")
    ajustes = cliente.get(
        "/api/settings/values",
        keys="sonar.technicalDebt.developmentCost,sonar.technicalDebt.ratingGrid",
    )
    # Los valores por defecto no se devuelven como "settings" sino como definiciones;
    # si no aparecen, se informa que rige el valor de fábrica.
    valores = {a["key"]: a.get("value") for a in ajustes.get("settings", [])}
    info(f"Costo de desarrollo por línea (min): {valores.get('sonar.technicalDebt.developmentCost', 'valor por defecto')}")
    info(f"Grilla de la calificación de mantenibilidad: {valores.get('sonar.technicalDebt.ratingGrid', 'valor por defecto')}")
    info("Listo. Ya podés correr compilar_corpus.py y analizar.py.")


if __name__ == "__main__":
    main()
