import pyodbc

def get_connection():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=LOGS;"
        "UID=NEXUM;"
        "PWD=Bogotacolombia2025;"
    )
    return conn
