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
from app.api.monitor_rpa import notificacion as monitor_notificacion
from app.bll.monitor_rpa_bll import obtener_dashboard, listar_encabezados_rpa, listar_detalles_rpa_paginados, listar_todos_detalles_por_origen, buscar_detalle_por_cedulaBLL
from app.bll.gateway_bll import (
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
"""
Instancia de APIRouter para registrar rutas relacionadas con los microservicios.
"""
router = APIRouter()

"""
Modelo de datos para representar la información de matrícula de una persona.

Campos:
    - CC: Cédula de ciudadanía.
    - ciudad: Ciudad asociada.
    - matricula: Número de matrícula.
    - direccion: Dirección registrada.
    - vinculadoA: Entidad o persona a la que está vinculado.
"""

class ResultadoModel(BaseModel):
    CC: str
    ciudad: Optional[str] = None
    matricula: Optional[str] = None
    direccion: Optional[str] = None
    vinculadoA: Optional[str] = None

"""
Modelo que representa los datos extraídos de la base RUNT (vehículos).

Campos:
    - cedula: Documento del propietario.
    - placaVehiculo: Placa del vehículo.
    - tipoServicio, estadoVehiculo, claseVehiculo, etc.: Información detallada del vehículo.
    - polizaSOAT: Estado de la póliza obligatoria de seguros.
    - revisionTecnomecanica: Estado de revisión técnica.
"""

class ResultadoRuntModel(BaseModel):
    cedula:str
    placaVehiculo: Optional[str] = None
    tipoServicio: Optional[str] = None
    estadoVehiculo: Optional[str] = None
    claseVehiculo: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    numeroSerie: Optional[str] = None
    numeroChasis: Optional[str] = None
    cilindraje: Optional[str] = None
    tipoCombustible: Optional[str] = None
    autoridadTransito: Optional[str] = None
    linea: Optional[str] = None
    color: Optional[str] = None
    numeroMotor: Optional[str] = None
    numeroVIN: Optional[str] = None
    tipoCarroceria: Optional[str] = None
    polizaSOAT: Optional[str] = None
    revisionTecnomecanica: Optional[str] = None
    limitacionesPropiedad: Optional[str] = None
    garantiasAFavorDe: Optional[str] = None

class ResultadoSimitModel(BaseModel):
    cedula:str
    tipo: Optional[str] = None
    placa: Optional[str] = None
    secretaria: Optional[str] = None
    
"""
Modelo de respuesta para datos provenientes del RUES (Registro Único Empresarial y Social).

Campos:
    - cedula: Documento del solicitante.
    - nombre, identificacion, categoria, etc.: Información registrada en la Cámara de Comercio.
"""

class ResultadoRuesModel(BaseModel):
    cedula: str
    nombre: Optional[str] = None
    identificacion: Optional[str] = None
    categoria: Optional[str] = None
    camaraComercio: Optional[str] = None
    numeroMatricula: Optional[str] = None
    actividadEconomica: Optional[str] = None
"""
Modelo de respuesta de los datos relacionados con FamiSanar (EPS o aseguradora de salud).

Campos:
    - cedula: Documento del afiliado.
    - nombres, apellidos, estado, IPS, convenio, etc.: Información de afiliación a salud.
"""

class ResultadoFamiSanarModel(BaseModel):
    cedula: str
    nombres: Optional[str]= None
    apellidos: Optional[str]= None
    estado: Optional[str]= None
    IPS: Optional[str]= None
    convenio: Optional[str]= None
    tipo: Optional[str]= None
    categoria: Optional[str]= None
    semanas: Optional[str]= None
    fechaNacimiento: Optional[str]= None
    edad: Optional[str]= None
    sexo: Optional[str]= None
    direccion: Optional[str]= None
    telefono: Optional[str]= None
    departamento: Optional[str]= None
    municipio: Optional[str]= None
    causal: Optional[str]= None

class ResultadoNuevaEpsModel(BaseModel):
    cedula: str
    nombre: Optional[str]= None
    fechaNacimiento: Optional[str]= None
    edad: Optional[str]= None
    sexo: Optional[str]= None
    antiguedad: Optional[str]= None
    fechaAfiliacion: Optional[str]= None
    epsAnterior: Optional[str]= None
    direccion: Optional[str]= None
    telefono: Optional[str]= None
    celular: Optional[str]= None
    email: Optional[str]= None
    municipio: Optional[str]= None
    departamento: Optional[str]= None
    observacion: Optional[str]= None

class ResultadoVigilanciaModel(BaseModel):
    radicado: str
    fechaInicial: str
    fechaFinal: str
    fechaActuacion: Optional[str] = None
    actuacion: Optional[str] = None
    anotacion: Optional[str] = None
    fechaIniciaTermino: Optional[str] = None
    fechaFinalizaTermino: Optional[str] = None
    fechaRegistro: Optional[str] = None
    radicadoNuevo: Optional[str] = None

class ResultadoWhatsAppModel(BaseModel):
    indicativo: str
    numero: str
    tiene_whatsApp: Optional[str] = None

class ResultadoCamaraComercioModel(BaseModel):
    cedula: str
    identificacion: Optional[str] = None
    primerNombre: Optional[str] = None
    segundoNombre: Optional[str] = None
    primerApellido: Optional[str] = None
    segundoApellido: Optional[str] = None
    direccion: Optional[str] = None
    pais: Optional[str] = None
    departamento: Optional[str] = None
    municipio: Optional[str] = None
    telefono: Optional[str] = None
    correo: Optional[str] = None


# ----- GATEWAY -----
"""
Endpoint: get_all_permisos

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para obtener todos los permisos.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
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

# ----- JURIDICA - Impulso Procesal -----
"""
Endpoint: gateway_upload_preforma_impulso

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para upload preforma impulso.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/juridica/upload_preforma_impulso", tags=["Impulso Procesal"])
async def gateway_upload_preforma_impulso(file: UploadFile = File(...)):
    try:
        form_data = MultipartEncoder(
            fields={"file": (file.filename, await file.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )

        headers = {"Content-Type": form_data.content_type}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MICRO_URLS['JURIDICA']}/impulsoProcesal/UploadPreformaImpulsoUno",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_export_preforma_impulso

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para export preforma impulso.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/juridica/export_preforma_impulso", tags=["Impulso Procesal"])
async def gateway_export_preforma_impulso():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/impulsoProcesal/ExportPreformaImpulso")
            response.raise_for_status()
            return response.content  # Es un archivo Excel
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_export_preforma_carta

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para export preforma carta.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/juridica/export_preforma_carta", tags=["Impulso Procesal"])
async def gateway_export_preforma_carta():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/impulsoProcesal/ExportPreformaCartaImpulso")
            response.raise_for_status()
            return response.content  # Es un archivo Word
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_generar_documentos

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para generar documentos.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/juridica/generar_documentos", tags=["Documentos"])
async def gateway_generar_documentos(
    request: Request,
    output: str = Query("pdf"),
    preforma: int = Query(1)
):
    try:
        body = await request.body()
        headers = {"Content-Type": "application/json"}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MICRO_URLS['JURIDICA']}/impulsoProcesal/GuardarCartaImpulso?output={output}&preforma={preforma}",
                content=body,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print("🔥 Error en el gateway:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_exportar_cartas_impulso

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para exportar cartas impulso.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/juridica/exportar_cartas_impulso", tags=["Impulso Procesal"])
async def gateway_exportar_cartas_impulso(processId: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/impulsoProcesal/ExportarCartasImpulso",
                params={"processId": processId}
            )
            response.raise_for_status()

            return Response(
                content=response.content,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename=Cartas_Impulso_{processId}.zip"
                }
            )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ----- JURIDICA - Generar Documentos Procesales -----
"""
Endpoint: gateway_guardar_carta_impulso

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para guardar carta impulso.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/juridica/guardar_carta_impulso", tags=["Impulso Procesal"])
async def gateway_guardar_carta_impulso(
    request: Request,
    output: str = Query("pdf"),
    preforma: int = Query(1)
):
    try:
        async with httpx.AsyncClient() as client:
            body = await request.body()
            headers = {"Content-Type": "application/json"}

            # 🔥 Incluye los parámetros en la URL del microservicio
            response = await client.post(
                f"{MICRO_URLS['JURIDICA']}/impulsoProcesal/GuardarCartaImpulso?output={output}&preforma={preforma}",
                content=body,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

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

# ---------- ENDPOINT: Foco Resultado  ----------
"""
Endpoint: gateway_consultar_focosResult

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para consultar foco resultado.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/focos/resultado/consultar", tags=["Foco Resultado"])
async def gateway_consultar_focosResult(filtros: Dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['PLANEACION']}/focos/resultado/consultar", json=filtros)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

"""
Endpoint: gateway_insertar_focosResult

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para insertar foco resultado.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/focos/resultado/insertar", tags=["Foco Resultado"])
async def gateway_insertar_focosResult(filtros: Dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['PLANEACION']}/focos/resultado/insertar", json=filtros)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ---------- ENDPOINT: Foco Trabajable  ----------
"""
Endpoint: gateway_consultar_focosTraba

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para consultar focos traba.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/focos/trabajable/consultar", tags=["Foco Trabajable"])
async def gateway_consultar_focosTraba(filtros: Dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['PLANEACION']}/focos/trabajable/consultar", json=filtros)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ---------- ENDPOINT: IA  ----------
"""
Endpoint: gateway_obtener_predicciones

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para obtener predicciones.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/IA/predicciones", tags=["IA"])
async def gateway_obtener_predicciones():
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f"{MICRO_URLS['IA']}/predicciones")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        traceback_str = traceback.format_exc()
        print("❌ ERROR GATEWAY /IA/predicciones:")
        print(traceback_str)
        return JSONResponse(status_code=500, content={"error": str(e), "trace": traceback_str})
"""
Endpoint: gateway_listarAutomatizaciones

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para listar automatizaciones.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/Jurica/listarAutomatizaciones", tags=["Automatizaciones"])
async def gateway_listarAutomatizaciones():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizaciones")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_listarAutomatizacionesRunt

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente. para listar automatizaciones Runt.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/Jurica/listarAutomatizacionesRunt", tags=["Automatizaciones Runt"])
async def gateway_listarAutomatizaciones():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesRunt")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_listarAutomatizacionesRues

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente. para listar automatizaciones Rues.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/Jurica/listarAutomatizacionesRues", tags=["Automatizaciones Rues"])
async def gateway_listarAutomatizaciones():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesRues")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})   
"""
Endpoint: gateway_listarAutomatizacionesDetalle

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para listar Automatizaciones Detalle.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/Jurica/listarAutomatizacionesDetalle", tags=["Automatizaciones"])
async def gateway_listarAutomatizacionesDetalle(id_encabezado):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizaciones/{id_encabezado}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_listarAutomatizacionesDetalleRunt

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/Jurica/listarAutomatizacionesDetalleRunt", tags=["Automatizaciones Runt"])
async def gateway_listarAutomatizacionesDetalle(id_encabezado):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesRunt/{id_encabezado}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_listarAutomatizacionesDetalleRues

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente Rues.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/Jurica/listarAutomatizacionesDetalleRues", tags=["Automatizaciones Rues"])
async def gateway_listarAutomatizacionesDetalle(id_encabezado):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesRues/{id_encabezado}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})   


#------------- ENDPOINT: SUPER NOTARIADO RPA -------------
"""
Endpoint: gateway_guardar_excel_notariado

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para guardar excel notariado.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/excel/guardarNotariado", tags=["Excel"])
async def gateway_guardar_excel_notariado(request: Request):
    try:
        form = await request.form()
        file = form["file"]
        idUsuario = int(form["idUsuario"])
        print(f"🧾 idUsuario recibido en gateway: {idUsuario}")


        content = await file.read()

        form_data = MultipartEncoder(
            fields={
                "file": (file.filename, content, file.content_type),
                "idUsuario": str(idUsuario)
            }
        )
        headers = {"Content-Type": form_data.content_type}

        timeout = httpx.Timeout(3600.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{MICRO_URLS['JURIDICA']}/superNotariado_api/excel/guardar",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        import traceback
        print("🔥 ERROR EN GATEWAY /guardarNotariado:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_ver_archivo_excel_json

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para ver archivo excel/json

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/excel/ver_jsonNotariado", tags=["Excel"])
async def gateway_ver_archivo_excel_json(nombre: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/superNotariado_api/excel/ver_json", 
                params={"nombre": nombre}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_ver_archivo_excel

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/excel/verNotariado", tags=["Excel"])
async def gateway_ver_archivo_excel(nombre: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/superNotariado_api/excel/ver", 
                params={"nombre": nombre}
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={nombre}"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_descargar_pdf_notariado

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para descargar pdf notariado.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/excel/descargar_pdf_notariado", tags=["Excel"])
async def gateway_descargar_pdf_notariado(cedula: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/superNotariado_api/excel/descargar_pdf",
                params={"Cedula": cedula}
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={cedula}.pdf"
                }
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

"""
Endpoint: gateway_descargar_plantilla

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para descargar plantilla.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/excel/plantillaNotariado", tags=["Excel"])
async def gateway_descargar_plantilla():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/superNotariado_api/excel/plantilla"
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=plantilla_superNotariado.xlsx"}
            )
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        return JSONResponse(
            status_code=500 if error_msg else 200,
            content={"error": error_msg}
        )
"""
Endpoint: gateway_listar_detalles_agrupados

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para listar detalles agrupados.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/superNotariado_api/detalle/listar_agrupado", tags=["SuperNotariado"])
async def gateway_listar_detalles_agrupados():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/superNotariado_api/detalle/listar_agrupado")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_darUsuarioCC

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para dar Usuario CC.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""

@router.get("/superNotariado_api/usuarioCC", tags=["SuperNotariado"])
async def gateway_darUsuarioCC():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacion/porCC")
            resp.raise_for_status()
            data = resp.json()
            id_enc = data.get("idEncabezado")
            ced    = data.get("CC")

            if id_enc is None or ced is None:
                raise HTTPException(502, "Super Notariado no devolvió idEncabezado y cedula")

        await monitor_notificacion("SUPER NOTARIADO", id_enc)

        return {"CC": ced}

    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
"""
Endpoint: gateway_dar_usuario_disponible

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para dar usuario disponible.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/superNotariado_api/darUsuario", tags=["SuperNotariado"])
async def gateway_dar_usuario_disponible():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/superNotariado_api/darUsuario")
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as http_err:
        # Reenviamos el código de error y el cuerpo de la respuesta tal como vino
        return JSONResponse(
            status_code=http_err.response.status_code,
            content=http_err.response.json()
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_guardar_resultado_automatizacion

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para guardar resultado automatizacion.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/superNotariado_api/automatizacion/resultado", tags=["SuperNotariado"])
async def gateway_guardar_resultado_automatizacion(request: Request):
    raw_bytes = await request.body()
    print("🔥 RAW BYTES:", raw_bytes)
    body_str = raw_bytes.decode("utf-8", errors="ignore")

    try:
        data = json.loads(body_str)
    except json.JSONDecodeError:
        try:
            data = sanitize_and_parse_json(body_str)
        except json.JSONDecodeError as e:
            print("❌ JSONDecodeError:", e)
            traceback.print_exc()
            raise HTTPException(status_code=422, detail=f"JSON inválido: {e.msg}")

    try:
        resultado = ResultadoModel(**data)
    except ValidationError as ve:
        print("❌ ValidationError:", ve.errors())
        raise HTTPException(status_code=422, detail=ve.errors())

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{MICRO_URLS['JURIDICA']}/superNotariado_api/automatizacion/resultado",
                json=resultado.dict()
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as he:
        print("❌ HTTPStatusError:", he.response.text)
        raise HTTPException(status_code=he.response.status_code, detail=he.response.text)
    except Exception as e:
        print("❌ Exception al llamar Jurídica:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def sanitize_and_parse_json(json_string: str) -> dict:
    cleaned = re.sub(r'\s+', ' ', json_string.strip())
    
    def escape_inner_quotes(match):
        key = match.group(1)
        colon_space = match.group(2)
        opening_quote = match.group(3) 
        value_content = match.group(4)
        
        escaped_content = value_content.replace('"', '\\"')
        
        return f'{key}{colon_space}{opening_quote}{escaped_content}"'
    
    pattern = r'("[\w\s]+")(\s*:\s*)(")([^"]*(?:"[^"]*)*[^"]*?)(?="(?:\s*[,}]))'
    sanitized = re.sub(pattern, escape_inner_quotes, cleaned)
    
    try:
        return json.loads(sanitized)
    except json.JSONDecodeError:
        return parse_json_manually(cleaned)


def parse_json_manually(json_string: str) -> dict:
    """
    Parser manual para JSON con comillas problemáticas.
    """
    import re
    
    content = json_string.strip()
    if content.startswith('{') and content.endswith('}'):
        content = content[1:-1]
    
    result = {}
    
    pairs = []
    current_pair = ""
    in_value = False
    quote_count = 0
    
    for char in content:
        if char == '"':
            quote_count += 1
        elif char == ':' and quote_count % 2 == 0:
            in_value = True
        elif char == ',' and quote_count % 2 == 0 and in_value:
            pairs.append(current_pair.strip())
            current_pair = ""
            in_value = False
            continue
        
        current_pair += char
    
    if current_pair.strip():
        pairs.append(current_pair.strip())
    
    for pair in pairs:
        if ':' not in pair:
            continue
            
        colon_pos = -1
        quote_count = 0
        for i, char in enumerate(pair):
            if char == '"':
                quote_count += 1
            elif char == ':' and quote_count % 2 == 0:
                colon_pos = i
                break
        
        if colon_pos == -1:
            continue
            
        key_part = pair[:colon_pos].strip()
        value_part = pair[colon_pos + 1:].strip()
        
        key = key_part.strip('"')
        
        if value_part.startswith('"') and value_part.endswith('"'):
            value = value_part[1:-1] 
        else:
            value = value_part
        
        result[key] = value
    
    return result

"""
Endpoint: gateway_exportar_resultados_notariado_tanda

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para exportar resultados notariado tanda.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/excel/exportar_resultadosNotariado", tags=["Excel"])
async def gateway_exportar_resultados_notariado_tanda(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/superNotariado_api/excel/exportar_resultados",
                params={"id_encabezado": id_encabezado}
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=resultado_{id_encabezado}.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_listarAutomatizacionesDetalleResumido

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para listar detalle resumido.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/Juridica/listarAutomatizacionesDetalleResumido", tags=["Automatizaciones"])
async def gateway_listarAutomatizacionesDetalleResumido(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/juridica_api/listarAutomatizacionesDetalleResumido",
                params={"id_encabezado": id_encabezado}
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content={"error": str(e), "detail": e.response.text}
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/notificarFinalizacionSuperNotariado")
async def gateway_notificar_finalizacion_supernotariado(payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['JURIDICA']}/superNotariado_api/notificarFinalizacionSuperNotariado", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/Juridica/listarAutomatizacionesSuperNotariado", tags=["SuperNotariado"])
async def gw_listar_automatizaciones_SuperNotariado(
    offset: int | None = Query(None),
    limit: int  | None = Query(None)
):
    params = {}
    if offset is not None: params["offset"] = offset
    if limit  is not None: params["limit"]  = limit
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesSuperNotariado", params=params)
        r.raise_for_status()
        return r.json()
    
@router.get("/Juridica/automatizacionesSuperNotariado/{id_encabezado}/resumen", tags=["Automatizaciones SuperNotariado"])
async def gw_resumen_encabezado(id_encabezado: int):
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesSuperNotariado/{id_encabezado}/resumen")
        r.raise_for_status()
        return r.json()

#----------- ENDPOINT: RUNT RPA ----------------
"""
Endpoint: gateway_guardar_excel_runt

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para guardar excel runt.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/excel/guardarRunt", tags=["Runt"])
async def gateway_guardar_excel_runt(request: Request):
    try:
        form = await request.form()
        file = form["file"]
        idUsuario = int(form["idUsuario"])
        print(f"🧾 idUsuario recibido en gateway: {idUsuario}")


        content = await file.read()

        form_data = MultipartEncoder(
            fields={
                "file": (file.filename, content, file.content_type),
                "idUsuario": str(idUsuario)
            }
        )
        headers = {"Content-Type": form_data.content_type}

        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{MICRO_URLS['JURIDICA']}/runt_api/excel/guardarRunt",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        import traceback
        print("🔥 ERROR EN GATEWAY /guardarRunt:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_listar_archivos_excel

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para listar archivos excel.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/excel/listarRunt", tags=["Excel"])
async def gateway_listar_archivos_excel():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/runt_api/excel/listar")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_ver_archivo_excel

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para ver archivo excel.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/excel/verRunt", tags=["Excel"])
async def gateway_ver_archivo_excel(nombre: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/runt_api/excel/ver", params={"nombre": nombre})
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_descargar_plantilla

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para descargar plantilla.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/excel/plantillaRunt", tags=["Excel"])
async def gateway_descargar_plantilla():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/runt_api/excel/plantilla"
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=plantilla_runt.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_listar_detalles_agrupados

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente 

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/runt_api/detalle/listar_agrupadoRunt", tags=["Runt"])
async def gateway_listar_detalles_agrupados():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/runt_api/detalle/listar_agrupadoRunt")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

"""
Endpoint: gateway_darUsuarioCC

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para Dar usuario CC

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/runt_api/usuarioCC", tags=["Runt"])
async def gateway_darUsuarioCC():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionRunt/porCC")
            resp.raise_for_status()
            data = resp.json()
            id_enc = data.get("idEncabezado")
            ced    = data.get("cedula")

            if id_enc is None or ced is None:
                raise HTTPException(502, "Runt no devolvió idEncabezado y cedula")

        await monitor_notificacion("RUNT", id_enc)

        return {"cedula": ced}

    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
"""
Endpoint: gateway_guardar_resultado_automatizacion

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para guardar resultado automatizacion.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/runt_api/automatizacion/resultado", tags=["Runt"])
async def gateway_guardar_resultado_automatizacion(request: Request):
    try:
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8', errors='replace')
        body_str_cleaned = re.sub(r'[\r\n]+', ' ', body_str)

        print("📥 Body recibido (raw):", body_str)
        
        raw_body = json.loads(body_str_cleaned)
        print("📦 Body como dict:", raw_body)

        resultado = ResultadoRuntModel(**raw_body)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MICRO_URLS['JURIDICA']}/runt_api/automatizacion/resultadoRunt",
                json=resultado.dict()
            )
            response.raise_for_status()
            return response.json()

    except json.decoder.JSONDecodeError as je:
        print("❌ Error de decodificación JSON:", je)
        return JSONResponse(status_code=400, content={"error": "JSON inválido", "detail": str(je)})

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"🔥 ERROR CRÍTICO: {str(e)}\n{tb}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error interno del servidor", "detail": str(e)}
        )

"""
Endpoint: gateway_descargar_pdf_notariado

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para descagar pdf notariado.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/excel/descargar_pdf_runt", tags=["Excel"])
async def gateway_descargar_pdf_notariado(cedula: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/runt_api/excel/descargar_pdf",
                params={"Cedula": cedula}
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={cedula}.pdf"
                }
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_exportar_resultados_runt_tanda

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para exportar resultados runt tanda.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/excel/exportar_resultadosRunt", tags=["Excel"])
async def gateway_exportar_resultados_runt_tanda(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/runt_api/excel/exportar_resultados",
                params={"id_encabezado": id_encabezado}
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=resultado_{id_encabezado}.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.post("/notificarFinalizacionRunt", tags=["Runt"])
async def gateway_notificar_finalizacion_runt(payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['JURIDICA']}/runt_api/notificarFinalizacionRunt", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/Juridica/listarAutomatizacionesRunt", tags=["Runt"])
async def gw_listar_automatizaciones_Runt(
    offset: int | None = Query(None),
    limit: int  | None = Query(None)
):
    params = {}
    if offset is not None: params["offset"] = offset
    if limit  is not None: params["limit"]  = limit
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesRunt", params=params)
        r.raise_for_status()
        return r.json()
    
@router.get("/Juridica/automatizacionesRunt/{id_encabezado}/resumen", tags=["Automatizaciones Runt"])
async def gw_resumen_encabezado(id_encabezado: int):
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesRunt/{id_encabezado}/resumen")
        r.raise_for_status()
        return r.json()

#----------- ENDPOINT: RUES RPA ----------------
"""
Endpoint: gateway_guardar_excel_rues

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para guardar excel rues.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/excel/guardarRues", tags=["Rues"])
async def gateway_guardar_excel_rues(request: Request):
    try:
        form = await request.form()
        file = form["file"]
        idUsuario = int(form["idUsuario"])
        print(f"🧾 idUsuario recibido en gateway: {idUsuario}")


        content = await file.read()

        form_data = MultipartEncoder(
            fields={
                "file": (file.filename, content, file.content_type),
                "idUsuario": str(idUsuario)
            }
        )
        headers = {"Content-Type": form_data.content_type}

        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{MICRO_URLS['JURIDICA']}/rues_api/excel/guardarRues",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        import traceback
        print("🔥 ERROR EN GATEWAY /guardarRues:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_listar_archivos_excel

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para listar archivos excel.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/excel/listarRues", tags=["Excel"])
async def gateway_listar_archivos_excel():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/rues_api/excel/listar")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_ver_archivo_excel

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para ver archivo excel.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/excel/verRues", tags=["Excel"])
async def gateway_ver_archivo_excel(nombre: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/rues_api/excel/ver", params={"nombre": nombre})
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_descargar_plantilla

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para descargar plantilla.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/excel/plantillaRues", tags=["Excel"])
async def gateway_descargar_plantilla():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/rues_api/excel/plantilla"
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=plantilla_rues.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_listar_detalles_agrupados

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para listar detalles agrupados.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/rues_api/detalle/listar_agrupadoRues", tags=["Rues"])
async def gateway_listar_detalles_agrupados():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/rues_api/detalle/listar_agrupadoRues")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_darUsuarioCC

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para dar usuario CC.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/rues_api/usuarioCC", tags=["Rues"])
async def gateway_darUsuarioCC():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionRues/porCC")
            resp.raise_for_status()
            data = resp.json()
            id_enc = data.get("idEncabezado")
            ced    = data.get("cedula")

            if id_enc is None or ced is None:
                raise HTTPException(502, "Rues no devolvió idEncabezado y cedula")

        await monitor_notificacion("RUES", id_enc)

        return {"cedula": ced}

    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_guardar_resultado_automatizacion

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para guardar_resultado_automatizacion.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""

@router.post("/rues_api/automatizacion/resultado", tags=["Rues"])
async def gateway_guardar_resultado_automatizacion(request: Request):
    try:
        raw_text = await request.body()
        decoded_text = raw_text.decode("utf-8", errors="ignore")

        def corregir_comillas_internas(texto: str) -> str:
            dentro_campo = False
            nuevo = ''
            i = 0
            while i < len(texto):
                c = texto[i]
                if c == '"':
                    if i > 0 and texto[i - 1] == ':' and texto[i + 1] != '"':
                        dentro_campo = True
                    elif dentro_campo and (i + 1 == len(texto) or texto[i + 1] in [',', '}']):
                        dentro_campo = False
                    elif dentro_campo:
                        nuevo += '\\'
                nuevo += c
                i += 1
            return nuevo

        safe_json_text = corregir_comillas_internas(decoded_text)

        raw_body = json.loads(safe_json_text)
        print("🌐 Gateway recibió payload corregido:", raw_body)

    except Exception as e:
        print("❌ Error al parsear JSON:", str(e))
        print("📦 Contenido recibido (original):", decoded_text)
        return JSONResponse(
            status_code=400,
            content={"error": "JSON inválido tras sanitización", "detalle": str(e)}
        )

    try:
        ResultadoRuesModel(**raw_body)
    except ValidationError as ve:
        print("❌ Validación en gateway:", ve.json())
        raise HTTPException(status_code=422, detail=ve.errors())

    try:
        async with httpx.AsyncClient(timeout=3600.0) as client:
            upstream_url = f"{MICRO_URLS['JURIDICA']}/rues_api/automatizacion/resultadoRues"
            resp = await client.post(upstream_url, json=raw_body)
            resp.raise_for_status()
    except httpx.HTTPStatusError as hse:
        return JSONResponse(
            status_code=hse.response.status_code,
            content=hse.response.json()
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail="Bad gateway")
    return JSONResponse(status_code=resp.status_code, content=resp.json())

@router.get("/excel/descargar_pdf_rues", tags=["Excel"])
async def gateway_descargar_pdf_notariado(cedula: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/rues_api/excel/descargar_pdf",
                params={"Cedula": cedula}
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={cedula}.pdf"
                }
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_descargar_pdf_notariado

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para descargar_pdf_notariado.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""

@router.get("/excel/exportar_resultadosRues", tags=["Excel"])
async def gateway_exportar_resultados_rues_tanda(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/rues_api/excel/exportar_resultados",
                params={"id_encabezado": id_encabezado}
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=resultado_{id_encabezado}.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.post("/notificarFinalizacionRues")
async def gateway_notificar_finalizacion_rues(payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['JURIDICA']}/rues_api/notificarFinalizacionRues", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/Juridica/listarAutomatizacionesRues", tags=["Rues"])
async def gw_listar_automatizaciones_Rues(
    offset: int | None = Query(None),
    limit: int  | None = Query(None)
):
    params = {}
    if offset is not None: params["offset"] = offset
    if limit  is not None: params["limit"]  = limit
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesRues", params=params)
        r.raise_for_status()
        return r.json()
    
@router.get("/Juridica/automatizacionesRues/{id_encabezado}/resumen", tags=["Automatizaciones Rues"])
async def gw_resumen_encabezado(id_encabezado: int):
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesRues/{id_encabezado}/resumen")
        r.raise_for_status()
        return r.json()
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
#----------- ENDPOINT: FAMISANAR RPA ----------------
"""
Endpoint: gateway_guardar_excel_runt

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para guardar_excel_runt.


Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/excel/guardarFamiSanar", tags=["FamiSanar"])
async def gateway_guardar_excel_famisanar(request: Request):
    try:
        form = await request.form()
        file = form["file"]
        idUsuario = int(form["idUsuario"])
        print(f"🧾 idUsuario recibido en gateway: {idUsuario}")


        content = await file.read()

        form_data = MultipartEncoder(
            fields={
                "file": (file.filename, content, file.content_type),
                "idUsuario": str(idUsuario)
            }
        )
        headers = {"Content-Type": form_data.content_type}

        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{MICRO_URLS['SALUD']}/famisanar_api/excel/guardarFamiSanar",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        import traceback
        print("🔥 ERROR EN GATEWAY /guardarFamisanar:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_descargar_plantilla

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para descargar_plantilla.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/excel/plantillaFamiSanar", tags=["Excel"])
async def gateway_descargar_plantilla():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['SALUD']}/famisanar_api/excel/plantilla"
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=plantilla_famisanar.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_listar_detalles_agrupados

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para listar_detalles_agrupados.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/famisanar_api/detalle/listar_agrupadoFamiSanar", tags=["FamiSanar"])
async def gateway_listar_detalles_agrupados():
    try:
        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{MICRO_URLS['SALUD']}/famisanar_api/detalle/listar_agrupadoFamiSanar")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_darUsuarioCC

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para darUsuarioCC.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/famisanar_api/usuarioCC", tags=["FamiSanar"])
async def gateway_darUsuarioCC():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{MICRO_URLS['SALUD']}/famisanar_api/automatizacionFamiSanar/porCC")
            resp.raise_for_status()
            data = resp.json()
            id_enc = data.get("idEncabezado")
            ced    = data.get("cedula")

            if id_enc is None or ced is None:
                raise HTTPException(502, "FamiSanar no devolvió idEncabezado y cedula")

        await monitor_notificacion("FAMISANAR", id_enc)

        return {"cedula": ced}

    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
"""
Endpoint: gateway_guardar_resultado_automatizacion

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para guardar_resultado_automatizacion.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.post("/famisanar_api/automatizacion/resultado", tags=["FamiSanar"])
async def gateway_guardar_resultado_automatizacion(request: Request):
    raw_body = await request.json()

    # 2) (Opcional) valida con Pydantic
    try:
        ResultadoFamiSanarModel(**raw_body)
    except ValidationError as ve:
        print("❌ Validación en gateway:", ve.json())
        raise HTTPException(status_code=422, detail=ve.errors())

    # 3) Reenvía al microservicio
    try:
        async with httpx.AsyncClient(timeout=3600.0) as client:
            upstream_url = f"{MICRO_URLS['SALUD']}/famisanar_api/automatizacion/resultadoFamiSanar"
            resp = await client.post(upstream_url, json=raw_body)
            # si el upstream devolvió un error HTTP (4xx/5xx), lanza
            resp.raise_for_status()
    except httpx.HTTPStatusError as hse:
        # Propaga el status y el JSON de error del micro
        return JSONResponse(
            status_code=hse.response.status_code,
            content=hse.response.json()
        )
    except Exception as e:
        # Errores de conexión, timeout, etc.
        print("🔥 Error al llamar al microservicio:", str(e))
        raise HTTPException(status_code=502, detail="Bad gateway")

    # 4) Devuelve tal cual lo que vino del micro
    return JSONResponse(status_code=resp.status_code, content=resp.json())
"""
Endpoint: gateway_listarAutomatizacionesDetalle

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para listarAutomatizacionesDetalle.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/Salud/listarAutomatizacionesDetalleFamiSanar", tags=["Automatizaciones FamiSanar"])
async def gateway_listarAutomatizacionesDetalle(id_encabezado):
    try:
        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{MICRO_URLS['SALUD']}/famisanar_api/automatizacionesFamiSanar/{id_encabezado}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
"""
Endpoint: gateway_listarAutomatizaciones

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para listarAutomatizaciones.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/Salud/listarAutomatizacionesFamiSanar", tags=["Automatizaciones FamiSanar"])
async def gw_listar_automatizaciones_famisanar(
    offset: int | None = Query(None),
    limit: int  | None = Query(None)
):
    params = {}
    if offset is not None: params["offset"] = offset
    if limit  is not None: params["limit"]  = limit
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['SALUD']}/famisanar_api/automatizacionesFamiSanar", params=params)
        r.raise_for_status()
        return r.json()

"""
Endpoint: gateway_exportar_resultados_famisanar_tanda

Descripción:
Este endpoint redirige una solicitud al microservicio correspondiente para exportar_resultados_famisanar_tanda.

Parámetros:
    Ver firma.

Retorna:
    JSON con datos o error HTTP.
"""
@router.get("/excel/exportar_resultadosFamiSanar", tags=["Excel"])
async def gateway_exportar_resultados_famisanar_tanda(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['SALUD']}/famisanar_api/excel/exportar_resultados",
                params={"id_encabezado": id_encabezado}
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=resultado_{id_encabezado}.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/notificarFinalizacionFamiSanar")
async def gateway_notificar_finalizacion_famisanar(payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['SALUD']}/famisanar_api/notificarFinalizacionFamiSanar", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
  
@router.get("/Salud/automatizacionesFamiSanar/{id_encabezado}/detalles", tags=["Automatizaciones FamiSanar"])
async def gateway_listarDetallesPaginado(id_encabezado: int, offset: int = 0, limit: int = 50, cc: str | None = Query(None)):
    try:
        timeout = httpx.Timeout(120.0, connect=10.0)
        params = {"offset": offset, "limit": limit}
        if cc:
            params["cc"] = cc
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                f"{MICRO_URLS['SALUD']}/famisanar_api/automatizacionesFamiSanar/{id_encabezado}/detalles",
                params=params
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/Salud/automatizacionesFamiSanar/{id_encabezado}/resumen", tags=["Automatizaciones FamiSanar"])
async def gw_resumen_encabezado(id_encabezado: int):
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['SALUD']}/famisanar_api/automatizacionesFamiSanar/{id_encabezado}/resumen")
        r.raise_for_status()
        return r.json()
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
async def gateway_analizar_productividad(archivo: UploadFile = File(...)):
    try:
        file_content = await archivo.read()
        form_data = MultipartEncoder(
            fields={"archivo": (archivo.filename, file_content, archivo.content_type)}
        )
        headers = {"Content-Type": form_data.content_type}

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MICRO_URLS['CONVERSOR']}/productividad/analizar_productividad",
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
                f"{MICRO_URLS['CONVERSOR']}/productividad/descargar_grafico"
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

#----------- ENDPOINT: SIMIT RPA ----------------
@router.get("/simit_api/detalle/listar_agrupadoSimit", tags=["Simit"])
async def gateway_listar_detalles_agrupados():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/simit_api/detalle/listar_agrupadoSimit")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/Jurica/listarAutomatizacionesSimit", tags=["Automatizaciones Simit"])
async def gateway_listarAutomatizaciones():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesSimit")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/Jurica/listarAutomatizacionesDetalleSimit", tags=["Automatizaciones Simit"])
async def gateway_listarAutomatizacionesDetalle(id_encabezado):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesSimit/{id_encabezado}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/excel/plantillaSimit", tags=["Excel"])
async def gateway_descargar_plantilla():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/simit_api/excel/plantilla"
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=plantilla_simit.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/excel/guardarSimit", tags=["Simit"])
async def gateway_guardar_excel_simit(request: Request):
    try:
        form = await request.form()
        file = form["file"]
        idUsuario = int(form["idUsuario"])
        print(f"🧾 idUsuario recibido en gateway: {idUsuario}")


        content = await file.read()

        form_data = MultipartEncoder(
            fields={
                "file": (file.filename, content, file.content_type),
                "idUsuario": str(idUsuario)
            }
        )
        headers = {"Content-Type": form_data.content_type}

        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{MICRO_URLS['JURIDICA']}/simit_api/excel/guardarSimit",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        import traceback
        print("🔥 ERROR EN GATEWAY /guardarSimit:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/exportar_resultadosSimit", tags=["Excel"])
async def gateway_exportar_resultados_simit_tanda(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/simit_api/excel/exportar_resultados",
                params={"id_encabezado": id_encabezado}
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=resultado_{id_encabezado}.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    

@router.post("/simit_api/automatizacion/resultado", tags=["Simit"])
async def gateway_guardar_resultado_automatizacion(request: Request):
    try:
        # 🔥 Obtiene el body crudo en bytes
        body_bytes = await request.body()
        print("🔥 BODY CRUDO (bytes):", body_bytes)

        # 🔥 Intenta decodificarlo como texto
        body_str = body_bytes.decode('utf-8', errors='replace')
        print("🔥 BODY DECODED (str):", body_str)

        # ✅ Reemplaza saltos de línea no escapados
        body_str_sin_saltos = body_str.replace('\n', ' ').replace('\r', ' ')
        print("🔥 BODY SIN SALTOS DE LÍNEA:", body_str_sin_saltos)

        # Si realmente es JSON, lo parsea
        try:
            import json
            json_recibido = json.loads(body_str_sin_saltos)
            print("✅ JSON PARSEADO:", json_recibido)
        except Exception as parse_err:
            print("❌ NO ES JSON VÁLIDO:", parse_err)
            return {"error": "El body no es un JSON válido", "body_str": body_str_sin_saltos}

        # Ahora valida contra tu modelo
        resultado = ResultadoSimitModel(**json_recibido)
        print("✅ MODELO VALIDADO:", resultado.dict())

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MICRO_URLS['JURIDICA']}/simit_api/automatizacion/resultadoSimit",
                json=resultado.dict()
            )
            response.raise_for_status()
            return response.json()

    except ValidationError as ve:
        print("❌ ERROR DE VALIDACIÓN:", ve)
        return JSONResponse(
            status_code=422,
            content={"error": "Error de validación", "detail": ve.errors()}
        )

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"🔥 ERROR CRÍTICO: {str(e)}\n{tb}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error interno del servidor", "detail": str(e)}
        )


@router.post("/notificarFinalizacionSimit")
async def gateway_notificar_finalizacion_simit(payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['JURIDICA']}/simit_api/notificarFinalizacionSimit", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    

@router.get("/simit_api/usuarioCC", tags=["Simit"])
async def gateway_darUsuarioCC():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionSimit/porCC")
            resp.raise_for_status()
            data = resp.json()
            id_enc = data.get("idEncabezado")
            ced    = data.get("cedula")

            if id_enc is None or ced is None:
                raise HTTPException(502, "Simit no devolvió idEncabezado y cedula")

        await monitor_notificacion("SIMIT", id_enc)

        return {"cedula": ced}

    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/Juridica/listarAutomatizacionesSimit", tags=["Simit"])
async def gw_listar_automatizaciones_Simit(
    offset: int | None = Query(None),
    limit: int  | None = Query(None)
):
    params = {}
    if offset is not None: params["offset"] = offset
    if limit  is not None: params["limit"]  = limit
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesSimit", params=params)
        r.raise_for_status()
        return r.json()
    
@router.get("/Juridica/automatizacionesSimit/{id_encabezado}/resumen", tags=["Automatizaciones Simit"])
async def gw_resumen_encabezado(id_encabezado: int):
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesSimit/{id_encabezado}/resumen")
        r.raise_for_status()
        return r.json()
    
#----------- ENDPOINT: NUEVA EPS RPA ----------------
@router.post("/excel/guardarNuevaEps", tags=["Nueva Eps"])
async def gateway_guardar_excel_nuevaEps(request: Request):
    try:
        form = await request.form()
        file = form["file"]
        idUsuario = int(form["idUsuario"])
        print(f"🧾 idUsuario recibido en gateway: {idUsuario}")


        content = await file.read()

        form_data = MultipartEncoder(
            fields={
                "file": (file.filename, content, file.content_type),
                "idUsuario": str(idUsuario)
            }
        )
        headers = {"Content-Type": form_data.content_type}

        timeout = httpx.Timeout(200.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{MICRO_URLS['SALUD']}/nuevaeps_api/excel/guardarNuevaEps",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        import traceback
        print("🔥 ERROR EN GATEWAY /guardarNuevaEps:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/plantillaNuevaEps", tags=["Excel"])
async def gateway_descargar_plantilla():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['SALUD']}/nuevaeps_api/excel/plantilla"
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=plantilla_nuevaEps.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/nuevaeps_api/detalle/listar_agrupadoNuevaEps", tags=["Nueva Eps"])
async def gateway_listar_detalles_agrupados():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['SALUD']}/nuevaeps_api/detalle/listar_agrupadoNuevaEps")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/nuevaeps_api/usuarioCC", tags=["Nueva Eps"])
async def gateway_darUsuarioCC():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{MICRO_URLS['SALUD']}/nuevaeps_api/automatizacionNuevaEps/porCC"
            )
            resp.raise_for_status()
            data = resp.json()
            id_enc = data.get("idEncabezado")
            ced    = data.get("cedula")

            if id_enc is None or ced is None:
                raise HTTPException(502, "Nueva Eps no devolvió idEncabezado y cédula")

        await monitor_notificacion("NUEVA EPS", id_enc)
        return {"cedula": ced}

    except httpx.HTTPStatusError as e:
        # Sigue devolviendo el detalle del microservicio
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        # Imprime el detalle para desarrollo
        print(f"HTTPStatusError en usuarioCC: {detalle}")
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        # Formatea el traceback completo
        tb = traceback.format_exc()
        # Imprime error y traceback en consola
        print("Error inesperado en usuarioCC:", e)
        print(tb)
        # Devuelve también el trace en el JSON (sólo en desarrollo)
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "trace": tb
            }
        )
@router.post("/nuevaeps_api/automatizacion/resultado", tags=["Nueva Eps"])
async def gateway_guardar_resultado_automatizacion(request: Request):
    try:
        body_bytes = await request.body()

        body_str = body_bytes.decode("utf-8", errors="replace")
        body_str = re.sub(r"[\r\n\t]+", " ", body_str)

        body_str = re.sub(
            r'("epsAnterior"\s*:\s*".*?)"COMF"(\s*,)',
            r'\1COMF"\2',
            body_str,
        )

        body_str = re.sub(r'""+', '"', body_str)

        raw_body = json.loads(body_str)


        resultado = ResultadoNuevaEpsModel(**raw_body)
        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MICRO_URLS['SALUD']}/nuevaeps_api/automatizacion/resultadoNuevaEps",
                json=resultado.dict()
            )
            response.raise_for_status()
            return response.json()

    except json.decoder.JSONDecodeError as je:
        print("❌ Error de decodificación JSON:", je)
        return JSONResponse(status_code=400, content={"error": "JSON inválido", "detail": str(je)})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/Salud/listarAutomatizacionesDetalleNuevaEps", tags=["Automatizaciones Nueva Eps"])
async def gateway_listarAutomatizacionesDetalle(id_encabezado):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['SALUD']}/nuevaeps_api/automatizacionesNuevaEps/{id_encabezado}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/Salud/listarAutomatizacionesNuevaEps", tags=["Automatizaciones Nueva Eps"])
async def gateway_listarAutomatizaciones():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['SALUD']}/nuevaeps_api/automatizacionesNuevaEps")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/exportar_resultadosNuevaEps", tags=["Excel"])
async def gateway_exportar_resultados_nuevaeps_tanda(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['SALUD']}/nuevaeps_api/excel/exportar_resultados",
                params={"id_encabezado": id_encabezado}
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=resultado_{id_encabezado}.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/notificarFinalizacionNuevaEps")
async def gateway_notificar_finalizacion_nuevaEps(payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['SALUD']}/nuevaeps_api/notificarFinalizacionNuevaEps", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
  
@router.get("/Salud/automatizacionesNuevaEps/{id_encabezado}/resumen", tags=["Automatizaciones Nueva Eps"])
async def gw_resumen_nuevaeps(id_encabezado: int):
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['SALUD']}/nuevaeps_api/automatizacionesNuevaEps/{id_encabezado}/resumen")
        r.raise_for_status()
        return r.json()

@router.get("/Salud/automatizacionesNuevaEps/{id_encabezado}/detalles", tags=["Automatizaciones Nueva Eps"])
async def gw_detalles_paginados_nuevaeps(
    id_encabezado: int,
    offset: int = Query(0),
    limit: int = Query(10),
    cc: str = Query(None)
):
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(
            f"{MICRO_URLS['SALUD']}/nuevaeps_api/automatizacionesNuevaEps/{id_encabezado}/detalles",
            params={"offset": offset, "limit": limit, **({"cc": cc} if cc else {})}
        )
        r.raise_for_status()
        return r.json()
    
@router.get("/Salud/listarAutomatizacionesNuevaEps", tags=["Automatizaciones Nueva Eps"])
async def gw_listar_automatizaciones_nuevaeps(
    offset: int | None = Query(None),
    limit: int  | None = Query(None)
):
    params = {}
    if offset is not None: params["offset"] = offset
    if limit  is not None: params["limit"]  = limit
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['SALUD']}/nuevaeps_api/automatizacionesNuevaEps", params=params)
        r.raise_for_status()
        return r.json()

    
#----------- ENDPOINT: VIGILANCIA RPA ----------------
@router.get("/vigilancia_api/detalle/listar_agrupadoVigilancia", tags=["Vigilancia"])
async def gateway_listar_detalles_agrupados():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/vigilancia_api/detalle/listar_agrupadoVigilancia")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/Jurica/listarAutomatizacionesVigilancia", tags=["Automatizaciones Vigilancia"])
async def gateway_listarAutomatizaciones():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesVigilancia")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/Jurica/listarAutomatizacionesDetalleVigilancia", tags=["Automatizaciones Vigilancia"])
async def gateway_listarAutomatizacionesDetalle(id_encabezado):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesVigilancia/{id_encabezado}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/excel/plantillaVigilancia", tags=["Excel"])
async def gateway_descargar_plantilla():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/vigilancia_api/excel/plantilla"
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=plantilla_vigilancia.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/excel/guardarVigilancia", tags=["Vigilancia"])
async def gateway_guardar_excel_vigilancia(request: Request):
    try:
        form = await request.form()
        file = form["file"]
        idUsuario = int(form["idUsuario"])
        print(f"🧾 idUsuario recibido en gateway: {idUsuario}")


        content = await file.read()

        form_data = MultipartEncoder(
            fields={
                "file": (file.filename, content, file.content_type),
                "idUsuario": str(idUsuario)
            }
        )
        headers = {"Content-Type": form_data.content_type}

        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{MICRO_URLS['JURIDICA']}/vigilancia_api/excel/guardarVigilancia",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        import traceback
        print("🔥 ERROR EN GATEWAY /guardarVigilancia:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/exportar_resultadosVigilancia", tags=["Excel"])
async def gateway_exportar_resultados_vigilancia_tanda(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/vigilancia_api/excel/exportar_resultados",
                params={"id_encabezado": id_encabezado}
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=resultado_{id_encabezado}.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    

@router.post("/vigilancia_api/automatizacion/resultado", tags=["Vigilancia"])
async def gateway_guardar_resultado_automatizacion(request: Request):
    try:
        # 🔥 Obtiene el body crudo en bytes
        body_bytes = await request.body()
        print("🔥 BODY CRUDO (bytes):", body_bytes)

        # 🔥 Intenta decodificarlo como texto
        body_str = body_bytes.decode('utf-8', errors='replace')
        print("🔥 BODY DECODED (str):", body_str)

        # ✅ Reemplaza saltos de línea no escapados
        body_str_sin_saltos = body_str.replace('\n', ' ').replace('\r', ' ')
        print("🔥 BODY SIN SALTOS DE LÍNEA:", body_str_sin_saltos)

        # Si realmente es JSON, lo parsea
        try:
            import json
            json_recibido = json.loads(body_str_sin_saltos)
            print("✅ JSON PARSEADO:", json_recibido)
        except Exception as parse_err:
            print("❌ NO ES JSON VÁLIDO:", parse_err)
            return {"error": "El body no es un JSON válido", "body_str": body_str_sin_saltos}

        # Ahora valida contra tu modelo
        resultado = ResultadoVigilanciaModel(**json_recibido)
        print("✅ MODELO VALIDADO:", resultado.dict())

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MICRO_URLS['JURIDICA']}/vigilancia_api/automatizacion/resultadoVigilancia",
                json=resultado.dict()
            )
            response.raise_for_status()
            return response.json()

    except ValidationError as ve:
        print("❌ ERROR DE VALIDACIÓN:", ve)
        return JSONResponse(
            status_code=422,
            content={"error": "Error de validación", "detail": ve.errors()}
        )

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"🔥 ERROR CRÍTICO: {str(e)}\n{tb}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error interno del servidor", "detail": str(e)}
        )


@router.post("/notificarFinalizacionVigilancia")
async def gateway_notificar_finalizacion_simit(payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['JURIDICA']}/vigilancia_api/notificarFinalizacionVigilancia", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/vigilancia_api/usuarioRadicado", tags=["Vigilancia"])
async def gateway_darUsuarioRadicado():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionVigilancia/porRadicado"
            )
            resp.raise_for_status()
            data = resp.json()

            id_enc       = data.get("idEncabezado")
            fecha_ini    = data.get("fechaInicial")
            fecha_fin    = data.get("fechaFinal")
            radicado     = data.get("radicado")


            if not all([id_enc,fecha_ini, fecha_fin, radicado]):
                raise HTTPException(
                    status_code=502,
                    detail="Faltan datos: radicado, fechaInicial, fechaFinal o idEncabezado"
                )

            await monitor_notificacion("VIGILANCIA", id_enc)

        return {
            "fechaInicial":  fecha_ini,
            "fechaFinal":    fecha_fin,
            "radicado":      radicado
        }
    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/Juridica/listarAutomatizacionesVigilancia", tags=["Vigilancia"])
async def gw_listar_automatizaciones_Vigilancia(
    offset: int | None = Query(None),
    limit: int  | None = Query(None)
):
    params = {}
    if offset is not None: params["offset"] = offset
    if limit  is not None: params["limit"]  = limit
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesVigilancia", params=params)
        r.raise_for_status()
        return r.json()
    
@router.get("/Juridica/automatizacionesVigilancia/{id_encabezado}/resumen", tags=["Automatizaciones Vigilancia"])
async def gw_resumen_encabezado(id_encabezado: int):
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesVigilancia/{id_encabezado}/resumen")
        r.raise_for_status()
        return r.json()
    
#-------------- PAUSAS RPA -------------------------------------------------------------------
@router.post("/vigilancia_api/pausar/{id_encabezado}", tags=["Vigilancia"])
async def gateway_pausar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['JURIDICA']}/vigilancia_api/pausar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        
        return resp.json()

@router.post("/vigilancia_api/reanudar/{id_encabezado}", tags=["Vigilancia"])
async def gateway_reanudar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['JURIDICA']}/vigilancia_api/reanudar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        
        return resp.json()
    
@router.post("/simit_api/pausar/{id_encabezado}", tags=["Simit"])
async def gateway_pausar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['JURIDICA']}/simit_api/pausar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        
        return resp.json()

@router.post("/simit_api/reanudar/{id_encabezado}", tags=["Simit"])
async def gateway_reanudar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['JURIDICA']}/simit_api/reanudar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        
        return resp.json()
    
@router.post("/rues_api/pausar/{id_encabezado}", tags=["Rues"])
async def gateway_pausar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['JURIDICA']}/rues_api/pausar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        
        return resp.json()

@router.post("/rues_api/reanudar/{id_encabezado}", tags=["Rues"])
async def gateway_reanudar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['JURIDICA']}/rues_api/reanudar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    
@router.post("/superNotariado_api/pausar/{id_encabezado}", tags=["SuperNotariado"])
async def gateway_pausar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['JURIDICA']}/superNotariado_api/pausar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        
        return resp.json()

@router.post("/superNotariado_api/reanudar/{id_encabezado}", tags=["SuperNotariado"])
async def gateway_reanudar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['JURIDICA']}/superNotariado_api/reanudar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@router.post("/runt_api/pausar/{id_encabezado}", tags=["Runt"])
async def gateway_pausar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['JURIDICA']}/runt_api/pausar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        
        return resp.json()

@router.post("/runt_api/reanudar/{id_encabezado}", tags=["Runt"])
async def gateway_reanudar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['JURIDICA']}/runt_api/reanudar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    
@router.post("/famisanar_api/pausar/{id_encabezado}", tags=["FamiSanar"])
async def gateway_pausar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['SALUD']}/famisanar_api/pausar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        
        return resp.json()

@router.post("/famisanar_api/reanudar/{id_encabezado}", tags=["FamiSanar"])
async def gateway_reanudar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['SALUD']}/famisanar_api/reanudar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    
@router.post("/nuevaeps_api/pausar/{id_encabezado}", tags=["Nueva Eps"])
async def gateway_pausar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['SALUD']}/nuevaeps_api/pausar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        
        return resp.json()

@router.post("/nuevaeps_api/reanudar/{id_encabezado}", tags=["Nueva Eps"])
async def gateway_reanudar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['SALUD']}/nuevaeps_api/reanudar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    
@router.post("/WhatsApp_api/pausar/{id_encabezado}", tags=["WhatsApp"])
async def gateway_pausar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['WHATSAPP']}/numero_api/pausar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        
        return resp.json()

@router.post("/WhatsApp_api/reanudar/{id_encabezado}", tags=["WhatsApp"])
async def gateway_reanudar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['WHATSAPP']}/numero_api/reanudar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    
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

#----------- ENDPOINT: WHATSAPP RPA ----------------
@router.post("/excel/guardarWhatsApp", tags=["WhatsApp"])
async def gateway_guardar_excel_WhatsApp(request: Request):
    try:
        form = await request.form()
        file = form["file"]
        idUsuario = int(form["idUsuario"])
        print(f"🧾 idUsuario recibido en gateway: {idUsuario}")


        content = await file.read()

        form_data = MultipartEncoder(
            fields={
                "file": (file.filename, content, file.content_type),
                "idUsuario": str(idUsuario)
            }
        )
        headers = {"Content-Type": form_data.content_type}

        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{MICRO_URLS['WHATSAPP']}/numero_api/excel/guardarWhatsApp",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        import traceback
        print("🔥 ERROR EN GATEWAY /guardarWhatsApp:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/plantillaWhatsApp", tags=["WhatsApp"])
async def gateway_descargar_plantilla():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['WHATSAPP']}/numero_api/excel/plantilla"
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=plantilla_whatsApp.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/WhatsApp_api/detalle/listar_agrupadoWhatsApp", tags=["WhatsApp"])
async def gateway_listar_detalles_agrupados():
    try:
        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{MICRO_URLS['WHATSAPP']}/numero_api/detalle/listar_agrupadoWhatsApp")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/WhatsApp_api/usuarioNumero", tags=["WhatsApp"])
async def gateway_darUsuarioCC():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{MICRO_URLS['WHATSAPP']}/numero_api/automatizacionWhatsApp/porNumero")
            resp.raise_for_status()
            data = resp.json()

            id_enc = data.get("idEncabezado")
            indicativo = data.get("indicativo")
            numero = data.get("numero")

            if id_enc is None or numero is None:
                raise HTTPException(502, "WhatsApp no devolvió idEncabezado y numero")

        await monitor_notificacion("WHATSAPP", id_enc)

        return {
            "indicativo": indicativo,
            "numero": numero
        }

    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/WhatsApp_api/automatizacion/resultado", tags=["WhatsApp"])
async def gateway_guardar_resultado_automatizacion(request: Request):
    raw_body = await request.json()

    try:
        ResultadoWhatsAppModel(**raw_body)
    except ValidationError as ve:
        print("❌ Validación en gateway:", ve.json())
        raise HTTPException(status_code=422, detail=ve.errors())

    try:
        async with httpx.AsyncClient(timeout=3600.0) as client:
            upstream_url = f"{MICRO_URLS['WHATSAPP']}/numero_api/automatizacion/resultadoWhatsApp"
            resp = await client.post(upstream_url, json=raw_body)
            resp.raise_for_status()
    except httpx.HTTPStatusError as hse:
        return JSONResponse(
            status_code=hse.response.status_code,
            content=hse.response.json()
        )
    except Exception as e:
        print("🔥 Error al llamar al microservicio:", str(e))
        raise HTTPException(status_code=502, detail="Bad gateway")

    return JSONResponse(status_code=resp.status_code, content=resp.json())

@router.get("/WhatsApp/listarAutomatizacionesDetalleWhatsApp", tags=["Automatizaciones WhatsApp"])
async def gateway_listarAutomatizacionesDetalle(id_encabezado):
    try:
        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{MICRO_URLS['WHATSAPP']}/numero_api/automatizacionesWhatsApp/{id_encabezado}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/WhatsApp/listarAutomatizacionesWhatsApp", tags=["Automatizaciones WhatsApp"])
async def gateway_listarAutomatizaciones():
    try:
        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{MICRO_URLS['WHATSAPP']}/numero_api/automatizacionesWhatsApp")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/exportar_resultadosWhatsApp", tags=["Excel"])
async def gateway_exportar_resultados_WhatsApp_tanda(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['WHATSAPP']}/numero_api/excel/exportar_resultados",
                params={"id_encabezado": id_encabezado}
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=resultado_{id_encabezado}.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/notificarFinalizacionWhatsApp")
async def gateway_notificar_finalizacion_WhatsApp(payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['WHATSAPP']}/numero_api/notificarFinalizacionWhatsApp", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
#-----------CAMARA DE COMERCIO------------------------------------
@router.get("/camaraComercio_api/detalle/listar_agrupadoCamaraComercio", tags=["Camara Comercio"])
async def gateway_listar_detalles_agrupados():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/detalle/listar_agrupadoCamaraComercio")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/Jurica/listarAutomatizacionesCamaraComercio", tags=["Automatizaciones Camara Comercio"])
async def gateway_listarAutomatizaciones():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesCamaraComercio")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/notificarFinalizacionCamaraComercio", tags=["Camara Comercio"])
async def gateway_notificar_finalizacion_runt(payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['JURIDICA']}/camaraComercio_api/notificarFinalizacionCamaraComercio", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/Jurica/listarAutomatizacionesDetalleCamaraComercio", tags=["Automatizaciones Camara Comercio"])
async def gateway_listarAutomatizacionesDetalle(id_encabezado):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesCamaraComercio/{id_encabezado}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/camaraComercio_api/pausar/{id_encabezado}", tags=["Camara Comercio"])
async def gateway_pausar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['JURIDICA']}/camaraComercio_api/pausar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        
        return resp.json()
    
@router.post("/camaraComercio_api/reanudar/{id_encabezado}", tags=["Camara Comercio"])
async def gateway_reanudar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['JURIDICA']}/camaraComercio_api/reanudar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    
@router.get("/excel/plantillaCamaraComercio", tags=["Excel"])
async def gateway_descargar_plantilla():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/camaraComercio_api/excel/plantilla"
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=plantilla_camaraComercio.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/excel/guardarCamaraComercio", tags=["Camara Comercio"])
async def gateway_guardar_excel_camaraComercio(request: Request):
    try:
        form = await request.form()
        file = form["file"]
        idUsuario = int(form["idUsuario"])
        print(f"🧾 idUsuario recibido en gateway: {idUsuario}")


        content = await file.read()

        form_data = MultipartEncoder(
            fields={
                "file": (file.filename, content, file.content_type),
                "idUsuario": str(idUsuario)
            }
        )
        headers = {"Content-Type": form_data.content_type}

        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{MICRO_URLS['JURIDICA']}/camaraComercio_api/excel/guardarCamaraComercio",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        import traceback
        print("🔥 ERROR EN GATEWAY /guardarCamaraComercio:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/exportar_resultadosCamaraComercio", tags=["Excel"])
async def gateway_exportar_resultados_camaraComercio_tanda(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/camaraComercio_api/excel/exportar_resultados",
                params={"id_encabezado": id_encabezado}
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=resultado_{id_encabezado}.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
def escape_unescaped_quotes_in_values(text: str) -> str:
    def fix_quotes(match):
        key = match.group(1)
        value = match.group(2)
        # Escapa comillas dobles sin escapar dentro del valor
        fixed_value = re.sub(r'(?<!\\)"', r'\\"', value)
        return f'"{key}": "{fixed_value}"'

    # Aplica sobre cada par clave:valor tipo string
    return re.sub(r'"([^"]+)"\s*:\s*"([^"]*?)"', fix_quotes, text)


@router.post("/camaraComercio_api/automatizacion/resultado", tags=["Camara Comercio"])
async def gateway_guardar_resultado_automatizacion(request: Request):
    try:
        raw = await request.body()
        text = raw.decode("utf-8", errors="replace")

        try:
            data = json.loads(text)
        except json.JSONDecodeError as je:
            print("❗ JSON inválido, intentando auto-escape de comillas internas:", je)
            text_fixed = escape_unescaped_quotes_in_values(text)
            print("📄 JSON corregido:\n", text_fixed)
            data = json.loads(text_fixed)

        resultado = ResultadoCamaraComercioModel(**data)
        payload = resultado.model_dump() if hasattr(resultado, "model_dump") else resultado.dict()

        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{MICRO_URLS['JURIDICA']}/camaraComercio_api/automatizacion/resultadoCamaraComercio",
                json=payload
            )
            r.raise_for_status()
            return r.json()

    except json.JSONDecodeError as je:
        return JSONResponse(status_code=400, content={"error": "JSON inválido", "detail": str(je)})

    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={"error": "Error interno del servidor", "detail": str(e), "trace": traceback.format_exc()}
        )

@router.get("/camaraComercio_api/usuarioCC", tags=["Camara Comercio"])
async def gateway_darUsuarioCC():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionCamaraComercio/porCC")
            resp.raise_for_status()
            data = resp.json()
            id_enc = data.get("idEncabezado")
            ced    = data.get("cedula")

            if id_enc is None or ced is None:
                raise HTTPException(502, "Camara Comercio no devolvió idEncabezado y cedula")

        await monitor_notificacion("CAMARACOMERCIO", id_enc)

        return {"cedula": ced}

    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/Juridica/listarAutomatizacionesCamaraComercio", tags=["Camara Comercio"])
async def gw_listar_automatizaciones_CamaraComercio(
    offset: int | None = Query(None),
    limit: int  | None = Query(None)
):
    params = {}
    if offset is not None: params["offset"] = offset
    if limit  is not None: params["limit"]  = limit
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesCamaraComercio", params=params)
        r.raise_for_status()
        return r.json()
    
@router.get("/Juridica/automatizacionesCamaraComercio/{id_encabezado}/resumen", tags=["Camara Comercio"])
async def gw_resumen_encabezado(id_encabezado: int):
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesCamaraComercio/{id_encabezado}/resumen")
        r.raise_for_status()
        return r.json()


#----------- ENVIO CORREO ------------------------------------
@router.post("/correos/email/upload_excel", tags=["Email Masivo"])
async def gateway_correos_upload_excel(file: UploadFile = File(...)):
    """
    Sube el Excel al servidor (EMAIL_MASIVO_DIR) y devuelve el nombre guardado.
    Este nombre luego se envía en el payload como 'excelFileName'.
    """
    try:
        base_dir = os.getenv("EMAIL_MASIVO_DIR")
        base_dir = os.path.normpath(base_dir)
        os.makedirs(base_dir, exist_ok=True)

        # Nombre seguro
        original = file.filename or "destinatarios.xlsx"
        safe_name = re.sub(r"[^a-zA-Z0-9_.\- ]", "_", original).strip() or "destinatarios.xlsx"
        dest = os.path.join(base_dir, safe_name)

        # Guardar archivo
        content = await file.read()
        with open(dest, "wb") as f:
            f.write(content)

        print("📄 Excel guardado en:", dest)
        return {"serverFileName": safe_name}
    except Exception as e:
        print("❌ Error upload_excel:", e)
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/correos/adjuntos/subir", tags=["Email Masivo"])
async def gateway_correos_subir_adjuntos(
    files: List[UploadFile] = File(...),
    folder: Optional[str] = Form(None)
):
    base_dir = os.getenv("EMAIL_ATTACH_DIR", os.path.join(os.getcwd(), "data", "emails", "attachments"))
    base_dir = os.path.normpath(base_dir)

    folder = (folder or "").strip()
    if folder and folder.lower() != "string":
        safe_folder = re.sub(r"[^a-zA-Z0-9_.\- ]", "_", folder)
        base_dir = os.path.join(base_dir, safe_folder)
    saved = []
    for f in files:
        safe_name = re.sub(r"[^a-zA-Z0-9_.\- ]", "_", f.filename or "adjunto.bin")
        dest = os.path.join(base_dir, safe_name)
        with open(dest, "wb") as out:
            out.write(await f.read())
        saved.append(safe_name)
    return {"base_dir": os.path.abspath(base_dir), "saved": saved}

@router.post("/correos/Email", tags=["Email Masivo"])
async def gateway_impulso_email(payload: dict):
    try:
        timeout = httpx.Timeout(1200.0, connect=10.0) 
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{MICRO_URLS['EMAIL']}/EmailMasivo",
                json=payload
            )
        try:
            json_response = response.json()
            return JSONResponse(content=json_response, status_code=response.status_code)
        except Exception as inner_err:
            print("ERROR al parsear JSON:", str(inner_err))
            return JSONResponse(content={"raw": response.text}, status_code=response.status_code)

    except Exception as e:
        print("ERROR AL ENVIAR REQUEST:")
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/docs/generar", tags=["Documentos"])
async def gateway_generar_docs(payload: dict = Body(...)):
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{MICRO_URLS['EMAIL']}/GenerarDocsPDF",
                json=payload
            )
            resp.raise_for_status()
            return Response(
                content=resp.content,
                media_type="application/zip",
                headers={"Content-Disposition": f'attachment; filename="documentos_personalizados.zip"'}
            )
    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/correos/email/download_excel", tags=["Impulso Email"])
async def gateway_correos_download_excel(
    file: str = Query(..., description="Nombre devuelto por /correos/email/upload_excel")
):
    try:
        base_dir = os.getenv("EMAIL_MASIVO_DIR", os.path.join(os.getcwd(), "data", "emails", "excels"))
        base_dir = os.path.normpath(base_dir)

        safe = re.sub(r"[^a-zA-Z0-9_.\- /\\]", "_", file).strip()
        path = os.path.normpath(os.path.join(base_dir, safe))

        base_norm = os.path.normpath(base_dir)
        if not (path == base_norm or path.startswith(base_norm + os.sep)):
            return JSONResponse(status_code=400, content={"error": "Ruta inválida"})

        if not os.path.isfile(path):
            return JSONResponse(status_code=404, content={"error": f"No existe: {safe}"})

        with open(path, "rb") as f:
            data = f.read()

        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'inline; filename="{os.path.basename(path)}"'}
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/correos/senders", tags=["Email Masivo"])
async def gateway_listar_remitentes_simples():
    import os
    senders = []
    i = 1
    while True:
        addr = os.getenv(f"EMAIL_{i}")
        if not addr:
            break
        senders.append(addr.strip())
        i += 1
    return {"emails": senders}

@router.get("/correos/encabezados", tags=["Correos"])
async def gw_listar_encabezados():
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{MICRO_URLS['EMAIL']}/EmailEnvios/Encabezados")
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/correos/detalle", tags=["Correos"])
async def gw_listar_detalle(idEncabezado: int = Query(...)):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{MICRO_URLS['EMAIL']}/EmailEnvios/Detalle", params={"idEncabezado": idEncabezado})
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))