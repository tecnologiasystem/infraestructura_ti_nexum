import pyodbc
from typing import List, Optional
from pydantic import BaseModel
from app.config.database import get_connection
from datetime import datetime

class DetalleModel(BaseModel):
    """
    Modelo que representa un registro detalle en la tabla RuntDetalle.
    Cada atributo es un campo que describe características del vehículo o registro.
    Algunos atributos son opcionales porque no siempre están presentes.
    Sirve para validar y estructurar los datos entrantes o almacenados.
    """
    cedula: str
    placaVehiculo: Optional[str]
    tipoServicio: Optional[str]
    estadoVehiculo: Optional[str]
    claseVehiculo: Optional[str]
    marca: Optional[str]
    modelo: Optional[str]
    numeroSerie: Optional[str]
    numeroChasis: Optional[str]
    cilindraje: Optional[str]
    tipoCombustible: Optional[str]
    autoridadTransito: Optional[str]
    linea: Optional[str]
    color: Optional[str]
    numeroMotor: Optional[str]
    numeroVIN: Optional[str]
    tipoCarroceria: Optional[str]
    polizaSOAT: Optional[str]
    revisionTecnomecanica: Optional[str]
    limitacionesPropiedad: Optional[str]
    garantiasAFavorDe: Optional[str]

class EncabezadoModel(BaseModel):
    """
    Modelo que representa un encabezado de lote o tanda en la tabla RuntEncabezado.
    Contiene información general del lote, como:
      - Tipo de automatización
      - Id del usuario que subió los datos
      - Fecha en que se cargó la tanda
      - Total de registros que contiene
      - Lista de detalles asociados (DetalleModel)
    Sirve para agrupar y manejar el conjunto de datos relacionados.
    """
    automatizacion: str
    idUsuario: int
    fechaCargue: datetime
    totalRegistros: int
    estado: Optional[str] = "En proceso" 
    detalles: List[DetalleModel]

def insertar_encabezado(encabezado: EncabezadoModel) -> int:
    """
    Inserta un registro de encabezado en la base de datos.

    Flujo:
      - Abre conexión a la base de datos.
      - Ejecuta un INSERT que retorna el idEncabezado generado.
      - Si la inserción es exitosa, devuelve el idEncabezado.
      - En caso de fallo devuelve -1.
      - Asegura cerrar cursor y conexión para evitar problemas de conexión.
    
    Parámetros:
      - encabezado: objeto con datos del lote a insertar.
    
    Retorna:
      - idEncabezado insertado o -1 si hubo error.
    
    Uso:
      Es el primer paso para crear una tanda y luego insertar sus detalles asociados.
    """
    conn = get_connection()
    if conn is None:
        return -1
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO RuntEncabezado (automatizacion, idUsuario, fechaCargue, totalRegistros, estado)
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
    Inserta un registro detalle en la base de datos vinculado a un encabezado.

    Flujo:
      - Abre conexión.
      - Ejecuta el procedimiento almacenado SP_CRUD_RUNT_DETALLE con acción=1 (insert).
      - Inserta todos los campos del detalle.
      - Confirma la transacción.
      - Retorna True y None si todo va bien.
      - Si ocurre error, retorna None y el mensaje del error.
      - Cierra conexión y cursor.

    Parámetros:
      - idEncabezado: ID de la tanda a la que pertenece el detalle.
      - detalle: objeto con los datos del detalle.

    Uso:
      Se llama una vez por cada detalle para guardarlos asociados a su encabezado.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            EXEC SP_CRUD_RUNT_DETALLE 
                @accion=1,
                @idEncabezado=?, 
                @cedula=?, 
                @placaVehiculo=?, 
                @tipoServicio=?, 
                @estadoVehiculo=?, 
                @claseVehiculo=?, 
                @marca=?, 
                @modelo=?, 
                @numeroSerie=?, 
                @numeroChasis=?, 
                @cilindraje=?, 
                @tipoCombustible=?, 
                @autoridadTransito=?, 
                @linea=?, 
                @color=?, 
                @numeroMotor=?, 
                @numeroVIN=?, 
                @tipoCarroceria=?, 
                @polizaSOAT=?, 
                @revisionTecnomecanica=?, 
                @limitacionesPropiedad=?, 
                @garantiasAFavorDe=?
        """, idEncabezado, detalle.cedula, detalle.placaVehiculo, detalle.tipoServicio,
            detalle.estadoVehiculo, detalle.claseVehiculo, detalle.marca, detalle.modelo,
            detalle.numeroSerie, detalle.numeroChasis, detalle.cilindraje, detalle.tipoCombustible,
            detalle.autoridadTransito, detalle.linea, detalle.color, detalle.numeroMotor,
            detalle.numeroVIN, detalle.tipoCarroceria, detalle.polizaSOAT,
            detalle.revisionTecnomecanica, detalle.limitacionesPropiedad, detalle.garantiasAFavorDe)

        conn.commit()
        return True, None 
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def insertar_detalle_resultadoRunt(resultado: DetalleModel) -> bool:
    """
    Actualiza o inserta información de un detalle RUNT a partir de un resultado recibido.

    Proceso:
      - Obtiene el encabezado más reciente en progreso (automatización RUNT).
      - Busca detalles de esa cédula SOLO en el encabezado más reciente.
      - Si encuentra un detalle vacío en el encabezado reciente, lo actualiza.
      - Si no encuentra detalle vacío, inserta uno nuevo en el encabezado más reciente.
      - Realiza commit y retorna True si todo salió bien.
      - Si ocurre algún error, retorna False.

    Parámetros:
      - resultado: datos que se desean actualizar o insertar.

    Uso:
      Mantiene los resultados organizados en el lote más reciente que está en progreso.
    """
    conn = get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        # Primero obtener el encabezado más reciente de RUNT
        cursor.execute("""
            SELECT TOP 1 idEncabezado
            FROM RuntEncabezado
            WHERE automatizacion = 'RUNT'
            ORDER BY fechaCargue DESC
        """)
        
        row = cursor.fetchone()
        if not row:
            print(f"❌ No se encontró encabezado RUNT para cédula {resultado.cedula}")
            return False
            
        id_encabezado_reciente = row[0]
        print(f"🔍 Encabezado más reciente encontrado: {id_encabezado_reciente}")

        # Buscar detalles de esta cédula SOLO en el encabezado más reciente
        cursor.execute("""
            SELECT idDetalle, placaVehiculo, tipoServicio, estadoVehiculo, claseVehiculo,
                   marca, modelo, numeroSerie, numeroChasis, cilindraje, tipoCombustible,
                   autoridadTransito, linea, color, numeroMotor, numeroVIN, tipoCarroceria,
                   polizaSOAT, revisionTecnomecanica, limitacionesPropiedad, garantiasAFavorDe
            FROM RuntDetalle WITH(NOLOCK)
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
                EXEC SP_CRUD_RUNT_DETALLE 
                    @accion=2,
                    @idDetalle=?,
                    @placaVehiculo=?,
                    @tipoServicio=?,
                    @estadoVehiculo=?,
                    @claseVehiculo=?,
                    @marca=?,
                    @modelo=?,
                    @numeroSerie=?,
                    @numeroChasis=?,
                    @cilindraje=?,
                    @tipoCombustible=?,
                    @autoridadTransito=?,
                    @linea=?,
                    @color=?,
                    @numeroMotor=?,
                    @numeroVIN=?,
                    @tipoCarroceria=?,
                    @polizaSOAT=?,
                    @revisionTecnomecanica=?,
                    @limitacionesPropiedad=?,
                    @garantiasAFavorDe=?
            """, (
                detalle_vacio,
                resultado.placaVehiculo,
                resultado.tipoServicio,
                resultado.estadoVehiculo,
                resultado.claseVehiculo,
                resultado.marca,
                resultado.modelo,
                resultado.numeroSerie,
                resultado.numeroChasis,
                resultado.cilindraje,
                resultado.tipoCombustible,
                resultado.autoridadTransito,
                resultado.linea,
                resultado.color,
                resultado.numeroMotor,
                resultado.numeroVIN,
                resultado.tipoCarroceria,
                resultado.polizaSOAT,
                resultado.revisionTecnomecanica,
                resultado.limitacionesPropiedad,
                resultado.garantiasAFavorDe
            ))
        else:
            # Insertar nuevo detalle en el encabezado más reciente
            print(f"✅ Insertando nuevo detalle para cédula {resultado.cedula} en encabezado más reciente {id_encabezado_reciente}")
            
            cursor.execute("""
                EXEC SP_CRUD_RUNT_DETALLE 
                    @accion=1,
                    @idEncabezado=?,
                    @cedula=?,
                    @placaVehiculo=?,
                    @tipoServicio=?,
                    @estadoVehiculo=?,
                    @claseVehiculo=?,
                    @marca=?,
                    @modelo=?,
                    @numeroSerie=?,
                    @numeroChasis=?,
                    @cilindraje=?,
                    @tipoCombustible=?,
                    @autoridadTransito=?,
                    @linea=?,
                    @color=?,
                    @numeroMotor=?,
                    @numeroVIN=?,
                    @tipoCarroceria=?,
                    @polizaSOAT=?,
                    @revisionTecnomecanica=?,
                    @limitacionesPropiedad=?,
                    @garantiasAFavorDe=?
            """, (
                id_encabezado_reciente,
                resultado.cedula,
                resultado.placaVehiculo,
                resultado.tipoServicio,
                resultado.estadoVehiculo,
                resultado.claseVehiculo,
                resultado.marca,
                resultado.modelo,
                resultado.numeroSerie,
                resultado.numeroChasis,
                resultado.cilindraje,
                resultado.tipoCombustible,
                resultado.autoridadTransito,
                resultado.linea,
                resultado.color,
                resultado.numeroMotor,
                resultado.numeroVIN,
                resultado.tipoCarroceria,
                resultado.polizaSOAT,
                resultado.revisionTecnomecanica,
                resultado.limitacionesPropiedad,
                resultado.garantiasAFavorDe
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
    """
    Obtiene todos los detalles RUNT junto con la información del encabezado.

    Proceso:
      - Realiza una consulta con JOIN para obtener datos completos.
      - Convierte los resultados a una lista de diccionarios.
      - Agrupa los registros por cédula.
      - Retorna la lista agrupada con formato:
        [{"cedula": "xxx", "detalles": [ {...}, {...} ]}, ...]

    Uso:
      Facilita la visualización y manejo de datos organizados por cliente.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.cedula, d.*
            FROM RuntDetalle d
            INNER JOIN RuntEncabezado e ON d.idEncabezado = e.idEncabezado
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

def obtener_detalles_agrupados_Runt():
    """
    Obtiene detalles RUNT pero solo con campos no vacíos en campos clave,
    para filtrar registros incompletos o vacíos.

    Proceso:
      - Consulta con filtros ISNULL para solo traer registros con datos significativos.
      - Agrupa y retorna la lista de datos agrupados por cédula.

    Uso:
      Mejora la calidad de los datos presentados o procesados.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cedula, placaVehiculo, tipoServicio, estadoVehiculo, claseVehiculo,
                   marca, modelo, numeroSerie, numeroChasis, cilindraje, tipoCombustible,
                   autoridadTransito, linea, color, numeroMotor, numeroVIN, tipoCarroceria,
                   polizaSOAT, revisionTecnomecanica, limitacionesPropiedad, garantiasAFavorDe
            FROM RuntDetalle WITH (NOLOCK)
            WHERE 
                ISNULL(placaVehiculo, '') <> '' OR 
                ISNULL(tipoServicio, '') <> '' OR 
                ISNULL(estadoVehiculo, '') <> '' OR 
                ISNULL(claseVehiculo, '') <> '' OR 
                ISNULL(marca, '') <> '' OR 
                ISNULL(modelo, '') <> '' OR 
                ISNULL(numeroChasis, '') <> ''
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

def obtener_correo_usuarioRunt(id_usuario: int) -> str:
    """
    Consulta el correo electrónico de un usuario por su ID.

    Proceso:
      - Consulta tabla UsuariosApp buscando el correo asociado al idUsuarioApp.
      - Retorna el correo si se encuentra.
      - Retorna None si no existe o ocurre error.

    Uso:
      Utilizado para enviar notificaciones o reportes al usuario correcto.
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
    Obtiene todos los detalles vinculados a un encabezado específico.

    Parámetros:
      - id_encabezado: ID de la tanda/lote de registros.

    Proceso:
      - Consulta la tabla RuntDetalle filtrando por idEncabezado.
      - Devuelve la lista de detalles en formato de diccionarios.
      - Retorna lista vacía si no encuentra o si ocurre error.

    Uso:
      Útil para extraer resultados de una tanda específica para exportación o análisis.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cedula, placaVehiculo, tipoServicio, estadoVehiculo,
                   claseVehiculo, marca, modelo, numeroSerie, numeroChasis,
                   cilindraje, tipoCombustible, autoridadTransito, linea, color,
                   numeroMotor, numeroVIN, tipoCarroceria, polizaSOAT, revisionTecnomecanica,
                   limitacionesPropiedad, garantiasAFavorDe
            FROM RuntDetalle WITH (NOLOCK)
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
            FROM RuntEncabezado
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
            FROM RuntEncabezado
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
            UPDATE RuntEncabezado
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
            UPDATE RuntEncabezado
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
            UPDATE RuntEncabezado
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
    UPDATE dbo.RuntDetalle
    SET
      placaVehiculo      = CASE WHEN placaVehiculo      IS NULL OR placaVehiculo      = '' THEN 'Pausado' ELSE placaVehiculo      END
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
    UPDATE dbo.RuntDetalle
    SET
      placaVehiculo      = CASE WHEN placaVehiculo      = 'Pausado' THEN NULL ELSE placaVehiculo     END
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