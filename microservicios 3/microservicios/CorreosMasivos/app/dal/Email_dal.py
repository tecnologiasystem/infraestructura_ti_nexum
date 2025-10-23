from app.config.database import get_connection

def crear_encabezado(descripcion: str | None, id_usuario: int | None, total_registros: int) -> int:
    conn = get_connection(); cur = conn.cursor()
    cur.execute("""
        EXEC [dbo].[SP_CRUD_EmailEnvios]
        @Accion=1,
        @descripcion=?,
        @idUsuario=?,
        @totalRegistros=?
    """, (descripcion, id_usuario, total_registros))
    row = cur.fetchone(); cur.close(); conn.close()
    return int(row[0]) if row else None


def registrar_detalle(id_encabezado, email, asunto, cuerpo, adjuntos):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        EXEC [dbo].[SP_CRUD_EmailEnvios]
        @Accion = 2,
        @idEncabezado = ?,
        @email_destinatario = ?,
        @asunto = ?,
        @cuerpo = ?,
        @adjuntos = ?,
        @estado_envio = 'PENDIENTE'
    """, (id_encabezado, email, asunto, cuerpo, adjuntos))
    row = cursor.fetchone()
    cursor.close()
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
    cur.close(); conn.close()


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
    cur.close(); conn.close()
    return dict(zip(cols, row)) if row else None