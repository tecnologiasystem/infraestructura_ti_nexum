from app.config.database import get_connection

def consultar_parametros(modulo=None, nombre=None):
    conn = get_connection()
    cursor = conn.cursor()

    result = []

    if modulo:
        cursor.execute("EXEC sp_ConsultarParametrosGenerales @modulo = ?", modulo)
        rows = cursor.fetchall()
        for row in rows:
            result.append({
                "nombre": row.nombre,
                "valor": row.valor
            })
    elif nombre:
        cursor.execute("EXEC sp_ConsultarParametrosGenerales @nombre = ?", nombre)
        row = cursor.fetchone()
        if row:
            result.append({
                "valor": row.valor
            })
    else:
        result.append({"error": "Debes enviar 'modulo' o 'nombre'"})

    conn.close()
    return result

def obtener_encabezados_completados():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT idEncabezado, automatizacion, idUsuario, totalRegistros, fechaCargue
        FROM NEXUM.dbo.RuntEncabezado
        WHERE estado = 'Completado'
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "idUsuario": row.idUsuario,
            "totalRegistros": row.totalRegistros,
            "fechaCargue": row.fechaCargue
        })

    return result

def obtener_valor_token(modulo: str, nombre: str) -> float:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        EXEC sp_ConsultarParametrosGenerales @modulo = ?, @nombre = ?
    """, modulo, nombre)

    row = cursor.fetchone()
    conn.close()

    if row:
        valor_str = str(row.valor).replace(",", ".")
        return float(valor_str)

    return 0.0
