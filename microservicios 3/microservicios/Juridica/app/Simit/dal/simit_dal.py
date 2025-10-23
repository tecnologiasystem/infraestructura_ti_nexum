import pyodbc
from typing import List, Optional
from pydantic import BaseModel
from app.config.database import get_connection
from datetime import datetime

# -------------------------------------------------------------------------------------
# MODELOS DE DATOS
# -------------------------------------------------------------------------------------

class DetalleModel(BaseModel):
    cedula: str
    tipo: Optional[str]
    placa: Optional[str]
    secretaria: Optional[str]

class EncabezadoModel(BaseModel):
    """
    Modelo que representa el encabezado o agrupación de detalles de Simit.

    Campos:
    - automatizacion: Nombre o etiqueta que identifica el proceso o lote.
    - idUsuario: Identificador del usuario que realiza la carga.
    - fechaCargue: Fecha y hora cuando se realiza la carga de datos.
    - totalRegistros: Cantidad total de registros válidos para este encabezado.
    - detalles: Lista con objetos DetalleModel relacionados a este encabezado.
    """
    automatizacion: str
    idUsuario: int
    fechaCargue: datetime
    totalRegistros: int
    estado: Optional[str] = "En proceso"
    detalles: List[DetalleModel]

# -------------------------------------------------------------------------------------
# FUNCIONES DE ACCESO A DATOS (DAL)
# -------------------------------------------------------------------------------------

def insertar_encabezado(encabezado: EncabezadoModel) -> int:
    """
    Inserta un nuevo registro de encabezado en la tabla SimitEncabezado.

    Pasos:
    1. Obtiene conexión a base de datos.
    2. Inserta la información del encabezado usando SQL parametrizado para evitar inyección.
    3. Usa OUTPUT para capturar el idEncabezado generado automáticamente.
    4. Hace commit para guardar los cambios.
    5. Retorna el idEncabezado generado para uso posterior (relacionar detalles).
    6. En caso de error o falta de conexión, retorna -1.

    Importancia:
    - Es crucial guardar primero el encabezado para poder luego asociar
      los detalles a este id.
    - La función imprime el id generado para facilitar debugging.
    """
    conn = get_connection()
    if conn is None:
        return -1
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO SimitEncabezado (automatizacion, idUsuario, fechaCargue, totalRegistros, estado)
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
            # No se obtuvo id, algo falló
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
    Inserta un detalle asociado a un encabezado específico en la tabla SimitDetalle.

    Parámetros:
    - idEncabezado: id del encabezado al que pertenece el detalle.
    - detalle: objeto DetalleModel con la info a insertar.

    Pasos:
    1. Establece conexión con la base.
    2. Ejecuta el procedimiento almacenado SP_CRUD_SIMIT_DETALLE con acción 1 (insert).
    3. Envía todos los campos necesarios para el detalle.
    4. Hace commit para confirmar la inserción.
    5. Retorna (True, None) en éxito o (None, mensaje_error) en fallo.
    6. Incluye manejo de excepciones con traceback para debugging.

    Importancia:
    - Esta función asegura que cada detalle quede correctamente asociado a su encabezado.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            EXEC SP_CRUD_SIMIT_DETALLE 
                @accion=1,
                @idEncabezado=?, 
                @cedula=?, 
                @tipo=?, 
                @placa=?, 
                @secretaria=?
        """, idEncabezado, detalle.cedula, detalle.tipo, detalle.placa, detalle.secretaria)
        conn.commit()
        return True, None 
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def insertar_detalle_resultadoSimit(resultado: DetalleModel) -> bool:
    """
    Actualiza o inserta la información de detalle resultante de la automatización Simit.

    Proceso:
    1. Obtiene conexión y consulta todos los detalles asociados a la cédula dada.
    2. Busca un registro vacío (sin datos) para actualizar con la nueva info.
    3. Si encuentra un registro vacío, actualiza con los datos nuevos (acción 2).
    4. Si no hay registro vacío, obtiene el idEncabezado del primer detalle con esa cédula.
    5. Inserta un nuevo detalle con los datos proporcionados (acción 1).
    6. Hace commit y retorna True en éxito, False en fallo.
    7. Maneja excepciones con impresión detallada para depuración.

    Importancia:
    - Evita duplicidad actualizando registros vacíos.
    - Si no hay registros vacíos, agrega nuevos datos correctamente.
    """
    conn = get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        # Buscar todos los detalles con esa cédula
        cursor.execute("""
            SELECT idDetalle, tipo, placa, secretaria
            FROM SimitDetalle WITH(NOLOCK)
            WHERE cedula = ?
            ORDER BY numItem
        """, resultado.cedula)
        detalles = cursor.fetchall()

        # Buscar el primer registro completamente vacío
        detalle_vacio = None
        for detalle in detalles:
            id_detalle = detalle[0]
            campos = detalle[1:]
            # Revisa si todos los campos están vacíos o nulos
            if all(not campo or str(campo).strip() == "" for campo in campos):
                detalle_vacio = id_detalle
                break

        if detalle_vacio:
            idDetalle = detalle_vacio
            print("✅ Actualizando detalle existente con idDetalle =", idDetalle)

            # Actualiza registro vacío con datos nuevos
            cursor.execute("""
                EXEC SP_CRUD_SIMIT_DETALLE 
                    @accion=2,
                    @idDetalle=?,
                    @tipo=?,
                    @placa=?,
                    @secretaria=?
            """, (
                idDetalle,
                resultado.tipo,
                resultado.placa,
                resultado.secretaria
            ))
        else:
            # No hay detalle vacío, inserta uno nuevo
            cursor.execute("""
                SELECT TOP 1 idEncabezado 
                FROM SimitDetalle WITH(NOLOCK)
                WHERE cedula = ?
                ORDER BY idDetalle
            """, resultado.cedula)
            row = cursor.fetchone()
            if not row:
                # No encontró encabezado asociado, no puede insertar
                return False
            idEncabezado = row[0]

            cursor.execute("""
                EXEC SP_CRUD_SIMIT_DETALLE 
                    @accion=1,
                    @idEncabezado=?,
                    @cedula=?,
                    @tipo=?,
                    @placa=?,
                    @secretaria=?
            """, (
                idEncabezado,
                resultado.cedula,
                resultado.tipo,
                resultado.placa,
                resultado.secretaria
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
    Obtiene la lista completa de detalles junto con el encabezado, agrupados por cédula.

    Pasos:
    - Ejecuta consulta para obtener todos los detalles relacionados con sus encabezados.
    - Ordena por cédula para facilitar agrupación.
    - Convierte cada fila de resultado a diccionario con nombre de columnas.
    - Agrupa los detalles en un diccionario usando la cédula como clave.
    - Devuelve una lista con cada cédula y sus detalles asociados.
    - En caso de error o falta de conexión, retorna lista vacía.

    Utilidad:
    - Facilita visualizar o procesar todos los detalles por usuario.
    - Útil para reportes o exportaciones.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.cedula, d.*
            FROM SimitDetalle d
            INNER JOIN SimitEncabezado e ON d.idEncabezado = e.idEncabezado
            ORDER BY e.cedula
        """)

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        agrupado = {}
        for item in data:
            cedula = item["cedula"]
            if cedula not in agrupado:
                agrupado[cedula] = []
            agrupado[cedula].append(item)

        return [
            {"cedula": cedula, "detalles": detalles}
            for cedula, detalles in agrupado.items()
        ]

    except Exception as e:
        import traceback
        traceback.print_exc()
        return []

    finally:
        cursor.close()
        conn.close()

def obtener_detalles_agrupados_Simit():
    """
    Obtiene detalles que tienen datos no vacíos en al menos uno de los campos tipo, placa o secretaria.

    Pasos:
    - Consulta los detalles con condición de no estar vacíos en esos campos.
    - Ordena resultados por cédula.
    - Agrupa y devuelve en formato similar a obtener_detalles_agrupados.
    - Retorna lista vacía si falla conexión o hay error.

    Propósito:
    - Filtra registros con datos útiles para mostrar o procesar.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cedula, tipo, placa, secretaria
            FROM SimitDetalle WITH (NOLOCK)
            WHERE 
                ISNULL(tipo, '') <> '' OR 
                ISNULL(placa, '') <> '' OR 
                ISNULL(secretaria, '') <> ''
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

        return [
            {"cedula": cc, "detalles": detalles}
            for cc, detalles in agrupado.items()
        ]

    except Exception as e:
        import traceback
        traceback.print_exc()
        return []

    finally:
        cursor.close()
        conn.close()

def obtener_correo_usuarioSimit(id_usuario: int) -> str:
    """
    Obtiene el correo electrónico del usuario en base a su ID.

    Pasos:
    - Consulta la tabla UsuariosApp por el correo del usuario con idUsuarioApp igual a id_usuario.
    - Retorna el correo como string si existe, o None si no existe o falla la consulta.

    Utilidad:
    - Permite enviar notificaciones o alertas al usuario relacionadas con Simit.
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
    Obtiene los detalles de Simit que están asociados a un encabezado específico.

    Parámetros:
    - id_encabezado: identificador del encabezado por el cual filtrar.

    Pasos:
    - Ejecuta consulta filtrando por idEncabezado.
    - Ordena resultados por cédula para presentación ordenada.
    - Retorna lista con diccionarios que representan cada detalle encontrado.
    - Si no hay resultados o falla la conexión, retorna lista vacía.

    Aplicación:
    - Util para obtener detalles para un lote o tanda en particular.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cedula, tipo, placa, secretaria
            FROM SimitDetalle WITH (NOLOCK)
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
            FROM SimitEncabezado
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
            FROM SimitEncabezado
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
            UPDATE SimitEncabezado
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
            UPDATE SimitEncabezado
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
            UPDATE SimitEncabezado
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
    UPDATE dbo.SimitDetalle
    SET
      secretaria      = CASE WHEN secretaria      IS NULL OR secretaria      = '' THEN 'Pausado' ELSE secretaria      END
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
    UPDATE dbo.SimitDetalle
    SET
      secretaria      = CASE WHEN secretaria      = 'Pausado' THEN NULL ELSE secretaria     END
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