import pyodbc
from typing import List, Optional
from pydantic import BaseModel
from app.config.database import get_connection
from datetime import datetime

class DetalleModel(BaseModel):
    cedula: str

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
            INSERT INTO CamaraComercioEncabezado (automatizacion, idUsuario, fechaCargue, totalRegistros, estado)
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
            EXEC SP_CRUD_CAMARACOMERCIO_DETALLE 
                @accion=1,
                @idEncabezado=?, 
                @cedula=?
        """, idEncabezado, detalle.cedula)

        conn.commit()
        return True, None 
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def insertar_detalle_resultadoCamaraComercio(resultado: DetalleModel) -> bool:
    conn = get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TOP 1 idEncabezado
            FROM CamaraComercioEncabezado
            WHERE automatizacion = 'Camara de Comercio'
            ORDER BY fechaCargue DESC
        """)
        
        row = cursor.fetchone()
        if not row:
            print(f"❌ No se encontró encabezado CAMARA COMERCIO para cédula {resultado.cedula}")
            return False
            
        id_encabezado_reciente = row[0]
        print(f"🔍 Encabezado más reciente encontrado: {id_encabezado_reciente}")

        cursor.execute("""
            SELECT idDetalle, identificacion, primerNombre, segundoNombre, primerApellido,
                   segundoApellido, direccion, pais, departamento, municipio, telefono,
                   correo
            FROM CamaraComercioDetalle WITH(NOLOCK)
            WHERE cedula = ? AND idEncabezado = ?
            ORDER BY numItem
        """, resultado.cedula, id_encabezado_reciente)
        
        detalles = cursor.fetchall()

        detalle_vacio = None
        
        for detalle in detalles:
            id_detalle = detalle[0]
            campos = detalle[1:]
            
            if all(not campo or str(campo).strip() == "" for campo in campos):
                detalle_vacio = id_detalle
                break

        if detalle_vacio:
            print(f"✅ Actualizando detalle existente con idDetalle = {detalle_vacio} para cédula {resultado.cedula} en encabezado {id_encabezado_reciente}")

            cursor.execute("""
                EXEC SP_CRUD_CAMARACOMERCIO_DETALLE 
                    @accion=2,
                    @idDetalle=?,
                    @identificacion=?,
                    @primerNombre=?,
                    @segundoNombre=?,
                    @primerApellido=?,
                    @segundoApellido=?,
                    @direccion=?,
                    @pais=?,
                    @departamento=?,
                    @municipio=?,
                    @telefono=?,
                    @correo=?
            """, (
                detalle_vacio,
                resultado.identificacion,
                resultado.primerNombre,
                resultado.segundoNombre,
                resultado.primerApellido,
                resultado.segundoApellido,
                resultado.direccion,
                resultado.pais,
                resultado.departamento,
                resultado.municipio,
                resultado.telefono,
                resultado.correo
            ))
        else:
            print(f"✅ Insertando nuevo detalle para cédula {resultado.cedula} en encabezado más reciente {id_encabezado_reciente}")
            
            cursor.execute("""
                EXEC SP_CRUD_CAMARACOMERCIO_DETALLE 
                    @accion=1,
                    @idEncabezado=?,
                    @cedula=?,
                    @identificacion=?,
                    @primerNombre=?,
                    @segundoNombre=?,
                    @primerApellido=?,
                    @segundoApellido=?,
                    @direccion=?,
                    @pais=?,
                    @departamento=?,
                    @municipio=?,
                    @telefono=?,
                    @correo=?
            """, (
                id_encabezado_reciente,
                resultado.cedula,
                resultado.identificacion,
                resultado.primerNombre,
                resultado.segundoNombre,
                resultado.primerApellido,
                resultado.segundoApellido,
                resultado.direccion,
                resultado.pais,
                resultado.departamento,
                resultado.municipio,
                resultado.telefono,
                resultado.correo
            ))

        conn.commit()
        return True

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Error al insertar/actualizar detalle para cédula {resultado.cedula}: {str(e)}")
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
            SELECT e.cedula, d.*
            FROM CamaraComercioDetalle d
            INNER JOIN CamaraComercioEncabezado e ON d.idEncabezado = e.idEncabezado
            ORDER BY e.cedula
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

def obtener_detalles_agrupados_CamaraComercio():
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cedula, identificacion, primerNombre, segundoNombre,
                   primerApellido, segundoApellido, direccion, pais,
                   departamento, municipio, telefono, correo
            FROM CamaraComercioDetalle WITH (NOLOCK)
            WHERE 
                ISNULL(direccion, '') <> '' OR 
                ISNULL(pais, '') <> '' OR 
                ISNULL(departamento, '') <> '' OR 
                ISNULL(municipio, '') <> '' OR 
                ISNULL(telefono, '') <> '' OR 
                ISNULL(correo, '') <> ''
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

def obtener_correo_usuarioCamaraComercio(id_usuario: int) -> str:
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
            SELECT cedula, identificacion, primerNombre, segundoNombre,
                   primerApellido, segundoApellido, direccion, pais,
                   departamento, municipio, telefono, correo
            FROM CamaraComercioDetalle WITH (NOLOCK)
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
            FROM CamaraComercioEncabezado
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
            FROM CamaraComercioEncabezado
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
            UPDATE CamaraComercioEncabezado
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
            UPDATE CamaraComercioEncabezado
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
            UPDATE CamaraComercioEncabezado
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
    UPDATE dbo.CamaraComercioDetalle
    SET
      identificacion      = CASE WHEN identificacion      IS NULL OR identificacion      = '' THEN 'Pausado' ELSE identificacion      END
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
    UPDATE dbo.CamaraComercioDetalle
    SET
      identificacion      = CASE WHEN identificacion      = 'Pausado' THEN NULL ELSE identificacion     END
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