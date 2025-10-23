import os
import yaml
import pyodbc

"""
Importación de librerías necesarias:
- os: permite trabajar con funciones del sistema operativo, como verificar si existen carpetas o crear nuevas.
- yaml: se utiliza para leer archivos de configuración que estén escritos en formato YAML (.yaml o .yml).
- pyodbc: permite establecer una conexión a bases de datos SQL Server utilizando el protocolo ODBC.
"""

def conectar_sql(config):
    """
    Establece una conexión con SQL Server usando los datos proporcionados en el diccionario `config`.

    Parámetros:
    - config (dict): debe contener las siguientes claves:
        - server: dirección IP o nombre del servidor + puerto.
        - database: nombre de la base de datos a la que se conectará.
        - username: usuario de SQL Server con permisos válidos.
        - password: contraseña del usuario.

    Proceso:
    - Se construye un string de conexión utilizando el driver ODBC para SQL Server.
    - El string usa los valores del diccionario `config` para personalizar la conexión.
    - Finalmente, se retorna el objeto `pyodbc.Connection` activo, que se puede usar para ejecutar queries.

    Retorna:
    - Objeto de conexión `pyodbc.Connection`.

    Ejemplo de uso:
    conn = conectar_sql(CONFIG_NEXUM)
    """
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={config['server']};DATABASE={config['database']};"
        f"UID={config['username']};PWD={config['password']}"
    )
    return pyodbc.connect(conn_str)

"""
Bloque para verificación de existencia del directorio 'logs'.

Propósito:
- Antes de que el sistema intente escribir archivos de logs, verifica si la carpeta 'logs' ya existe.
- Si no existe, la crea automáticamente usando `os.makedirs`.

Esto evita errores como FileNotFoundError cuando se intenta escribir logs en un directorio que aún no existe.
"""
if not os.path.exists("logs"):
    os.makedirs("logs")

"""
Carga de archivo de configuración general.

Ruta:
- Se espera que el archivo esté en 'app/config/config.yaml'.

Proceso:
- Abre el archivo en modo lectura ('r').
- Usa la función `yaml.safe_load()` para convertir el contenido YAML a un diccionario Python.
- El resultado se guarda en la variable `config`, que luego puede usarse para extraer rutas, flags o parámetros.

Este archivo puede contener configuraciones globales del sistema, rutas de entrada/salida, tokens, o claves que no cambian frecuentemente.
"""
with open("app/config/config.yaml", "r") as f:
    config = yaml.safe_load(f)

"""
Definición de constantes de conexión a distintas bases de datos.

Cada constante es un diccionario con los siguientes campos:
- server: IP y puerto del servidor SQL.
- database: nombre de la base de datos específica.
- username: usuario que tiene permisos en esa base.
- password: contraseña de ese usuario.

Estas configuraciones son útiles para tener acceso rápido y separado a cada entorno sin tener que repetir código.

CONFIG_NEXUM:
    Base de datos principal del sistema donde está la lógica del negocio.

CONFIG_OLAP:
    Base de datos de análisis y reportes, comúnmente usada por herramientas BI.

CONFIG_INTEGRACION:
    Base intermedia utilizada para staging, sincronización de fuentes externas o integración con otros sistemas.
"""

CONFIG_NEXUM = {
    "server": "172.18.72.111,1433",
    "database": "NEXUM",
    "username": "NEXUM",
    "password": "NuevaContraseña123"
}

CONFIG_OLAP = {
    "server": "172.18.73.22,1433",
    "database": "OLAP",
    "username": "reporte",
    "password": "Nuevacontraseña123+"
}

CONFIG_INTEGRACION = {
    "server": "172.18.73.76,1433",
    "database": "Integracion",
    "username": "NEXUM",
    "password": "NuevaContraseña123"
}
