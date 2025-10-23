from app.config.database import get_connection_logs, get_connection

"""
Importa funciones de conexión:
- get_connection_logs: conexión a la base de datos de logs.
- get_connection: conexión a la base de datos principal.
"""



"""
Función: obtener_logs

Obtiene todos los registros de inicio de sesión en el rango indicado.

Parámetros opcionales:
    desde (str): Fecha de inicio del filtro.
    hasta (str): Fecha final del filtro.

Ejecuta:
    EXEC sp_LogsInicioSesion @desde = ?, @hasta = ?

Retorna:
    Lista de logs con columnas como usuario, fecha, etc.
"""
def obtener_logs(desde=None, hasta=None):
    conn = get_connection_logs()
    cursor = conn.cursor()
    query = "EXEC sp_LogsInicioSesion @desde = ?, @hasta = ?"
    cursor.execute(query, desde, hasta)
    rows = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    resultados = [dict(zip(columns, row)) for row in rows]
    cursor.close()
    conn.close()
    return resultados



"""
Función: obtener_campanas_por_usuario

Consulta las campañas asociadas a cada usuario.

Realiza un JOIN entre:
    - UsuariosApp
    - UsuariosCampanas
    - Campana

Retorna:
    Diccionario con el username como llave y una lista de descripciones de campañas como valor.
"""
def obtener_campanas_por_usuario():
    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT ua.username, c.descripcionCampana
        FROM UsuariosApp ua
        JOIN UsuariosCampanas uc ON ua.idUsuarioApp = uc.idUsuarioApp
        JOIN Campana c ON uc.idCampana = c.idCampana
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    campanas = {}
    for username, descripcion in rows:
        campanas.setdefault(username, []).append(descripcion)
    return campanas



"""
Función: obtener_logs_con_campanas

Filtra logs de inicio de sesión con campañas asociadas a cada usuario.

Parámetros:
    usuario (str): Nombre de usuario a filtrar (si está vacío, se retorna todo).
    desde (str): Fecha inicial del filtro.
    hasta (str): Fecha final del filtro.

Proceso:
    - Consulta logs por rango de fecha.
    - Consulta campañas por usuario.
    - Asocia campañas al log correspondiente si el usuario coincide.

Retorna:
    Lista de logs con los campos originales más una nueva columna 'campanas'.
"""
def obtener_logs_con_campanas(usuario: str, desde: str, hasta: str):
    logs = obtener_logs(desde, hasta)
    campanas_por_usuario = obtener_campanas_por_usuario()

    resultados = []
    for log in logs:
        if usuario and log["usuario"] != usuario:
            continue
        user = log["usuario"]
        log["campanas"] = ", ".join(campanas_por_usuario.get(user, []))
        resultados.append(log)

    return resultados
