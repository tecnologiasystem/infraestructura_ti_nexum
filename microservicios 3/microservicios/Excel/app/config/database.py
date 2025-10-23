import pyodbc

def get_connection():
    """
    Establece y retorna una conexión a la base de datos SQL Server.

    Detalles de configuración:
    - DRIVER: Especifica el controlador ODBC utilizado para conectarse a SQL Server. En este caso, el driver es 'ODBC Driver 17 for SQL Server'.
    - SERVER: IP del servidor al que se quiere conectar. Se incluye el puerto (1433) después de la coma.
    - DATABASE: Nombre de la base de datos a la que se conectará, en este caso 'NEXUM'.
    - UID: Usuario con permisos para conectarse a la base de datos.
    - PWD: Contraseña correspondiente al usuario.

    Retorna:
    - Una conexión activa (`conn`) que puede usarse para ejecutar queries u operaciones sobre la base de datos.

    Nota:
    - Si la conexión falla, el error se lanzará directamente, por lo que se recomienda manejar esta función dentro de bloques try/except donde se use.
    """
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=NEXUM;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;"
    )
    return conn
