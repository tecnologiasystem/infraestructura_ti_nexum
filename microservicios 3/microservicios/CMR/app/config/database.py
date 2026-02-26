import pyodbc

def get_connection():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.73.22,1433;"
        "DATABASE=Natalia-Whatsapp;"
        "UID=whatsapp;"
        "PWD=Nuevacontraseña12345;",
        autocommit=True 
    )
    return conn
