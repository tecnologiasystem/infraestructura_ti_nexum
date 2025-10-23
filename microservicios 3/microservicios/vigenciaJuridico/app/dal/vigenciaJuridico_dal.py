import pyodbc
from typing import List, Optional
from pydantic import BaseModel
from app.config.database import get_connection
from datetime import datetime

class DetalleModel(BaseModel):
    nombre: str
    cedula: str
    vigencia: Optional[str]
    fechaConsulta: Optional[str]
    
class EncabezadoModel(BaseModel):
    automatizacion: str
    idUsuario: int
    fechaCargue: datetime
    totalRegistros: int
    estado: Optional[str] = "En proceso"
    detalles: List[DetalleModel]

def insertar_detalle_resultadoVigencia(resultado: DetalleModel) -> bool:
    conn = get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT TOP 1 idDetalle
            FROM VigenciaDetalle WITH (UPDLOCK, ROWLOCK)
            WHERE cedula = ?
              AND (vigencia IS NULL OR LTRIM(RTRIM(vigencia)) = '')
              AND (fechaConsulta IS NULL OR LTRIM(RTRIM(fechaConsulta)) = '')
            ORDER BY idDetalle
        """, (resultado.cedula,))
        row = cursor.fetchone()

        if row:
            idDetalle = row[0]
            cursor.execute("""
                EXEC SP_CRUD_VIGENCIA_DETALLE
                    @accion = 2,
                    @idDetalle = ?,
                    @vigencia = ?,
                    @fechaConsulta = ?
            """, (idDetalle, resultado.vigencia, resultado.fechaConsulta))
        else:
            cursor.execute("""
                SELECT TOP 1 idEncabezado, ISNULL(nombre,'') AS nombre
                FROM VigenciaDetalle WITH (NOLOCK)
                WHERE cedula = ?
                ORDER BY idDetalle
            """, (resultado.cedula,))
            row = cursor.fetchone()
            if not row:
                idEncabezado = None
                nombre_final = resultado.nombre or ""
            else:
                idEncabezado, nombre_bd = row
                nombre_final = nombre_bd if nombre_bd.strip() != "" else (resultado.nombre or "")

            if idEncabezado is None:

                print("⚠️ No se encontró idEncabezado para la cédula:", resultado.cedula)
                return False

            cursor.execute("""
                DECLARE @idDetalle INT;
                EXEC SP_CRUD_VIGENCIA_DETALLE
                    @accion = 1,
                    @idDetalle = @idDetalle OUTPUT,
                    @idEncabezado = ?,
                    @nombre = ?,
                    @cedula = ?,
                    @vigencia = ?,
                    @fechaConsulta = ?;
                SELECT @idDetalle;
            """, (idEncabezado, nombre_final, resultado.cedula, resultado.vigencia, resultado.fechaConsulta))
            _ = cursor.fetchone()[0]  

        conn.commit()
        return True

    except Exception:
        import traceback
        print("❌ Error en insertar_detalle_resultadoVigencia:")
        traceback.print_exc()
        return False
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass


def obtener_CC_aConsultarVigencia():
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT TOP 1 
            e.idEncabezado,
             CAST(d.cedula AS VARCHAR(150)) AS cedula
                FROM VigenciaEncabezado e
        JOIN VigenciaDetalle d ON e.idEncabezado = d.idEncabezado
        WHERE (d.vigencia = '' OR d.vigencia IS NULL)
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
    