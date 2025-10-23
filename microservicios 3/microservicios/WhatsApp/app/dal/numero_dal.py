import pyodbc
from typing import List, Optional
from pydantic import BaseModel
from app.config.database import get_connection
from datetime import datetime

class DetalleModel(BaseModel):
    indicativo: str
    numero: str

class EncabezadoModel(BaseModel):
    automatizacion: str
    idUsuario: int
    fechaCargue: datetime
    totalRegistros: int
    estado: Optional[str] = "En proceso"
    detalles: List[DetalleModel]

def obtener_automatizacionesWhatsApp():
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
                COUNT(CASE 
                    WHEN d.tiene_whatsApp IS NOT NULL AND LTRIM(RTRIM(d.tiene_whatsApp)) <> '' THEN 1 
                END) AS detallesIngresados
            FROM WhatsAppEncabezado e
            LEFT JOIN WhatsAppDetalle d ON e.idEncabezado = d.idEncabezado
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

def obtener_automatizacion_por_idWhatsApp(id_encabezado: int):
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
                d.indicativo, 
                d.numero,
                d.tiene_whatsApp
            FROM WhatsAppEncabezado e
            LEFT JOIN WhatsAppDetalle d ON e.idEncabezado = d.idEncabezado
            WHERE e.idEncabezado = ?
              AND d.numero IS NOT NULL
              AND LTRIM(RTRIM(d.numero)) <> ''
        """, id_encabezado)
        return cursor.fetchall()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_numero_aConsultarWhatsApp():
    """
    Devuelve la primera cédula que aún no ha sido procesada (sin nombres)
    para su automatización.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
              e.idEncabezado,
              d.indicativo,
              CAST(d.numero AS VARCHAR(50)) AS numero
            FROM WhatsAppEncabezado e
            JOIN WhatsAppDetalle d ON e.idEncabezado = d.idEncabezado
            WHERE (d.tiene_whatsApp = '' OR d.tiene_whatsApp IS NULL)
              AND e.idEncabezado = (
                  SELECT TOP 1 e2.idEncabezado
                  FROM WhatsAppEncabezado e2
                  JOIN WhatsAppDetalle d2 ON e2.idEncabezado = d2.idEncabezado
                  WHERE d2.tiene_whatsApp = '' OR d2.tiene_whatsApp IS NULL
                  ORDER BY e2.idEncabezado ASC
              )
            ORDER BY d.idDetalle ASC
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
            INSERT INTO WhatsAppEncabezado (automatizacion, idUsuario, fechaCargue, totalRegistros, estado)
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
            EXEC SP_CRUD_WHATSAPP_DETALLE
                @accion=1,
                @idEncabezado=?,
                @indicativo=?,
                @numero=?
        """, (
            idEncabezado,
            detalle.indicativo,
            detalle.numero
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

def insertar_detalle_resultadoWhatsApp(resultado: DetalleModel) -> bool:
    """
    Inserta o actualiza el resultado de la automatización en el detalle,
    buscando un registro vacío para actualizar o insertando uno nuevo.
    """
    conn = get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT idDetalle, tiene_whatsApp
            FROM WhatsAppDetalle WITH(NOLOCK)
            WHERE numero = ?
        """, resultado.numero)
        detalles = cursor.fetchall()

        detalle_vacio = None
        for detalle in detalles:
            id_detalle = detalle[0]
            campos = detalle[1:]
            if all(not campo or str(campo).strip() == "" for campo in campos):
                detalle_vacio = id_detalle
                break

        if detalle_vacio:
            idDetalle = detalle_vacio
            cursor.execute("""
                EXEC SP_CRUD_WHATSAPP_DETALLE
                @accion=2,
                @idDetalle=?,
                @indicativo=?,
                @numero=?, 
                @tiene_whatsApp=?
            """, (
                idDetalle,
                resultado.indicativo,
                resultado.numero,
                resultado.tiene_whatsApp
            ))

        else:
            cursor.execute("""
                SELECT TOP 1 idEncabezado 
                FROM WhatsAppEncabezado WITH(NOLOCK)
                WHERE automatizacion = 'WhatsApp'
                AND totalRegistros > 0
                ORDER BY fechaCargue DESC
            """)
            row = cursor.fetchone()
            if not row:
                return False
            idEncabezado = row[0]

            cursor.execute("""
            EXEC SP_CRUD_WHATSAPP_DETALLE
            @accion=1,
            @idEncabezado=?, 
            @indicativo=?,
            @numero=?, 
            @tiene_whatsApp=?
        """, (
            idEncabezado,
            resultado.indicativo,
            resultado.numero,
            resultado.tiene_whatsApp
        ))


        conn.commit()
        return True

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False

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
            SELECT numero, tiene_whatsApp
            FROM WhatsAppDetalle WITH (NOLOCK)
            WHERE 
                ISNULL(tiene_whatsApp, '') <> ''
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

def obtener_correo_usuarioWhatsApp(id_usuario: int) -> Optional[str]:
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
            SELECT indicativo, numero, tiene_whatsApp
            FROM WhatsAppDetalle WITH (NOLOCK)
            WHERE idEncabezado = ?
            ORDER BY numero
        """, id_encabezado)

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]

        if not columns:
            columns = ["indicativo","numero", "tiene_whatsApp"]  

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
            FROM WhatsAppEncabezado
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
            FROM WhatsAppEncabezado
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
            UPDATE WhatsAppEncabezado
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

#--------- PAUSAR---------------------------------------------
def marcar_pausa_encabezado(id_encabezado: int, fecha_pausa: datetime) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE WhatsAppEncabezado
            SET estado = ?, fechaPausa = ?
            WHERE idEncabezado = ?
        """, 'Pausado', fecha_pausa, id_encabezado)
        conn.commit()
        return True
    except:
        return False
    finally:
        cursor.close()
        conn.close()

def quitar_pausa_encabezado(id_encabezado: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE WhatsAppEncabezado
            SET estado = ?, fechaPausa = NULL
            WHERE idEncabezado = ?
        """, 'En proceso', id_encabezado)
        conn.commit()
        return True
    except:
        return False
    finally:
        cursor.close()
        conn.close()
def pausar_detalle_encabezado(id_encabezado: int) -> bool:
    sql = """
    UPDATE dbo.WhatsAppDetalle
    SET
      tiene_whatsApp      = CASE WHEN tiene_whatsApp      IS NULL OR tiene_whatsApp      = '' THEN 'Pausado' ELSE tiene_whatsApp      END
    WHERE idEncabezado = ?
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, id_encabezado)
        conn.commit()
        return True
    except:
        return False
    finally:
        cur.close()
        conn.close()

def reanudar_detalle_encabezado(id_encabezado: int) -> bool:
    sql = """
    UPDATE dbo.WhatsAppDetalle
    SET
      tiene_whatsApp      = CASE WHEN tiene_whatsApp      = 'Pausado' THEN NULL ELSE tiene_whatsApp     END
    WHERE idEncabezado = ?
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, id_encabezado)
        conn.commit()
        return True
    except:
        return False
    finally:
        cur.close()
        conn.close()