from app.config.database import get_connection
from typing import Optional, List, Dict, Any

# Nota:
# - Este microservicio ya usa el SP [dbo].[SP_CRUD_EmailEnvios] para encabezados (Accion=5)
#   y detalle (Accion=6).
# - Para el tablero (dashboard), usamos consultas agregadas directas sobre tablas.
# - Si en tu BD los nombres de tablas difieren, ajusta los nombres en las consultas.

def listar_encabezados():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("EXEC [dbo].[SP_CRUD_EmailEnvios] @Accion = 5")
    rows = cursor.fetchall()
    columnas = [col[0] for col in cursor.description]
    cursor.close()
    conn.close()
    return [dict(zip(columnas, row)) for row in rows]

def listar_detalles_por_encabezado(id_encabezado):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("EXEC [dbo].[SP_CRUD_EmailEnvios] @Accion = 6, @idEncabezado = ?", (id_encabezado,))
    rows = cursor.fetchall()
    columnas = [col[0] for col in cursor.description]
    cursor.close()
    conn.close()
    return [dict(zip(columnas, row)) for row in rows]


def _fetchall_dict(cursor) -> List[Dict[str, Any]]:
    rows = cursor.fetchall()
    cols = [c[0] for c in cursor.description]
    return [dict(zip(cols, row)) for row in rows]


def dashboard_resumen(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    idUsuario: Optional[int] = None,
    remitente: Optional[str] = None,
) -> Dict[str, Any]:
    """Métricas globales (KPI) del envío de correos."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    ;WITH base AS (
    SELECT
        d.estado_envio,
        d.fecha_registro,
        d.fecha_envio,
        d.error_detalle,
        e.remitente AS remitente,
        e.idUsuario
    FROM dbo.EmailEnviosDetalle d
    LEFT JOIN dbo.EmailEnviosEncabezado e ON e.idEncabezado = d.idEncabezado
    WHERE ( ? IS NULL OR d.fecha_registro >= ? )
      AND ( ? IS NULL OR d.fecha_registro < DATEADD(DAY, 1, ?))
      AND ( ? IS NULL OR e.idUsuario = ? )
      AND ( ? IS NULL OR e.remitente = ? )
),
p95calc AS (
    SELECT
      PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY DATEDIFF(SECOND, fecha_registro, fecha_envio))
      OVER () AS p95_segundos_envio
    FROM base
    WHERE fecha_envio IS NOT NULL
)
SELECT
    COUNT(1) AS total,
    SUM(CASE WHEN estado_envio = 'ENVIADO' THEN 1 ELSE 0 END) AS enviados,
    SUM(CASE WHEN estado_envio = 'ERROR' THEN 1 ELSE 0 END) AS errores,
    SUM(CASE WHEN (estado_envio IS NULL OR estado_envio NOT IN ('ENVIADO','ERROR')) THEN 1 ELSE 0 END) AS pendientes,
    CAST(100.0 * SUM(CASE WHEN estado_envio = 'ERROR' THEN 1 ELSE 0 END) / NULLIF(COUNT(1),0) AS DECIMAL(10,2)) AS pct_error,
    CAST(100.0 * SUM(CASE WHEN estado_envio = 'ENVIADO' THEN 1 ELSE 0 END) / NULLIF(COUNT(1),0) AS DECIMAL(10,2)) AS pct_enviado,
    CAST(AVG(CASE WHEN fecha_envio IS NOT NULL THEN DATEDIFF(SECOND, fecha_registro, fecha_envio) END) AS DECIMAL(18,2)) AS avg_segundos_envio,
    CAST((SELECT TOP 1 p95_segundos_envio FROM p95calc) AS DECIMAL(18,2)) AS p95_segundos_envio
FROM base;

    """

    params = [
        fecha_inicio, fecha_inicio,
        fecha_fin, fecha_fin,
        idUsuario, idUsuario,
        remitente, remitente,
    ]
    cursor.execute(query, params)
    row = cursor.fetchone()
    cols = [c[0] for c in cursor.description]
    cursor.close()
    conn.close()
    return dict(zip(cols, row)) if row else {}


def dashboard_por_remitente(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    idUsuario: Optional[int] = None,
    remitente: Optional[str] = None,
    top: int = 50,
) -> List[Dict[str, Any]]:
    """Métricas agrupadas por remitente (cuenta)."""
    conn = get_connection()
    cursor = conn.cursor()

    query = f"""
    SELECT TOP ({int(top)})
        e.remitente AS remitente,
        COUNT(1) AS total,
        SUM(CASE WHEN d.estado_envio = 'ENVIADO' THEN 1 ELSE 0 END) AS enviados,
        SUM(CASE WHEN d.estado_envio = 'ERROR' THEN 1 ELSE 0 END) AS errores,
        SUM(CASE WHEN (d.estado_envio IS NULL OR d.estado_envio NOT IN ('ENVIADO','ERROR')) THEN 1 ELSE 0 END) AS pendientes,
        CAST(100.0 * SUM(CASE WHEN d.estado_envio = 'ERROR' THEN 1 ELSE 0 END) / NULLIF(COUNT(1),0) AS DECIMAL(10,2)) AS pct_error,
        CAST(AVG(CASE WHEN d.fecha_envio IS NOT NULL THEN DATEDIFF(SECOND, d.fecha_registro, d.fecha_envio) END) AS DECIMAL(18,2)) AS avg_segundos_envio
    FROM dbo.EmailEnviosDetalle d
    LEFT JOIN dbo.EmailEnviosEncabezado e ON e.idEncabezado = d.idEncabezado
    WHERE ( ? IS NULL OR d.fecha_registro >= ? )
      AND ( ? IS NULL OR d.fecha_registro < DATEADD(DAY, 1, ?))
      AND ( ? IS NULL OR e.idUsuario = ? )
    GROUP BY e.remitente
    ORDER BY errores DESC, total DESC;
    """
    params = [fecha_inicio, fecha_inicio, fecha_fin, fecha_fin, idUsuario, idUsuario]
    cursor.execute(query, params)
    data = _fetchall_dict(cursor)
    cursor.close()
    conn.close()
    return data


def dashboard_por_dia(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    idUsuario: Optional[int] = None,
    remitente: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Series por día (para ver tendencia)."""
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        CAST(d.fecha_registro AS DATE) AS dia,
        COUNT(1) AS total,
        SUM(CASE WHEN d.estado_envio = 'ENVIADO' THEN 1 ELSE 0 END) AS enviados,
        SUM(CASE WHEN d.estado_envio = 'ERROR' THEN 1 ELSE 0 END) AS errores,
        SUM(CASE WHEN (d.estado_envio IS NULL OR d.estado_envio NOT IN ('ENVIADO','ERROR')) THEN 1 ELSE 0 END) AS pendientes,
        CAST(100.0 * SUM(CASE WHEN d.estado_envio = 'ERROR' THEN 1 ELSE 0 END) / NULLIF(COUNT(1),0) AS DECIMAL(10,2)) AS pct_error
    FROM dbo.EmailEnviosDetalle d
    LEFT JOIN dbo.EmailEnviosEncabezado e ON e.idEncabezado = d.idEncabezado
    WHERE ( ? IS NULL OR d.fecha_registro >= ? )
      AND ( ? IS NULL OR d.fecha_registro < DATEADD(DAY, 1, ?))
      AND ( ? IS NULL OR e.idUsuario = ? )
      AND ( ? IS NULL OR e.remitente = ? )
    GROUP BY CAST(d.fecha_registro AS DATE)
    ORDER BY dia ASC;
    """
    params = [
        fecha_inicio, fecha_inicio,
        fecha_fin, fecha_fin,
        idUsuario, idUsuario,
        remitente, remitente,
    ]
    cursor.execute(query, params)
    data = _fetchall_dict(cursor)
    cursor.close()
    conn.close()
    return data


def dashboard_top_errores(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    idUsuario: Optional[int] = None,
    remitente: Optional[str] = None,
    top: int = 20,
) -> List[Dict[str, Any]]:
    """Top de errores (para saber qué está fallando)."""
    conn = get_connection()
    cursor = conn.cursor()
    query = f"""
    SELECT TOP ({int(top)})
        LEFT(ISNULL(d.error_detalle, '(sin detalle)'), 220) AS error,
        COUNT(1) AS cantidad
    FROM dbo.EmailEnviosDetalle d
    LEFT JOIN dbo.EmailEnviosEncabezado e ON e.idEncabezado = d.idEncabezado
    WHERE d.estado_envio = 'ERROR'
      AND ( ? IS NULL OR d.fecha_registro >= ? )
      AND ( ? IS NULL OR d.fecha_registro < DATEADD(DAY, 1, ?))
      AND ( ? IS NULL OR e.idUsuario = ? )
      AND ( ? IS NULL OR e.remitente = ? )
    GROUP BY LEFT(ISNULL(d.error_detalle, '(sin detalle)'), 220)
    ORDER BY COUNT(1) DESC;
    """
    params = [
        fecha_inicio, fecha_inicio,
        fecha_fin, fecha_fin,
        idUsuario, idUsuario,
        remitente, remitente,
    ]
    cursor.execute(query, params)
    data = _fetchall_dict(cursor)
    cursor.close()
    conn.close()
    return data