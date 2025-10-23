import pyodbc
from typing import List, Optional
from pydantic import BaseModel
from app.config.database import get_connection
from datetime import datetime

class DetalleModel(BaseModel):
    radicado: str
    fechaInicial: Optional[str]
    fechaFinal: Optional[str]
    fechaActuacion: Optional[str]
    actuacion: Optional[str]
    anotacion: Optional[str]
    fechaIniciaTermino: Optional[str]
    fechaFinalizaTermino: Optional[str]
    fechaRegistro: Optional[str]
    radicadoNuevo: Optional[str]

    
class EncabezadoModel(BaseModel):
    automatizacion: str
    idUsuario: int
    fechaCargue: datetime
    totalRegistros: int
    estado: Optional[str] = "En proceso"
    detalles: List[DetalleModel]

def insertar_encabezado(encabezado: EncabezadoModel) -> int:
    conn = get_connection()
    if conn is None:
        return -1
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO VigilanciaEncabezado (automatizacion, idUsuario, fechaCargue, totalRegistros, estado)
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
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
                EXEC SP_CRUD_VIGILANCIA_DETALLE 
                    @accion=1,
                    @idEncabezado=?, 
                    @radicado=?, 
                    @fechaInicial=?,
                    @fechaFinal=?,
                    @fechaActuacion=?, 
                    @actuacion=?, 
                    @anotacion=?, 
                    @fechaIniciaTermino=?, 
                    @fechaFinalizaTermino=?, 
                    @fechaRegistro=?, 
                    @radicadoNuevo=?
            """, idEncabezado, detalle.radicado, detalle.fechaInicial, detalle.fechaFinal, detalle.fechaActuacion, detalle.actuacion,
                detalle.anotacion, detalle.fechaIniciaTermino, detalle.fechaFinalizaTermino, detalle.fechaRegistro,
                detalle.radicadoNuevo)

        conn.commit()
        return True, None 
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def insertar_detalle_resultadoVigilancia(resultado: DetalleModel) -> bool:
    conn = get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT idDetalle, fechaActuacion, actuacion, anotacion, fechaIniciaTermino,
                   fechaFinalizaTermino, fechaRegistro, radicadoNuevo
            FROM VigilanciaDetalle WITH(NOLOCK)
            WHERE radicado = ?
            ORDER BY numItem
        """, resultado.radicado)
        detalles = cursor.fetchall()

        # Buscar primer detalle vacío
        detalle_vacio = None
        for detalle in detalles:
            id_detalle = detalle[0]
            campos = detalle[1:]
            if all(not campo or str(campo).strip() == "" for campo in campos):
                detalle_vacio = id_detalle
                break

        if detalle_vacio:
            idDetalle = detalle_vacio
            print("✅ Actualizando detalle existente con idDetalle =", idDetalle)

            cursor.execute("""
                EXEC SP_CRUD_VIGILANCIA_DETALLE 
                    @accion=2,
                    @idDetalle=?,
                    @fechaActuacion=?,
                    @actuacion=?,
                    @anotacion=?,
                    @fechaIniciaTermino=?,
                    @fechaFinalizaTermino=?,
                    @fechaRegistro=?,
                    @radicadoNuevo=?
            """, (
                idDetalle,
                resultado.fechaActuacion,
                resultado.actuacion,
                resultado.anotacion,
                resultado.fechaIniciaTermino,
                resultado.fechaFinalizaTermino,
                resultado.fechaRegistro,
                resultado.radicadoNuevo
            ))
        else:
            # Si no hay registro vacío, insertar nuevo detalle
            cursor.execute("""
                SELECT TOP 1 idEncabezado 
                FROM VigilanciaDetalle WITH(NOLOCK)
                WHERE radicado = ?
                ORDER BY idDetalle
            """, resultado.radicado)
            row = cursor.fetchone()
            if not row:
                return False
            idEncabezado = row[0]

            cursor.execute("""
                EXEC SP_CRUD_VIGILANCIA_DETALLE 
                    @accion=1,
                    @idEncabezado=?,
                    @radicado=?,
                    @fechaInicial=?,
                    @fechaFinal=?,
                    @fechaActuacion=?,
                    @actuacion=?,
                    @anotacion=?,
                    @fechaIniciaTermino=?,
                    @fechaFinalizaTermino=?,
                    @fechaRegistro=?,
                    @radicadoNuevo=?
            """, (
                idEncabezado,
                resultado.radicado,
                resultado.fechaInicial,
                resultado.fechaFinal,
                resultado.fechaActuacion,
                resultado.actuacion,
                resultado.anotacion,
                resultado.fechaIniciaTermino,
                resultado.fechaFinalizaTermino,
                resultado.fechaRegistro,
                resultado.radicadoNuevo
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

def obtener_detalles_agrupados():
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.radicado, d.*
            FROM VigilanciaDetalle d
            INNER JOIN VigilanciaEncabezado e ON d.idEncabezado = e.idEncabezado
            ORDER BY e.radicado
        """)

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        agrupado = {}
        for item in data:
            radicado = item["radicado"]
            agrupado.setdefault(radicado, []).append(item)

        return [{"radicado": c, "detalles": dets} for c, dets in agrupado.items()]

    except Exception as e:
        import traceback
        traceback.print_exc()
        return []

    finally:
        cursor.close()
        conn.close()

def obtener_detalles_agrupados_Vigilancia():
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT radicado, fechaInicial, fechaFinal, fechaActuacion, actuacion, anotacion, fechaIniciaTermino,
                   fechaFinalizaTermino, fechaRegistro, radicadoNuevo
            FROM VigilanciaDetalle WITH (NOLOCK)
            WHERE 
                ISNULL(fechaActuacion, '') <> '' OR 
                ISNULL(actuacion, '') <> '' OR 
                ISNULL(anotacion, '') <> '' OR 
                ISNULL(fechaIniciaTermino, '') <> '' OR 
                ISNULL(fechaFinalizaTermino, '') <> '' OR 
                ISNULL(fechaRegistro, '') <> '' OR 
                ISNULL(radicadoNuevo, '') <> ''
            ORDER BY radicado
        """)

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        agrupado = {}
        for item in data:
            radicado = item["radicado"]
            agrupado.setdefault(radicado, []).append(item)

        return [{"radicado": radicado, "detalles": detalles} for radicado, detalles in agrupado.items()]

    except Exception as e:
        import traceback
        traceback.print_exc()
        return []

    finally:
        cursor.close()
        conn.close()

def obtener_correo_usuarioVigilancia(id_usuario: int) -> str:
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
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT radicado, fechaInicial, fechaFinal, fechaActuacion, actuacion, anotacion, fechaIniciaTermino,
                   fechaFinalizaTermino, fechaRegistro, radicadoNuevo
            FROM VigilanciaDetalle WITH (NOLOCK)
            WHERE idEncabezado = ?
            ORDER BY radicado
        """, id_encabezado)

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
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
            FROM VigilanciaEncabezado
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
            FROM VigilanciaEncabezado
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
            UPDATE VigilanciaRuntEncabezado
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
            UPDATE VigilanciaEncabezado
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
            UPDATE VigilanciaEncabezado
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
    UPDATE dbo.VigilanciaDetalle
    SET
      actuacion      = CASE WHEN actuacion      IS NULL OR actuacion      = '' THEN 'Pausado' ELSE actuacion      END
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
    UPDATE dbo.VigilanciaDetalle
    SET
      actuacion      = CASE WHEN actuacion      = 'Pausado' THEN NULL ELSE actuacion     END
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
