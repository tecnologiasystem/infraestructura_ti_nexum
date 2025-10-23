import pyodbc

def get_connection():
    """
    Obtiene una conexión a la base de datos NEXUM en el servidor 172.18.72.111.
    Utiliza el driver ODBC 17 para SQL Server con credenciales definidas.
    """
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=NEXUM;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;"
    )
    return conn

def get_connection2():
    """
    Obtiene una conexión a la base de datos NEXUM_LOGIN en el servidor 172.18.73.76.
    Utiliza el driver ODBC 17 para SQL Server con credenciales definidas.
    """
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.73.76,1433;"
        "DATABASE=NEXUM_LOGIN;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;"
    )
    return conn

def get_connection_logs():
    """
    Obtiene una conexión a la base de datos LOGS en el servidor 172.18.72.111.
    Utiliza el driver ODBC 17 para SQL Server con credenciales definidas.
    """
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=LOGS;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;"
    )
    return conn
