"""
Esta función crea y retorna una conexión a la base de datos SQL Server utilizando pyodbc.

- Usa el controlador ODBC Driver 17 para SQL Server.
- Se conecta al servidor con IP 172.18.72.111 y puerto 1433.
- Usa la base de datos 'NEXUM' con usuario 'NEXUM' y la contraseña proporcionada.
- La conexión se establece con autocommit activado, para que los cambios se confirmen automáticamente.

Retorna: objeto de conexión pyodbc.Connection para ejecutar consultas en la base.
"""

import pyodbc

def get_connection():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=NEXUM;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;",
        autocommit=True  # Activa el autocommit para que cada operación se confirme automáticamente
    )
    return conn
