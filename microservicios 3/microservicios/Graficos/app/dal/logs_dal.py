from app.config.database import get_connection_logs

def obtener_logs_por_dia():
    """
    Esta función se conecta a la base de datos LOGS y consulta la cantidad de inicios de sesión
    (logins) agrupados por día, junto con una lista de los usuarios que iniciaron sesión ese día.

    Proceso detallado:
    1. Se establece la conexión a la base de datos LOGS usando `get_connection_logs()`.
    2. Se crea un cursor para ejecutar la consulta SQL.
    3. La consulta SQL hace lo siguiente:
        - `CONVERT(DATE, entrada) AS fecha`: convierte la fecha y hora de entrada a solo fecha.
        - `COUNT(*) AS total`: cuenta cuántos registros (logins) hubo en esa fecha.
        - `STRING_AGG(usuario, ', ') AS usuarios`: agrupa todos los usuarios que iniciaron sesión en esa fecha en una sola cadena separada por comas.
        - `GROUP BY CONVERT(DATE, entrada)`: agrupa los datos por fecha de entrada.
        - `ORDER BY fecha`: ordena los resultados cronológicamente.
    4. La consulta se ejecuta y se obtienen todos los resultados con `fetchall()`.
    5. Se cierra la conexión a la base de datos.
    6. Se retorna una lista de tuplas con la estructura: (fecha, total, usuarios)

    Retorno:
        List[Tuple[datetime.date, int, str]] - Lista de tuplas con fecha, número total de accesos, y lista de usuarios por día.
    """

    conn = get_connection_logs()
    cursor = conn.cursor()

    query = """
    SELECT 
        CONVERT(DATE, entrada) AS fecha,
        COUNT(*) AS total,
        STRING_AGG(usuario, ', ') AS usuarios
    FROM [LOGS].[dbo].[logins]
    GROUP BY CONVERT(DATE, entrada)
    ORDER BY fecha
    """

    cursor.execute(query)
    resultados = cursor.fetchall()
    conn.close()
    return resultados
