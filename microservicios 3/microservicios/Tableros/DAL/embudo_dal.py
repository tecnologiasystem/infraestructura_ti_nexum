import pyodbc
from config.database import get_connection

def get_funnel_data() -> list[dict]:
    """
    Ejecuta una consulta con CTEs (Common Table Expressions) para calcular las 6 etapas
    principales del embudo de llamadas (funnel) y devuelve una lista de diccionarios con
    el nombre de cada etapa y el conteo correspondiente.

    Retorna:
        List[dict]: Lista con diccionarios que contienen:
            - "etapa": nombre de la etapa del embudo
            - "cnt": cantidad de registros para esa etapa
    """
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    WITH
      cte_total AS (
        SELECT COUNT(*) AS cnt
        FROM ReporteLlamada
      ),
      cte_answered AS (
        SELECT COUNT(*) AS cnt
        FROM ReporteLlamada
        WHERE time_sec > 0
      ),
      cte_rpc AS (
        SELECT COUNT(*) AS cnt
        FROM ReporteLlamada
        WHERE time_sec > 0
          AND call_cod_id IN ('AA','AC','CONV')     -- RPC_CODES: contacto efectivo
      ),
      cte_promises AS (
        SELECT COUNT(*) AS cnt
        FROM ReporteLlamada
        WHERE call_cod_id IN ('PM','PP')           -- PROMISE_CODES: promesas de pago
      ),
      cte_commit_pay AS (
        SELECT COUNT(*) AS cnt
        FROM ReporteLlamada
        WHERE call_cod_id IN ('CP','PDROP')        -- COMMIT_CODES: pago inicial
      ),
      cte_full_pay AS (
        SELECT COUNT(*) AS cnt
        FROM ReporteLlamada
        WHERE call_cod_id IN ('FP','FULL')         -- FULL_CODES: pago completo
      )
    SELECT etapa, cnt
    FROM (
      SELECT 'Total Assignments'            AS etapa, cnt FROM cte_total
      UNION ALL
      SELECT 'Answered Calls'              AS etapa, cnt FROM cte_answered
      UNION ALL
      SELECT 'Right Party Contacts'        AS etapa, cnt FROM cte_rpc
      UNION ALL
      SELECT 'Payment Promises'            AS etapa, cnt FROM cte_promises
      UNION ALL
      SELECT 'Commitment + Payment Made'   AS etapa, cnt FROM cte_commit_pay
      UNION ALL
      SELECT 'Commitment + Full Payment'   AS etapa, cnt FROM cte_full_pay
    ) AS funnel
    ORDER BY CASE funnel.etapa
      WHEN 'Total Assignments'           THEN 1
      WHEN 'Answered Calls'              THEN 2
      WHEN 'Right Party Contacts'        THEN 3
      WHEN 'Payment Promises'            THEN 4
      WHEN 'Commitment + Payment Made'   THEN 5
      WHEN 'Commitment + Full Payment'   THEN 6
    END;
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()

    # Transformamos cada fila en un dict con keys 'etapa' y 'cnt'
    return [{"etapa": row[0], "cnt": row[1]} for row in rows]


def get_call_metrics_by_hour() -> list[dict]:
    """
    Consulta los datos de llamadas agrupados por hora y calcula:
    total llamadas, llamadas contestadas, abandonadas, contacto efectivo y promesas de pago.

    Retorna:
        List[dict]: Cada dict contiene métricas por hora con los campos:
            - hora (int)
            - total (int)
            - contestadas (int)
            - abandonadas (int)
            - contacto_efectivo (int)
            - promesas_pago (int)
    """
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    SELECT 
        DATEPART(HOUR, date_call) AS hora,
        COUNT(*) AS total,
        SUM(CASE WHEN time_sec > 0 THEN 1 ELSE 0 END) AS contestadas,
        SUM(CASE WHEN status_name = 'abandoned' THEN 1 ELSE 0 END) AS abandonadas,
        SUM(CASE WHEN call_cod_id IN ('AA','AC','CONV') THEN 1 ELSE 0 END) AS contacto_efectivo,
        SUM(CASE WHEN call_cod_id IN ('PM','PP') THEN 1 ELSE 0 END) AS promesas_pago
    FROM ReporteLlamada WITH(NOLOCK)
    GROUP BY DATEPART(HOUR, date_call)
    ORDER BY hora
    """

    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()

    return [{
        "hora": row[0],
        "total": row[1],
        "contestadas": row[2],
        "abandonadas": row[3],
        "contacto_efectivo": row[4],
        "promesas_pago": row[5],
    } for row in rows]


def get_cumulative_commitments_comparison() -> list[dict]:
    """
    Compara el acumulado porcentual de compromisos de pago entre la fecha más reciente y
    la misma fecha de la semana pasada, agrupado por hora.

    Retorna:
        List[dict]: Cada dict con:
            - hora (int)
            - cumsum_today (float): acumulado porcentual hoy
            - cumsum_2weeks (float): acumulado porcentual hace una semana
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    DECLARE @ultima_fecha   DATE = (
      SELECT MAX(CAST(date_call AS DATE))
      FROM ReporteLlamada
    );

    DECLARE @fecha_semanapasada DATE = DATEADD(DAY, -7, @ultima_fecha);

    DECLARE @total_today INT = (
      SELECT COUNT(*) 
      FROM ReporteLlamada
      WHERE CAST(date_call AS DATE) = @ultima_fecha
    );

    DECLARE @total_past INT = (
      SELECT COUNT(*)
      FROM ReporteLlamada
      WHERE CAST(date_call AS DATE) = @fecha_semanapasada
    );

    ;WITH commits_today AS (
        SELECT DATEPART(HOUR, date_call) AS hora, COUNT(*) AS cantidad
        FROM ReporteLlamada
        WHERE call_cod_id IN ('CP', 'PDROP')
          AND CAST(date_call AS DATE) = @ultima_fecha
        GROUP BY DATEPART(HOUR, date_call)
    ),
    commits_past AS (
        SELECT DATEPART(HOUR, date_call) AS hora, COUNT(*) AS cantidad
        FROM ReporteLlamada
        WHERE call_cod_id IN ('CP', 'PDROP')
          AND CAST(date_call AS DATE) = @fecha_semanapasada
        GROUP BY DATEPART(HOUR, date_call)
    )
    SELECT 
        h.hora,
        ROUND(
          100.0 * SUM(ISNULL(ct.cantidad,0)) 
              OVER (ORDER BY h.hora 
                    ROWS UNBOUNDED PRECEDING)
          / NULLIF(@total_today,0)
        , 2) AS cumsum_today_pct,
        ROUND(
          100.0 * SUM(ISNULL(cp.cantidad,0)) 
              OVER (ORDER BY h.hora 
                    ROWS UNBOUNDED PRECEDING)
          / NULLIF(@total_past,0)
        , 2) AS cumsum_lastweek_pct
    FROM (
        SELECT TOP (24) ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS hora
        FROM master..spt_values
    ) h
    LEFT JOIN commits_today ct ON h.hora = ct.hora
    LEFT JOIN commits_past  cp ON h.hora = cp.hora
    ORDER BY h.hora;
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    return [
        {"hora": row[0], "cumsum_today": row[1], "cumsum_2weeks": row[2]}
        for row in rows
    ]


def get_assignments_campaign_raw(idUsuario: int, rol: str) -> list[dict]:
    """
    Obtiene las asignaciones de campaña para un usuario y rol específico.

    Si el rol es administrador, devuelve las campañas de todas las campañas para la última fecha.
    Si es coordinador, filtra solo por sus campañas asignadas.

    Parámetros:
        - idUsuario (int): ID del usuario
        - rol (str): Rol del usuario

    Retorna:
        List[dict]: Lista con dicts que contienen 'name' y 'value' para cada campaña.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(CAST(date_call AS date)) FROM ReporteLlamada")
    ultima_fecha = cursor.fetchone()[0]
    if not ultima_fecha:
        conn.close()
        return []

    if rol.lower() in ['administrador', 'admin']:
        # Administrador ve todas las campañas
        sql = """
            SELECT ISNULL(campaign_name,'Sin campaña') AS name, COUNT(*) AS value
            FROM ReporteLlamada
            WHERE CAST(date_call AS date) = ?
            GROUP BY campaign_name
            ORDER BY value DESC;
        """
        cursor.execute(sql, (ultima_fecha,))
    else:
        # Coordinador ve solo sus campañas asignadas
        sql = """
            SELECT ISNULL(r.campaign_name,'Sin campaña') AS name, COUNT(*) AS value
            FROM ReporteLlamada r
            INNER JOIN UsuariosCampanas uc ON r.campaign_id = uc.idCampana
            WHERE uc.idUsuarioApp = ? AND CAST(r.date_call AS date) = ?
            GROUP BY r.campaign_name
            ORDER BY value DESC;
        """
        cursor.execute(sql, (idUsuario, ultima_fecha))

    rows = cursor.fetchall()
    conn.close()
    return [{"name": row[0], "value": row[1]} for row in rows]
