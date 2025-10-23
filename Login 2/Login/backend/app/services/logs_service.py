import pyodbc
from datetime import datetime, time, timedelta
from database.connection import get_pyodbc_connection

def registrar_login(id_usuario: int, nombre_usuario: str, token: str, ip_cliente: str, id_rol: int = None):
    conn = get_pyodbc_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO [LOGS].[dbo].[logins] (idUsuario, usuario, token, entrada, vencimiento, IP, idRol)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    ahora = datetime.now()
    
    # Fecha y hora de vencimiento: hoy a las 6:00 PM
    vencimiento = datetime.combine(ahora.date(), time(18, 0))

    # Si ya pasaron las 7:00 PM, poner vencimiento mañana a las 6:00 PM
    if ahora >= vencimiento:
        vencimiento = datetime.combine(ahora.date() + timedelta(days=1), time(19, 0))

    cursor.execute(query, (id_usuario, nombre_usuario, token, ahora, vencimiento, ip_cliente, id_rol))
    conn.commit()
    cursor.close()
    conn.close()
