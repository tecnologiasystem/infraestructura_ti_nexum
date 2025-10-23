import pyodbc
from app.config.database import get_connection
from datetime import datetime
import pytz
import base64

def log_user_activity(idUsuario, idDestinatario, mensaje, fecha, file=None, fileName=None):
    """
    Registra una actividad de chat en la base de datos (mensaje privado o grupal).

    Parámetros:
    - idUsuario (str/int): ID del usuario que envía el mensaje.
    - idDestinatario (str): ID del destinatario (puede ser "grupo_<idCampana>").
    - mensaje (str): Contenido del mensaje.
    - fecha (datetime): Fecha y hora del envío.
    - file (bytes, opcional): Archivo adjunto en formato binario.
    - fileName (str, opcional): Nombre del archivo adjunto.

    Lógica:
    - Si el destinatario es un grupo, se extrae el ID de campaña del string.
    - Se ejecuta el procedimiento almacenado `sp_ChatMensajes` con la operación correspondiente.
    - Se valida que el destinatario privado sea numérico.
    - Se hace commit de la transacción.
    - Devuelve None si todo sale bien, o mensaje de error si ocurre una excepción.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        if isinstance(idDestinatario, str) and idDestinatario.startswith("grupo_"):
            idCampana = int(idDestinatario.replace("grupo_", ""))
            cursor.execute("""
                EXECUTE [sp_ChatMensajes] 
                    @Operacion=?, 
                    @idChat=?, 
                    @idRemitente=?, 
                    @idDestinatario=?, 
                    @mensaje=?, 
                    @fechaEnvio=?, 
                    @estado=?,
                    @idCampana=?,
                    @file=?,
                    @fileName=?
            """, 7, None, int(idUsuario), None, mensaje, fecha, 1, idCampana, file, fileName)
        else:
            if not str(idDestinatario).isdigit():
                raise ValueError("Destinatario debe ser un ID de usuario numérico")
            cursor.execute("""
                EXECUTE [sp_ChatMensajes] 
                    @Operacion=?, 
                    @idChat=?, 
                    @idRemitente=?, 
                    @idDestinatario=?,  
                    @mensaje=?, 
                    @fechaEnvio=?, 
                    @estado=?,
                    @idCampana=?,       
                    @file=?,
                    @fileName=?
            """, 1, None, int(idUsuario), int(idDestinatario), mensaje, fecha, 1, None, file, fileName)

        conn.commit()
        print("✅ Commit exitoso")
        return None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar SP: {e}"

    finally:
        cursor.close()
        conn.close()

def traerChatsDAL(idUsuario, recipient_id):
    """
    Trae los mensajes privados entre dos usuarios desde la base de datos.

    Parámetros:
    - idUsuario (int): Usuario que hace la consulta.
    - recipient_id (int): Usuario con quien conversa.

    Retorna:
    - Lista de mensajes (dict) si tiene éxito, o error si ocurre una excepción.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            EXECUTE [sp_ChatMensajes] @Operacion=?, @idRemitente=?,  @estado=?, @idDestinatario=?
        """, 5, idUsuario, 1, recipient_id)
        rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        data = [dict(zip(col_names, row)) for row in rows]
        return data, None
    except Exception as e:
        return None, f"Error al ejecutar SP: {e}"
    finally:
        cursor.close()
        conn.close()

def buscarPersonasDAL(nombre, idUsuarioApp):
    """
    Busca usuarios para chatear por nombre desde la base de datos.

    Parámetros:
    - nombre (str): Nombre a buscar.
    - idUsuarioApp (int): Usuario que realiza la búsqueda.

    Retorna:
    - Lista de usuarios coincidentes o mensaje de error.
    """
    conn = get_connection()
    if conn is None:
        return None, "❌ Error al conectar con la base de datos"

    try:
        cursor = conn.cursor()
        cursor.execute("""
            EXEC [sp_BuscarUsuariosChatsXNombre] @Accion=?, @idUsuarioApp=?, @Nombre=?
        """, 5, idUsuarioApp, nombre)
        rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        data = [dict(zip(col_names, row)) for row in rows]
        return data, None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"❌ Error al buscar personas: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_campanas_usuario_dal(id_usuario):
    """
    Obtiene las campañas a las que pertenece un usuario (para chats grupales).

    Parámetros:
    - id_usuario (int): ID del usuario.

    Retorna:
    - Lista de IDs de campañas como strings.
    """
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT idCampana FROM usuariosCampanas WHERE idUsuarioApp = ?
        """, id_usuario)
        rows = cursor.fetchall()
        return [str(row[0]) for row in rows]
    except Exception as e:
        import traceback
        traceback.print_exc()
        return []
    finally:
        cursor.close()
        conn.close()

def traer_chats_grupo_dal(idCampana):
    """
    Trae los mensajes grupales de una campaña específica.

    Parámetros:
    - idCampana (int): ID de la campaña.

    Retorna:
    - Lista de mensajes grupales (dict).
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            EXECUTE [sp_ChatMensajes] @Operacion=?, @idCampana=?, @estado=?
        """, 6, idCampana, 1)
        rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        data = [dict(zip(col_names, row)) for row in rows]
        return data, None
    except Exception as e:
        return None, f"Error al traer chats grupales: {e}"
    finally:
        cursor.close()
        conn.close()

def guardar_mensaje_grupo_dal(payload):
    """
    Guarda un mensaje grupal en la base de datos reutilizando `log_user_activity()`.

    Parámetros:
    - payload (dict): Información del mensaje grupal.

    Retorna:
    - Resultado de `log_user_activity`.
    """
    return log_user_activity(
        idUsuario=payload.get("sender_id"),
        idDestinatario=f"grupo_{payload.get('room')}",
        mensaje=payload.get("message", "{adjunto}"),
        fecha=datetime.now(pytz.timezone("America/Bogota")),
        file=payload.get("file"),
        fileName=payload.get("fileName"),
    )

def obtener_usuarios_de_campana_dal(id_campana):
    """
    Obtiene todos los usuarios de una campaña y su rol.

    Parámetros:
    - id_campana (int): ID de la campaña.

    Retorna:
    - Lista de usuarios (dict) con nombre y rol.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.idUsuarioApp, u.nombre, r.Rol
            FROM usuariosCampanas uc
            JOIN UsuariosApp u ON uc.idUsuarioApp = u.idUsuarioApp
            JOIN roles r ON u.idRol = r.idRol
            WHERE uc.idCampana = ?
        """, id_campana)

        rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        return [dict(zip(col_names, row)) for row in rows], None
    except Exception as e:
        return None, f"Error al obtener usuarios de campaña: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_rol_usuario_dal(id_usuario):
    """
    Devuelve el rol de un usuario según su ID.

    Parámetros:
    - id_usuario (int): ID del usuario.

    Retorna:
    - Rol del usuario (str), o mensaje de error.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error de conexión"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.rol FROM UsuariosApp u JOIN roles r ON u.idRol = r.idRol WHERE u.idUsuarioApp = ?
        """, id_usuario)
        row = cursor.fetchone()
        return row[0] if row else None, None
    except Exception as e:
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def guardar_mensaje_general_dal(payload):
    """
    Guarda un mensaje general (broadcast) en la base de datos.

    Parámetros:
    - payload (dict): Diccionario con los datos del mensaje general.

    Retorna:
    - True si todo fue exitoso, o mensaje de error.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO MensajesGenerales (idRemitente, mensaje, fechaEnvio, fileName, fileAdjunto)
            VALUES (?, ?, GETDATE(), ?, ?)
        """, payload["sender_id"], payload.get("message", "{adjunto}"), payload.get("fileName"), payload.get("fileAdjunto"))
        conn.commit()
        return True, None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al guardar mensaje general: {e}"
    finally:
        cursor.close()
        conn.close()

def traer_mensajes_generales_dal():
    """
    Retorna todos los mensajes generales (broadcast) guardados en la base de datos.

    Retorna:
    - Lista de mensajes con estructura de diccionario, o mensaje de error.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT mg.idMensaje, mg.idRemitente, u.nombre AS nombreRemitente,
                   mg.mensaje, mg.fechaEnvio, mg.fileName, mg.fileAdjunto
            FROM MensajesGenerales mg
            LEFT JOIN UsuariosApp u ON mg.idRemitente = u.idUsuarioApp
            ORDER BY mg.fechaEnvio ASC 
        """)
        rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        data = [dict(zip(col_names, row)) for row in rows]
        return data, None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al traer mensajes generales: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_permisos_usuario_dal(id_usuario):
    """
    Obtiene los permisos de menú de un usuario basándose en su rol asignado.

    Parámetros:
    - id_usuario (int): ID del usuario.

    Retorna:
    - Lista de permisos con flags de ver, crear, editar, eliminar.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT idRol FROM UsuariosApp WHERE idUsuarioApp = ?
        """, id_usuario)
        row = cursor.fetchone()
        if not row:
            return None, f"No se encontró el usuario {id_usuario}"
        idRol = row[0]

        cursor.execute("""
            SELECT id, ruta, permisoVer, permisoCrear, permisoEditar, permisoEliminar
            FROM permisosMenu
            WHERE idRol = ? AND estado = 1
        """, idRol)

        rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        permisos = [dict(zip(col_names, row)) for row in rows]

        return permisos, None

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al obtener permisos: {e}"

    finally:
        cursor.close()
        conn.close()

