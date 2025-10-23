"""
Módulo de conexión a bases de datos usando pyodbc.

Define funciones para conectarse a diferentes bases:
- NEXUM (base principal)
- NEXUM_LOGIN (base de autenticación)
- LOGS (base exclusiva de auditoría)

Cada función devuelve una conexión activa a la base correspondiente.
"""

import pyodbc


"""
Retorna una conexión activa a la base de datos principal NEXUM.

Esta base contiene la lógica del sistema (áreas, campañas, usuarios, etc.).
"""
def get_connection():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=NEXUM;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;"
    )
    return conn


"""
Retorna una conexión a la base de datos NEXUM_LOGIN.

Esta base se usa para autenticación u operaciones ligadas al login
en ambientes separados del core principal.
"""
def get_connection2():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.73.76,1433;"
        "DATABASE=NEXUM_LOGIN;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;"
    )
    return conn


"""
Retorna una conexión a la base de datos LOGS.

Esta base contiene exclusivamente los registros de auditoría
e historial de acciones dentro del sistema.
"""
def get_connection_logs():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=LOGS;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;"
    )
    return conn
