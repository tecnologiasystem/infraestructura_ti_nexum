import pyodbc
from typing import List, Optional
from pydantic import BaseModel
from app.config.database import get_connection
from datetime import datetime

class DetalleModel(BaseModel):
    """
    Modelo que representa el detalle individual de una automatización FamiSanar.
    """
    cedula: str
    nombres: Optional[str]
    apellidos: Optional[str]
    estado: Optional[str]
    IPS: Optional[str]
    convenio: Optional[str]
    tipo: Optional[str]
    categoria: Optional[str]
    semanas: Optional[str]
    fechaNacimiento: Optional[str]
    edad: Optional[str]
    sexo: Optional[str]
    direccion: Optional[str]
    telefono: Optional[str]
    departamento: Optional[str]
    municipio: Optional[str]
    causal: Optional[str]

class EncabezadoModel(BaseModel):
    """
    Modelo que representa el encabezado general de una tanda de automatización.
    """
    automatizacion: str
    idUsuario: int
    fechaCargue: datetime
    totalRegistros: int
    estado: Optional[str] = "En proceso"
    detalles: List[DetalleModel]

def obtener_automatizacionesFamiSanar():
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
                COUNT(DISTINCT d.cedula) AS detallesIngresados
            FROM FamiSanarEncabezado e
            LEFT JOIN FamiSanarDetalle d ON e.idEncabezado = d.idEncabezado
            LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
            GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
            ORDER BY e.fechaCargue DESC
        """)
        return cursor.fetchall(), None
    except Exception as e:
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_automatizacion_por_idFamiSanar(id_encabezado: int):
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
                d.cedula,
                d.nombres,
                d.apellidos,
                d.estado,
                d.IPS,
                d.convenio,
                d.tipo,
                d.categoria,
                d.semanas,
                d.fechaNacimiento,
                d.edad,
                d.sexo,
                d.direccion,
                d.telefono,
                d.departamento,
                d.municipio,
                d.causal
            FROM FamiSanarEncabezado e
            LEFT JOIN FamiSanarDetalle d ON e.idEncabezado = d.idEncabezado
            WHERE e.idEncabezado = ?
              AND d.cedula IS NOT NULL
              AND LTRIM(RTRIM(d.cedula)) <> ''
        """, id_encabezado)
        return cursor.fetchall()
    except Exception as e:
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_CC_aConsultarFamiSanar():
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
              CAST(d.cedula AS VARCHAR(50)) AS cedula
            FROM FamiSanarEncabezado e
            JOIN FamiSanarDetalle d ON e.idEncabezado = d.idEncabezado
            WHERE (d.nombres = '' OR d.nombres IS NULL)
              AND e.idEncabezado = (
                  SELECT TOP 1 e2.idEncabezado
                  FROM FamiSanarEncabezado e2
                  JOIN FamiSanarDetalle d2 ON e2.idEncabezado = d2.idEncabezado
                  WHERE d2.nombres = '' OR d2.nombres IS NULL
                  ORDER BY e2.idEncabezado ASC
              )
            ORDER BY NEWID()
        """)
        return cursor.fetchall(), None
    except Exception as e:
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
            INSERT INTO FamiSanarEncabezado (automatizacion, idUsuario, fechaCargue, totalRegistros, estado)
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
            EXEC SP_CRUD_FAMISANAR_DETALLE 
                @accion=1,
                @idEncabezado=?, 
                @cedula=?, 
                @nombres=?, 
                @apellidos=?, 
                @estado=?, 
                @IPS=?, 
                @convenio=?, 
                @tipo=?, 
                @categoria=?, 
                @semanas=?, 
                @fechaNacimiento=?, 
                @edad=?, 
                @sexo=?,
                @direccion=?, 
                @telefono=?, 
                @departamento=?, 
                @municipio=?, 
                @causal=?
        """, (
            idEncabezado,
            detalle.cedula,
            detalle.nombres,
            detalle.apellidos,
            detalle.estado,
            detalle.IPS,
            detalle.convenio,
            detalle.tipo,
            detalle.categoria,
            detalle.semanas,
            detalle.fechaNacimiento,
            detalle.edad,
            detalle.sexo,
            detalle.direccion,
            detalle.telefono,
            detalle.departamento,
            detalle.municipio,
            detalle.causal
        ))

        conn.commit()
        return True, None 
    except Exception as e:
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def insertar_detalle_resultadoFamiSanar(resultado: DetalleModel) -> bool:
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
            SELECT idDetalle, nombres, apellidos, estado, IPS,
                   convenio, tipo, categoria, semanas, fechaNacimiento, edad, sexo,
                   direccion, telefono, departamento, municipio, causal
            FROM FamiSanarDetalle WITH(NOLOCK)
            WHERE cedula = ?
            ORDER BY numItem
        """, resultado.cedula)
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
                EXEC SP_CRUD_FAMISANAR_DETALLE 
                @accion=2,
                @idDetalle=?, 
                @cedula=?, 
                @nombres=?, 
                @apellidos=?, 
                @estado=?, 
                @IPS=?, 
                @convenio=?, 
                @tipo=?, 
                @categoria=?, 
                @semanas=?, 
                @fechaNacimiento=?, 
                @edad=?, 
                @sexo=?,
                @direccion=?, 
                @telefono=?, 
                @departamento=?, 
                @municipio=?, 
                @causal=?
            """, (
                idDetalle,
                resultado.cedula,
                resultado.nombres,
                resultado.apellidos,
                resultado.estado,
                resultado.IPS,
                resultado.convenio,
                resultado.tipo,
                resultado.categoria,
                resultado.semanas,
                resultado.fechaNacimiento,
                resultado.edad,
                resultado.sexo,
                resultado.direccion,
                resultado.telefono,
                resultado.departamento,
                resultado.municipio,
                resultado.causal
            ))

        else:
            cursor.execute("""
                SELECT TOP 1 idEncabezado 
                FROM FamiSanarEncabezado WITH(NOLOCK)
                WHERE automatizacion = 'FamiSanar'
                AND totalRegistros > 0
                ORDER BY fechaCargue DESC
            """)
            row = cursor.fetchone()
            if not row:
                return False
            idEncabezado = row[0]

            cursor.execute("""
                EXEC SP_CRUD_FAMISANAR_DETALLE 
                @accion=1,
                @idEncabezado=?, 
                @cedula=?, 
                @nombres=?, 
                @apellidos=?, 
                @estado=?, 
                @IPS=?, 
                @convenio=?, 
                @tipo=?, 
                @categoria=?, 
                @semanas=?, 
                @fechaNacimiento=?, 
                @edad=?, 
                @sexo=?,
                @direccion=?, 
                @telefono=?, 
                @departamento=?, 
                @municipio=?, 
                @causal=?
            """, (
                idEncabezado,
                resultado.cedula,
                resultado.nombres,
                resultado.apellidos,
                resultado.estado,
                resultado.IPS,
                resultado.convenio,
                resultado.tipo,
                resultado.categoria,
                resultado.semanas,
                resultado.fechaNacimiento,
                resultado.edad,
                resultado.sexo,
                resultado.direccion,
                resultado.telefono,
                resultado.departamento,
                resultado.municipio,
                resultado.causal
            ))

        conn.commit()
        return True

    except Exception as e:
        return False

    finally:
        cursor.close()
        conn.close()

def obtener_detalles_agrupados_FamiSanar():
    """
    Obtiene detalles no vacíos y agrupa la información por cédula.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cedula, nombres, apellidos, estado, IPS,
                   convenio, tipo, categoria, semanas, fechaNacimiento, edad, sexo, direccion, 
                   telefono, departamento, municipio, causal
            FROM FamiSanarDetalle WITH (NOLOCK)
            WHERE 
                ISNULL(nombres, '') <> '' OR 
                ISNULL(apellidos, '') <> '' OR 
                ISNULL(estado, '') <> '' OR 
                ISNULL(IPS, '') <> '' OR 
                ISNULL(convenio, '') <> '' OR 
                ISNULL(categoria, '') <> '' OR 
                ISNULL(telefono, '') <> ''
            ORDER BY cedula
        """)

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        agrupado = {}
        for item in data:
            cc = item["cedula"]
            if cc not in agrupado:
                agrupado[cc] = []
            agrupado[cc].append(item)

        return [{"cedula": cc, "detalles": detalles} for cc, detalles in agrupado.items()]

    except Exception as e:
        return []

    finally:
        cursor.close()
        conn.close()

def obtener_correo_usuarioFamiSanar(id_usuario: int) -> Optional[str]:
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
            SELECT cedula, nombres, apellidos, estado, IPS, convenio,
                   tipo, categoria, semanas, fechaNacimiento, edad,
                   sexo, direccion, telefono, departamento, municipio, causal
            FROM FamiSanarDetalle WITH (NOLOCK)
            WHERE idEncabezado = ?
            ORDER BY cedula
        """, id_encabezado)

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
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
            FROM FamiSanarEncabezado
            WHERE idEncabezado = ?
        """, idEncabezado)
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
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
            FROM FamiSanarEncabezado
            WHERE idEncabezado = ?
        """, idEncabezado)
        row = cursor.fetchone()
        return bool(row[0]) if row else False
    except Exception as e:
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
            UPDATE FamiSanarEncabezado
            SET correoEnviado = 1
            WHERE idEncabezado = ?
        """, idEncabezado)
        conn.commit()
        return True
    except Exception as e:
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
            UPDATE FamisanarEncabezado
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
            UPDATE FamisanarEncabezado
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
    UPDATE dbo.FamiSanarDetalle
    SET
      nombres      = CASE WHEN nombres      IS NULL OR nombres      = '' THEN 'Pausado' ELSE nombres      END
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
    UPDATE dbo.FamiSanarDetalle
    SET
      nombres      = CASE WHEN nombres      = 'Pausado' THEN NULL ELSE nombres     END
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

def contar_detalles_por_encabezado(id_encabezado: int, cc: str = None):
    conn = get_connection()
    if conn is None:
        return 0
    try:
        cursor = conn.cursor()
        if cc and cc.strip():
            cursor.execute("""
                SELECT COUNT(1)
                FROM FamiSanarDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                  AND LTRIM(RTRIM(d.cedula)) = LTRIM(RTRIM(?))
            """, (id_encabezado, cc.strip()))
        else:
            cursor.execute("""
                SELECT COUNT(1)
                FROM FamiSanarDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
            """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0
    finally:
        cursor.close()
        conn.close()


def obtener_detalles_por_encabezado_paginado(id_encabezado: int, offset: int, limit: int, cc: str = None):
    """
    Devuelve filas paginadas de detalles para un encabezado (con filtro opcional por cédula).
    """
    conn = get_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        if cc and cc.strip():
            cursor.execute("""
                SELECT 
                    d.idDetalle,
                    d.cedula,
                    d.nombres,
                    d.apellidos,
                    d.estado,
                    d.IPS,
                    d.convenio,
                    d.tipo,
                    d.categoria,
                    d.semanas,
                    d.edad,
                    d.sexo,
                    d.telefono,
                    d.departamento,
                    d.municipio,
                    d.causal
                FROM FamiSanarDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                  AND LTRIM(RTRIM(d.cedula)) = LTRIM(RTRIM(?))
                ORDER BY d.idDetalle ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (id_encabezado, cc.strip(), offset, limit))
        else:
            cursor.execute("""
                SELECT 
                    d.idDetalle,
                    d.cedula,
                    d.nombres,
                    d.apellidos,
                    d.estado,
                    d.IPS,
                    d.convenio,
                    d.tipo,
                    d.categoria,
                    d.semanas,
                    d.edad,
                    d.sexo,
                    d.telefono,
                    d.departamento,
                    d.municipio,
                    d.causal
                FROM FamiSanarDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                ORDER BY d.idDetalle ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (id_encabezado, offset, limit))
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, r)) for r in cursor.fetchall()]
    except Exception:
        return []
    finally:
        cursor.close()
        conn.close()

def contar_total_por_encabezado(id_encabezado: int) -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM FamiSanarDetalle
            WHERE idEncabezado = ?
        """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_procesados_por_encabezado(id_encabezado: int) -> int:
    """
    Cuenta como PROCESADO si tiene algún dato de salida y NO está marcado como 'Pausado'.
    Ajusta las columnas a tus nombres reales si difieren.
    """
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM FamiSanarDetalle d
            WHERE d.idEncabezado = ?
              AND (
                    (NULLIF(LTRIM(RTRIM(d.nombres))   ,'') IS NOT NULL AND LTRIM(RTRIM(d.nombres)) <> 'Pausado')
                 OR (NULLIF(LTRIM(RTRIM(d.apellidos)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.estado))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.IPS))       ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.convenio))  ,'') IS NOT NULL)
              )
        """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_encabezados_famisanar() -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(1) FROM FamiSanarEncabezado WITH(NOLOCK)")
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def obtener_encabezados_paginado_famisanar(offset: int, limit: int):
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
            FROM FamiSanarEncabezado e
            LEFT JOIN FamiSanarDetalle d ON e.idEncabezado = d.idEncabezado
            LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
            GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
            ORDER BY e.fechaCargue DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, (offset, limit))
        return cursor.fetchall()
    finally:
        cursor.close(); conn.close()
