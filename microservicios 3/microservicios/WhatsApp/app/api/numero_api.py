from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Form, Request, Body, status
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
import pandas as pd
from io import BytesIO
import os
import numpy as np
from datetime import datetime
import hashlib
import json
import asyncio
import time
import io

from app.rabbit import rabbit_publish, rabbit_consume_from_queue, rabbit_publish_to_queue

from app.bll.numero_bll import (
    procesar_resultado_automatizacionWhatsApp,
    ResultadoWhatsAppModel,
    enviar_correo_finalizacionWhatsApp,
    procesar_archivo_excel,
    obtener_automatizacion_por_idWhatsApp,
    obtener_automatizacionNumeroWhatsApp,
    listar_automatizaciones_estadoWhatsApp,
    obtener_automatizacionWhatsApp, enviar_correo_finalizacion_por_encabezado,
    pausar_encabezado, reanudar_encabezado
)

from app.dal.numero_dal import DetalleModel, EncabezadoModel, obtener_detalles_agrupados_WhatsApp, obtener_detalles_por_encabezado

router = APIRouter()

RABBIT_ROUTING_KEY = os.getenv("RABBIT_ROUTING_KEY", "result")
RABBIT_NUMEROS_QUEUE = os.getenv("RABBIT_NUMEROS_QUEUE", "whatsapp.numeros.disponibles")
RABBIT_NUMEROS_TIMEOUT = float(os.getenv("RABBIT_NUMEROS_TIMEOUT", "3.0"))
IDEMPOTENCY_TTL_SEC = int(os.getenv("RESULTADOS_IDEMPOTENCY_TTL", "0"))
_idempotency_seen: dict[str, float] = {}

def _gc_idempotency():
    if IDEMPOTENCY_TTL_SEC <= 0:
        _idempotency_seen.clear()
        return
    now = time.time()
    for k, ts in list(_idempotency_seen.items()):
        if ts <= now:
            _idempotency_seen.pop(k, None)

def _payload_idem_key(payload: dict) -> str | None:
    if IDEMPOTENCY_TTL_SEC <= 0:
        return None
    try:
        campos = {
            "indicativo": payload.get("indicativo"),
            "numero": payload.get("numero"),
            "tiene_whatsApp": payload.get("tiene_whatsApp"),
        }
        stable = json.dumps(campos, separators=(",", ":"), sort_keys=True, ensure_ascii=False)
        return hashlib.sha1(stable.encode("utf-8")).hexdigest()
    except:
        return None
    
@router.get("/automatizacionesWhatsApp", tags=["WhatsApp"])
def get_automatizaciones():
    return listar_automatizaciones_estadoWhatsApp()


@router.get("/automatizacionesWhatsApp/{id_encabezado}", tags=["WhatsApp"])
def get_automatizacion_por_id(id_encabezado: int):
    """
    Obtiene los detalles de una automatización específica dado su id.
    Lanza error 404 si no existe la automatización.
    """
    resultado = obtener_automatizacionWhatsApp(id_encabezado)
    if not resultado:
        raise HTTPException(status_code=404, detail="Automatización no encontrada")
    return resultado


@router.get("/automatizacionWhatsApp/porNumero", tags=["Automatizacion WhatsApp"])
async def get_numero_aConsultar():
    """
    Obtiene el próximo número disponible desde la cola de RabbitMQ.
    Si no hay números disponibles retorna 404.
    
    Este endpoint consume de una cola work queue, garantizando que
    cada número solo sea procesado por una máquina (sin duplicados).
    """
    try:
        # Consumir de la cola de RabbitMQ
        mensaje = await rabbit_consume_from_queue(
            queue_name=RABBIT_NUMEROS_QUEUE,
            timeout=RABBIT_NUMEROS_TIMEOUT
        )
        
        if not mensaje:
            return JSONResponse(
                status_code=404, 
                content={"error": "No hay números disponibles en la cola"}
            )
        
        # Parsear el mensaje JSON
        data = json.loads(mensaje)
        return {
            "idEncabezado": data["idEncabezado"],
            "indicativo": data["indicativo"],
            "numero": data["numero"]
        }
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=500, 
            content={"error": "Formato de mensaje inválido en la cola"}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/excel/plantilla", tags=["Excel"])
def descargar_plantilla():
    """
    Permite descargar la plantilla Excel estándar para el proceso WhatsApp.
    Valida existencia del archivo antes de devolverlo.
    """
    plantilla_path = r"\\172.18.73.76\Uipat Datos\WhatsApp\Plantilla\plantilla_whatsApp.xlsx"
    if not os.path.exists(plantilla_path):
        return JSONResponse(status_code=404, content={"error": "Plantilla no encontrada"})
    return FileResponse(
        path=plantilla_path,
        filename="plantilla_whatsApp.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.post("/excel/guardarWhatsApp", tags=["WhatsApp"])
async def guardar_excel(
    file: UploadFile = File(...),
    idUsuario: int = Form(...)
):
    """
    Recibe un Excel, lo procesa directamente sin guardar en disco.
    Retorna los datos, nombre del resumen virtual y total de filas.
    """
    try:
        # Leer contenido directamente desde memoria
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), dtype=str)

        # Limpiar y normalizar columnas
        df.columns = [col.strip().upper() for col in df.columns]
        df.replace({np.nan: "", np.inf: None, -np.inf: None}, inplace=True)

        num_filas = len(df)

        # Generar resumen en memoria (sin guardar en disco)
        resumen_filename = f"resumen_{file.filename}"
        resumen_df = pd.DataFrame({"Cantidad de filas": [num_filas]})

        # Preparar detalles
        detalles = []
        for _, row in df.iterrows():
            numero_valor = row.get("NUMERO", "")
            indicativo_valor = row.get("INDICATIVO", "")
            numero_str = numero_valor.strip() if numero_valor else ""
            indicativo_str = indicativo_valor.strip() if indicativo_valor else ""
            detalles.append(DetalleModel(
                indicativo=indicativo_str,
                numero=numero_str
            ))

        # Crear encabezado
        encabezado = EncabezadoModel(
            automatizacion="WhatsApp",
            idUsuario=idUsuario,
            fechaCargue=datetime.now(),
            totalRegistros=num_filas,
            estado="En proceso",
            detalles=detalles
        )

        idEncabezado = procesar_archivo_excel(encabezado)
        
        # Poblar la cola de RabbitMQ con los números de este encabezado
        try:
            print(f"📦 Poblando cola con {num_filas} números del encabezado {idEncabezado}...")
            for detalle in detalles:
                mensaje = {
                    "idEncabezado": idEncabezado,
                    "indicativo": detalle.indicativo,
                    "numero": detalle.numero
                }
                await rabbit_publish_to_queue(
                    queue_name=RABBIT_NUMEROS_QUEUE,
                    body=json.dumps(mensaje, ensure_ascii=False).encode("utf-8")
                )
            print(f"✅ Cola poblada exitosamente")
        except Exception as e:
            print(f"⚠️  Error al poblar cola: {e}")
            # No fallar la carga si hay error en la cola

        return {
            "data": df.to_dict(orient="records"),
            "resumen": resumen_filename,
            "filas": num_filas,
            "idEncabezado": idEncabezado
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


# =========================
#   NUEVO: ENDPOINT COLA
# =========================
@router.post("/automatizacion/resultadoWhatsApp", tags=["Automatizacion WhatsApp"])
async def recibir_resultado(request: Request):
    """
    Publica el resultado en RabbitMQ (durable). Devuelve 202 si se encola,
    o 200 si es duplicado reciente (idempotencia por contenido).
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="JSON inválido")

    _gc_idempotency()
    idem_key = _payload_idem_key(payload)
    if idem_key and idem_key in _idempotency_seen:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"success": True, "mensaje": "Duplicado ignorado (auto-idempotencia por contenido)", "idempotent": True}
        )

    try:
        await rabbit_publish(
            routing_key=RABBIT_ROUTING_KEY,
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"idem_key": idem_key} if idem_key else {}
        )
        if idem_key:
            _idempotency_seen[idem_key] = time.time() + IDEMPOTENCY_TTL_SEC
        return JSONResponse(status_code=status.HTTP_202_ACCEPTED,
                            content={"success": True, "mensaje": "Encolado en RabbitMQ"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo publicar en RabbitMQ: {e}")

@router.get("/detalle/listar_agrupadoWhatsApp", tags=["WhatsApp"])
def listar_detalles_agrupados():
    """Retorna la lista de detalles agrupados para WhatsApp."""
    try:
        datos = obtener_detalles_agrupados_WhatsApp()
        return {"data": datos}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/excel/exportar_resultados", tags=["Excel"])
def exportar_resultados_por_tanda(id_encabezado: int = Query(...)):
    """
    Exporta los resultados de una tanda (automatización) a un Excel descargable.
    """
    try:
        data = obtener_detalles_por_encabezado(id_encabezado)

        if not data:
            return JSONResponse(status_code=404, content={"error": "No se encontraron resultados para esta tanda"})

        df = pd.DataFrame(data)
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=tanda_{id_encabezado}.xlsx"}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/notificarFinalizacionWhatsApp", tags=["WhatsApp"])
def notificar_finalizacion(idEncabezado: int = Body(..., embed=True)):
    """Envía correo de finalización al usuario que subió la base."""
    try:
        enviado = enviar_correo_finalizacion_por_encabezado(idEncabezado)
        if enviado:
            return {"success": True, "mensaje": "Correo enviado"}
        else:
            return {"success": False, "mensaje": "No se pudo enviar el correo"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pausar/{id_encabezado}", tags=["WhatsApp"])
def api_pausar_encabezado(id_encabezado: int):
    success = pausar_encabezado(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo pausar el encabezado")
    return {"success": True}


@router.post("/reanudar/{id_encabezado}", tags=["WhatsApp"])
def api_reanudar_encabezado(id_encabezado: int):
    success = reanudar_encabezado(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo reanudar el encabezado")
    return {"success": True}
