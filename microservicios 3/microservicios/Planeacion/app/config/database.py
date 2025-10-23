import pyodbc

def get_connection():
    """
    Establece y retorna una conexión a la base de datos SQL Server usando pyodbc.

    Parámetros de conexión:
    - DRIVER: Driver ODBC para SQL Server 2017 (ODBC Driver 17 for SQL Server).
    - SERVER: Dirección IP del servidor y puerto (172.18.72.111,1433).
    - DATABASE: Nombre de la base de datos a conectar (NEXUM).
    - UID: Usuario para la conexión (NEXUM).
    - PWD: Contraseña para la conexión (NuevaContraseña123).

    :return: objeto de conexión pyodbc
    """
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=NEXUM;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;"
    )
    return conn
