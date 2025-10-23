import pyodbc
from typing import List, Optional
from pydantic import BaseModel
from app.config.database import get_connection
from datetime import datetime

class DetalleModel(BaseModel):
    nombreCompleto: str
    departamento: Optional[str]
    ciudad: Optional[str]
    especialidad: Optional[str]
    idNombres: Optional[str]
    idDetalleJuridico: Optional[str]
    idActuaciones: Optional[str]
    
    
class EncabezadoModel(BaseModel):
    automatizacion: str
    idUsuario: int
    fechaCargue: datetime
    totalRegistros: int
    estado: Optional[str] = "En proceso"
    detalles: List[DetalleModel]

def insertar_detalle_resultadoJuridico(resultado: DetalleModel) -> bool:
    conn = get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        # Buscar detalles existentes para ese nombre
        cursor.execute("""
            SELECT idDetalle, idNombres, idDetalleJuridico, idActuaciones
            FROM JuridicoDetalle WITH(NOLOCK)
            WHERE nombreCompleto = ?
            ORDER BY numItem
        """, (resultado.nombreCompleto,))
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
                EXEC SP_CRUD_JuridicoDetalle
                    @Accion = 2,
                    @idDetalle = ? ,
                    @idNombres = ?,
                    @idDetalleJuridico = ?,
                    @idActuaciones = ?
            """, (
                idDetalle,
                resultado.idNombres,
                resultado.idDetalleJuridico,
                resultado.idActuaciones
            ))

        else:
            # Si no hay registro vacío, buscar idEncabezado
            cursor.execute("""
                SELECT TOP 1 idEncabezado
                FROM JuridicoDetalle WITH(NOLOCK)
                WHERE nombreCompleto = ?
                ORDER BY idDetalle
            """, (resultado.nombreCompleto,))
            row = cursor.fetchone()
            if not row:
                print("⚠️ No se encontró idEncabezado para nombreCompleto:", resultado.nombreCompleto)
                return False

            idEncabezado = row[0]

            # Crear un parámetro de salida para recibir el idDetalle generado
            idDetalle_output = cursor.execute("SELECT CAST(0 AS INT)").fetchval()

            cursor.execute("""
                DECLARE @idDetalle INT;
                EXEC SP_CRUD_JuridicoDetalle
                    @Accion = 1,
                    @idDetalle = @idDetalle OUTPUT,
                    @idEncabezado = ?,
                    @nombreCompleto = ?,
                    @departamento = ?,
                    @ciudad = ?,
                    @especialidad = ?,
                    @idNombres = ?,
                    @idDetalleJuridico = ?,
                    @idActuaciones = ?;
                SELECT @idDetalle;
            """, (
                idEncabezado,
                resultado.nombreCompleto,
                resultado.departamento,
                resultado.ciudad,
                resultado.especialidad,
                resultado.idNombres,
                resultado.idDetalleJuridico,
                resultado.idActuaciones
            ))

            nuevo_idDetalle = cursor.fetchone()[0]
            print("🆕 Se insertó nuevo detalle con idDetalle =", nuevo_idDetalle)

        conn.commit()
        return True

    except Exception as e:
        import traceback
        print("❌ Error en insertar_detalle_resultadoJuridico:")
        traceback.print_exc()
        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def obtener_Info_aConsultarJuridico():
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT TOP 1 
            e.idEncabezado,
             CAST(d.nombreCompleto AS VARCHAR(150)) AS nombreCompleto,
            CONVERT(VARCHAR(150), d.departamento, 120) AS departamento,
            CONVERT(VARCHAR(150), d.ciudad, 120) AS ciudad,
            CONVERT(VARCHAR(150), d.especialidad, 120) AS especialidad
                FROM JuridicoEncabezado e
        JOIN JuridicoDetalle d ON e.idEncabezado = d.idEncabezado
        WHERE (d.idNombres = '' OR d.idNombres IS NULL)
        ORDER BY NEWID ()

            """)
        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar SP: {e}"

    finally:
        cursor.close()
        conn.close()
        
#anterior juridico--------------------------------------------------------------------
def procesar_juridico_completo(json_data: dict) -> bool:

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Caso cuando no hay detalle ni actuaciones
        if json_data.detalle == "vacio":
            # Eliminar por nombre si es necesario
            cursor.execute("EXEC SP_CRUD_JuridicoDetalle @Accion = 3, @nombreCompleto = ?", 
                           (json_data.nombreCompleto))
            row = cursor.fetchone()
            if row:
                id_detalle = row[0]  # ← Aquí sí capturas el idDetalle  

            # Reemplaza "vacio" con None
            id_detalle_juridico = json_data.detalle
            id_actuaciones = json_data.actuaciones

            # Ejecuta la actualización de FKs
            cursor.execute("""
                EXEC SP_CRUD_JuridicoDetalle
                @Accion = 2,
                @idDetalle = ?, 
                @idDetalleJuridico = ?, 
                @idActuaciones = ?;
            """, (
                id_detalle,
                id_detalle_juridico,
                id_actuaciones
            ))
            conn.commit()
            return True
    except Exception as e:
        print("❌ Error en procesar_juridico_completo:", str(e))
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

#nombres juridico-----------------------------------------
def procesar_juridico_nombre(data: dict) -> Optional[int]:
    conn = get_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()

        cursor.execute("""
            DECLARE @idDetalle INT;
            EXEC SP_CRUD_NombreJuridico
                @Accion = 1,
                @idDetalle = @idDetalle OUTPUT,
                @idProceso = ?, 
                @idConexion = ?, 
                @llaveProceso = ?, 
                @fechaProceso = ?, 
                @fechaUltimaActuacion = ?, 
                @despacho = ?, 
                @departamento = ?, 
                @sujetosProcesales = ?, 
                @esPrivado = ?, 
                @cantFilas = ?;
            SELECT @idDetalle;
        """, (
            data.get("idProceso"),
            data.get("idConexion"),
            data.get("llaveProceso"),
            data.get("fechaProceso"),
            data.get("fechaUltimaActuacion"),
            data.get("despacho"),
            data.get("departamento"),
            data.get("sujetosProcesales"),
            data.get("esPrivado"),
            data.get("cantFilas")
        ))

        row = cursor.fetchone()
        conn.commit()
        return int(row[0]) if row else None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    finally:
        cursor.close()
        conn.close()


#detalle juridico-----------------------------------------
def procesar_juridico_detalle(data: dict) -> Optional[int]:
    conn = get_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()

        cursor.execute("""
            DECLARE @idDetalleJuridico INT;
            EXEC SP_CRUD_DetalleJuridico
                @Accion = 1,
                @idDetalleJuridico = @idDetalleJuridico OUTPUT,
                @idProceso = ?, 
                @llaveProceso = ?, 
                @idConexion = ?, 
                @esPrivado = ?, 
                @fechaProceso = ?, 
                @codDespachoCompleto = ?, 
                @despacho = ?, 
                @ponente = ?, 
                @tipoProceso = ?, 
                @claseProceso = ?, 
                @subclaseProceso = ?, 
                @recurso = ?, 
                @ubicacion = ?, 
                @contenidoRadicacion = ?, 
                @fechaConsulta = ?, 
                @ultimaActualizacion = ?;
            SELECT @idDetalleJuridico;
        """, (
            data.get("idProceso"),
            data.get("llaveProceso"),
            data.get("idConexion"),
            data.get("esPrivado"),
            data.get("fechaProceso"),
            data.get("codDespachoCompleto"),
            data.get("despacho"),
            data.get("ponente"),
            data.get("tipoProceso"),
            data.get("claseProceso"),
            data.get("subclaseProceso"),
            data.get("recurso"),
            data.get("ubicacion"),
            data.get("contenidoRadicacion"),
            data.get("fechaConsulta"),
            data.get("ultimaActualizacion")
        ))

        row = cursor.fetchone()
        conn.commit()
        return int(row[0]) if row else None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    finally:
        cursor.close()
        conn.close()

#actuaciones juridico-----------------------------------------
def procesar_juridico_actuaciones(data: dict) -> Optional[int]:
    conn = get_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()

        cursor.execute("""
            DECLARE @idActuacionesJuridico INT;
            EXEC SP_CRUD_ActuacionesJuridico
                @Accion = 1,
                @idActuacionesJuridico = @idActuacionesJuridico OUTPUT,
                @idProceso = ?, 
                @idRegActuacion = ?, 
                @llaveProceso = ?, 
                @consActuacion = ?, 
                @fechaActuacion = ?, 
                @actuacion = ?, 
                @anotacion = ?, 
                @fechaInicial = ?, 
                @fechaFinal = ?, 
                @fechaRegistro = ?, 
                @codRegla = ?, 
                @conDocumentos = ?, 
                @cant = ?;
            SELECT @idActuacionesJuridico;
        """, (
            data.get("idProceso"),
            data.get("idRegActuacion"),
            data.get("llaveProceso"),
            data.get("consActuacion"),
            data.get("fechaActuacion"),
            data.get("actuacion"),
            data.get("anotacion"),
            data.get("fechaInicial"),
            data.get("fechaFinal"),
            data.get("fechaRegistro"),
            data.get("codRegla"),
            data.get("conDocumentos"),
            data.get("cant")
        ))

        row = cursor.fetchone()
        conn.commit()
        return int(row[0]) if row else None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    finally:
        cursor.close()
        conn.close()
