import pyodbc
from typing import List, Optional
from pydantic import BaseModel
from app.config.database import get_connection
from datetime import datetime

class DetalleModel(BaseModel):
    cedula: str
    radicado: Optional[str]
    proceso: Optional[str]
    departamento: Optional[str]
    coorporacion: Optional[str]
    distrito: Optional[str]
    despacho: Optional[str]
    telefono: Optional[str]
    correo: Optional[str]
    fechaProvidencia: Optional[str]
    tipoProceso: Optional[str]
    subclaseProceso: Optional[str]
    ciudad: Optional[str]
    especialidad: Optional[str]
    numeroDespacho: Optional[str]
    direccion: Optional[str]
    celular: Optional[str]
    fechaPublicacion: Optional[str]
    sujetos: Optional[str]
    actuaciones: Optional[str]

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
            INSERT INTO TybaEncabezado (automatizacion, idUsuario, fechaCargue, totalRegistros, estado)
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
            EXEC SP_CRUD_TYBA_DETALLE 
                @accion=1,
                @idEncabezado=?, 
                @cedula=?, 
                @radicado=?, 
                @proceso=?, 
                @departamento=?, 
                @coorporacion=?, 
                @distrito=?, 
                @despacho=?, 
                @telefono=?, 
                @correo=?, 
                @fechaProvidencia=?, 
                @tipoProceso=?, 
                @subclaseProceso=?, 
                @ciudad=?, 
                @especialidad=?, 
                @numeroDespacho=?, 
                @direccion=?, 
                @celular=?, 
                @fechaPublicacion=?, 
                @sujetos=?, 
                @actuaciones=?
        """, idEncabezado, detalle.cedula, detalle.radicado, detalle.proceso,
            detalle.departamento, detalle.coorporacion, detalle.distrito, detalle.despacho,
            detalle.telefono, detalle.correo, detalle.fechaProvidencia, detalle.tipoProceso,
            detalle.subclaseProceso, detalle.ciudad, detalle.especialidad, detalle.numeroDespacho,
            detalle.direccion, detalle.celular, detalle.fechaPublicacion,
            detalle.sujetos, detalle.actuaciones)

        conn.commit()
        return True, None 
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def insertar_detalle_resultadoTyba(resultado: DetalleModel) -> bool:
    conn = get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TOP 1 idEncabezado
            FROM TybaEncabezado
            WHERE automatizacion = 'TYBA'
            ORDER BY fechaCargue DESC
        """)
        
        row = cursor.fetchone()
        if not row:
            print(f"❌ No se encontró encabezado TYBA para cédula {resultado.cedula}")
            return False
            
        id_encabezado_reciente = row[0]
        print(f"🔍 Encabezado más reciente encontrado: {id_encabezado_reciente}")

        # Buscar detalles de esta cédula SOLO en el encabezado más reciente
        cursor.execute("""
            SELECT idDetalle, radicado, proceso, departamento, coorporacion,
                   distrito, despacho, telefono, correo, fechaProvidencia, tipoProceso,
                   subclaseProceso, ciudad, especialidad, numeroDespacho, direccion, celular,
                   fechaPublicacion, sujetos, actuaciones
            FROM TybaDetalle WITH(NOLOCK)
            WHERE cedula = ? AND idEncabezado = ?
            ORDER BY numItem
        """, resultado.cedula, id_encabezado_reciente)
        
        detalles = cursor.fetchall()

        # Buscar primer detalle vacío en el encabezado reciente
        detalle_vacio = None
        
        for detalle in detalles:
            id_detalle = detalle[0]
            campos = detalle[1:]  # Los campos de datos (sin idDetalle)
            
            if all(not campo or str(campo).strip() == "" for campo in campos):
                detalle_vacio = id_detalle
                break

        if detalle_vacio:
            # Actualizar el detalle vacío encontrado
            print(f"✅ Actualizando detalle existente con idDetalle = {detalle_vacio} para cédula {resultado.cedula} en encabezado {id_encabezado_reciente}")

            cursor.execute("""
                EXEC SP_CRUD_TYBA_DETALLE 
                    @accion=2,
                    @idDetalle=?,
                    @radicado=?, 
                    @proceso=?, 
                    @departamento=?, 
                    @coorporacion=?, 
                    @distrito=?, 
                    @despacho=?, 
                    @telefono=?, 
                    @correo=?, 
                    @fechaProvidencia=?, 
                    @tipoProceso=?, 
                    @subclaseProceso=?, 
                    @ciudad=?, 
                    @especialidad=?, 
                    @numeroDespacho=?, 
                    @direccion=?, 
                    @celular=?, 
                    @fechaPublicacion=?, 
                    @sujetos=?, 
                    @actuaciones=?
            """, (
                detalle_vacio,
                resultado.radicado,
                resultado.proceso,
                resultado.departamento,
                resultado.coorporacion,
                resultado.distrito,
                resultado.despacho,
                resultado.telefono,
                resultado.correo,
                resultado.fechaProvidencia,
                resultado.tipoProceso,
                resultado.subclaseProceso,
                resultado.ciudad,
                resultado.especialidad,
                resultado.numeroDespacho,
                resultado.direccion,
                resultado.celular,
                resultado.fechaPublicacion,
                resultado.sujetos,
                resultado.actuaciones
            ))
        else:
            # Insertar nuevo detalle en el encabezado más reciente
            print(f"✅ Insertando nuevo detalle para cédula {resultado.cedula} en encabezado más reciente {id_encabezado_reciente}")
            
            cursor.execute("""
                EXEC SP_CRUD_TYBA_DETALLE 
                    @accion=1,
                    @idEncabezado=?,
                    @cedula=?,
                    @radicado=?, 
                    @proceso=?, 
                    @departamento=?, 
                    @coorporacion=?, 
                    @distrito=?, 
                    @despacho=?, 
                    @telefono=?, 
                    @correo=?, 
                    @fechaProvidencia=?, 
                    @tipoProceso=?, 
                    @subclaseProceso=?, 
                    @ciudad=?, 
                    @especialidad=?, 
                    @numeroDespacho=?, 
                    @direccion=?, 
                    @celular=?, 
                    @fechaPublicacion=?, 
                    @sujetos=?, 
                    @actuaciones=?
            """, (
                id_encabezado_reciente,
                resultado.cedula,
                resultado.radicado,
                resultado.proceso,
                resultado.departamento,
                resultado.coorporacion,
                resultado.distrito,
                resultado.despacho,
                resultado.telefono,
                resultado.correo,
                resultado.fechaProvidencia,
                resultado.tipoProceso,
                resultado.subclaseProceso,
                resultado.ciudad,
                resultado.especialidad,
                resultado.numeroDespacho,
                resultado.direccion,
                resultado.celular,
                resultado.fechaPublicacion,
                resultado.sujetos,
                resultado.actuaciones
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
            FROM TybaDetalle d
            INNER JOIN TybaEncabezado e ON d.idEncabezado = e.idEncabezado
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

def obtener_detalles_agrupados_Tyba():
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cedula, radicado, proceso, departamento, coorporacion,
                   distrito, despacho, telefono, correo, fechaProvidencia, tipoProceso,
                   subclaseProceso, ciudad, especialidad, numeroDespacho, direccion, celular,
                   fechaPublicacion, sujetos, actuaciones
            FROM TybaDetalle WITH (NOLOCK)
            WHERE 
                ISNULL(proceso, '') <> '' OR 
                ISNULL(departamento, '') <> '' OR 
                ISNULL(coorporacion, '') <> '' OR 
                ISNULL(despacho, '') <> '' OR 
                ISNULL(telefono, '') <> '' OR 
                ISNULL(correo, '') <> '' OR 
                ISNULL(fechaProvidencia, '') <> ''
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

def obtener_correo_usuarioTyba(id_usuario: int) -> str:
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
            SELECT cedula, radicado, proceso, departamento, coorporacion,
                   distrito, despacho, telefono, correo, fechaProvidencia, tipoProceso,
                   subclaseProceso, ciudad, especialidad, numeroDespacho, direccion, celular,
                   fechaPublicacion, sujetos, actuaciones
            FROM TybaDetalle WITH (NOLOCK)
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
            FROM TybaEncabezado
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
            FROM TybaEncabezado
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
            UPDATE TybaEncabezado
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
            UPDATE TybaEncabezado
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
            UPDATE TybaEncabezado
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
    UPDATE dbo.TybaDetalle
    SET
      radicado      = CASE WHEN radicado      IS NULL OR radicado      = '' THEN 'Pausado' ELSE radicado      END
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
    UPDATE dbo.TybaDetalle
    SET
      radicado      = CASE WHEN radicado      = 'Pausado' THEN NULL ELSE radicado     END
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