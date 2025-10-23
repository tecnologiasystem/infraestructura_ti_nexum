from sqlalchemy import create_engine

"""
Configuración de conexión a la base de datos utilizando SQLAlchemy y el driver ODBC para SQL Server.
"""

"""
Dirección IP del servidor y el puerto de SQL Server.
"""
DB_SERVER = '172.18.72.111,1433'

"""
Nombre de la base de datos a la que se conectará.
"""
DB_NAME = 'NEXUM'

"""
Usuario autorizado con permisos sobre la base de datos.
"""
DB_USER = 'NEXUM'

"""
Contraseña del usuario especificado.
"""
DB_PASSWORD = 'NuevaContraseña123'

"""
Se construye la cadena de conexión usando el conector ODBC con autenticación básica.
El formato para SQLAlchemy con ODBC es:
mssql+pyodbc://<usuario>:<contraseña>@<servidor>/<basededatos>?driver=<nombre_driver>
"""
CONN_STR = f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}?driver=ODBC+Driver+17+for+SQL+Server"

"""
Se crea el engine, que es el objeto principal de SQLAlchemy para interactuar con la base de datos.
Permite ejecutar consultas, cargar datos con pandas, y gestionar conexiones de manera eficiente.
"""
engine = create_engine(CONN_STR)


