import pyodbc

def get_connection():
    """
    Esta función establece y retorna una conexión a una base de datos SQL Server usando pyodbc.

    Desglose detallado:

    1. Importación de pyodbc:
       - pyodbc es un módulo que permite conectar a bases de datos ODBC, en este caso SQL Server.

    2. Definición de la función get_connection:
       - No recibe parámetros.
       - Su propósito es crear y devolver un objeto conexión que permita ejecutar consultas.

    3. pyodbc.connect(...):
       - Aquí se establece la cadena de conexión con los parámetros necesarios:
         * DRIVER: Indica el controlador ODBC a usar, en este caso 'ODBC Driver 17 for SQL Server'.
         * SERVER: La dirección IP o nombre del servidor y el puerto SQL Server (172.18.72.111,1433).
         * DATABASE: El nombre de la base de datos a conectar, aquí 'NEXUM'.
         * UID: El usuario de la base de datos, 'NEXUM'.
         * PWD: La contraseña asociada, 'NuevaContraseña123'.

       - autocommit=True:
         * Esto habilita que las operaciones SQL se confirmen automáticamente sin requerir commit manual,
           lo que puede ser útil para evitar bloqueos o para operaciones simples.

    4. Retorno:
       - La función retorna el objeto conexión creado, para que pueda usarse para crear cursores y ejecutar consultas.

    Consideraciones de seguridad:
    - Aunque la función funciona, tener usuario y contraseña hardcodeados es riesgoso en producción.
    - Se recomienda usar variables de entorno o archivos de configuración seguros para manejar credenciales.

    Ejemplo de uso:
    ```
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tabla")
    rows = cursor.fetchall()
    conn.close()
    ```

    Esto permite conectar y consultar datos en la base NEXUM de manera segura y eficiente.
    """
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=NEXUM;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;",
        autocommit=True  
    )
    return conn

