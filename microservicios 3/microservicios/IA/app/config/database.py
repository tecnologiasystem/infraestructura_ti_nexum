import pyodbc

"""
Establece una conexión a la base de datos SQL Server con los parámetros configurados.

Parámetros de conexión utilizados:
- DRIVER: controlador ODBC para SQL Server.
- SERVER: IP del servidor SQL y puerto (1433).
- DATABASE: nombre de la base de datos destino.
- UID: usuario con permisos.
- PWD: contraseña del usuario.
- autocommit=True: activa la ejecución automática sin necesidad de commits manuales.

Returns:
    conn (pyodbc.Connection): Objeto de conexión a la base de datos.
"""
def get_connection():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=NEXUM;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;",
        autocommit=True
    )
    return conn
