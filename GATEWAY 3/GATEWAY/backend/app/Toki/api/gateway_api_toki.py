from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Query, Body, Form
import httpx
from urllib.parse import unquote
from fastapi.responses import StreamingResponse,FileResponse
from config.microservices_config import MICRO_URLS
from typing import Dict, Optional, List
import io
import pandas as pd
from fastapi import Query
from starlette.responses import JSONResponse
from requests_toolbelt.multipart.encoder import MultipartEncoder
from fastapi.responses import Response
from pydantic import BaseModel
from starlette.responses import JSONResponse
from typing import Optional
import json, re, unicodedata
from pydantic import ValidationError 
import re
"""
Instancia de APIRouter para registrar rutas relacionadas con los microservicios.
"""
router = APIRouter()

# ---------- ENDPOINT: Chats ----------
"""
Endpoint: gateway_usuarios_grupo

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para usuarios grupo.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/usuariosGrupo", tags=["Chats"])
async def gateway_usuarios_grupo(user_id: int = Query(...), idCampana: int = Query(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['CHAT']}/chat/usuariosGrupo",
                params={"user_id": user_id, "idCampana": idCampana}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios del grupo: {str(e)}")
"""
Endpoint: gateway_get_chats

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para get chats.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/getChats", tags=["Chats"])
async def gateway_get_chats(user_id: str, recipient_id: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['CHAT']}/chat/traerChats",
                params={"user_id": user_id, "recipient_id": recipient_id}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al contactar microservicio de chat: {str(e)}")
"""
Endpoint: gateway_buscar_personas

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para buscar personas 

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/buscarPersonas", tags=["Chats"])
async def gateway_buscar_personas(
    query: str = Query(""),
    user_id: int = Query(None)  
):
    if user_id is None:
        raise HTTPException(status_code=400, detail="user_id es obligatorio")

    try:
        print('➡️ Entré a gateway con query:', query, 'y user_id:', user_id)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['CHAT']}/chat/buscarPersonas",
                params={"query": query, "user_id": user_id}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al contactar microservicio de chat: {str(e)}")
"""
Endpoint: gateway_traer_chats_grupo

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para traer chats grupo.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/traerChatsGrupo", tags=["Chats"])
async def gateway_traer_chats_grupo(room: int = Query(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['CHAT']}/chat/traerChatsGrupo",
                params={"room": room}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al contactar microservicio de chat (grupo): {str(e)}")
"""
Endpoint: gateway_registrar_mensaje_privado

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para registrar mensaje privado.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/registrarMensaje", tags=["Chats"])
async def gateway_registrar_mensaje_privado(payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MICRO_URLS['CHAT']}/chat/registrarMensaje",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar mensaje privado: {str(e)}")
"""
Endpoint: gateway_personas_agrupadas_por_campana

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para personas agrupadas por campana.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/chats/personasAgrupadas", tags=["Chats"])
async def gateway_personas_agrupadas_por_campana():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['CHAT']}/chat/personasAgrupadasPorCampana")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al contactar microservicio de chat: {str(e)}")

"""
Endpoint: gateway_guardar_mensaje_grupal

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para guardar mensaje grupal.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/guardarMensajeGrupo", tags=["Chats"])
async def gateway_guardar_mensaje_grupal(payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MICRO_URLS['CHAT']}/chat/guardarMensajeGrupo",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar mensaje grupal: {str(e)}")

"""
Endpoint: gateway_guardar_mensaje_general

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para guardar mensaje general.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/guardarMensajeGeneral", tags=["Chats"])
async def gateway_guardar_mensaje_general(payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MICRO_URLS['CHAT']}/chat/guardarMensajeGeneral",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar mensaje general: {str(e)}")

"""
Endpoint: gateway_traer_mensajes_generales

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/traerMensajesGenerales", tags=["Chats"])
async def gateway_traer_mensajes_generales():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['CHAT']}/chat/traerMensajesGenerales"
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al traer mensajes generales: {str(e)}")

@router.get("/puedeEnviarMensajeGeneral/{id_usuario}", tags=["Chats"])
async def gateway_puede_enviar_mensaje_general(id_usuario: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['CHAT']}/chat/puedeEnviarMensajeGeneral/{id_usuario}"
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al verificar permiso: {str(e)}")
