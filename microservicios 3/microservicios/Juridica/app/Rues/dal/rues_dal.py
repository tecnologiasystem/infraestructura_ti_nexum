import pyodbc
from typing import List, Optional
from pydantic import BaseModel
from app.config.database import get_connection
from datetime import datetime

# ----------------------------------------------------
# MODELOS para datos de RUES

class DetalleModel(BaseModel):
    """
    Modelo Pydantic que representa un detalle de RUES con campos opcionales.
    """
    cedula: str
    nombre: Optional[str]
    identificacion: Optional[str]
    categoria: Optional[str]
    camaraComercio: Optional[str]
    numeroMatricula: Optional[str]
    actividadEconomica: Optional[str]

class EncabezadoModel(BaseModel):
    """
    Modelo Pydantic que representa el encabezado de una automatización RUES,
    incluyendo la lista de detalles asociados.
    """
    automatizacion: str
    idUsuario: int
    fechaCargue: datetime
    totalRegistros: int
    estado: Optional[str] = "En proceso"
    detalles: List[DetalleModel]

# ----------------------------------------------------
# FUNCIONES DE ACCESO A DATOS (DAL)

def insertar_encabezado(encabezado: EncabezadoModel) -> int:
    """
    Inserta un nuevo registro en la tabla RuesEncabezado con la info del encabezado.
    Retorna el ID insertado o -1 en caso de error.
    """
    conn = get_connection()
    if conn is None:
        return -1
    try:
        cursor = conn.cursor()
        # Inserción con OUTPUT para obtener idEncabezado generado automáticamente
        cursor.execute("""
            INSERT INTO RuesEncabezado (automatizacion, idUsuario, fechaCargue, totalRegistros, estado)
            OUTPUT INSERTED.idEncabezado
            VALUES (?, ?, ?, ?, ?)
        """, encabezado.automatizacion, encabezado.idUsuario,
             encabezado.fechaCargue, encabezado.totalRegistros, encabezado.estado)

        row = cursor.fetchone()
        conn.commit()
        return int(row[0]) if row else -1
    except Exception as e:
        import traceback
        traceback.print_exc()
        return -1
    finally:
        cursor.close()
        conn.close()

def insertar_detalle(idEncabezado: int, detalle: DetalleModel):
    """
    Inserta un detalle relacionado con un encabezado en RuesDetalle.
    Usa procedimiento almacenado con acción 1 para inserción.
    Retorna (True, None) si éxito, o (None, error) si falla.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            EXEC SP_CRUD_RUES_DETALLE 
                @accion=1,
                @idEncabezado=?, 
                @cedula=?, 
                @nombre=?, 
                @identificacion=?, 
                @categoria=?, 
                @camaraComercio=?, 
                @numeroMatricula=?,  
                @actividadEconomica=? 
        """, idEncabezado, detalle.cedula, detalle.nombre, detalle.identificacion,
             detalle.categoria, detalle.camaraComercio, detalle.numeroMatricula,
            detalle.actividadEconomica)
        conn.commit()
        return True, None 
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def insertar_detalle_resultadoRues(resultado: DetalleModel) -> bool:
    """
    Inserta o actualiza el detalle de RUES con los resultados obtenidos en la automatización.

    Lógica:
    - Busca todos los detalles por cédula.
    - Busca el primer detalle con campos vacíos para actualizarlo.
    - Si no hay detalle vacío, inserta un nuevo detalle con acción 1 usando idEncabezado existente.
    - Retorna True si operación exitosa, False en caso contrario.
    """
    conn = get_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()

        # Obtener detalles existentes para la cédula
        cursor.execute("""
            SELECT idDetalle, nombre, identificacion, categoria, camaraComercio,
                   numeroMatricula, actividadEconomica
            FROM RuesDetalle WITH(NOLOCK)
            WHERE cedula = ?
            ORDER BY numItem
        """, resultado.cedula)
        detalles = cursor.fetchall()

        # Buscar primer detalle con campos vacíos para actualizar
        detalle_vacio = None
        for detalle in detalles:
            id_detalle = detalle[0]
            campos = detalle[1:]
            if all(not campo or str(campo).strip() == "" for campo in campos):
                detalle_vacio = id_detalle
                break

        if detalle_vacio:
            # Actualizar detalle vacío con datos nuevos (acción 2)
            cursor.execute("""
                EXEC SP_CRUD_RUES_DETALLE 
                    @accion=2,
                    @idDetalle=?,
                    @cedula=?,
                    @nombre=?,
                    @identificacion=?,
                    @categoria=?,
                    @camaraComercio=?,
                    @numeroMatricula=?,
                    @actividadEconomica=?
            """, (
                detalle_vacio,
                resultado.cedula,
                resultado.nombre,
                resultado.identificacion,
                resultado.categoria,
                resultado.camaraComercio,
                resultado.numeroMatricula,
                resultado.actividadEconomica
            ))
        else:
            # Insertar nuevo detalle usando idEncabezado del primer detalle existente
            cursor.execute("""
                SELECT TOP 1 idEncabezado 
                FROM RuesDetalle WITH(NOLOCK)
                WHERE cedula = ?
                ORDER BY idDetalle
            """, resultado.cedula)
            row = cursor.fetchone()
            if not row:
                return False
            idEncabezado = row[0]

            cursor.execute("""
                EXEC SP_CRUD_RUES_DETALLE 
                    @accion=1,
                    @idEncabezado=?,
                    @cedula=?,
                    @nombre=?,
                    @identificacion=?,
                    @categoria=?,
                    @camaraComercio=?,
                    @numeroMatricula=?,
                    @actividadEconomica=?
            """, (
                idEncabezado,
                resultado.cedula,
                resultado.nombre,
                resultado.identificacion,
                resultado.categoria,
                resultado.camaraComercio,
                resultado.numeroMatricula,
                resultado.actividadEconomica
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

def obtener_detalles_agrupados_Rues():
    """
    Obtiene todos los detalles agrupados por cédula para facilitar análisis o reportes.

    Pasos:
    - Consulta todos los detalles junto con su encabezado.
    - Organiza los resultados en un diccionario agrupado por cédula.
    - Retorna lista con diccionarios de la forma {"cedula": ..., "detalles": [...]}
    - Retorna lista vacía en caso de error.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.cedula, d.*
            FROM RuesDetalle d
            INNER JOIN RuesEncabezado e ON d.idEncabezado = e.idEncabezado
            ORDER BY d.cedula
        """)

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        agrupado = {}
        for item in data:
            cedula = item["cedula"]
            agrupado.setdefault(cedula, []).append(item)

        return [{"cedula": c, "detalles": dets} for c, dets in agrupado.items()]

    except Exception as e:
        import traceback
        traceback.print_exc()
        return []
    finally:
        cursor.close()
        conn.close()

def obtener_correo_usuarioRues(id_usuario: int) -> Optional[str]:
    """
    Obtiene el correo electrónico del usuario con id_usuario.

    Retorna el correo o None si no se encuentra o hay error.
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
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cedula, nombre, identificacion, categoria,
                   camaraComercio, numeroMatricula, actividadEconomica
            FROM RuesDetalle WITH (NOLOCK)
            WHERE idEncabezado = ?
            ORDER BY cedula
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
            FROM RuesEncabezado
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
            FROM RuesEncabezado
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
            UPDATE RuesEncabezado
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
            UPDATE RuesEncabezado
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
            UPDATE RuesEncabezado
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
    UPDATE dbo.RuesDetalle
    SET
      numeroMatricula      = CASE WHEN numeroMatricula      IS NULL OR numeroMatricula      = '' THEN 'Pausado' ELSE numeroMatricula    END
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
    UPDATE dbo.RuesDetalle
    SET
      numeroMatricula      = CASE WHEN numeroMatricula      = 'Pausado' THEN NULL ELSE numeroMatricula     END
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
