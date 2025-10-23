from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from app.bll.chat_bll import (
    traerChatsBll,
    buscarPersonasBLL,
    registrar_actividad,
    traer_chats_grupo_bll,
    guardar_mensaje_grupo_bll,
    tiene_permiso_enviar_general,
    guardar_mensaje_general_bll,
    traer_mensajes_generales_bll
)
import os
import shutil

"""
Importa FastAPI Router y excepciones estándar,
así como funciones de la capa lógica BLL relacionadas con el sistema de chat.
"""

router = APIRouter()



"""
Este endpoint permite registrar un nuevo mensaje privado entre dos usuarios.

Internamente llama al procedimiento almacenado encargado de registrar la actividad del chat
privado, incluyendo el mensaje y cualquier archivo adjunto enviado.
"""
@router.post("/registrarMensaje")
async def registrar_mensaje_privado(payload: dict):
    try:
        error = registrar_actividad(
            usuario=payload["sender_id"],
            destinatario=payload["recipient_id"],
            mensaje=payload.get("message", "{adjunto}"),
            file=payload.get("file"),
            fileName=payload.get("fileName")
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}



"""
Este endpoint retorna todos los mensajes existentes entre dos usuarios específicos (usuario y destinatario),
lo cual permite reconstruir la conversación privada entre ambos.

El resultado se obtiene desde la lógica de negocio (BLL), la cual a su vez consulta la base de datos.
"""
@router.get("/traerChats")
def traer_chats(user_id: int = Query(...), recipient_id: int = Query(...)):
    datos, error = traerChatsBll(user_id, recipient_id)
    if error:
        raise HTTPException(status_code=500 if "Error" in error else 404, detail=error)
    return datos



"""
Este endpoint realiza una búsqueda de posibles usuarios con los que se puede iniciar una conversación.

La búsqueda se basa en un texto (query) y el usuario que realiza la consulta. Sirve como autocompletado
o filtro de personas disponibles en la plataforma.
"""
@router.get("/buscarPersonas")
async def buscar_personas(query: str = "", user_id: int = Query(...)):
    personas, error = buscarPersonasBLL(query, user_id)
    if error:
        raise HTTPException(status_code=500, detail=error)
    return personas



"""
Este endpoint retorna todos los mensajes grupales asociados a una campaña específica.

Los mensajes grupales están relacionados con una sala virtual representada por un ID de campaña.
"""
@router.get("/traerChatsGrupo")
def traer_chats_grupo(room: int = Query(...)):
    datos, error = traer_chats_grupo_bll(room)
    if error:
        raise HTTPException(status_code=500 if "Error" in error else 404, detail=error)
    return datos



"""
Permite registrar un mensaje en un chat grupal.

El destinatario se codifica como "grupo_{idCampana}" para identificarlo como un grupo dentro del sistema.
También se pueden incluir archivos adjuntos si aplica.
"""
@router.post("/guardarMensajeGrupo")
async def guardar_mensaje_grupal(payload: dict):
    try:
        registrar_actividad(
            usuario=payload["sender_id"],
            destinatario=f"grupo_{payload['idCampana']}",
            mensaje=payload.get("message", "{adjunto}"),
            file=payload.get("file"),
            fileName=payload.get("fileName")
        )
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}



"""
Este endpoint retorna la lista de usuarios que pertenecen a una campaña específica.

Es útil para mostrar quiénes están en el grupo de chat o quienes tienen permiso de visualización o participación.
"""
@router.get("/usuariosGrupo")
def obtener_usuarios_grupo(user_id: int = Query(...), idCampana: int = Query(...)):
    from app.bll.chat_bll import obtener_usuarios_de_campana_bll
    usuarios, error = obtener_usuarios_de_campana_bll(user_id, idCampana)
    if error:
        raise HTTPException(status_code=403, detail=error)
    return usuarios



"""
Este endpoint permite guardar un mensaje en el canal general del sistema,
pero solo si el usuario tiene permisos habilitados para realizar esa acción.

Además, se maneja cualquier error de validación o sistema al intentar guardar el mensaje.
"""
@router.post("/guardarMensajeGeneral")
async def guardar_mensaje_general(payload: dict):
    try:
        if not tiene_permiso_enviar_general(payload["sender_id"]):
            raise HTTPException(status_code=403, detail="No tiene permiso para enviar mensajes generales")
        success, error = guardar_mensaje_general_bll(payload)
        if error:
            raise HTTPException(status_code=500, detail=error)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}



"""
Obtiene todos los mensajes publicados en el canal general del sistema.

Este canal suele ser público o global para la empresa, y está disponible solo para lectura.
"""
@router.get("/traerMensajesGenerales")
async def traer_mensajes_generales():
    datos, error = traer_mensajes_generales_bll()
    if error:
        raise HTTPException(status_code=500, detail=error)
    return datos



"""
Valida si un usuario específico tiene permiso para enviar mensajes al canal general.

Esto es útil para controlar roles de comunicación masiva y evitar abusos del canal global.
"""
@router.get("/puedeEnviarMensajeGeneral/{id_usuario}")
async def puede_enviar_mensaje_general(id_usuario: int):
    try:
        permiso = tiene_permiso_enviar_general(id_usuario)
        return {"puedeEnviar": permiso}
    except Exception as e:
        return {"puedeEnviar": False, "error": str(e)}

