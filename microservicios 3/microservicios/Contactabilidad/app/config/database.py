def get_connection():
    """
    Retorna la cadena de conexión para establecer una conexión con el servidor SQL Server.

    Este string es utilizado por librerías como pyodbc o SQLAlchemy para conectarse a la base de datos.

    Contiene:
    - DRIVER: el driver ODBC para SQL Server (versión 17 en este caso)
    - SERVER: dirección IP y puerto del servidor de base de datos
    - DATABASE: nombre de la base de datos a la que se desea conectar
    - UID: usuario de conexión
    - PWD: contraseña asociada al usuario

    NOTA: Esta función no abre ni valida la conexión, solo devuelve el string.
    Es útil si se desea centralizar la configuración en un solo lugar y reutilizarla.
    """
    return (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=NEXUM;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;"
    )
