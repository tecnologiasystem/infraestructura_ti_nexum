import pyodbc
from typing import List, Optional
from pydantic import BaseModel
from app.config.database import get_connection
from datetime import datetime

# ---------------------------------------------------
# Modelos de datos para la aplicación usando Pydantic
# ---------------------------------------------------
class DetalleModel(BaseModel):
    cedula: str
    nombre: Optional[str]
    fechaNacimiento: Optional[str]
    edad: Optional[str]
    sexo: Optional[str]
    antiguedad: Optional[str]
    fechaAfiliacion: Optional[str]
    epsAnterior: Optional[str]
    direccion: Optional[str]
    telefono: Optional[str]
    celular: Optional[str]
    email: Optional[str]
    municipio: Optional[str]
    departamento: Optional[str]
    observacion: Optional[str]

class EncabezadoModel(BaseModel):
    automatizacion: str
    idUsuario: int
    fechaCargue: datetime
    totalRegistros: int
    estado: Optional[str] = "En proceso"
    detalles: List[DetalleModel]

# ---------------------------------------------------
# FUNCIONES PRINCIPALES - Operaciones con la base de datos
# ---------------------------------------------------

def obtener_automatizacionesNuevaEps():
    """
    Obtiene las automatizaciones de la base de datos con el conteo de detalles ingresados.
    Devuelve tupla (filas, error) donde filas es lista de resultados o None si hay error.
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
                COUNT(DISTINCT d.cedula) AS detallesIngresados
            FROM NuevaEpsEncabezado e
            LEFT JOIN NuevaEpsDetalle d ON e.idEncabezado = d.idEncabezado
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

def obtener_automatizacion_por_idNuevaEps(id_encabezado: int):
    """
    Obtiene los datos completos de una automatización específica, incluyendo detalles.
    Retorna lista con filas o None + error en caso de fallo.
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
                d.cedula,
                d.nombre,
                d.fechaNacimiento,
                d.edad,
                d.sexo,
                d.antiguedad,
                d.fechaAfiliacion,
                d.epsAnterior,
                d.direccion,
                d.telefono,
                d.celular,
                d.email,
                d.municipio,
                d.departamento,
                d.observacion
            FROM NuevaEpsEncabezado e
            LEFT JOIN NuevaEpsDetalle d ON e.idEncabezado = d.idEncabezado
            WHERE e.idEncabezado = ?
        """, id_encabezado)
        return cursor.fetchall()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_CC_aConsultarNuevaEps():
    """
    Obtiene las cédulas que aún no tienen nombre asignado para automatización.
    Útil para saber qué registros necesitan ser procesados.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.idEncabezado,
             CAST(d.cedula AS VARCHAR(50)) AS cedula
            FROM NuevaEpsEncabezado e
            JOIN NuevaEpsDetalle d ON e.idEncabezado = d.idEncabezado
            WHERE (d.nombre = '' OR d.nombre IS NULL)
              AND e.idEncabezado = (
                  SELECT TOP 1 e2.idEncabezado
                  FROM NuevaEpsEncabezado e2
                  JOIN NuevaEpsDetalle d2 ON e2.idEncabezado = d2.idEncabezado
                  WHERE d2.nombre = '' OR d2.nombre IS NULL
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
    Inserta un registro en la tabla NuevaEpsEncabezado y retorna el id generado.
    Retorna -1 en caso de error.
    """
    conn = get_connection()
    if conn is None:
        return -1
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO NuevaEpsEncabezado (automatizacion, idUsuario, fechaCargue, totalRegistros, estado)
            OUTPUT INSERTED.idEncabezado
            VALUES (?, ?, ?, ?, ?)
        """, encabezado.automatizacion, encabezado.idUsuario,
             encabezado.fechaCargue, encabezado.totalRegistros, encabezado.estado)
        row = cursor.fetchone()
        conn.commit()
        if row:
            id_encabezado = int(row[0])
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
    Inserta un detalle asociado a un encabezado en NuevaEpsDetalle.
    Retorna (True, None) si fue exitoso, o (None, error) si hubo problema.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        ((
            idEncabezado,
            detalle.cedula,
            detalle.nombre,
            detalle.fechaNacimiento,
            detalle.edad,
            detalle.sexo,
            detalle.antiguedad,
            detalle.fechaAfiliacion,
            detalle.epsAnterior,
            detalle.direccion,
            detalle.telefono,
            detalle.celular,
            detalle.email,
            detalle.municipio,
            detalle.departamento,
            detalle.observacion
        ))

        cursor.execute("""
            EXEC SP_CRUD_NUEVAEPS_DETALLE 
                @accion=1,
                @idEncabezado=?, 
                @cedula=?, 
                @nombre=?, 
                @fechaNacimiento=?, 
                @edad=?, 
                @sexo=?, 
                @antiguedad=?, 
                @fechaAfiliacion=?, 
                @epsAnterior=?, 
                @direccion=?, 
                @telefono=?, 
                @celular=?, 
                @email=?,
                @municipio=?, 
                @departamento=?, 
                @observacion=?
        """, (
            idEncabezado,
            detalle.cedula,
            detalle.nombre,
            detalle.fechaNacimiento,
            detalle.edad,
            detalle.sexo,
            detalle.antiguedad,
            detalle.fechaAfiliacion,
            detalle.epsAnterior,
            detalle.direccion,
            detalle.telefono,
            detalle.celular,
            detalle.email,
            detalle.municipio,
            detalle.departamento,
            detalle.observacion
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

def insertar_detalle_resultadoNuevaEps(resultado: DetalleModel) -> bool:
    """
    Inserta o actualiza el detalle resultado para una cédula específica.
    Si existe un detalle vacío, lo actualiza, si no, inserta uno nuevo.
    """
    conn = get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        # Buscar detalles existentes con la misma cédula
        cursor.execute("""
            SELECT idDetalle, nombre, fechaNacimiento, edad, sexo,
                   antiguedad, fechaAfiliacion, epsAnterior, direccion,
                   telefono, celular, email, municipio, departamento, observacion
            FROM NuevaEpsDetalle WITH(NOLOCK)
            WHERE cedula = ?
            ORDER BY numItem
        """, resultado.cedula)
        detalles = cursor.fetchall()

        # Buscar primer detalle vacío (todos sus campos vacíos)
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

            # Actualiza el detalle vacío con los nuevos datos
            cursor.execute("""
                EXEC SP_CRUD_NUEVAEPS_DETALLE 
                @accion=2,
                @idDetalle=?, 
                @cedula=?, 
                @nombre=?, 
                @fechaNacimiento=?, 
                @edad=?, 
                @sexo=?, 
                @antiguedad=?, 
                @fechaAfiliacion=?, 
                @epsAnterior=?, 
                @direccion=?, 
                @telefono=?, 
                @celular=?, 
                @email=?,
                @municipio=?, 
                @departamento=?, 
                @observacion=?
            """, (
                idDetalle,
                resultado.cedula,
                resultado.nombre,
                resultado.fechaNacimiento,
                resultado.edad,
                resultado.sexo,
                resultado.antiguedad,
                resultado.fechaAfiliacion,
                resultado.epsAnterior,
                resultado.direccion,
                resultado.telefono,
                resultado.celular,
                resultado.email,
                resultado.municipio,
                resultado.departamento,
                resultado.observacion
            ))

        else:
            # Si no hay detalle vacío, insertar uno nuevo asociado al encabezado más reciente
            cursor.execute("""
                SELECT TOP 1 idEncabezado 
                FROM NuevaEpsEncabezado WITH(NOLOCK)
                WHERE automatizacion = 'NuevaEps'
                  AND totalRegistros > 0
                ORDER BY fechaCargue DESC
            """)
            row = cursor.fetchone()
            if not row:
                return False
            idEncabezado = row[0]

            cursor.execute("""
                EXEC SP_CRUD_NUEVAEPS_DETALLE 
                @accion=1,
                @idEncabezado=?, 
                @cedula=?, 
                @nombre=?, 
                @fechaNacimiento=?, 
                @edad=?, 
                @sexo=?, 
                @antiguedad=?, 
                @fechaAfiliacion=?, 
                @epsAnterior=?, 
                @direccion=?, 
                @telefono=?, 
                @celular=?, 
                @email=?,
                @municipio=?, 
                @departamento=?, 
                @observacion=?
            """, (
                idEncabezado,  
                resultado.cedula,
                resultado.nombre,
                resultado.fechaNacimiento,
                resultado.edad,
                resultado.sexo,
                resultado.antiguedad,
                resultado.fechaAfiliacion,
                resultado.epsAnterior,
                resultado.direccion,
                resultado.telefono,
                resultado.celular,
                resultado.email,
                resultado.municipio,
                resultado.departamento,
                resultado.observacion
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
    """
    Obtiene detalles completos agrupados por cédula, incluyendo todos los registros de detalles.
    Retorna una lista de diccionarios con estructura {"cedula": ..., "detalles": [...]}
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.cedula, d.*
            FROM NuevaEpsDetalle d
            INNER JOIN NuevaEpsEncabezado e ON d.idEncabezado = e.idEncabezado
            ORDER BY e.cedula
        """)

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        agrupado = {}
        for item in data:
            cedula = item["cedula"]
            agrupado.setdefault(cedula, []).append(item)

        return [{"cedula": cedula, "detalles": detalles} for cedula, detalles in agrupado.items()]

    except Exception as e:
        import traceback
        traceback.print_exc()
        return []

    finally:
        cursor.close()
        conn.close()

def obtener_detalles_agrupados_NuevaEps():
    """
    Obtiene detalles agrupados por cédula pero solo registros con datos no nulos en campos importantes.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cedula, nombre, fechaNacimiento, edad, sexo,
                   antiguedad, fechaAfiliacion, epsAnterior, direccion, telefono, 
                   celular, email, municipio, departamento, observacion
            FROM NuevaEpsDetalle WITH (NOLOCK)
            WHERE 
                ISNULL(nombre, '') <> '' OR 
                ISNULL(fechaNacimiento, '') <> '' OR 
                ISNULL(edad, '') <> '' OR 
                ISNULL(sexo, '') <> '' OR 
                ISNULL(antiguedad, '') <> '' OR 
                ISNULL(fechaAfiliacion, '') <> '' OR 
                ISNULL(direccion, '') <> ''
            ORDER BY cedula
        """)

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        agrupado = {}
        for item in data:
            cc = item["cedula"]
            agrupado.setdefault(cc, []).append(item)

        return [{"cedula": cc, "detalles": detalles} for cc, detalles in agrupado.items()]

    except Exception as e:
        import traceback
        traceback.print_exc()
        return []

    finally:
        cursor.close()
        conn.close()

def obtener_correo_usuarioNuevaEps(id_usuario: int) -> Optional[str]:
    """
    Obtiene el correo electrónico de un usuario dado su id.
    Retorna el correo o None si no se encuentra.
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
    Obtiene los detalles asociados a un encabezado específico, ordenados por cédula.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cedula, nombre, fechaNacimiento, edad, sexo, antiguedad,
                   fechaAfiliacion, epsAnterior, direccion, telefono, celular,
                   email, municipio, departamento, observacion
            FROM NuevaEpsDetalle WITH (NOLOCK)
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
            FROM NuevaEpsEncabezado
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
            FROM NuevaEpsEncabezado
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
            UPDATE NuevaEpsEncabezado
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
            UPDATE NuevaEpsEncabezado
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
            UPDATE NuevaEpsEncabezado
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
    UPDATE dbo.NuevaEpsDetalle
    SET
      nombre      = CASE WHEN nombre      IS NULL OR nombre      = '' THEN 'Pausado' ELSE nombre      END
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
    UPDATE dbo.NuevaEpsDetalle
    SET
      nombre      = CASE WHEN nombre      = 'Pausado' THEN NULL ELSE nombre     END
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

def contar_total_por_encabezadoNuevaEps(id_encabezado: int) -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(1) FROM NuevaEpsDetalle WHERE idEncabezado = ?", id_encabezado)
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_procesados_por_encabezadoNuevaEps(id_encabezado: int) -> int:
    """
    Cuenta como PROCESADO si tiene algún dato de salida y el nombre no es 'Pausado'.
    Ajusta campos si tu esquema difiere.
    """
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM NuevaEpsDetalle d WITH(NOLOCK)
            WHERE d.idEncabezado = ?
              AND (
                   (NULLIF(LTRIM(RTRIM(d.nombre)),'') IS NOT NULL AND LTRIM(RTRIM(d.nombre)) <> 'Pausado')
                OR NULLIF(LTRIM(RTRIM(d.fechaNacimiento)),'') IS NOT NULL
                OR NULLIF(LTRIM(RTRIM(d.edad)),'') IS NOT NULL
                OR NULLIF(LTRIM(RTRIM(d.sexo)),'') IS NOT NULL
                OR NULLIF(LTRIM(RTRIM(d.antiguedad)),'') IS NOT NULL
                OR NULLIF(LTRIM(RTRIM(d.fechaAfiliacion)),'') IS NOT NULL
                OR NULLIF(LTRIM(RTRIM(d.epsAnterior)),'') IS NOT NULL
                OR NULLIF(LTRIM(RTRIM(d.direccion)),'') IS NOT NULL
                OR NULLIF(LTRIM(RTRIM(d.telefono)),'') IS NOT NULL
                OR NULLIF(LTRIM(RTRIM(d.celular)),'') IS NOT NULL
                OR NULLIF(LTRIM(RTRIM(d.email)),'') IS NOT NULL
                OR NULLIF(LTRIM(RTRIM(d.municipio)),'') IS NOT NULL
                OR NULLIF(LTRIM(RTRIM(d.departamento)),'') IS NOT NULL
                OR NULLIF(LTRIM(RTRIM(d.observacion)),'') IS NOT NULL
              )
        """, id_encabezado)
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def obtener_detalles_paginados_por_encabezadoNuevaEps(
    id_encabezado: int, offset: int, limit: int, cc: Optional[str]
):
    conn = get_connection(); cursor = conn.cursor()
    try:
        base = """
           SELECT d.idDetalle, d.cedula, d.nombre, d.fechaNacimiento, d.edad, d.sexo, d.antiguedad,
                  d.fechaAfiliacion, d.epsAnterior, d.direccion, d.telefono, d.celular, d.email,
                  d.municipio, d.departamento, d.observacion
           FROM NuevaEpsDetalle d WITH(NOLOCK)
           WHERE d.idEncabezado = ?
        """
        params = [id_encabezado]
        if cc and cc.strip():
            base += " AND CAST(d.cedula AS VARCHAR(50)) LIKE ?"
            params.append(f"%{cc.strip()}%")
        base += " ORDER BY d.idDetalle OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params += [offset, limit]
        cursor.execute(base, tuple(params))
        rows = cursor.fetchall()
        columns = [c[0] for c in cursor.description]
        items = [dict(zip(columns, r)) for r in rows]

        count_q = "SELECT COUNT(1) FROM NuevaEpsDetalle d WHERE d.idEncabezado = ?"
        count_params = [id_encabezado]
        if cc and cc.strip():
            count_q += " AND CAST(d.cedula AS VARCHAR(50)) LIKE ?"
            count_params.append(f"%{cc.strip()}%")
        cursor.execute(count_q, tuple(count_params))
        total = int(cursor.fetchone()[0] or 0)

        return items, total
    finally:
        cursor.close(); conn.close()

# --- TOTAL DE ENCABEZADOS ---
def contar_encabezadosNuevaEps() -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(1) FROM NuevaEpsEncabezado WITH(NOLOCK)")
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

# --- ENCABEZADOS PAGINADOS ---
def obtener_encabezados_paginadoNuevaEps(offset: int, limit: int):
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                e.estado,
                u.nombre AS nombreUsuario,
                COUNT(DISTINCT d.cedula) AS detallesIngresados
            FROM NuevaEpsEncabezado e
            LEFT JOIN NuevaEpsDetalle d ON e.idEncabezado = d.idEncabezado
            LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
            GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
            ORDER BY e.fechaCargue DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, (offset, limit))
        return cursor.fetchall()
    finally:
        cursor.close(); conn.close()
