import requests
"""
Se importa el módulo `requests` que permite hacer peticiones HTTP.
Se usa para enviar solicitudes POST al API de 360NRS para enviar los SMS.
"""

import base64
"""
Se importa `base64` para codificar el usuario y contraseña en formato básico HTTP (Basic Auth).
Este es el método requerido por el servicio 360NRS para autenticación.
"""

# ---------------------- FUNCIÓN 1: Dividir mensaje largo ----------------------

def dividir_mensaje(mensaje, max_length=160):
    """
    Divide un mensaje de texto en partes de longitud máxima `max_length` (por defecto 160 caracteres),
    que es el límite habitual para SMS tradicionales.

    Parámetros:
    - mensaje (str): El contenido completo del mensaje.
    - max_length (int): Tamaño máximo permitido por parte. Default: 160.

    Retorna:
    - Lista de strings, cada uno representa una parte del mensaje original.
    """
    partes = []
    for i in range(0, len(mensaje), max_length):
        partes.append(mensaje[i:i+max_length])
    return partes

# ---------------------- FUNCIÓN 2: Enviar SMS con autenticación ----------------------

def enviar_sms_360nrs(numero, mensaje):
    """
    Función encargada de enviar uno o varios SMS (si el mensaje es largo) usando el servicio 360NRS.

    Parámetros:
    - numero (str): Número telefónico del destinatario, debe incluir prefijo internacional.
    - mensaje (str): El contenido del SMS a enviar.

    Retorna:
    - Lista de resultados por cada parte enviada. Cada resultado contiene:
        - status: código de estado HTTP de la petición.
        - body: respuesta textual del servidor 360NRS.

    Lógica:
    1. Se codifica el usuario y contraseña en Base64 para autenticarse.
    2. Se construyen los headers necesarios.
    3. Se divide el mensaje si excede los 160 caracteres.
    4. Se envía cada parte como una solicitud POST al API de 360NRS.
    5. Se recopilan todos los resultados y se retornan para análisis.
    """

    # Credenciales de autenticación en 360NRS
    username = "Systemgroup"
    password = "UTow81$$"

    # URL del servicio REST de 360NRS para envío de SMS
    url = "https://dashboard.360nrs.com/api/rest/sms"

    # Codificación en Base64 para Basic Authentication
    auth = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Basic {auth}"  # Se envía el header Authorization con formato requerido
    }

    # Se divide el mensaje en partes de máximo 160 caracteres
    partes = dividir_mensaje(mensaje)

    for idx, parte in enumerate(partes, start=1):
        print(f"Enviando parte {idx}: {parte}")  # Log en consola útil para trazabilidad

    resultados = []

    for parte in partes:
        # Construcción del payload a enviar a la API
        payload = {
            "to": numero,       # Número de destino
            "text": parte,      # Parte del mensaje
            "from": "App360"    # Remitente personalizado definido en 360NRS
        }

        # Envío del SMS vía POST
        res = requests.post(url, headers=headers, json=payload)

        # Guardar el resultado para cada parte enviada
        resultados.append({
            "status": res.status_code,  # 200 = OK, otros = errores
            "body": res.text            # Cuerpo de respuesta de la API
        })

    return resultados
