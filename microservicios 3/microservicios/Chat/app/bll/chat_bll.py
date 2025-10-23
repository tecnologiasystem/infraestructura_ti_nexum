from app.dal.chat_dal import (
    log_user_activity,
    traerChatsDAL,
    buscarPersonasDAL,
    obtener_campanas_usuario_dal,
    traer_chats_grupo_dal,
    guardar_mensaje_grupo_dal,
    guardar_mensaje_general_dal,
    traer_mensajes_generales_dal,
    obtener_permisos_usuario_dal
)
from datetime import datetime
import pytz

def crear_conversacion_id(user1_id, user2_id):
    """
    Genera un identificador único para una conversación entre dos usuarios.
    
    Parámetros:
    - user1_id, user2_id: IDs de los dos usuarios.

    Retorna:
    - Un string con formato: "menorID_mayorID" para mantener consistencia, 
      sin importar el orden de entrada.
    """
    return f"{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"

def registrar_actividad(usuario, destinatario, mensaje, file=None, fileName=None):
    """
    Registra la actividad de un usuario al enviar un mensaje.

    Parámetros:
    - usuario: ID del remitente.
    - destinatario: ID del receptor (otro usuario o grupo).
    - mensaje: contenido textual del mensaje.
    - file: contenido binario o codificado del archivo (opcional).
    - fileName: nombre del archivo adjunto (opcional).

    Lógica:
    - Se imprime en consola la actividad para monitoreo.
    - Se llama a la función `log_user_activity` del DAL con los parámetros adecuados.
      Se incluye la fecha actual con zona horaria de Bogotá.
    
    Retorna:
    - Resultado del proceso de guardado desde el DAL.
    """
    print(f"🧠 BLL → registrar_actividad: de {usuario} para {destinatario}, mensaje: {mensaje}, archivo:{fileName}")

    return log_user_activity(
        idUsuario=str(usuario),
        idDestinatario=str(destinatario),
        mensaje=mensaje,
        fecha=datetime.now(pytz.timezone('America/Bogota')),
        file=file,
        fileName=fileName,
    )

def traerChatsBll(idUsuario, recipient_id):
    """
    Obtiene el historial de chat entre un usuario y su destinatario (otro usuario).

    Parámetros:
    - idUsuario: ID del usuario solicitante.
    - recipient_id: ID del destinatario de la conversación.

    Retorna:
    - Lista de mensajes desde el DAL.
    """
    return traerChatsDAL(idUsuario, recipient_id)

def buscarPersonasBLL(nombre, idUsuarioApp):
    """
    Permite buscar otros usuarios por nombre, útil para autocompletar destinatarios.

    Parámetros:
    - nombre: texto parcial o completo del nombre a buscar.
    - idUsuarioApp: ID del usuario que está realizando la búsqueda.

    Retorna:
    - Resultados obtenidos desde el DAL.
    """
    return buscarPersonasDAL(nombre, idUsuarioApp)

def obtener_campanas_usuario_bll(id_usuario):
    """
    Retorna la lista de campañas a las que pertenece un usuario.

    Parámetros:
    - id_usuario: ID del usuario a consultar.

    Retorna:
    - Lista de IDs de campañas.
    """
    return obtener_campanas_usuario_dal(id_usuario)

def traer_chats_grupo_bll(idCampana):
    """
    Obtiene los mensajes enviados dentro de una campaña/grupo específico.

    Parámetros:
    - idCampana: ID de la campaña o sala.

    Retorna:
    - Lista de mensajes del grupo.
    """
    return traer_chats_grupo_dal(idCampana)

def guardar_mensaje_grupo_bll(payload):
    """
    Guarda un mensaje enviado a un grupo.

    Parámetros:
    - payload: diccionario con datos del mensaje (remitente, sala, contenido, archivo).

    Retorna:
    - Resultado del guardado desde el DAL.
    """
    return guardar_mensaje_grupo_dal(payload)

def obtener_usuarios_de_campana_bll(idUsuarioApp, idCampana):
    """
    Obtiene la lista de usuarios dentro de una campaña, solo si el solicitante es un coordinador.

    Parámetros:
    - idUsuarioApp: ID del usuario solicitante.
    - idCampana: ID de la campaña de interés.

    Lógica:
    - Primero se verifica si el usuario tiene rol de "coordinador" consultando el DAL.
    - Si es coordinador, se le permite consultar los usuarios de esa campaña.
    - En caso contrario, retorna error por no estar autorizado.

    Retorna:
    - Lista de usuarios en la campaña o un mensaje de error si no está autorizado.
    """
    from app.dal.chat_dal import obtener_usuarios_de_campana_dal, obtener_rol_usuario_dal

    rol, error = obtener_rol_usuario_dal(idUsuarioApp)
    if error or rol.lower() != "coordinador":
        return None, "No autorizado"

    return obtener_usuarios_de_campana_dal(idCampana)

def guardar_mensaje_general_bll(payload):
    """
    Guarda un mensaje general enviado a todos los usuarios.

    Parámetros:
    - payload: diccionario con datos del mensaje (remitente, contenido, archivo, etc.)

    Retorna:
    - Resultado del guardado desde el DAL.
    """
    return guardar_mensaje_general_dal(payload)

def traer_mensajes_generales_bll():
    """
    Recupera todos los mensajes generales disponibles en la plataforma.

    Retorna:
    - Lista de mensajes generales desde la base de datos.
    """
    return traer_mensajes_generales_dal()

def tiene_permiso_enviar_general(id_usuario):
    """
    Verifica si un usuario tiene permiso para enviar mensajes generales.

    Parámetros:
    - id_usuario: ID del usuario a verificar.

    Lógica:
    - Consulta todos los permisos del usuario.
    - Si el usuario tiene permiso de "crear" en la ruta "/mensajesGenerales", retorna True.
    - En cualquier otro caso (sin permisos o error), retorna False.

    Retorna:
    - True si tiene permiso de creación general, False en caso contrario.
    """
    permisos, error = obtener_permisos_usuario_dal(id_usuario)
    if error or not permisos:
        return False
    for p in permisos:
        if p['ruta'] == '/mensajesGenerales' and p['permisoCrear'] == 1:
            return True
    return False
