from fastapi import APIRouter, Request, Body, Response
from fastapi import HTTPException, Query
from fastapi.responses import JSONResponse
from app.bll.Email_bll import enviar_correos_masivos, generar_documentos_personalizados_zip, reanudar_envio_por_encabezado
import pandas as pd
from fastapi.responses import StreamingResponse
from app.core.emailclick_queue import EmailQueue
import json
from app.dal.Email_dal import actualizar_estado_encabezado, pausar_pendientes_por_encabezado, reanudar_pausados_por_encabezado

router = APIRouter()

email_queue = EmailQueue()

def _handler_email(payload: dict) -> dict:
    action = (payload.get("action") or "").lower().strip()

    # ✅ Resume desde BD
    if action == "resume":
        return reanudar_envio_por_encabezado(
            id_encabezado=payload.get("idEncabezado"),
            sender_email=payload.get("senderEmail"),
            user_id=payload.get("idUsuario") or payload.get("userId"),
        )

    # ✅ Envío nuevo
    result = enviar_correos_masivos(payload)

    if isinstance(result, JSONResponse):
        try:
            return json.loads(result.body.decode("utf-8"))
        except Exception:
            return {"raw": result.body.decode("utf-8", errors="ignore")}

    return result if isinstance(result, dict) else {"result": str(result)}

@router.post('/EmailMasivo')
async def email_masivo(payload: dict | None = Body(default=None)):
    try:
        data = payload
        if data is None:
            return JSONResponse({"error": "Body vacío o no-JSON. Enviar application/json con el payload."}, status_code=400)

        print("📥 Datos recibidos en FastAPI (encolado):", data)

        job_id = email_queue.enqueue(data)

        return JSONResponse(
            content={
                "message": "Job encolado. Se procesará en segundo plano (1 worker en fila).",
                "job_id": job_id,
                "status_url": f"/EmailMasivo/status/{job_id}"
            },
            status_code=202
        )

    except Exception as e:
        print(f"❌ Error en /EmailMasivo: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/GenerarDocsPDF")
async def generar_docs_pdf(payload: dict = Body(...)):
    """
    payload: {
      excelFileName: str,
      templateHtml: str,
      fileNameTemplate: str (ej. documento_{Var1}.pdf),
      output: "pdf"
    }
    """
    try:
      zip_bytes, err = generar_documentos_personalizados_zip(payload)
      if err:
          return JSONResponse({"error": err}, status_code=400)
      return Response(
          content=zip_bytes,
          media_type="application/zip",
          headers={"Content-Disposition": 'attachment; filename="documentos_personalizados.zip"'}
      )
    except Exception as e:
      return JSONResponse({"error": str(e)}, status_code=500)
    
@router.get("/EmailMasivo/status/{job_id}")
async def email_masivo_status(job_id: str):
    return JSONResponse(content=email_queue.get_status(job_id))

@router.post("/EmailEnvios/Reanudar/{id_encabezado}")
def reanudar(id_encabezado: int):
    actualizar_estado_encabezado(id_encabezado, "EN_PROCESO")

    # Encolar job
    job_id = email_queue.enqueue({
        "action": "resume",
        "idEncabezado": id_encabezado
    })

    return {"ok": True, "estado": "EN_PROCESO", "job_id": job_id}

@router.post("/EmailEnvios/Pausar/{id_encabezado}")
def pausar(id_encabezado: int):
    actualizar_estado_encabezado(id_encabezado, "PAUSADO")
    pausar_pendientes_por_encabezado(id_encabezado)
    return {"ok": True, "estado": "PAUSADO"}
