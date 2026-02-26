from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Query, Body, Form
import httpx
from urllib.parse import unquote
from urllib.parse import quote
from zoneinfo import ZoneInfo
from fastapi.responses import StreamingResponse, RedirectResponse
from datetime import datetime, time as dtime
from config.microservices_config import MICRO_URLS
from typing import Dict, Optional, List, Any
import io
import pandas as pd
from fastapi import Query
from starlette.responses import JSONResponse
from requests_toolbelt.multipart.encoder import MultipartEncoder
from fastapi.responses import Response
from pydantic import BaseModel,Field
from starlette.responses import JSONResponse
from api.monitor_rpa import notificacion as monitor_notificacion
from bll.monitor_rpa_bll import obtener_dashboard, listar_encabezados_rpa, listar_detalles_rpa_paginados, listar_todos_detalles_por_origen, buscar_detalle_por_cedulaBLL
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

@router.get("/__debug_file")
def debug_file():
    return {"running_file": __file__}

# ---- HELPERS PARA REMITENTE DIREECCIONAR A MICROSERVICIO IMAGENES---------------------
def pick_emailclick_micro(sender_email: str) -> str:
    sender_email = (sender_email or "").replace(" ", "").strip().lower()

    # Opción A: lista explícita de remitentes de Perú
    PERU_SENDERS = {
        "comunicaciones.peru@sgnpl.com",
    }
    if sender_email in PERU_SENDERS:
        return MICRO_URLS["EMAILCLICKPERU"]

    return MICRO_URLS["EMAILCLICKCOLOMBIA"]

# ---- HELPERS PARA REMITENTE DIREECCIONAR A MICROSERVICIO MASIVOS---------------------
def pick_emailclick_microMASIVOS(sender_email: str) -> str:
    sender_email = (sender_email or "").replace(" ", "").strip().lower()

    # Opción A: lista explícita de remitentes de Perú
    PERU_SENDERS = {
        "comunicaciones.peru@sgnpl.com",
    }
    if sender_email in PERU_SENDERS:
        return MICRO_URLS["EMAILPERU"]

    return MICRO_URLS["EMAIL"]

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
            correo = data.get("correo")

            if id_enc is None or ced is None:
                raise HTTPException(502, "Super Notariado no devolvió idEncabezado y cedula")

        await monitor_notificacion("SUPER NOTARIADO", id_enc)

        return {"CC": ced, "correo": correo}

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
        url = f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionRunt/porCC"
        timeout = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            id_enc = data.get("idEncabezado")
            ced = data.get("cedula")
            correo = data.get("correo")
            if id_enc is None or ced is None:
                raise HTTPException(502, "Runt no devolvió idEncabezado y cedula")
        await monitor_notificacion("RUNT", id_enc)

        return {"cedula": ced, "correo": correo}

    except httpx.RequestError as e:
        return JSONResponse(status_code=502, content={"error": "Error llamando microservicio", "detail": repr(e)})

    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": repr(e)})

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
            correo = data.get("correo")

            if id_enc is None or ced is None:
                raise HTTPException(502, "Rues no devolvió idEncabezado y cedula")

        await monitor_notificacion("RUES", id_enc)

        return {"cedula": ced, "correo": correo}

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
            correo = data.get("correo")

            if id_enc is None or ced is None:
                raise HTTPException(502, "FamiSanar no devolvió idEncabezado y cedula")

        await monitor_notificacion("FAMISANAR", id_enc)

        return {"cedula": ced, "correo": correo}

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

        # 🔥 Intenta decodificarlo como texto
        body_str = body_bytes.decode('utf-8', errors='replace')

        # ✅ Reemplaza saltos de línea no escapados
        body_str_sin_saltos = body_str.replace('\n', ' ').replace('\r', ' ')

        # Si realmente es JSON, lo parsea
        try:
            import json
            json_recibido = json.loads(body_str_sin_saltos)
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
            correo = data.get("correo")

            if id_enc is None or ced is None:
                raise HTTPException(502, "Simit no devolvió idEncabezado y cedula")

        await monitor_notificacion("SIMIT", id_enc)

        return {"cedula": ced, "correo": correo}

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
            correo = data.get("correo")

            if id_enc is None or ced is None:
                raise HTTPException(502, "Nueva Eps no devolvió idEncabezado y cédula")

        await monitor_notificacion("NUEVA EPS", id_enc)
        return {"cedula": ced, "correo": correo}

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

        # 🔥 Intenta decodificarlo como texto
        body_str = body_bytes.decode('utf-8', errors='replace')

        # ✅ Reemplaza saltos de línea no escapados
        body_str_sin_saltos = body_str.replace('\n', ' ').replace('\r', ' ')

        # Si realmente es JSON, lo parsea
        try:
            import json
            json_recibido = json.loads(body_str_sin_saltos)
        except Exception as parse_err:
            print("❌ NO ES JSON VÁLIDO:", parse_err)
            return {"error": "El body no es un JSON válido", "body_str": body_str_sin_saltos}

        # Ahora valida contra tu modelo
        resultado = ResultadoVigilanciaModel(**json_recibido)

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
            correo       = data.get("correo")

            if not all([id_enc,fecha_ini, fecha_fin, radicado, correo]):
                raise HTTPException(
                    status_code=502,
                    detail="Faltan datos: radicado, fechaInicial, fechaFinal o idEncabezado"
                )

            await monitor_notificacion("VIGILANCIA", id_enc)

        return {
            "fechaInicial":  fecha_ini,
            "fechaFinal":    fecha_fin,
            "radicado":      radicado,
            "correo":       correo
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

@router.get("/WhatsApp/stats", tags=["WhatsApp"])
async def gateway_whatsapp_stats():
    """
    Obtiene estadísticas de validación de números de WhatsApp.
    
    Returns:
        JSON con números validados y contador de pendientes
    """
    try:
        from config.db_config import get_connection

        conn = get_connection()
        cur = conn.cursor()
        
        # Obtener números validados
        cur.execute("""
            SELECT numero, tiene_whatsApp, fecha_validacion 
            FROM [NEXUM].[dbo].[WhatsAppDetalle] WITH(NOLOCK)
            WHERE tiene_whatsApp <> ''
            AND idEncabezado = 44
        """)
        validados = [{"numero": row[0], "tiene_whatsApp": row[1], "fecha_validacion": row[2]} 
                    for row in cur.fetchall()]

        # Obtener contador de pendientes 
        cur.execute("""
            SELECT COUNT(*) as pendientes
            FROM [NEXUM].[dbo].[WhatsAppDetalle] WITH(NOLOCK)
            WHERE tiene_whatsApp = ''
            AND idEncabezado = 44
        """)
        pendientes = cur.fetchone()[0]

        cur.close()
        conn.close()

        return {
            "data": validados,
            "pendientes": pendientes
        }

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
            correo = data.get("correo")

            if id_enc is None or ced is None or correo is None:
                raise HTTPException(502, "Camara Comercio no devolvió idEncabezado y cedula")

        await monitor_notificacion("CAMARACOMERCIO", id_enc)

        return {"cedula": ced, "correo": correo}

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
    sender = payload.get("senderEmail", "")
    micro_base = pick_emailclick_microMASIVOS(sender)
    try:
        timeout = httpx.Timeout(12000.0, connect=10.0) 
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{micro_base}/EmailMasivo",
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
            r = await client.get(f"{MICRO_URLS['EMAILREPORTES']}/EmailEnvios/Encabezados")
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
            r = await client.get(f"{MICRO_URLS['EMAILREPORTES']}/EmailEnvios/Detalle", params={"idEncabezado": idEncabezado})
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/correos/exportarExcelPorEncabezado", tags=["Correos"])
async def gateway_exportar_excel_por_encabezado(idEncabezado: int = Query(...)):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{MICRO_URLS['EMAILREPORTES']}/EmailEnvios/ExportarExcelPorEncabezado",
                params={"idEncabezado": idEncabezado}
            )
            resp.raise_for_status()
            filename = resp.headers.get("content-disposition", 'attachment; filename="reporte.xlsx"')
            return StreamingResponse(
                io.BytesIO(resp.content),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": filename}
            )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _clean_params(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None and v != ""}

@router.get("/correos/dashboard/resumen", tags=["Correos"])
async def gw_correos_dashboard_resumen(
    fecha_inicio: str | None = Query(None),
    fecha_fin: str | None = Query(None),
    idUsuario: int | None = Query(None),
    remitente: str | None = Query(None),
):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{MICRO_URLS['EMAILREPORTES']}/EmailEnvios/Dashboard/Resumen",
                params=_clean_params({
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin,
                    "idUsuario": idUsuario,
                    "remitente": remitente,
                }),
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correos/dashboard/porRemitente", tags=["Correos"])
async def gw_correos_dashboard_por_remitente(
    fecha_inicio: str | None = Query(None),
    fecha_fin: str | None = Query(None),
    idUsuario: int | None = Query(None),
):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{MICRO_URLS['EMAILREPORTES']}/EmailEnvios/Dashboard/PorRemitente",
                params=_clean_params({"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin, "idUsuario": idUsuario}),
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correos/dashboard/porDia", tags=["Correos"])
async def gw_correos_dashboard_por_dia(
    fecha_inicio: str | None = Query(None),
    fecha_fin: str | None = Query(None),
    idUsuario: int | None = Query(None),
    remitente: str | None = Query(None),
):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{MICRO_URLS['EMAILREPORTES']}/EmailEnvios/Dashboard/PorDia",
                params=_clean_params({
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin,
                    "idUsuario": idUsuario,
                    "remitente": remitente,
                }),
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correos/dashboard/topErrores", tags=["Correos"])
async def gw_correos_dashboard_top_errores(
    fecha_inicio: str | None = Query(None),
    fecha_fin: str | None = Query(None),
    idUsuario: int | None = Query(None),
    remitente: str | None = Query(None),
    top: int = Query(20, ge=1, le=100),
):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{MICRO_URLS['EMAILREPORTES']}/EmailEnvios/Dashboard/TopErrores",
                params=_clean_params({
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin,
                    "idUsuario": idUsuario,
                    "remitente": remitente,
                    "top": top,
                }),
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------- PAUSAR CORREOS MASIVOS------------------------------
@router.post("/correos/encabezados/{id_encabezado}/pausar", tags=["Correos"])
async def gw_email_pausar(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{MICRO_URLS['EMAIL']}/EmailEnvios/Pausar/{id_encabezado}")
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/correos/encabezados/{id_encabezado}/reanudar", tags=["Correos"])
async def gw_email_reanudar(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{MICRO_URLS['EMAIL']}/EmailEnvios/Reanudar/{id_encabezado}")
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/correos/encabezados/{id_encabezado}/cancelar", tags=["Correos"])
async def gw_email_cancelar(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{MICRO_URLS['EMAIL']}/EmailEnvios/Cancelar/{id_encabezado}")
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
#--------------RPA JURIDICO-------------------------------------
@router.get("/juridicoBot_api/detalle/listar_agrupadoJuridico", tags=["Juridico"])
async def gateway_listar_detalles_agrupados():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/detalle/listar_agrupadoJuridico")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/Jurica/listarAutomatizacionesJuridico", tags=["Automatizaciones Juridico"])
async def gateway_listarAutomatizaciones():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesJuridico")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/Jurica/listarAutomatizacionesDetalleJuridico", tags=["Automatizaciones Juridico"])
async def gateway_listarAutomatizacionesDetalle(id_encabezado):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesJuridico/{id_encabezado}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/excel/plantillaJuridico", tags=["Excel"])
async def gateway_descargar_plantilla():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/juridica_api/excel/plantilla"
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=plantilla_juridico.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/excel/guardarJuridico", tags=["Juridico"])
async def gateway_guardar_excel_Juridico(request: Request):
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
                f"{MICRO_URLS['JURIDICA']}/juridica_api/excel/guardarJuridico",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        import traceback
        print("🔥 ERROR EN GATEWAY /guardarJuridico:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/exportar_resultadosJuridico", tags=["Excel"])
async def gateway_exportar_resultados_juridico_tanda(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/juridica_api/excel/exportar_resultados",
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

    
@router.post("/notificarFinalizacionJuridico")
async def gateway_notificar_finalizacion_juridico(payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['JURIDICA']}/juridica_api/notificarFinalizacionJuridico", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/Juridica/accion5", tags=["Juridico"])
async def gw_accion5(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/acciones/{id_encabezado}/accion5")
        r.raise_for_status()
        return r.json()

@router.get("/Juridica/accion4", tags=["Juridico"])
async def gw_accion4(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/acciones/{id_encabezado}/accion4")
        r.raise_for_status()
        return r.json()


#--------------RPA TYBA-------------------------------------
class ResultadoTybaModel(BaseModel):
    cedula: str
    radicado: Optional[str]
    proceso: Optional[str]
    departamento: Optional[str]
    coorporacion: Optional[str]
    distrito: Optional[str]
    despacho: Optional[str]
    telefono: Optional[str]
    correo: Optional[str]
    fechaProvidencia: Optional[str]
    tipoProceso: Optional[str]
    subclaseProceso: Optional[str]
    ciudad: Optional[str]
    especialidad: Optional[str]
    numeroDespacho: Optional[str]
    direccion: Optional[str]
    celular: Optional[str]
    fechaPublicacion: Optional[str]
    sujetos: Optional[str]
    actuaciones: Optional[str]

@router.get("/Jurica/listarAutomatizacionesTyba", tags=["Automatizaciones Tyba"])
async def gateway_listarAutomatizaciones():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesTyba")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/Jurica/listarAutomatizacionesDetalleTyba", tags=["Automatizaciones Tyba"])
async def gateway_listarAutomatizacionesDetalle(id_encabezado):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesTyba/{id_encabezado}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.post("/excel/guardarTyba", tags=["Tyba"])
async def gateway_guardar_excel_tyba(request: Request):
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
                f"{MICRO_URLS['JURIDICA']}/tyba_api/excel/guardarTyba",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        import traceback
        print("🔥 ERROR EN GATEWAY /guardarTyba:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/excel/listarTyba", tags=["Excel"])
async def gateway_listar_archivos_excel():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/tyba_api/excel/listar")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/excel/plantillaTyba", tags=["Excel"])
async def gateway_descargar_plantilla():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/tyba_api/excel/plantilla"
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=plantilla_tyba.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/tyba_api/detalle/listar_agrupadoTyba", tags=["Tyba"])
async def gateway_listar_detalles_agrupados():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/tyba_api/detalle/listar_agrupadoTyba")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/tyba_api/usuarioCC", tags=["Tyba"])
async def gateway_darUsuarioCC():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionTyba/porCC")
            resp.raise_for_status()
            data = resp.json()
            id_enc = data.get("idEncabezado")
            ced    = data.get("cedula")
            correo = data.get("correo")

            if id_enc is None or ced is None or correo is None:
                raise HTTPException(502, "Runt no devolvió idEncabezado, cedula y correo")

        await monitor_notificacion("TYBA", id_enc)

        return {"cedula": ced, "correo": correo}

    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.post("/tyba_api/automatizacion/resultado", tags=["Tyba"])
async def gateway_guardar_resultado_automatizacion(request: Request):
    try:
        # Decodificar sin reemplazar caracteres inválidos
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')

        # Limpieza más robusta: reemplaza caracteres de control no válidos para JSON
        body_str_cleaned = re.sub(r'[\x00-\x1F\x7F]+', ' ', body_str)

        print("📥 Body recibido (raw):", body_str_cleaned)

        # Cargar JSON limpio
        raw_body = json.loads(body_str_cleaned)
        print("📦 Body como dict:", raw_body)

        resultado = ResultadoTybaModel(**raw_body)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MICRO_URLS['JURIDICA']}/tyba_api/automatizacion/resultadoTyba",
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
    
@router.get("/excel/exportar_resultadosTyba", tags=["Excel"])
async def gateway_exportar_resultados_tyba_tanda(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/tyba_api/excel/exportar_resultados",
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
    
@router.post("/notificarFinalizacionTyba", tags=["Tyba"])
async def gateway_notificar_finalizacion_tyba(payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['JURIDICA']}/tyba_api/notificarFinalizacionTyba", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.post("/tyba_api/pausar/{id_encabezado}", tags=["Tyba"])
async def gateway_pausar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['JURIDICA']}/tyba_api/pausar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        
        return resp.json()

@router.post("/tyba_api/reanudar/{id_encabezado}", tags=["Tyba"])
async def gateway_reanudar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['JURIDICA']}/tyba_api/reanudar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

@router.get("/Juridica/listarAutomatizacionesTyba", tags=["Tyba"])
async def gw_listar_automatizaciones_Simit(
    offset: int | None = Query(None),
    limit: int  | None = Query(None)
):
    params = {}
    if offset is not None: params["offset"] = offset
    if limit  is not None: params["limit"]  = limit
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesTyba", params=params)
        r.raise_for_status()
        return r.json()
    
@router.get("/Juridica/automatizacionesTyba/{id_encabezado}/resumen", tags=["Automatizaciones Tyba"])
async def gw_resumen_encabezado(id_encabezado: int):
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        r = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesTyba/{id_encabezado}/resumen")
        r.raise_for_status()
        return r.json()
    
#--------------RPA VIGENCIA-------------------------------------
@router.get("/vigenciaJuridico_api/detalle/listar_agrupadoVigencia", tags=["Vigencia"])
async def gateway_listar_detalles_agrupados():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/detalle/listar_agrupadoVigencia")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/Jurica/listarAutomatizacionesVigencia", tags=["Automatizaciones Vigencia"])
async def gateway_listarAutomatizaciones():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesVigencia")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/Jurica/listarAutomatizacionesDetalleVigencia", tags=["Automatizaciones Vigencia"])
async def gateway_listarAutomatizacionesDetalle(id_encabezado):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MICRO_URLS['JURIDICA']}/juridica_api/automatizacionesVigencia/{id_encabezado}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(e)
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/excel/plantillaVigencia", tags=["Excel"])
async def gateway_descargar_plantilla():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/juridica_api/excel/plantillaVigencia"
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=plantilla_vigencia.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/excel/guardarVigencia", tags=["Vigencia"])
async def gateway_guardar_excel_Vigencia(request: Request):
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
                f"{MICRO_URLS['JURIDICA']}/juridica_api/excel/guardarVigencia",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        import traceback
        print("🔥 ERROR EN GATEWAY /guardarVigencia:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/exportar_resultadosVigencia", tags=["Excel"])
async def gateway_exportar_resultados_Vigencia_tanda(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['JURIDICA']}/juridica_api/excel/exportar_resultadosVigencia",
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

    
@router.post("/notificarFinalizacionVigencia")
async def gateway_notificar_finalizacion_Vigencia(payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['JURIDICA']}/juridica_api/notificarFinalizacionVigencia", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.post("/vigenciaJuridico_api/pausar/{id_encabezado}", tags=["Vigencia"])
async def gateway_pausar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['JURIDICA']}/juridica_api/pausar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        
        return resp.json()

@router.post("/vigenciaJuridico_api/reanudar/{id_encabezado}", tags=["Vigencia"])
async def gateway_reanudar_encabezado(id_encabezado: int):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{MICRO_URLS['JURIDICA']}/juridica_api/reanudar/{id_encabezado}"
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()

#--------- MENSAJES WHATSAPP------------------------------------------------------------
@router.post("/excel/guardarMensajeWhatsApp", tags=["Mensaje WhatsApp"])
async def gateway_guardar_excel_MensajeWhatsApp(request: Request):
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
                f"{MICRO_URLS['MENSAJESWHATSAPP']}/mensajeWhatsapp_api/excel/guardarWhatsApp",
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

@router.get("/excel/plantillaMensajeWhatsApp", tags=["WhatsApp"])
async def gateway_descargar_plantilla():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['MENSAJESWHATSAPP']}/mensajeWhatsapp_api/excel/plantilla"
            )
            response.raise_for_status()
            return Response(
                content=response.content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=plantilla_Mensajes_WhatsApp.xlsx"}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/WhatsApp_api/detalle/listar_agrupadoMensajeWhatsApp", tags=["WhatsApp"])
async def gateway_listar_detalles_agrupados():
    try:
        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{MICRO_URLS['MENSAJESWHATSAPP']}/mensajeWhatsapp_api/detalle/listar_agrupadoMensajeWhatsApp")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/MensajeWhatsApp_api/usuarioNumero", tags=["Mensaje WhatsApp"])
async def gateway_darUsuarioCC():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{MICRO_URLS['MENSAJESWHATSAPP']}/mensajeWhatsapp_api/automatizacionMensajeWhatsApp/porNumero")
            resp.raise_for_status()
            data = resp.json()

            id_enc = data.get("idEncabezado")
            numero = data.get("numero")
            mensaje = data.get("mensaje")
            correo = data.get("correo")

            if id_enc is None or numero is None:
                raise HTTPException(502, "WhatsApp no devolvió idEncabezado y numero")

        await monitor_notificacion("MENSAJEWHATSAPP", id_enc)

        mensaje_encoded = quote((mensaje or ""), safe="")

        return {
            "numero": numero,
            "mensaje": mensaje_encoded,
            "correo": correo
        }

    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/WhatsApp/listarAutomatizacionesDetalleMensajeWhatsApp", tags=["Automatizaciones WhatsApp"])
async def gateway_listarAutomatizacionesDetalle(id_encabezado):
    try:
        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{MICRO_URLS['MENSAJESWHATSAPP']}/mensajeWhatsapp_api/automatizacionesMensajeWhatsApp/{id_encabezado}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/WhatsApp/listarAutomatizacionesMensajeWhatsApp", tags=["Automatizaciones WhatsApp"])
async def gateway_listarAutomatizaciones():
    try:
        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{MICRO_URLS['MENSAJESWHATSAPP']}/mensajeWhatsapp_api/automatizacionesMensajeWhatsApp")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/exportar_resultadosMensajeWhatsApp", tags=["Excel"])
async def gateway_exportar_resultados_WhatsApp_tanda(id_encabezado: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{MICRO_URLS['MENSAJESWHATSAPP']}/mensajeWhatsapp_api/excel/exportar_resultados",
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

@router.post("/notificarFinalizacionMensajeWhatsApp")
async def gateway_notificar_finalizacion_WhatsApp(payload: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{MICRO_URLS['MENSAJESWHATSAPP']}/mensajeWhatsapp_api/notificarFinalizacionMensajeWhatsApp", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
#--------------RPA COLTEFINANCIERA-------------------------------------
class ResultadoColtefinancieraModel(BaseModel):
    CuentaDeposito: Optional[str]
    FechaTransaccion: Optional[str]
    FechaHoraAplicacion: Optional[str]
    Descripcion: Optional[str]
    Referencia: Optional[str]
    Debito: Optional[str]
    Credito: Optional[str]
    Tipo: Optional[str]

@router.post("/coltefinanciera_api/automatizacion/resultado", tags=["Coltefinanciera"])
async def gateway_guardar_resultado_automatizacion(request: Request):
    try:
        # Decodificar sin reemplazar caracteres inválidos
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')

        # Limpieza más robusta: reemplaza caracteres de control no válidos para JSON
        body_str_cleaned = re.sub(r'[\x00-\x1F\x7F]+', ' ', body_str)

        print("📥 Body recibido (raw):", body_str_cleaned)

        # Cargar JSON limpio
        raw_body = json.loads(body_str_cleaned)
        print("📦 Body como dict:", raw_body)

        resultado = ResultadoColtefinancieraModel(**raw_body)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MICRO_URLS['COLTEFINANCIERA']}/coltefinanciera_api/automatizacion/resultadoColtefinanciera",
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

#--------------RPA MENSAJES WHATSAPP-------------------------------------
class AdjItem(BaseModel):
    filename: str = Field(..., description="Nombre del archivo")
    mimetype: str = Field(..., description="MIME")
    base64:   str = Field(..., description="Contenido en base64 (sin 'data:...;base64,')")

class MensajeWhatsAppPayload(BaseModel):
    numeros: List[str]
    mensaje: str
    adjuntos: List[AdjItem] = []

@router.post("/MensajeWhatsApp/registrar", tags=["Mensaje WhatsApp"])
async def gateway_registrar_mensaje_whatsapp(
    request: Request,
    mensaje: str = Form(...),
    adjuntos: Optional[List[UploadFile]] = File(None),
):
    try:
        form_data = await request.form()
        numeros = form_data.getlist('numeros')
        campana = form_data.get('campana')

        # ⬇️ 1) Tomar el user-id (header preferido; si no, del form)
        user_from_header = request.headers.get("X-User-Id")
        id_usuario_app = None
        if user_from_header and str(user_from_header).isdigit():
            id_usuario_app = user_from_header
        else:
            id_usuario_form = form_data.get("idUsuarioApp")
            if id_usuario_form and str(id_usuario_form).isdigit():
                id_usuario_app = id_usuario_form

        if not numeros:
            return JSONResponse(status_code=400, content={"error": "No se recibieron números"})

        async with httpx.AsyncClient(timeout=120.0) as client:
            fields = []
            for n in numeros:
                fields.append(("numeros", n))
            fields.append(("mensaje", mensaje))
            if campana:
                fields.append(("campana", campana))

            # ⬇️ 2) Reenviar el user-id al micro (como campo form)
            if id_usuario_app:
                fields.append(("idUsuarioApp", str(id_usuario_app)))

            if adjuntos:
                for f in adjuntos:
                    content = await f.read()
                    await f.seek(0)
                    fields.append(("files", (f.filename, content, f.content_type or "application/octet-stream")))

            mp = MultipartEncoder(fields=fields)
            headers = {"Content-Type": mp.content_type}

            # (opcional) también puedes propagar el header al micro:
            if id_usuario_app:
                headers["X-User-Id"] = str(id_usuario_app)

            resp = await client.post(
                f"{MICRO_URLS['MENSAJESWHATSAPP']}/enviowhatsapp_api/whatsapp/registrar",
                content=mp.to_string(),
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        print("\n==== HTTPStatusError en Gateway ====")
        try:
            print("request:", e.request.method, str(e.request.url))
            print("response.status:", e.response.status_code)
            print("response.text:", e.response.text)
        except Exception:
            pass
        print("===========================================================")

        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        print("\n==== Exception NO HTTP en Gateway ====")
        print("type:", type(e).__name__)
        print("msg:", str(e))
        print("traceback:\n", "".join(traceback.format_exc()))
        print("===========================================================")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": "".join(traceback.format_exc())},
        )

TZ = ZoneInfo("America/Bogota")
HORA_INICIO = dtime(7, 0)   # 07:00
HORA_FIN    = dtime(19, 0)  # 19:00

@router.get("/gateway-rpa/MensajeWhatsApp/pendientes-json", tags=["Mensaje WhatsApp"])
async def gateway_pendientes_json(
    estado: str = Query("ENVIADO", description="Estado a marcar cuando se entregue al RPA")
):
    # Bloqueo por horario (solo entrega data entre 07:00 y 19:00, hora Bogotá)
    ahora_bo = datetime.now(TZ).time()
    if not (HORA_INICIO <= ahora_bo < HORA_FIN):
        return JSONResponse(
            status_code=200,
            content=[],
        )
    try:
        async with httpx.AsyncClient(timeout=360.0) as client:
            resp = await client.get(
                f"{MICRO_URLS['MENSAJESWHATSAPP']}/enviowhatsapp_api/whatsapp/pendientes-json",
                params={"estado": estado},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/MensajeWhatsApp/pendientes-json-npl", tags=["Mensaje WhatsApp"])
async def gateway_pendientes_json_npl(
    estado: str = Query("ENVIADO", description="Estado a marcar cuando se entregue al RPA")
):
    ahora_bo = datetime.now(TZ).time()
    if not (HORA_INICIO <= ahora_bo < HORA_FIN):
        return JSONResponse(status_code=200, content=[])
    try:
        async with httpx.AsyncClient(timeout=360.0) as client:
            resp = await client.get(
                f"{MICRO_URLS['MENSAJESWHATSAPP']}/enviowhatsapp_api/whatsapp/pendientes-json-npl",
                params={"estado": estado},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/MensajeWhatsApp/pendientes-json-jcap", tags=["Mensaje WhatsApp"])
async def gateway_pendientes_json_adamantine(
    estado: str = Query("ENVIADO", description="Estado a marcar cuando se entregue al RPA")
):
    ahora_bo = datetime.now(TZ).time()
    if not (HORA_INICIO <= ahora_bo < HORA_FIN):
        return JSONResponse(status_code=200, content=[])
    try:
        async with httpx.AsyncClient(timeout=30000.0) as client:
            resp = await client.get(
                f"{MICRO_URLS['MENSAJESWHATSAPP']}/enviowhatsapp_api/whatsapp/pendientes-json-jcap",
                params={"estado": estado},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/MensajeWhatsApp/pendientes-json-adamantine", tags=["Mensaje WhatsApp"])
async def gateway_pendientes_json_adamantine(
    estado: str = Query("ENVIADO", description="Estado a marcar cuando se entregue al RPA")
):
    ahora_bo = datetime.now(TZ).time()
    if not (HORA_INICIO <= ahora_bo < HORA_FIN):
        return JSONResponse(status_code=200, content=[])
    try:
        async with httpx.AsyncClient(timeout=3000.0) as client:
            resp = await client.get(
                f"{MICRO_URLS['MENSAJESWHATSAPP']}/enviowhatsapp_api/whatsapp/pendientes-json-adamantine",
                params={"estado": estado},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/MensajeWhatsApp/pendientes-json-credivalores", tags=["Mensaje WhatsApp"])
async def gateway_pendientes_json_credivalores(
    estado: str = Query("ENVIADO", description="Estado a marcar cuando se entregue al RPA")
):
    ahora_bo = datetime.now(TZ).time()
    if not (HORA_INICIO <= ahora_bo < HORA_FIN):
        return JSONResponse(status_code=200, content=[])
    try:
        async with httpx.AsyncClient(timeout=3000.0) as client:
            resp = await client.get(
                f"{MICRO_URLS['MENSAJESWHATSAPP']}/enviowhatsapp_api/whatsapp/pendientes-json-credivalores",
                params={"estado": estado},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/ClientesEnvioWhatsApp", tags=["Mensaje WhatsApp"])
async def gw_clientes_envio_top():
    url = f"{MICRO_URLS['MENSAJESWHATSAPP']}/enviowhatsapp_api/whatsapp/clientes"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

TRUE_SET  = {"1","si","sí","s","y","yes","true","verdadero","t","on"}
FALSE_SET = {"0","no","n","false","falso","f","off"}

def _normalize_si_no(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        raise ValueError("Valor 'tiene_whatsapp' vacío o nulo")

    if isinstance(value, (int, float)):
        if value == 1:
            return True
        if value == 0:
            return False

    s = str(value).strip().lower()
    if s in TRUE_SET:
        return True
    if s in FALSE_SET:
        return False
    raise ValueError(f"Valor 'tiene_whatsapp' no reconocido: {value!r}")

@router.post("/MensajeWhatsApp/actualizar-tiene", tags=["Mensaje WhatsApp"])
async def gateway_actualizar_tiene_whatsapp_json(request: Request):
    try:
        body: Dict[str, Any] = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"JSON inválido: {e}")

    numero = (body.get("numero") or "").strip()
    if not numero:
        raise HTTPException(status_code=422, detail="Falta o vacío: 'numero'")

    if "tiene_whatsapp" not in body:
        raise HTTPException(status_code=422, detail="Falta campo 'tiene_whatsapp'")

    try:
        tiene_bool = _normalize_si_no(body.get("tiene_whatsapp"))
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))

    payload = {"numero": numero, "tiene_whatsapp": tiene_bool}


    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{MICRO_URLS['MENSAJESWHATSAPP']}/enviowhatsapp_api/whatsapp/actualizar-tiene",
                json=payload
            )
            resp.raise_for_status()
            # Retorna tal cual la respuesta del micro
            try:
                return resp.json()
            except ValueError:
                # Si el micro devolviera texto plano
                return JSONResponse(status_code=resp.status_code, content={"detail": resp.text})

    except httpx.HTTPStatusError as e:
        # Burbujea el código y el detalle del micro
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

#----------- GESTIONES TESEO ----------------------------------------------------------
@router.post("/excel/guardarGestiones", tags=["Gestiones Teseo"])
async def gateway_guardar_excel_gestiones(request: Request):
    try:
        form = await request.form()
        file = form["file"]

        content = await file.read()

        form_data = MultipartEncoder(
            fields={
                "file": (file.filename, content, file.content_type)
            }
        )
        headers = {"Content-Type": form_data.content_type}

        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{MICRO_URLS['TESEO']}/gestiones_api/excel/guardarGestion",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        import traceback
        print("🔥 ERROR EN GATEWAY /guardarGestion:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})

#----------- ACUERDO DE PAGO -----------------------------------------------------------
@router.post("/excel/guardarAcuerdoPago", tags=["Acuerdo Pago"])
async def gateway_guardar_excel_AcuerdoPago(request: Request):
    try:
        form = await request.form()
        file = form["file"]

        content = await file.read()

        form_data = MultipartEncoder(
            fields={
                "file": (file.filename, content, file.content_type)
            }
        )
        headers = {"Content-Type": form_data.content_type}

        timeout = httpx.Timeout(120.0, connect=10.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{MICRO_URLS['TESEO']}/acuerdoPago_api/excel/guardarAcuerdo",
                content=form_data.to_string(),
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        import traceback
        print("🔥 ERROR EN GATEWAY /guardarAcuerdo:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/dni", tags=["Acuerdo Pago"])
async def gateway_obtener_dni_random(
    estado_from: str | None = Query(default="PENDIENTE"),
    estado_to:   str | None = Query(default="ENVIADO"),
):
    try:
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                f"{MICRO_URLS['TESEO']}/acuerdoPago_api/excel/dni",
                params={"estado_from": estado_from, "estado_to": estado_to},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        import traceback
        print("🔥 ERROR EN GATEWAY /excel/dni:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.api_route("/acuerdos/enviada", methods=["GET", "POST"], tags=["Acuerdo Pago"])
async def gateway_marcar_enviada_y_devolver(
    solo_activos: bool = Query(default=True),
    exige_estado: Optional[str] = Query(default="PENDIENTE"),
):
    """
    Llama al micro, que marca y devuelve el registro actualizado.
    Propaga 200 con JSON o 404 si no hay pendientes.
    """
    try:
        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{MICRO_URLS['TESEO']}/acuerdoPago_api/acuerdos/marcar-enviada",
                params={
                    "solo_activos": str(solo_activos).lower(),
                    "exige_estado": exige_estado
                },
            )
        if resp.status_code == 200:
            return resp.json()
        try:
            payload = resp.json()
        except Exception:
            payload = {"error": resp.text or "Error inesperado del microservicio"}
        return JSONResponse(status_code=resp.status_code, content=payload)

    except Exception as e:
        import traceback
        print("🔥 ERROR EN GATEWAY /acuerdos/marcar-enviada:")
        print(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": str(e)})

# ===================== EMAILCLICK=====================

@router.post("/emailclick/subir_excel", tags=["EmailClick"])
async def gw_emailclick_subir_excel(request: Request):
    try:
        form = await request.form()
        file = form["file"]
        sender = str(form.get("senderEmail", "")) 
        micro_base = pick_emailclick_micro(sender) 

        content = await file.read()

        form_data = MultipartEncoder(
            fields={
                "file": (file.filename, content, file.content_type)
            }
        )
        headers = {"Content-Type": form_data.content_type}

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            r = await client.post(
                f"{micro_base}/email_click_api/subir_excel", 
                content=form_data.to_string(),
                headers=headers,
            )

        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)

        return r.json()

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/emailclick/guardar_imagen", tags=["EmailClick"])
async def gw_emailclick_guardar_imagen(request: Request):
    try:
        form = await request.form()
        file = form["file"]
        areas = form["areas"]
        sender = str(form.get("senderEmail", ""))  
        micro_base = pick_emailclick_micro(sender) 

        content = await file.read()

        form_data = MultipartEncoder(
            fields={
                "file": (file.filename, content, file.content_type),
                "areas": str(areas),
            }
        )
        headers = {"Content-Type": form_data.content_type}

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
            r = await client.post(
                f"{micro_base}/email_click_api/guardar_imagen",
                content=form_data.to_string(),
                headers=headers,
            )

        if r.status_code >= 400:
            raise HTTPException(status_code=r.status_code, detail=r.text)

        return r.json()

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/emailclick/enviar_correos", tags=["EmailClick"])
async def gw_emailclick_enviar_correos(payload: dict):
    sender = payload.get("senderEmail", "")
    micro_base = pick_emailclick_micro(sender)

    url = f"{micro_base}/email_click_api/enviar_correos"
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(url, json=payload)
    if r.status_code >= 400:
    # devuelve el body del micro tal cual, para depurar
        raise HTTPException(status_code=r.status_code, detail=r.text)

    return r.json()

@router.post("/emailclick/programar_envio", tags=["EmailClick"])
async def gw_emailclick_programar_envio(payload: dict):
    """
    Proxy -> microservicio EmailClick: POST /programar_envio (json)
    payload esperado: { "subject": "...", "body": "...", "fecha_envio": "YYYY-MM-DDTHH:MM" }
    """
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0)) as client:
            r = await client.post(
                f"{MICRO_URLS['EMAILCLICKCOLOMBIA']}/email_click_api/programar_envio",
                json=payload
            )
            r.raise_for_status()
            return r.json()

    except httpx.HTTPStatusError as e:
        return JSONResponse(status_code=e.response.status_code, content={"error": e.response.text})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.api_route("/emailclick/static/{filename}", methods=["GET","HEAD"])
async def gw_emailclick_static(filename: str, senderEmail: str = ""):
    micro_base = pick_emailclick_micro(senderEmail)
    url = f"{micro_base}/static/{filename}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url)

    media = (
        "image/png"
        if filename.lower().endswith(".png")
        else r.headers.get("content-type", "application/octet-stream")
    )

    return Response(
        content=b"" if r.request.method == "HEAD" else r.content,
        status_code=r.status_code,
        media_type=media,
        headers={
            "Content-Length": str(len(r.content)),
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        }
    )

# ----------------REPORTES EMAIL CLICK----------------------
@router.get("/correos/encabezadosImagenes", tags=["Correos"])
async def gw_listar_encabezados():
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{MICRO_URLS['EMAILCLICKREPORTES']}/EmailEnvios/Encabezados")
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/correos/detalleImagenes", tags=["Correos"])
async def gw_listar_detalle(idEncabezado: int = Query(...)):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{MICRO_URLS['EMAILCLICKREPORTES']}/EmailEnvios/Detalle", params={"idEncabezado": idEncabezado})
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/correos/exportarExcelPorEncabezadoImagenes", tags=["Correos"])
async def gateway_exportar_excel_por_encabezado(idEncabezado: int = Query(...)):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{MICRO_URLS['EMAILCLICKREPORTES']}/EmailEnvios/ExportarExcelPorEncabezado",
                params={"idEncabezado": idEncabezado}
            )
            resp.raise_for_status()
            filename = resp.headers.get("content-disposition", 'attachment; filename="reporte.xlsx"')
            return StreamingResponse(
                io.BytesIO(resp.content),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": filename}
            )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _clean_params(d: dict) -> dict:
    # elimina None y '' para evitar idUsuario= (vacío) y otros
    return {k: v for k, v in d.items() if v is not None and v != ""}

@router.get("/correos/dashboard/resumenImagenes", tags=["Correos"])
async def gw_correos_dashboard_resumen(
    fecha_inicio: str | None = Query(None),
    fecha_fin: str | None = Query(None),
    idUsuario: int | None = Query(None),
    remitente: str | None = Query(None),
):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{MICRO_URLS['EMAILCLICKREPORTES']}/EmailEnvios/Dashboard/Resumen",
                params=_clean_params({
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin,
                    "idUsuario": idUsuario,
                    "remitente": remitente,
                }),
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correos/dashboard/porRemitenteImagenes", tags=["Correos"])
async def gw_correos_dashboard_por_remitente(
    fecha_inicio: str | None = Query(None),
    fecha_fin: str | None = Query(None),
    idUsuario: int | None = Query(None),
):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{MICRO_URLS['EMAILCLICKREPORTES']}/EmailEnvios/Dashboard/PorRemitente",
                params=_clean_params({"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin, "idUsuario": idUsuario}),
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correos/dashboard/porDiaImagenes", tags=["Correos"])
async def gw_correos_dashboard_por_dia(
    fecha_inicio: str | None = Query(None),
    fecha_fin: str | None = Query(None),
    idUsuario: int | None = Query(None),
    remitente: str | None = Query(None),
):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{MICRO_URLS['EMAILCLICKREPORTES']}/EmailEnvios/Dashboard/PorDia",
                params=_clean_params({
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin,
                    "idUsuario": idUsuario,
                    "remitente": remitente,
                }),
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/correos/dashboard/topErroresImagenes", tags=["Correos"])
async def gw_correos_dashboard_top_errores(
    fecha_inicio: str | None = Query(None),
    fecha_fin: str | None = Query(None),
    idUsuario: int | None = Query(None),
    remitente: str | None = Query(None),
    top: int = Query(20, ge=1, le=100),
):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{MICRO_URLS['EMAILCLICKREPORTES']}/EmailEnvios/Dashboard/TopErrores",
                params=_clean_params({
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin,
                    "idUsuario": idUsuario,
                    "remitente": remitente,
                    "top": top,
                }),
            )
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.api_route("/emailclick/track/{idDetalle}", methods=["GET", "HEAD"], tags=["EmailClick"])
async def gateway_emailclick_track(
    idDetalle: int,
    a: int = Query(1),
    senderEmail: str = ""
):
    """
    Endpoint público de tracking con redirect JavaScript.
    """
    try:
        print(f"🔵 [TRACK] Gateway recibe: idDetalle={idDetalle}, a={a}, senderEmail='{senderEmail}'")
        
        # Resolver a qué micro ir
        try:
            micro_base = pick_emailclick_micro(senderEmail)
            print(f"🔵 [TRACK] Micro base: {micro_base}")
        except Exception as e:
            print(f"❌ [TRACK] Error en pick_emailclick_micro: {e}")
            micro_base = MICRO_URLS.get("EMAILCLICKCOLOMBIA", "http://172.18.72.111:8023")
        
        micro_url = f"{micro_base}/email_click_api/track/{idDetalle}"
        print(f"🔵 [TRACK] URL del micro: {micro_url}")
        
        # Llamar al micro
        try:
            timeout = httpx.Timeout(10.0, connect=5.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
                r = await client.get(micro_url, params={"a": a})
            
            print(f"🟢 [TRACK] Respuesta: status={r.status_code}")
            
        except httpx.ConnectError as e:
            print(f"❌ [TRACK] Error de conexión al micro: {e}")
            return Response(
                content=b'<html><body><script>window.location.replace("https://optime.systemgroupglobal.com");</script></body></html>',
                status_code=200,
                media_type="text/html"
            )
        except httpx.TimeoutException as e:
            print(f"❌ [TRACK] Timeout al llamar micro: {e}")
            return Response(
                content=b'<html><body><script>window.location.replace("https://optime.systemgroupglobal.com");</script></body></html>',
                status_code=200,
                media_type="text/html"
            )
        
        # Manejar redirect
        if r.status_code in (301, 302, 303, 307, 308):
            location = r.headers.get("location", "")
            print(f"🟢 [TRACK] Es redirect! Location: {location}")
            
            if not location:
                print(f"⚠️ [TRACK] Redirect sin Location header")
                location = "https://optime.systemgroupglobal.com"
            
            # Escapar la URL para JavaScript
            location_safe = location.replace('"', '&quot;').replace("'", "\\'")
            
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0;url={location_safe}">
    <title>Redirigiendo...</title>
</head>
<body>
    <script>
        window.location.replace("{location_safe}");
    </script>
    <noscript>
        <p>Redirigiendo a <a href="{location_safe}">{location_safe}</a></p>
    </noscript>
</body>
</html>"""
            
            print(f"✅ [TRACK] Enviando HTML redirect a: {location}")
            
            return Response(
                content=html_content.encode('utf-8'),
                status_code=200,
                media_type="text/html; charset=utf-8",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0"
                }
            )
        
        # No es redirect, devolver contenido normal
        print(f"🔵 [TRACK] No es redirect, devolviendo contenido (status={r.status_code})")
        return Response(
            content=r.content,
            status_code=r.status_code,
            headers=dict(r.headers)
        )
        
    except Exception as e:
        print(f"❌ [TRACK] Error inesperado: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback
        return Response(
            content=b'<html><body><script>window.location.replace("https://optime.systemgroupglobal.com");</script><p>Error al procesar el tracking.</p></body></html>',
            status_code=200,
            media_type="text/html"
        )
        
@router.get("/emailclick/test-redirect")
async def test_redirect():
    """
    Endpoint de prueba con redirect JavaScript
    """
    try:
        location = "https://www.youtube.com/"
        location_safe = location.replace('"', '&quot;')
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0;url={location_safe}">
    <title>Test Redirect</title>
</head>
<body>
    <script>
        window.location.replace("{location_safe}");
    </script>
    <p>Test redirect a YouTube...</p>
</body>
</html>"""
        
        return Response(
            content=html_content.encode('utf-8'),
            status_code=200,
            media_type="text/html; charset=utf-8"
        )
    except Exception as e:
        print(f"❌ Error en test-redirect: {e}")
        import traceback
        traceback.print_exc()
        raise

#---------- RPA NOTIFICACIONES----------------------
@router.get("/vigilancia_api/correo", tags=["Vigilancia"])
async def gateway_darUsuarioRadicado():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{MICRO_URLS['JURIDICA']}/vigilancia_api/automatizacionVigilancia/correo"
            )
            resp.raise_for_status()
            data = resp.json()
            fechaUltimaCarga  = data.get("fechaCargue")
            correo       = data.get("correo")

        return {
            "correo": correo,
            "fechaUltimaCarga": fechaUltimaCarga
        }
    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/superNotariado_api/correo", tags=["Super Notariado"])
async def gateway_darUsuarioSN():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{MICRO_URLS['JURIDICA']}/superNotariado_api/automatizacionSuperNotariado/correo"
            )
            resp.raise_for_status()
            data = resp.json()
            fechaUltimaCarga  = data.get("fechaCargue")
            correo       = data.get("correo")

        return {
            "correo": correo,
            "fechaUltimaCarga": fechaUltimaCarga
        }
    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/rues_api/correo", tags=["RUES"])
async def gateway_darUsuarioRUES():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{MICRO_URLS['JURIDICA']}/rues_api/automatizacionRues/correo"
            )
            resp.raise_for_status()
            data = resp.json()
            fechaUltimaCarga  = data.get("fechaCargue")
            correo       = data.get("correo")

        return {
            "correo": correo,
            "fechaUltimaCarga": fechaUltimaCarga
        }
    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/famisanar_api/correo", tags=["FamiSanar"])
async def gateway_darUsuarioFamisanar():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{MICRO_URLS['SALUD']}/famisanar_api/automatizacionFamiSanar/correo"
            )
            resp.raise_for_status()
            data = resp.json()
            fechaUltimaCarga  = data.get("fechaCargue")
            correo       = data.get("correo")

        return {
            "correo": correo,
            "fechaUltimaCarga": fechaUltimaCarga
        }
    except httpx.HTTPStatusError as e:
        try:
            detalle = e.response.json()
        except ValueError:
            detalle = {"detail": e.response.text}
        return JSONResponse(status_code=e.response.status_code, content=detalle)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})