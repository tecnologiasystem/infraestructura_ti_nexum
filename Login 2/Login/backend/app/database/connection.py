import sqlalchemy
from sqlalchemy import create_engine
import pyodbc
from config import DATABASE_URL

# Convertir la cadena ODBC a formato SQLAlchemy
connection_string = f"mssql+pyodbc:///?odbc_connect={DATABASE_URL}"


engine = create_engine(connection_string)


def get_connection():
    conn = engine.connect()
    return conn

def get_pyodbc_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=172.18.72.111,1433;"
        "DATABASE=LOGS;"
        "Trusted_Connection=yes;"
    )
