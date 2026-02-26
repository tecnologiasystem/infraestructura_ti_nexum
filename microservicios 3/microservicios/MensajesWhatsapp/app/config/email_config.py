"""
Este módulo carga variables de entorno desde un archivo `.env` para configurar el envío de correos electrónicos.

- Usa la librería `python-dotenv` para cargar automáticamente las variables del archivo `.env` al entorno de ejecución.
- Extrae las variables de configuración:
  - REMITENTE: correo electrónico del remitente
  - PASSWORD: contraseña del remitente
  - SERVER: servidor SMTP (por defecto smtp.office365.com si no está definido)
  - PORT: puerto del servidor SMTP (por defecto 587 si no está definido)

Estas variables son usadas luego para enviar correos electrónicos autenticados.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # Carga variables de entorno desde el archivo .env en el directorio actual

REMITENTE = os.getenv("REMITENTE")  # Correo electrónico remitente
PASSWORD = os.getenv("PASSWORD")    # Contraseña del correo remitente
SERVER = os.getenv("SERVER", "smtp.office365.com")  # Servidor SMTP por defecto si no se especifica
PORT = int(os.getenv("PORT", 587))  # Puerto SMTP por defecto si no se especifica, convertido a entero
