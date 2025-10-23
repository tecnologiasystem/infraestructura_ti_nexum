from fastapi import APIRouter, Request, UploadFile, File, HTTPException, Query, Form, Body
import httpx
import os
import traceback
from zoneinfo import ZoneInfo
import time
import aiofiles
from urllib.parse import unquote
from fastapi.responses import StreamingResponse,FileResponse
from config.microservices_config import MICRO_URLS
from typing import Dict, Optional, List, Union
import io
from pathlib import Path
from datetime import datetime, time as dtime
import pandas as pd
from fastapi import Query
from starlette.responses import JSONResponse
from requests_toolbelt.multipart.encoder import MultipartEncoder
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator
from starlette.responses import JSONResponse
from app.api.monitor_rpa import notificacion as monitor_notificacion
from typing import Optional, Any
import json, re, unicodedata
from pydantic import ValidationError 
import re
from urllib.parse import quote

router = APIRouter()

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

            if id_enc is None or ced is None:
                raise HTTPException(502, "Runt no devolvió idEncabezado y cedula")

        await monitor_notificacion("TYBA", id_enc)

        return {"cedula": ced}

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

            if id_enc is None or numero is None:
                raise HTTPException(502, "WhatsApp no devolvió idEncabezado y numero")

        await monitor_notificacion("MENSAJEWHATSAPP", id_enc)

        mensaje_encoded = quote((mensaje or ""), safe="")

        return {
            "numero": numero,
            "mensaje": mensaje_encoded
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
                f"{MICRO_URLS['WHATSAPP']}/enviowhatsapp_api/whatsapp/registrar",
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
                f"{MICRO_URLS['WHATSAPP']}/enviowhatsapp_api/whatsapp/pendientes-json",
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
                f"{MICRO_URLS['WHATSAPP']}/enviowhatsapp_api/whatsapp/pendientes-json-npl",
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
        async with httpx.AsyncClient(timeout=3000.0) as client:
            resp = await client.get(
                f"{MICRO_URLS['WHATSAPP']}/enviowhatsapp_api/whatsapp/pendientes-json-jcap",
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
    url = f"{MICRO_URLS['WHATSAPP']}/enviowhatsapp_api/whatsapp/clientes"
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    exige_estado: Optional[str] = Query(default="ACTIVO"),
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