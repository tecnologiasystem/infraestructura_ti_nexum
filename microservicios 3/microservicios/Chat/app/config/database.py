import pyodbc

def get_connection():
    """
    Establece y retorna una conexión activa a la base de datos SQL Server.

    Uso:
    - Esta función centraliza la configuración de conexión para evitar repeticiones de código en múltiples módulos.
    - Es usada por otras funciones o capas del proyecto que necesitan interactuar con la base de datos.

    Parámetros:
    - No recibe parámetros de entrada.

    Retorna:
    - Objeto de conexión `pyodbc.Connection` activo hacia el servidor y base de datos configurados.

    Configuración de conexión:
    - DRIVER: Se especifica el driver ODBC para SQL Server compatible con versiones modernas.
    - SERVER: Dirección IP y puerto del servidor de base de datos.
    - DATABASE: Nombre de la base de datos a la que se conecta (NEXUM).
    - UID / PWD: Usuario y contraseña de autenticación SQL Server.

    Posibles errores:
    - Si la conexión falla (credenciales incorrectas, IP inaccesible, servidor caído), se lanzará una excepción `pyodbc.InterfaceError` o `pyodbc.OperationalError`.
    - Se recomienda envolver esta función en bloques try/except al usarla para manejo de errores.

    Seguridad:
    ⚠️ Este código contiene credenciales en texto plano. En producción se debe:
        - Mover la cadena de conexión a variables de entorno o un archivo `.env`.
        - Nunca versionar esta información sensible en repositorios públicos.
    """
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=NEXUM;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;"
    )
    return conn
