# backend/config.py
import os
from dotenv import load_dotenv
import pyodbc
from datetime import timedelta

load_dotenv()

# Cadena de conexión ODBC como antes
DB_DSN   = os.getenv("DB_DSN")
DB_USER  = os.getenv("DB_USER")
DB_PWD   = os.getenv("DB_PWD")
DB_NAME  = os.getenv("DB_NAME")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "cualquier_cadena_secreta")  # pon algo seguro en tu .env
JWT_ALGORITHM  = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

def get_connection():
    conn_str = f"{DB_DSN};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PWD}"
    return pyodbc.connect(conn_str)
