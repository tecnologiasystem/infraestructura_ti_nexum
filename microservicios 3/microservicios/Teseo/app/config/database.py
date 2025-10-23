import pyodbc

def get_connection():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=NEXUM;"
        "UID=NEXUM;"
        "PWD=NuevaContraseña123;",
        autocommit=True  # Activa el autocommit para que cada operación se confirme automáticamente
    )
    return conn

def get_connectionAcuerdo():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.79.20,1433;"
        "DATABASE=turnosvirtuales_dev;"
        "UID=j.gerena;"
        "PWD=HQNjmVVFLn8YwXyZ!5wtDF1;",
        autocommit=True  # Activa el autocommit para que cada operación se confirme automáticamente
    )
    return conn