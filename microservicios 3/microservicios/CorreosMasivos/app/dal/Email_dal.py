from app.config.database import get_connection

def crear_encabezado(descripcion: str | None, id_usuario: int | None, total_registros: int, remitente: str | None) -> int:
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        EXEC [dbo].[SP_CRUD_EmailEnvios]
        @Accion=1,
        @descripcion=?,
        @idUsuario=?,
        @totalRegistros=?,
        @remitente=?
    """, (descripcion, id_usuario, total_registros, remitente))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return int(row[0]) if row else None

def registrar_detalle(id_encabezado, email, asunto, cuerpo, adjuntos, cedula, nombre_cliente, campana):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        EXEC [dbo].[SP_CRUD_EmailEnvios]
        @Accion = 2,
        @idEncabezado = ?,
        @email_destinatario = ?,
        @asunto = ?,
        @cuerpo = ?,
        @adjuntos = ?, 
        @estado_envio = 'PENDIENTE',
        @cedula = ?,
        @nombre_cliente = ?,
        @campana = ?
    """, (id_encabezado, email, asunto, cuerpo, adjuntos, cedula, nombre_cliente, campana))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return int(row[0]) if row else None

def actualizar_estado_detalle(id_detalle: int, estado: str, error: str | None = None):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        EXEC [dbo].[SP_CRUD_EmailEnvios]
        @Accion=3,
        @idDetalle=?,
        @estado_envio=?,
        @error_detalle=?
    """, (id_detalle, estado, error))
    conn.commit()
    cur.close(); conn.close()

def finalizar_encabezado_si_completo(id_encabezado: int) -> dict | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        EXEC [dbo].[SP_CRUD_EmailEnvios]
        @Accion=7,
        @idEncabezado=?
    """, (id_encabezado,))
    row = cur.fetchone()
    cols = [c[0] for c in cur.description] if cur.description else []
    conn.commit()
    cur.close(); conn.close()
    return dict(zip(cols, row)) if row else None

def obtener_correo_usuario(id_usuario_app: int) -> str | None:
    """
    Devuelve el correo del usuario en NEXUM.dbo.UsuariosApp, o None si no existe.
    """
    if not id_usuario_app:
        return None
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT TOP 1 [correo]
        FROM [NEXUM].[dbo].[UsuariosApp]
        WHERE [idUsuarioApp] = ?
    """, (id_usuario_app,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row[0] if row and row[0] else None

def obtener_estado_encabezado(id_encabezado: int) -> str | None:
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT TOP 1 estado
        FROM [NEXUM].[dbo].[EmailEnviosEncabezado]
        WHERE idEncabezado = ?
    """, (id_encabezado,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return row[0] if row else None

def actualizar_estado_encabezado(id_encabezado: int, estado: str):
    conn = get_connection()
    cursor = conn.cursor()

    if estado == "FINALIZADO":
        cursor.execute("""
            UPDATE EmailEnviosEncabezado
            SET estado = ?, fechaFinalizacion = GETDATE()
            WHERE idEncabezado = ?
        """, (estado, id_encabezado))
    else:
        cursor.execute("""
            UPDATE EmailEnviosEncabezado
            SET estado = ?
            WHERE idEncabezado = ?
        """, (estado, id_encabezado))

    conn.commit()
    cursor.close()
    conn.close()

def cancelar_pendientes_por_encabezado(id_encabezado: int):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        UPDATE [NEXUM].[dbo].[EmailEnviosDetalle]
        SET estado_envio = 'CANCELADO'
        WHERE idEncabezado = ? AND estado_envio = 'PENDIENTE'
    """, (id_encabezado,))
    conn.commit()
    cur.close(); conn.close()

def listar_pendientes_por_encabezado(id_encabezado: int) -> list[dict]:
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT idDetalle, email_destinatario, asunto, cuerpo, adjuntos
        FROM [NEXUM].[dbo].[EmailEnviosDetalle]
        WHERE idEncabezado = ? AND estado_envio = 'PENDIENTE'
        ORDER BY idDetalle ASC
    """, (id_encabezado,))
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description]
    cur.close(); conn.close()
    return [dict(zip(cols, r)) for r in rows]

def registrar_detalles_bulk(id_encabezado: int, rows: list[dict], subject_tmpl: str, body_tmpl: str, adjuntos_str: str | None):
    """
    Inserta TODOS los detalles como PENDIENTE.
    OJO: Si tu SP no soporta bulk, esto igual hace muchos EXEC pero en una sola conexión (mucho más rápido).
    """
    conn = get_connection(); cur = conn.cursor()

    for r in rows:
        email = r["email"]
        asunto = r["asunto"]
        cuerpo = r["cuerpo"]
        cur.execute("""
            EXEC [dbo].[SP_CRUD_EmailEnvios]
            @Accion = 2,
            @idEncabezado = ?,
            @email_destinatario = ?,
            @asunto = ?,
            @cuerpo = ?,
            @adjuntos = ?,
            @estado_envio = 'PENDIENTE'
        """, (id_encabezado, email, asunto, cuerpo, adjuntos_str))

    conn.commit()
    cur.close(); conn.close()


def tomar_siguiente_pendiente(id_encabezado: int) -> dict | None:
    """
    Devuelve 1 pendiente (el más viejo). Idealmente deberías marcarlo 'EN_PROCESO' para evitar dobles workers.
    """
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT TOP 1 idDetalle, email_destinatario, asunto, cuerpo, adjuntos
        FROM [NEXUM].[dbo].[EmailEnviosDetalle]
        WHERE idEncabezado = ? AND estado_envio = 'PENDIENTE'
        ORDER BY idDetalle ASC
    """, (id_encabezado,))
    row = cur.fetchone()
    if not row:
        cur.close(); conn.close()
        return None
    cols = [c[0] for c in cur.description]
    cur.close(); conn.close()
    return dict(zip(cols, row))

def pausar_pendientes_por_encabezado(id_encabezado: int):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        UPDATE [NEXUM].[dbo].[EmailEnviosDetalle]
        SET estado_envio = 'PAUSADO'
        WHERE idEncabezado = ? AND estado_envio = 'PENDIENTE'
    """, (id_encabezado,))
    conn.commit()
    cur.close(); conn.close()

def reanudar_pausados_por_encabezado(id_encabezado: int):
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        UPDATE [NEXUM].[dbo].[EmailEnviosDetalle]
        SET estado_envio = 'PENDIENTE'
        WHERE idEncabezado = ? AND estado_envio = 'PAUSADO'
    """, (id_encabezado,))
    conn.commit()
    cur.close(); conn.close()

def listar_encabezados_en_proceso_con_pendientes() -> list[dict]:
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT e.idEncabezado, e.remitente, e.idUsuario
        FROM [NEXUM].[dbo].[EmailEnviosEncabezado] e
        INNER JOIN [NEXUM].[dbo].[EmailEnviosDetalle] d
            ON d.idEncabezado = e.idEncabezado
        WHERE e.estado = 'EN_PROCESO'
          AND d.estado_envio = 'PENDIENTE'
        ORDER BY e.idEncabezado ASC
    """)
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description]
    cur.close(); conn.close()
    return [dict(zip(cols, r)) for r in rows]

def contar_detalles_pendientes_o_pausados(id_encabezado: int) -> int:
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(1)
        FROM [NEXUM].[dbo].[EmailEnviosDetalle]
        WHERE idEncabezado = ?
          AND estado_envio IN ('PENDIENTE', 'PAUSADO')
    """, (id_encabezado,))
    n = cur.fetchone()[0] or 0
    cur.close(); conn.close()
    return int(n)

def contar_enviados_hoy_por_remitente(remitente: str) -> int:
    """
    Cuenta SOLO envíos efectivos (estado_envio='ENVIADO') del día de HOY por cuenta/remitente.
    NO cuenta ERROR.
    """
    if not remitente:
        return 0

    conn = get_connection(); cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(1)
        FROM [NEXUM].[dbo].[EmailEnviosDetalle] d
        INNER JOIN [NEXUM].[dbo].[EmailEnviosEncabezado] e
            ON e.idEncabezado = d.idEncabezado
        WHERE e.remitente = ?
          AND d.estado_envio = 'ENVIADO'
          AND CAST(d.fecha_envio AS DATE) = CAST(GETDATE() AS DATE)
    """, (remitente,))

    n = cur.fetchone()[0] or 0
    cur.close(); conn.close()
    return int(n)


def marcar_fecha_envio_si_falta(id_detalle: int):
    """
    Marca fecha_envio=GETDATE() si quedó ENVIADO y la fecha está NULL.
    (Esto permite que el conteo diario sea exacto)
    """
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        UPDATE [NEXUM].[dbo].[EmailEnviosDetalle]
        SET fecha_envio = GETDATE()
        WHERE idDetalle = ?
          AND estado_envio = 'ENVIADO'
          AND (fecha_envio IS NULL)
    """, (id_detalle,))
    conn.commit()
    cur.close(); conn.close()
