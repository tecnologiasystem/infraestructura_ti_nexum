from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Query, Body, Form
import httpx
from urllib.parse import unquote
from fastapi.responses import StreamingResponse,FileResponse, Any
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
from api.monitor_rpa import notificacion as monitor_notificacion
from bll.monitor_rpa_bll import obtener_dashboard, listar_encabezados_rpa, listar_detalles_rpa_paginados, listar_todos_detalles_por_origen, buscar_detalle_por_cedulaBLL
from bll.gateway_bll_connect import (
    obtener_permisos_por_usuarioBLL,
    obtener_permisos_por_rolBLL,
    obtener_todos_los_permisosBLL,
    obtener_permiso_por_idBLL,
    crear_permiso_menuBLL,
    editar_permiso_menuBLL,
    eliminar_permiso_menuBLL
)
import traceback
import tempfile
import os
from typing import Optional
import json, re, unicodedata
from pydantic import ValidationError 
import re

router = APIRouter()

@router.get("/")
def get_all_permisos():
    data, error = obtener_todos_los_permisosBLL()
    if error:
        raise HTTPException(status_code=500, detail=error)
    return data

"""
Endpoint: get_permisos_por_usuario

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para obtener permisos por usuario.
Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.

"""

@router.get("/porUsuario")
def get_permisos_por_usuario(idUsuarioApp: int = Query(...)):
    data, error = obtener_permisos_por_usuarioBLL(idUsuarioApp)
    if error:
        raise HTTPException(status_code=500, detail=error)
    return data

"""
Endpoint: get_permisos_por_rol

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para obtener permisos por rol

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""

@router.get("/porRol")
def get_permisos_por_rol(idRol: int = Query(...)):
    print(idRol)
    data, error = obtener_permisos_por_rolBLL(idRol)
    if error:
        raise HTTPException(status_code=500, detail=error)
    return data

"""
Endpoint: get_permiso_por_id

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para obtener permiso por id.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""

@router.get("/permisos/{id}")
def get_permiso_por_id(id: int):
    data, error = obtener_permiso_por_idBLL(id)
    if error:
        raise HTTPException(status_code=500, detail=error)
    return data
"""
Endpoint: crear_permiso

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para crear permiso menu.
~~~~~~~
Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/")
def crear_permiso(data: dict = Body(...)):
    data, error = crear_permiso_menuBLL(data)
    if error:
        raise HTTPException(status_code=500, detail=error)
    return {"success": True, "data": data}
"""
Endpoint: editar_permiso

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para editar permiso menu.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.put("/{id}")
def editar_permiso(id: int, data: dict = Body(...)):
    print(id, data)
    data, error = editar_permiso_menuBLL(id, data)
    if error:
        raise HTTPException(status_code=500, detail=error)
    return {"success": True, "data": data}
"""
Endpoint: eliminar_permiso

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para eliminar permiso menu.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.delete("/{id}")
def eliminar_permiso(id: int):
    data, error = eliminar_permiso_menuBLL(id)
    if error:
        raise HTTPException(status_code=500, detail=error)
    return {"success": True}

# ----- USUARIOS -----
"""
Endpoint: gateway_obtener_usuarios

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para obtener usuarios

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/usuarios/dar", tags=["Usuarios"])
async def gateway_obtener_usuarios():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['ADMINISTRACION']}/usuarios/dar")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

"""
Endpoint: gateway_obtener_usuarioID

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para obtener usuarios por ID.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/usuarios/darConID", tags=["Usuarios"])
async def gateway_obtener_usuarioID(idUsuario: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['ADMINISTRACION']}/usuarios/darConID", params={"idUsuario": idUsuario})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_crear_usuario

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para crear usuario.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/usuarios/crear", tags=["Usuarios"])
async def gateway_crear_usuario(usuario: Dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['ADMINISTRACION']}/usuarios/crear", json=usuario)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_editar_usuario

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para editar usuario.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.put("/usuarios/editar", tags=["Usuarios"])
async def gateway_editar_usuario(usuario: Dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{MICRO_URLS['ADMINISTRACION']}/usuarios/editar", json=usuario)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_eliminar_usuario

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para eliminar usuario.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.put("/usuarios/eliminar", tags=["Usuarios"])
async def gateway_eliminar_usuario(usuario: Dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{MICRO_URLS['ADMINISTRACION']}/usuarios/eliminar", json=usuario)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_activar_usuario

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para activar usuario.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.put("/usuarios/activar", tags=["Usuarios"])
async def gateway_activar_usuario(usuario: Dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{MICRO_URLS['ADMINISTRACION']}/usuarios/activar", json=usuario)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ----- CAMPANAS -----
"""
Endpoint: gateway_listar_campanas

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para listar campanas.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/campanas/dar", tags=["Campanas"])
async def gateway_listar_campanas():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MICRO_URLS['ADMINISTRACION']}/campanas/dar")
        response.raise_for_status()
        return response.json()
"""
Endpoint: gateway_crear_campana

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para crear campana.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/campanas/crear", tags=["Campanas"])
async def gateway_crear_campana(campana: Dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MICRO_URLS['ADMINISTRACION']}/campanas/crear", json=campana)
        response.raise_for_status()
        return response.json()
"""
Endpoint: gateway_editar_campana

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para editar campana.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.put("/campanas/editar", tags=["Campanas"])
async def gateway_editar_campana(campana: Dict):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{MICRO_URLS['ADMINISTRACION']}/campanas/editar", json=campana)
        response.raise_for_status()
        return response.json()
"""
Endpoint: gateway_eliminar_campana

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para eliminar campana.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.put("/campanas/eliminar", tags=["Campanas"])
async def gateway_eliminar_campana(campana: Dict):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{MICRO_URLS['ADMINISTRACION']}/campanas/eliminar", json=campana)
        response.raise_for_status()
        return response.json()
"""
Endpoint: gateway_activar_campana

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para activar campana.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.put("/campanas/activar", tags=["Campanas"])
async def gateway_activar_campana(campana: Dict):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{MICRO_URLS['ADMINISTRACION']}/campanas/activar", json=campana)
        response.raise_for_status()
        return response.json()

# ----- AREAS -----
"""
Endpoint: gateway_listar_areas

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para listar areas.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/areas/dar", tags=["Areas"])
async def gateway_listar_areas():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MICRO_URLS['ADMINISTRACION']}/areas/dar")
        response.raise_for_status()
        return response.json()
"""
Endpoint: gateway_crear_area

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente crear area.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/areas/crear", tags=["Areas"])
async def gateway_crear_area(area: Dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MICRO_URLS['ADMINISTRACION']}/areas/crear", json=area)
        response.raise_for_status()
        return response.json()
"""
Endpoint: gateway_editar_area

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para editar areas.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.put("/areas/editar", tags=["Areas"])
async def gateway_editar_area(area: Dict):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{MICRO_URLS['ADMINISTRACION']}/areas/editar", json=area)
        response.raise_for_status()
        return response.json()
"""
Endpoint: gateway_eliminar_area

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para eliminar area.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.put("/areas/eliminar", tags=["Areas"])
async def gateway_eliminar_area(area: Dict):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{MICRO_URLS['ADMINISTRACION']}/areas/eliminar", json=area)
        response.raise_for_status()
        return response.json()
"""
Endpoint: gateway_activar_area

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente activar area.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.put("/areas/activar", tags=["Areas"])
async def gateway_activar_area(area: Dict):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{MICRO_URLS['ADMINISTRACION']}/areas/activar", json=area)
        response.raise_for_status()
        return response.json()

# ----- ROLES -----
"""
Endpoint: gateway_listar_roles

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para listar roles.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/roles/dar", tags=["Roles"])
async def gateway_listar_roles():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MICRO_URLS['ADMINISTRACION']}/roles/dar")
        response.raise_for_status()
        return response.json()
"""
Endpoint: gateway_crear_rol

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para crear rol.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/roles/crear", tags=["Roles"])
async def gateway_crear_rol(rol: Dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MICRO_URLS['ADMINISTRACION']}/roles/crear", json=rol)
        response.raise_for_status()
        return response.json()
"""
Endpoint: gateway_editar_rol

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para editar rol.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.put("/roles/editar", tags=["Roles"])
async def gateway_editar_rol(rol: Dict):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{MICRO_URLS['ADMINISTRACION']}/roles/editar", json=rol)
        response.raise_for_status()
        return response.json()
"""
Endpoint: gateway_eliminar_rol

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para eliminar rol.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.put("/roles/eliminar", tags=["Roles"])
async def gateway_eliminar_rol(rol: Dict):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{MICRO_URLS['ADMINISTRACION']}/roles/eliminar", json=rol)
        response.raise_for_status()
        return response.json()
"""
Endpoint: gateway_activar_rol

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para activar rol.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.put("/roles/activar", tags=["Roles"])
async def gateway_activar_rol(rol: Dict):
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{MICRO_URLS['ADMINISTRACION']}/roles/activar", json=rol)
        response.raise_for_status()
        return response.json()

# ----- usuarios Campañas -------
"""
Endpoint: listar

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/usuariosCampanas/dar", tags=["Usuario - Campañas"])
async def listar():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['ADMINISTRACION']}/usuariosCampanas/listar")
            response.raise_for_status()  # Lanza excepción si status >= 400
            return response.json()
    except httpx.HTTPStatusError as http_err:
        return JSONResponse(
            status_code=http_err.response.status_code,
            content={"error": f"Error en microservicio ADMINISTRACION: {http_err.response.text}"}
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: crear

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para crear usuario.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/usuariosCampanas/crear", tags=["Usuario - Campañas"])
async def crear(request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{MICRO_URLS['ADMINISTRACION']}/usuariosCampanas/crear", json=body)
        return response.json()
"""
Endpoint: actualizar

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para actualizar usuario.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.put("/usuariosCampanas/actualizar", tags=["Usuario - Campañas"])
async def actualizar(request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.put(f"{MICRO_URLS['ADMINISTRACION']}/usuariosCampanas/actualizar", json=body)
        return response.json()
"""
Endpoint: eliminar

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para eliminar usuario.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.delete("/usuariosCampanas/eliminar", tags=["Usuario - Campañas"])
async def eliminar(request: Request):
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.request("DELETE", f"{MICRO_URLS['ADMINISTRACION']}/usuariosCampanas/eliminar", json=body)
        return response.json()
"""
Endpoint: asignar_campanas

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para asignar usuario.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.put("/usuariosCampanas/asignar", tags=["Usuario - Campañas"])
async def asignar_campanas(request: Request):
    try:
        body = await request.json()
        async with httpx.AsyncClient() as client:
            response = await client.request("PUT", f"{MICRO_URLS['ADMINISTRACION']}/usuariosCampanas/asignar", json=body)
        return response.json()
    except Exception as e:
        return {"detail": str(e)}

# ----- SMS -----
"""
Endpoint: gateway_enviar_sms_individual

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para enviar sms individual.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/sms/enviar_individual", tags=["SMS"])
async def gateway_enviar_sms_individual(payload: Dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['NOTIFICACIONES']}/sms/sms_send", json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_enviar_sms_masivo

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para enviar sms masivo.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/sms/enviar_masivo", tags=["SMS"])
async def gateway_enviar_sms_masivo(archivo: UploadFile = File(...)):
    try:
        file_content = await archivo.read()

        form_data = MultipartEncoder(
            fields={"archivo": (archivo.filename, file_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

        headers = {"Content-Type": form_data.content_type}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MICRO_URLS['NOTIFICACIONES']}/sms/sms/send_excel",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
#-------- GRAFICOS--------
"""
Endpoint: gateway_usuarios_por_campana

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para usuarios_por_campana.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/graficos/usuarios_por_campana", tags=["Gráficos"])
async def gateway_usuarios_por_campana():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['GRAFICOS']}/usuarios_por_campana")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_usuarios_por_rol

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para usuarios_por_rol.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/graficos/usuarios_por_rol", tags=["Gráficos"])
async def gateway_usuarios_por_rol():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['GRAFICOS']}/usuarios_por_rol")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_logs_por_dia

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente logs_por_dia.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/graficos/logs_por_dia", tags=["Gráficos"])
async def gateway_logs_por_dia():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['GRAFICOS']}/logs_por_dia")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print("🔥 Error en /graficos/logs_por_dia:", traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})


#----------- LOGS----------------
"""
Endpoint: gateway_ver_logs

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para ver_logs.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/logs/iniciosesion", tags=["Logs"])
async def gateway_ver_logs():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['ADMINISTRACION']}/logs/iniciosesion")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

"""
Endpoint: gateway_exportar_logs

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para exportar_logs.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/logs/iniciosesion/exportar", tags=["Logs"])
async def gateway_exportar_logs(
    usuario: str = Query(""),
    desde: str = Query(""),
    hasta: str = Query("")
):
    async with httpx.AsyncClient() as client:
        request = client.build_request(
            "GET",
            f"{MICRO_URLS['ADMINISTRACION']}/logs/iniciosesion/exportar",
            params={"usuario": usuario, "desde": desde, "hasta": hasta}
        )
        response = await client.send(request)

        return Response(
            content=response.content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=logs_inicio_sesion.xlsx"}
        )

#------------ EXCEL CONVERTIDO------------
"""
Endpoint: gateway_procesar_excel_conversor

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para procesar_excel_conversor.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/excel/conversor", tags=["Excel - Conversor"])
async def gateway_procesar_excel_conversor(
    archivo: UploadFile = File(...),
    columnas: str = Form("Saldo total, Capital, Oferta 1, Oferta 2, Oferta 3, Hasta 3 cuotas, Hasta 6 cuotas, Hasta 12 Cuotas, Pago Flexible, Cap consolidado, Saldo Total Cons, 6 Cuotas, 12 cuotas"),
    modo: str = Form("numerico")):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            contents = await archivo.read()
            tmp.write(contents)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            files = {
                "archivo": (archivo.filename, f, archivo.content_type)
            }
            data = {
                "columnas": columnas,
                "modo": modo
            }

            timeout = httpx.Timeout(900.0, connect=60.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{MICRO_URLS['CONVERSOR']}/conversor/procesar_excel/",
                    files=files,
                    data=data,
                )

                if response.status_code == 200:
                    return StreamingResponse(
                        response.aiter_bytes(),
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        headers={"Content-Disposition": "attachment; filename=archivo_procesado.xlsx"}
                    )
                else:
                    return JSONResponse(status_code=response.status_code, content={"error": response.text})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

#-------- INTEGRACION -----------------------
"""
Endpoint: gateway_importar_llamadas

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para importar_llamadas.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/contacto/importar", tags=["Contacto"])
async def gateway_importar_llamadas(fecha_inicio: str = Query(...), fecha_fin: str = Query(...)):
    try:
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.get(
                f"{MICRO_URLS['CONTACTO']}/importar",
                params={"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

#-------------- GAIL-------------------
"""
Endpoint: registrar_gail_campana

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para registrar_gail_campana

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/campanas/registrar-gail", tags=["Gail"])
async def registrar_gail_campana(request: Request):
    json_data = await request.json()
    async with httpx.AsyncClient(timeout=3600.0) as client:
        response = await client.post(f"{MICRO_URLS['GAIL']}/campanas/registrar-gail", json=json_data)
    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type", "application/json")
    )
"""
Endpoint: gateway_obtener_contact_lists_por_pais

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para obtener_contact_lists_por_pais.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/campanas/contact_lists/{pais}", tags=["Gail"])
async def gateway_obtener_contact_lists_por_pais(pais: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MICRO_URLS['GAIL']}/campanas/contact_lists/{pais}")
        response.raise_for_status()
        return response.json()
"""
Endpoint: gateway_obtener_secuencias_por_pais

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente obtener_secuencias_por_pais.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/campanas/secuencias/{pais}", tags=["Gail"])
async def gateway_obtener_secuencias_por_pais(pais: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MICRO_URLS['GAIL']}/campanas/secuencias/{pais}")
        response.raise_for_status()
        return response.json()
"""
Endpoint: gateway_obtener_reglas_por_pais

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para obtener_reglas_por_pais.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/campanas/reglas/{pais}", tags=["Gail"])
async def gateway_obtener_reglas_por_pais(pais: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MICRO_URLS['GAIL']}/campanas/reglas/{pais}")
        response.raise_for_status()
        return response.json()

@router.get("/campanas/descargar_plantilla", tags=["Gail"])
async def descargar_plantilla(nombre: str):
    file_path = f"D:\plantilla_gail\{nombre}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Plantilla no encontrada")
    
    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=nombre
    )

GAIL_BASE = "https://api.lula.com/v1"

API_KEYS_BY_COUNTRY = {
    "Dislicores": os.getenv("LULA_API_KEY_DISLICORES", ""),
    "Dominicana": os.getenv("LULA_API_KEY_DOMINICANA", ""),
    "SystemGroup Cobro": os.getenv("LULA_API_KEY_SYSTEMGROUPCOBRO", ""),
    "SystemGroup": os.getenv("LULA_API_KEY_SYSTEMGROUP", ""),
    "Operacion Peru": os.getenv("LULA_API_KEY_OPERACION_PERU", ""),
}

def _get_lula_key(pais: str) -> str:
    """Obtiene la API key para un país, decodificando el nombre si viene URL-encoded"""
    pais_decoded = unquote(pais)
    key = API_KEYS_BY_COUNTRY.get(pais_decoded)
    if not key:
        raise HTTPException(status_code=400, detail=f"No hay API key configurada para país: {pais_decoded}")
    return key

async def _lula_request(method: str, url: str, api_key: str, json: Dict[str, Any] | None = None):
    """Realiza una request a la API de Lula con manejo de errores"""
    headers = {"X-API-Key": api_key, "accept": "application/json"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.request(method, url, headers=headers, json=json)
        
        try:
            body = r.json()
        except Exception:
            body = {"raw": r.text}

        if not r.is_success:
            detail = body.get("message") or body.get("error") or body
            raise HTTPException(status_code=r.status_code, detail=detail)

        return body

# ============= GAIL ENDPOINTS =============

# --- CAMPAIGNS ---
@router.get("/lula/{pais}/campaigns", tags=["Lula"])
async def lula_list_campaigns(pais: str):
    """Lista todas las campañas de un país"""
    pais = unquote(pais) 
    api_key = _get_lula_key(pais)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(
            f"{GAIL_BASE}/campaigns",
            headers={"X-API-Key": api_key, "accept": "application/json"}
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json")
    )

@router.post("/lula/{pais}/campaigns", tags=["Lula"])
async def lula_create_campaign(pais: str, payload: Dict[str, Any]):
    """Crea una nueva campaña"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    return await _lula_request("POST", f"{GAIL_BASE}/campaigns", api_key, json=payload)

@router.post("/lula/{pais}/campaigns/{campaign_id}/start", tags=["Lula"])
async def lula_start_campaign(pais: str, campaign_id: str):
    """Inicia una campaña"""
    pais = unquote(pais) 
    api_key = _get_lula_key(pais)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{GAIL_BASE}/campaigns/{campaign_id}/start",
            headers={"X-API-Key": api_key, "accept": "application/json"}
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json")
    )

@router.post("/lula/{pais}/campaigns/{campaign_id}/resume", tags=["Lula"])
async def lula_resume_campaign(pais: str, campaign_id: str):
    """Reanuda una campaña pausada"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{GAIL_BASE}/campaigns/{campaign_id}/resume",
            headers={"X-API-Key": api_key, "accept": "application/json"}
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json")
    )

@router.post("/lula/{pais}/campaigns/{campaign_id}/stop", tags=["Lula"])
async def lula_stop_campaign(pais: str, campaign_id: str):
    """Detiene una campaña"""
    pais = unquote(pais)  
    api_key = _get_lula_key(pais)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{GAIL_BASE}/campaigns/{campaign_id}/stop",
            headers={"X-API-Key": api_key, "accept": "application/json"}
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json")
    )

@router.get("/lula/{pais}/campaigns/{campaign_id}/touchpoints", tags=["Lula"])
async def lula_touchpoints(
    pais: str,
    campaign_id: str,
    includeTranscripts: bool = True,
    page: int = 1,
    size: int = 10000
):
    """Obtiene touchpoints de una campaña"""
    pais = unquote(pais) 
    api_key = _get_lula_key(pais)
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.get(
            f"{GAIL_BASE}/campaigns/{campaign_id}/touchpoints",
            params={
                "includeTranscripts": str(includeTranscripts).lower(),
                "page": page,
                "size": size
            },
            headers={"X-API-Key": api_key, "accept": "application/json"}
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json")
    )

@router.get("/lula/{pais}/sequences", tags=["Lula"])
async def lula_list_sequences(pais: str, status: str = Query("active")):
    """Lista secuencias de un país"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(
            f"{GAIL_BASE}/sequences",
            params={"status": status},
            headers={"X-API-Key": api_key, "accept": "text/plain"}
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json")
    )

@router.get("/lula/{pais}/sequences/{sequence_id}", tags=["Lula"])
async def lula_get_sequence(pais: str, sequence_id: str):
    """Obtiene detalles de una secuencia"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(
            f"{GAIL_BASE}/sequences/{sequence_id}",
            headers={"X-API-Key": api_key, "accept": "application/json"}
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json")
    )

@router.post("/lula/{pais}/sequences", tags=["Lula"])
async def lula_create_sequence(pais: str, payload: Dict[str, Any]):
    """Crea una nueva secuencia"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    return await _lula_request("POST", f"{GAIL_BASE}/sequences", api_key, json=payload)

@router.put("/lula/{pais}/sequences/{sequence_id}", tags=["Lula"])
async def lula_update_sequence(pais: str, sequence_id: str, payload: Dict[str, Any]):
    """Actualiza una secuencia"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    return await _lula_request("PUT", f"{GAIL_BASE}/sequences/{sequence_id}", api_key, json=payload)

@router.post("/lula/{pais}/sequences/{sequence_id}/archive", tags=["Lula"])
async def lula_archive_sequence(pais: str, sequence_id: str):
    """Archiva una secuencia"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{GAIL_BASE}/sequences/{sequence_id}/archive",
            headers={"X-API-Key": api_key}
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json")
    )

@router.post("/lula/{pais}/sequences/{sequence_id}/restore", tags=["Lula"])
async def lula_restore_sequence(pais: str, sequence_id: str):
    """Restaura una secuencia archivada"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{GAIL_BASE}/sequences/{sequence_id}/restore",
            headers={"X-API-Key": api_key}
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json")
    )

@router.get("/lula/{pais}/contact_lists", tags=["Lula"])
async def lula_list_contact_lists(pais: str, status: str = Query("active")):
    """Lista listas de contactos"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(
            f"{GAIL_BASE}/contact_lists",
            params={"status": status},
            headers={"X-API-Key": api_key, "accept": "text/plain"}
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json")
    )

@router.post("/lula/{pais}/contact_lists", tags=["Lula"])
async def lula_create_contact_list(pais: str, payload: Dict[str, Any]):
    """Crea una lista de contactos"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    return await _lula_request("POST", f"{GAIL_BASE}/contact_lists", api_key, json=payload)

@router.get("/lula/{pais}/contact_lists/{list_id}/contacts", tags=["Lula"])
async def lula_get_contacts_in_list(pais: str, list_id: str):
    """Obtiene contactos de una lista"""
    pais = unquote(pais) 
    api_key = _get_lula_key(pais)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(
            f"{GAIL_BASE}/contact_lists/{list_id}/contacts",
            headers={"X-API-Key": api_key, "accept": "application/json"}
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json")
    )

@router.post("/lula/{pais}/contact_lists/{list_id}/archive", tags=["Lula"])
async def lula_archive_contact_list(pais: str, list_id: str):
    """Archiva una lista de contactos"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{GAIL_BASE}/contact_lists/{list_id}/archive",
            headers={"X-API-Key": api_key}
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json")
    )

@router.post("/lula/{pais}/contact_lists/{list_id}/restore", tags=["Lula"])
async def lula_restore_contact_list(pais: str, list_id: str):
    """Restaura una lista de contactos archivada"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(
            f"{GAIL_BASE}/contact_lists/{list_id}/restore",
            headers={"X-API-Key": api_key}
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json")
    )

@router.post("/lula/{pais}/contact_lists/{list_id}/add", tags=["Lula"])
async def lula_add_contacts_to_list(pais: str, list_id: str, payload: Dict[str, Any]):
    """Agrega contactos a una lista"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    return await _lula_request("POST", f"{GAIL_BASE}/contact_lists/{list_id}/add", api_key, json=payload)

# --- CONTACTS ---
@router.post("/lula/{pais}/contacts/bulk_add", tags=["Lula"])
async def lula_bulk_add_contacts(pais: str, payload: Dict[str, Any]):
    """Crea contactos en bulk"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    return await _lula_request("POST", f"{GAIL_BASE}/contacts/bulk_add", api_key, json=payload)

# --- REDIALING RULES ---
@router.get("/lula/{pais}/redialing_rules", tags=["Lula"])
async def lula_list_redialing_rules(pais: str):
    """Lista reglas de remarcado"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(
            f"{GAIL_BASE}/redialing_rules",
            headers={"X-API-Key": api_key, "accept": "application/json"}
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json")
    )

@router.get("/lula/{pais}/redialing_rules/{rule_id}", tags=["Lula"])
async def lula_get_redialing_rule(pais: str, rule_id: str):
    """Obtiene detalles de una regla de remarcado"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(
            f"{GAIL_BASE}/redialing_rules/{rule_id}",
            headers={"X-API-Key": api_key, "accept": "text/plain"}
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json")
    )

# --- SCRIPTS ---
@router.get("/lula/{pais}/scripts", tags=["Lula"])
async def lula_list_scripts(pais: str, direction: str = Query("outbound"), status: str = Query("active")):
    """Lista scripts disponibles"""
    pais = unquote(pais)
    api_key = _get_lula_key(pais)
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.get(
            f"{GAIL_BASE}/scripts",
            params={"direction": direction, "status": status},
            headers={"X-API-Key": api_key, "Accept": "application/json"}
        )
    return Response(
        content=r.content,
        status_code=r.status_code,
        media_type=r.headers.get("content-type", "application/json")
    )

#------------- TABLEROS -----------------------------  
@router.get("/embudo/funnel")
async def funnel():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MICRO_URLS['TABLEROS']}/Emb/embudo/funnel")
        response.raise_for_status()
        return response.json()
    
@router.get("/embudo/commitments-acumulados")
async def commitments_acumulados():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MICRO_URLS['TABLEROS']}/Emb/embudo/commitments-acumulados")
        response.raise_for_status()
        return response.json()
    
@router.get("/embudo/efectividad-por-hora")
async def efectividad_por_hora():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MICRO_URLS['TABLEROS']}/Emb/embudo/efectividad-por-hora")
        response.raise_for_status()
        return response.json()
    
@router.get("/embudo/by-campaign", tags=["Embudo"])
async def gateway_embudo_by_campaign(idUsuario: int = Query(...), rol: str = Query(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['TABLEROS']}/Emb/embudo/by-campaign",
                params={"idUsuario": idUsuario, "rol": rol}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/productividad/analizar_productividad", tags=["Productividad"])
async def gateway_analiar_productividad(archivo: UploadFile = File(...)):
    try:
        file_content = await archivo.read()
        form_data = MultipartEncoder(
            fields={"archivo": (archivo.filename, file_content, archivo.content_type)}
        )
        headers = {"Content-Type": form_data.content_type}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MICRO_URLS['TABLEROS']}/productividad/analizar_productividad",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/productividad/descargar_grafico", tags=["Productividad"])
async def gateway_descargar_grafico():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['TABLEROS']}/productividad/descargar_grafico"
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="image/png",
                headers={"Content-Disposition": "inline; filename=grafico_avance.png"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ----------- PROYECTOS -----------
@router.post("/api/project/proyecto/crear", tags=["Proyectos"])
async def gateway_crear_proyecto(proyecto: dict = Body(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['PROJECT_MANAGER']}/proyecto/crear", json=proyecto)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.put("/api/project/proyecto/editar", tags=["Proyectos"])
async def gateway_editar_proyecto(proyecto: dict = Body(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{MICRO_URLS['PROJECT_MANAGER']}/proyecto/editar", json=proyecto)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.delete("/api/project/proyecto/eliminar", tags=["Proyectos"])
async def gateway_eliminar_proyecto(idProyecto: int = Query(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{MICRO_URLS['PROJECT_MANAGER']}/proyecto/eliminar",
                                           params={"idProyecto": idProyecto})
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/api/project/proyecto/listar", tags=["Proyectos"])
async def gateway_listar_proyectos():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['PROJECT_MANAGER']}/proyecto/listar")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ----------- TAREAS -----------
@router.post("/api/project/tarea/crear", tags=["Tareas"])
async def gateway_crear_tarea(tarea: dict = Body(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['PROJECT_MANAGER']}/tarea/crear", json=tarea)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.put("/api/project/tarea/editar", tags=["Tareas"])
async def gateway_editar_tarea(tarea: dict = Body(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{MICRO_URLS['PROJECT_MANAGER']}/tarea/editar", json=tarea)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.delete("/api/project/tarea/eliminar", tags=["Tareas"])
async def gateway_eliminar_tarea(idTarea: int = Query(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{MICRO_URLS['PROJECT_MANAGER']}/tarea/eliminar",
                                           params={"idTarea": idTarea})
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/api/project/tarea/listar", tags=["Tareas"])
async def gateway_listar_tareas(idProyecto: int = Query(None)):
    try:
        async with httpx.AsyncClient() as client:
            params = {"idProyecto": idProyecto} if idProyecto else {}
            response = await client.get(f"{MICRO_URLS['PROJECT_MANAGER']}/tarea/listar", params=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ----------- RECURSOS -----------
@router.post("/api/project/recurso/crear", tags=["Recursos"])
async def gateway_crear_recurso(recurso: dict = Body(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['PROJECT_MANAGER']}/recurso/crear", json=recurso)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.put("/api/project/recurso/editar", tags=["Recursos"])
async def gateway_editar_recurso(recurso: dict = Body(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{MICRO_URLS['PROJECT_MANAGER']}/recurso/editar", json=recurso)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.delete("/api/project/recurso/eliminar", tags=["Recursos"])
async def gateway_eliminar_recurso(idRecurso: int = Query(...)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{MICRO_URLS['PROJECT_MANAGER']}/recurso/eliminar",
                                           params={"idRecurso": idRecurso})
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/api/project/recurso/listar", tags=["Recursos"])
async def gateway_listar_recursos():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['PROJECT_MANAGER']}/recurso/listar")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ------------- TABLEROS RPA-----------------------------
@router.get("/rpa/dashboard", tags=["MonitorRPA"])
async def gateway_rpa_dashboard():
    return obtener_dashboard()

@router.get("/rpa/encabezados", tags=["MonitorRPA"])
async def gateway_rpa_encabezados(
    origen: str = Query(..., description="FAMISANAR, RUNT, SUPER NOTARIADO, etc.")
):
    """
    Devuelve todos los encabezados para un RPA dado.
    """
    try:
        return listar_encabezados_rpa(origen)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rpa/encabezados/{origen}/{id_encabezado}/detalles", tags=["MonitorRPA"])
async def gateway_rpa_detalles_paginados(
    origen: str,
    id_encabezado: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, gt=0, le=100),
    cc: str | None = Query(None, description="Filtrar por número de cédula", alias="cc")):

    try:
        return listar_detalles_rpa_paginados(origen, id_encabezado, offset, limit, cc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/rpa/{origen}/detalles/descargar_todos", tags=["MonitorRPA"])
async def descargar_todos_detalles_por_origen(origen: str):
    """
    Exporta TODOS los detalles del origen completo como archivo Excel.
    """
    datos = listar_todos_detalles_por_origen(origen)

    if not datos:
        raise HTTPException(status_code=404, detail=f"No hay datos de {origen} para exportar.")

    df = pd.DataFrame(datos)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name=origen[:30])

    output.seek(0)
    filename = f"{origen}_detalles_completos.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/rpa/encabezados/{origen}/{id_encabezado}/detalles/buscar_por_cedula", tags=["MonitorRPA"])
async def api_buscar_por_cedula(origen: str, id_encabezado: int, cedula: str):
    try:
        resultados = buscar_detalle_por_cedulaBLL(origen, id_encabezado, cedula)
        return {"rows": resultados, "total": len(resultados)}
    except Exception as e:
        raise HTTPException(500, str(e))

# ---------- CRM ----------
@router.get("/crm/conversaciones", tags=["CRM"])
async def gw_listar_conversaciones(
    user_id: str | None = Query(None),
    is_active: bool | None = Query(None),
    canal: str | None = Query(None),
    campaign_id: int | None = Query(None),
):
    """
    Proxy al microservicio CRM para listar conversaciones.
    """
    params: dict = {}
    if user_id is not None:
        params["user_id"] = user_id
    if is_active is not None:
        params["is_active"] = str(is_active).lower() 
    if canal is not None:
        params["canal"] = canal
    if campaign_id is not None:
        params["campaign_id"] = campaign_id

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{MICRO_URLS['CRM']}/crm/conversaciones",
                params=params
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/crm/conversaciones/detalle/{conversacion_id}", tags=["CRM"])
async def gw_detalle_conversacion(conversacion_id: int):
    """
    Proxy al microservicio CRM para ver detalle de una conversación.
    Incluye:
      - datos de la conversación
      - lista de mensajes
      - resumen (ACUERDO/RECHAZO/EN_CONVERSACION)
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{MICRO_URLS['CRM']}/crm/conversaciones/detalle/{conversacion_id}"
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/crm/conversaciones/export", tags=["CRM"])
async def gw_export_conversaciones(
    fecha_inicio: str | None = Query(None),
    fecha_fin: str | None = Query(None),
    campaign_id: str | None = Query(None),
    intencion: str | None = Query(None),
    canal: str | None = Query(None),
    pais: Optional[str] = Query(None),
    current_state: Optional[str] = Query(None)
):
    params = {}

    if fecha_inicio:
        params["fecha_inicio"] = fecha_inicio
    if fecha_fin:
        params["fecha_fin"] = fecha_fin
    if campaign_id and campaign_id.lower() != "nan":
        params["campaign_id"] = campaign_id
    if intencion:
        params["intencion"] = intencion
    if canal:
        params["canal"] = canal
    if pais:
        params["pais"] = pais
    if current_state:
        params["current_state"] = current_state

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{MICRO_URLS['CRM']}/crm/conversaciones/export",
                params=params,
            )
            resp.raise_for_status()

            content_disp = resp.headers.get(
                "content-disposition",
                'attachment; filename="crm_export.xlsx"'
            )

            return StreamingResponse(
                io.BytesIO(resp.content),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": content_disp},
            )

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))