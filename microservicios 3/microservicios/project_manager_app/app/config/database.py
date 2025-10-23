import pyodbc

def get_connection():
    """
    Establece y devuelve una conexión a la base de datos SQL Server usando pyodbc.

    Detalles de la conexión:
    - DRIVER: Driver ODBC para SQL Server versión 17
    - SERVER: IP y puerto del servidor (172.18.72.111, puerto 1433)
    - DATABASE: Nombre de la base de datos (NEXUM)
    - UID: Usuario de conexión (NEXUM)
    - PWD: Contraseña para el usuario

    Retorna:
        conn (pyodbc.Connection): Objeto de conexión activo a la base de datos.

    Uso típico:
        conn = get_connection()
        cursor = conn.cursor()
        ...
        conn.close()
    """
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=NEXUM;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;"
    )
    return conn
