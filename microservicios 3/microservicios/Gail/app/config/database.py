import pyodbc

def get_connection():
    """
    Establece una conexión con la base de datos SQL Server utilizando ODBC.

    Esta función se encarga de construir la cadena de conexión con los parámetros:
    - DRIVER: controlador ODBC para SQL Server.
    - SERVER: IP del servidor con el puerto (en este caso: 172.18.72.111:1433).
    - DATABASE: nombre de la base de datos a conectar (NEXUM).
    - UID / PWD: credenciales de acceso (usuario y contraseña).

    Devuelve:
        conn (pyodbc.Connection): objeto de conexión activo a la base de datos.

    Si ocurre algún error durante la conexión, este se propaga como excepción.
    """
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=NEXUM;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;"
    )
    return conn
