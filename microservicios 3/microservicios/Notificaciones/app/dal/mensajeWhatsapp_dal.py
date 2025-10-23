import pyodbc
from typing import List, Optional
from pydantic import BaseModel
from app.config.database import get_connection
from datetime import datetime

class DetalleModel(BaseModel):
    numero: str
    mensaje: str

class EncabezadoModel(BaseModel):
    automatizacion: str
    idUsuario: int
    fechaCargue: datetime
    totalRegistros: int
    estado: Optional[str] = "En proceso"
    detalles: List[DetalleModel]

def obtener_automatizacionesMensajeWhatsApp():
    """
    Consulta todas las automatizaciones, junto con el total de registros y los ingresados,
    calculando el estado de avance para cada una.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
    SELECT 
        e.idEncabezado,
        e.automatizacion,
        e.fechaCargue,
        e.totalRegistros,
        e.estado,
        u.nombre AS nombreUsuario,
        COUNT(d.idDetalle) AS detallesIngresados
    FROM MensajeWhatsAppEncabezado e
    LEFT JOIN MensajeWhatsAppDetalle d ON e.idEncabezado = d.idEncabezado
    LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
    GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
    ORDER BY e.fechaCargue DESC
""")

        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_automatizacion_por_idMensajeWhatsApp(id_encabezado: int):
    """
    Recupera el encabezado y los detalles de una automatización específica por id.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                d.idDetalle,
                d.numero,
                d.mensaje
            FROM MensajeWhatsAppEncabezado e
            LEFT JOIN MensajeWhatsAppDetalle d ON e.idEncabezado = d.idEncabezado
            WHERE e.idEncabezado = ?
              AND d.mensaje IS NOT NULL
              AND LTRIM(RTRIM(d.mensaje)) <> ''
        """, id_encabezado)
        return cursor.fetchall()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_numero_aEnviarMensajeWhatsApp():
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
              e.idEncabezado,
              d.numero,
              CAST(d.mensaje AS VARCHAR(50)) AS mensaje
            FROM MensajeWhatsAppEncabezado e
            JOIN MensajeWhatsAppDetalle d ON e.idEncabezado = d.idEncabezado
              AND e.idEncabezado = (
                  SELECT TOP 1 e2.idEncabezado
                  FROM MensajeWhatsAppEncabezado e2
                  JOIN MensajeWhatsAppDetalle d2 ON e2.idEncabezado = d2.idEncabezado
                  ORDER BY e2.idEncabezado ASC
              )
            ORDER BY NEWID()
        """)
        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def insertar_encabezado(encabezado: EncabezadoModel) -> int:
    """
    Inserta un encabezado nuevo y devuelve su id generado.
    """
    conn = get_connection()
    if conn is None:
        return -1
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO MensajeWhatsAppEncabezado (automatizacion, idUsuario, fechaCargue, totalRegistros, estado)
            OUTPUT INSERTED.idEncabezado
            VALUES (?, ?, ?, ?, ?)
        """, encabezado.automatizacion, encabezado.idUsuario,
             encabezado.fechaCargue, encabezado.totalRegistros, encabezado.estado)

        row = cursor.fetchone()
        conn.commit()

        if row:
            id_encabezado = int(row[0])
            print("✅ Insert encabezado:", id_encabezado)
            return id_encabezado
        else:
            return -1
    except Exception as e:
        import traceback
        traceback.print_exc()
        return -1
    finally:
        cursor.close()
        conn.close()

def insertar_detalle(idEncabezado: int, detalle: DetalleModel):
    """
    Inserta un detalle asociado a un encabezado.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            EXEC SP_CRUD_MENSAJE_WHATSAPP_DETALLE
                @accion=1,
                @idEncabezado=?,
                @numero=?,
                @mensaje=?
        """, (
            idEncabezado,
            detalle.numero,
            detalle.mensaje
        ))

        conn.commit()
        return True, None 
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def obtener_detalles_agrupados_WhatsApp():
    """
    Obtiene detalles no vacíos y agrupa la información por cédula.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT numero, mensaje
            FROM MensajeWhatsAppDetalle WITH (NOLOCK)
            ORDER BY numero
        """)

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        agrupado = {}
        for item in data:
            numero= item["numero"]
            if numero not in agrupado:
                agrupado[numero] = []
            agrupado[numero].append(item)

        return [{"numero": numero, "detalles": detalles} for numero, detalles in agrupado.items()]

    except Exception as e:
        import traceback
        traceback.print_exc()
        return []

    finally:
        cursor.close()
        conn.close()

def obtener_correo_usuarioMensajeWhatsApp(id_usuario: int) -> Optional[str]:
    """
    Consulta el correo electrónico de un usuario dado su id.
    """
    conn = get_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT correo FROM UsuariosApp WHERE idUsuarioApp = ?", id_usuario)
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    finally:
        cursor.close()
        conn.close()

def obtener_detalles_por_encabezado(id_encabezado: int):
    """
    Obtiene todos los detalles asociados a un encabezado específico.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT numero, mensaje
            FROM MensajeWhatsAppDetalle WITH (NOLOCK)
            WHERE idEncabezado = ?
            ORDER BY numero
        """, id_encabezado)

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

        if not columns:
            columns = ["numero", "mensaje"]  

        return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        import traceback
        traceback.print_exc()
        return []

    finally:
        cursor.close()
        conn.close()

def obtener_idUsuario_por_encabezado(idEncabezado: int) -> Optional[int]:
    conn = get_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT idUsuario
            FROM MensajeWhatsAppEncabezado
            WHERE idEncabezado = ?
        """, idEncabezado)
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    finally:
        cursor.close()
        conn.close()

def correo_ya_enviado(idEncabezado: int) -> bool:
    conn = get_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT correoEnviado
            FROM MensajeWhatsAppEncabezado
            WHERE idEncabezado = ?
        """, idEncabezado)
        row = cursor.fetchone()
        return bool(row[0]) if row else False
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        conn.close()

def marcar_correo_enviado(idEncabezado: int) -> bool:
    conn = get_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE MensajeWhatsAppEncabezado
            SET correoEnviado = 1
            WHERE idEncabezado = ?
        """, idEncabezado)
        conn.commit()
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        conn.close()
