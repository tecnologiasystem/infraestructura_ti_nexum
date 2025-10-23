import pyodbc

def get_connectionGraficos():
    """
    Establece una conexión a la base de datos 'NEXUM' usando credenciales del usuario 'Analitica'.

    Retorna:
        pyodbc.Connection: Objeto de conexión activo hacia la base de datos.
    """
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=NEXUM;"
        "UID=Analitica;"
        "PWD=Bogotacolombia202020*;"
    )
    return conn


def get_connection_logs():
    """
    Establece una conexión a la base de datos 'LOGS' usando credenciales del usuario 'NEXUM'.

    Retorna:
        pyodbc.Connection: Objeto de conexión activo hacia la base de datos LOGS.
    """
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=LOGS;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;"
    )
    return conn
