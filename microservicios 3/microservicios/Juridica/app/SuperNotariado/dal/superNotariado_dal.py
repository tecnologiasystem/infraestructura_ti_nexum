import pyodbc
from typing import List, Optional
from pydantic import BaseModel
from app.config.database import get_connection
from datetime import datetime

# Modelos de datos para manejar la información de SuperNotariado

class DetalleModel(BaseModel):
    """
    Modelo que representa el detalle de un registro en SuperNotariado.
    Contiene:
    - CC: Identificación única (cedula)
    - ciudad: Ciudad asociada
    - matricula: Matrícula del registro
    - direccion: Dirección registrada
    - vinculadoA: Información adicional vinculada
    """
    CC: str
    ciudad: Optional[str] = None
    matricula: Optional[str] = None
    direccion: Optional[str] = None
    vinculadoA: Optional[str] = None

class EncabezadoModel(BaseModel):
    """
    Modelo que representa el encabezado o metadata del conjunto de detalles
    que se van a procesar.
    Contiene:
    - automatizacion: Nombre del proceso o automatización que genera estos datos
    - idUsuario: ID del usuario que carga la información
    - fechaCargue: Fecha y hora en que se hizo la carga
    - totalRegistros: Número total de detalles incluidos
    - detalles: Lista de objetos DetalleModel con la información específica
    """
    automatizacion: str
    idUsuario: int
    fechaCargue: datetime
    totalRegistros: int
    estado: Optional[str] = "En proceso"
    detalles: List[DetalleModel]

class ResultadoModel(BaseModel):
    """
    Modelo para recibir resultados o actualizaciones de la automatización.
    Contiene los mismos campos que DetalleModel, usualmente para actualizar detalles existentes.
    """
    CC: str
    ciudad: Optional[str] = None
    matricula: Optional[str] = None
    direccion: Optional[str] = None
    vinculadoA: Optional[str] = None


def insertar_encabezado(encabezado: EncabezadoModel) -> int:
    """
    Inserta un registro de encabezado en la base de datos.
    - Obtiene conexión y ejecuta inserción SQL con OUTPUT para obtener el id generado.
    - Si la inserción falla o no devuelve id, retorna -1.
    - Devuelve el id del encabezado insertado para usar en inserción de detalles.
    """
    conn = get_connection()
    if conn is None:
        return -1  # Error conexión
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO SuperNotariadoEncabezado (automatizacion, idUsuario, fechaCargue, totalRegistros, estado)
            OUTPUT INSERTED.idEncabezado
            VALUES (?, ?, ?, ?, ?)
        """, encabezado.automatizacion, encabezado.idUsuario, encabezado.fechaCargue, encabezado.totalRegistros, encabezado.estado)

        row = cursor.fetchone()
        conn.commit()

        if row:
            id_encabezado = int(row[0])
            print("✅ Insert directo exitoso:", id_encabezado)
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
    Inserta un detalle asociado a un encabezado específico.
    - Usa un procedimiento almacenado (SP_CRUD_SUPERNOTARIADO_DETALLE) con accion=1 para insertar.
    - Pasa todos los campos del detalle junto con el id del encabezado.
    - Confirma la transacción.
    - Retorna None o mensaje de error si falla la inserción.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            EXEC SP_CRUD_SUPERNOTARIADO_DETALLE 
                @accion=1,
                @idEncabezado=?, 
                @CC=?, 
                @ciudad=?, 
                @matricula=?, 
                @direccion=?, 
                @vinculadoA=?
        """, idEncabezado, detalle.CC, detalle.ciudad, detalle.matricula, detalle.direccion, detalle.vinculadoA)
        conn.commit()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar SP: {e}"
    finally:
        cursor.close()
        conn.close()


def crud_usuarios_consulta(accion: int, datos: dict = None):
    """
    Función general para operaciones CRUD sobre usuarios de consulta.
    - accion: Define la operación a ejecutar (1=insertar, 2=actualizar, 3=eliminar, 4=obtener por id, 5=otro, 6=listar todos).
    - datos: Diccionario con los datos necesarios para la operación.
    - Ejecuta procedimiento almacenado SP_CRUD_USUARIOSCONSULTA con los parámetros.
    - Dependiendo de la accion devuelve resultados:
      * Para insertar devuelve el id generado
      * Para obtener devuelve lista o registro
      * Para otros devuelve éxito o error.
    - Maneja excepciones y asegura cerrar conexiones.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    
    try:
        cursor = conn.cursor()

        params = {
            "idUsuarioConsulta": datos.get("idUsuarioConsulta") if datos else None,
            "correo": datos.get("correo") if datos else None,
            "usuario": datos.get("usuario") if datos else None,
            "contraseña": datos.get("contraseña") if datos else None,
            "estado": datos.get("estado") if datos else None,
            "fechaUso": datos.get("fechaUso") if datos else None,
        }

        cursor.execute("""
            EXEC SP_CRUD_USUARIOSCONSULTA 
                @accion=?, 
                @idUsuarioConsulta=?, 
                @correo=?, 
                @usuario=?, 
                @contraseña=?, 
                @estado=?, 
                @fechaUso=?
        """, accion, params["idUsuarioConsulta"], params["correo"], params["usuario"],
             params["contraseña"], params["estado"], params["fechaUso"])

        if accion == 1:
            # Insertar: retornar id generado
            row = cursor.fetchone()
            return {"idUsuarioConsulta": row[0]} if row else None
        elif accion in [4, 5, 6]:
            # Obtener registros o lista
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        else:
            # Actualizar o eliminar, confirma y retorna éxito
            conn.commit()
            return {"success": True}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar SP: {e}"

    finally:
        cursor.close()
        conn.close()


def insertar_detalle_resultado(resultado: ResultadoModel) -> bool:
    """
    Inserta o actualiza el detalle en base al resultado de la automatización.
    - Busca detalles existentes por CC y verifica si hay registros vacíos (sin matricula).
    - Si encuentra registro vacío, lo actualiza con nuevos datos.
    - Si no, busca el idEncabezado para insertar un nuevo registro.
    - Usa el SP_SPCRUD_SUPERNOTARIADO_DETALLE con accion=1 para insertar o accion=2 para actualizar.
    - Retorna True si la operación fue exitosa, False en caso contrario.
    """
    conn = get_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        # Buscar todos los detalles con esa CC
        cursor.execute("""
            SELECT idDetalle, matricula 
            FROM SuperNotariadoDetalle WITH(NOLOCK)
            WHERE CC = ?
            ORDER BY numItem
        """, resultado.CC)
        detalles = cursor.fetchall()

        detalle_vacio = None
        for detalle in detalles:
            if not detalle[1] or detalle[1].strip() == "":
                detalle_vacio = detalle
                break

        if detalle_vacio:
            idDetalle = detalle_vacio[0]
            print("Ejecutando actualización para idDetalle =", idDetalle)

            cursor.execute("""
                EXEC SP_CRUD_SUPERNOTARIADO_DETALLE 
                    @accion=?, 
                    @idDetalle=?, 
                    @ciudad=?, 
                    @matricula=?, 
                    @direccion=?, 
                    @vinculadoA=?
            """, 2, idDetalle, resultado.ciudad, resultado.matricula, resultado.direccion, resultado.vinculadoA)

        else:
            cursor.execute("""
                    SELECT TOP 1 idEncabezado 
                    FROM SuperNotariadoDetalle WITH(NOLOCK)
                    WHERE CC = ?
                    ORDER BY idDetalle
                """, resultado.CC)


            row = cursor.fetchone()
            if not row:
                print(f"❌ No se encontró idEncabezado para CC={resultado.CC} con matricula vacía")
                return False

            idEncabezado = row[0]

            cursor.execute("""
                EXEC SP_CRUD_SUPERNOTARIADO_DETALLE 
                    @accion=1,
                    @idEncabezado=?,
                    @CC=?,
                    @ciudad=?,
                    @matricula=?,
                    @direccion=?,
                    @vinculadoA=?
            """, idEncabezado, resultado.CC, resultado.ciudad, resultado.matricula, resultado.direccion, resultado.vinculadoA)

        conn.commit()
        return True

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False

    finally:
        cursor.close()
        conn.close()


def insertar_usuarios_desde_excel_df(df):
    """
    Inserta usuarios en la base desde un DataFrame de pandas.
    - Filtra usuarios válidos (que tengan Login no vacío).
    - Inserta en tabla usuariosConsulta con correo, usuario, contraseña, estado y fecha de uso actual.
    - Realiza commit para guardar los cambios.
    - Retorna True y cantidad de registros insertados, o False y mensaje de error.
    """
    conn = get_connection()
    if conn is None:
        return False, "Error al conectar a la base de datos"

    try:
        df = df[df["Login"].astype(str).str.strip() != ""]

        cursor = conn.cursor()

        for _, row in df.iterrows():
            correo = row.get("CORREOS", "").strip()
            usuario = row.get("Login", "").strip()
            contraseña = row.get("Contraseña", "").strip()
            estado = 1
            fechaUso = datetime.now()

            cursor.execute("""
                INSERT INTO [NEXUM].[dbo].[usuariosConsulta] 
                (correo, usuario, contraseña, estado, fechaUso)
                VALUES (?, ?, ?, ?, ?)
            """, correo, usuario, contraseña, estado, fechaUso)

        conn.commit()
        return True, len(df)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)

    finally:
        cursor.close()
        conn.close()


def obtener_y_ocupar_usuario():
    """
    Obtiene el primer usuario activo disponible y lo bloquea (estado=0).
    - Ejecuta un SP que obtiene y actualiza el primer usuario activo.
    - Retorna un diccionario con datos del usuario o None si no hay disponible.
    """
    conn = get_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()

        cursor.execute("EXEC dbo.sp_ObtenerYActualizarPrimerUsuarioActivo")
        row = cursor.fetchone()

        if not row:
            return None

        id_usuario, correo, usuario, contraseña = row
        fecha_uso = datetime.now()

        cursor.execute("""
            UPDATE [NEXUM].[dbo].[usuariosConsulta]
            SET estado = 0, fechaUso = ?
            WHERE idUsuarioConsulta = ?
        """, fecha_uso, id_usuario)

        conn.commit()

        return {
            "idUsuarioConsulta": id_usuario,
            "correo": correo,
            "usuario": usuario,
            "contraseña": contraseña,
            "estado": 0,
            "fechaUso": fecha_uso
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None

    finally:
        cursor.close()
        conn.close()


def obtener_detalles_agrupados():
    """
    Obtiene todos los detalles de SuperNotariado agrupados por CC (cedula).
    - Hace join entre detalle y encabezado para ordenar y agrupar.
    - Devuelve lista de diccionarios con cedula y lista de detalles asociados.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT CC, ciudad, matricula, direccion, vinculadoA
            FROM SuperNotariadoDetalle WITH (NOLOCK)
            ORDER BY CC
        """)

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        agrupado = {}
        for item in data:
            cc = item["CC"]
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


def obtener_correo_usuario(id_usuario: int) -> str:
    """
    Obtiene el correo electrónico asociado a un usuario dado su id.
    - Busca en la tabla UsuariosApp.
    - Retorna correo o None si no existe o error.
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
    Obtiene todos los detalles asociados a un encabezado específico.
    - Consulta en detalle filtrando por idEncabezado.
    - Devuelve lista de diccionarios con datos de cada detalle.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT CC, ciudad, matricula, direccion, vinculadoA
            FROM SuperNotariadoDetalle WITH (NOLOCK)
            WHERE idEncabezado = ?
            ORDER BY CC
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
            FROM SuperNotariadoEncabezado
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
            FROM SuperNotariadoEncabezado
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
            UPDATE SuperNotariadoEncabezado
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
            UPDATE SuperNotariadoEncabezado
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
            UPDATE SuperNotariadoEncabezado
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
    UPDATE dbo.SuperNotariadoDetalle
    SET
      matricula      = CASE WHEN matricula      IS NULL OR matricula      = '' THEN 'Pausado' ELSE matricula      END
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
    UPDATE dbo.SuperNotariadoDetalle
    SET
      matricula      = CASE WHEN matricula      = 'Pausado' THEN NULL ELSE matricula     END
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


    