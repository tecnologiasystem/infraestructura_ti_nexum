from fastapi import APIRouter, Request, Body
from fastapi import HTTPException, Query
from fastapi.responses import JSONResponse
from app.bll.Email_bll import enviar_correos_masivos, generar_documentos_personalizados_zip
import json
from app.dal.Email_dal import listar_encabezados, listar_detalles_por_encabezado
from fastapi.encoders import jsonable_encoder

router = APIRouter()

@router.post('/EmailMasivo')
async def email_masivo(payload: dict | None = Body(default=None) ):
    try:
        data = payload
        if data is None:
            try:
                body_text = None
                async def _read_body(req: Request):
                    nonlocal body_text
                    body_bytes = await req.body()
                    body_text = body_bytes.decode('utf-8', errors='ignore').strip()
                    return body_text
            except NameError:
                pass
        if data is None:
            return JSONResponse({"error": "Body vacío o no-JSON. Enviar application/json con el payload."}, status_code=400)
        print("📥 Datos recibidos en FastAPI:", data)
        result = enviar_correos_masivos(data)
        if isinstance(result, JSONResponse):
            return result
        return JSONResponse(content=result)
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
    
@router.get("/EmailEnvios/Encabezados")
async def email_encabezados():
    try:
        data = listar_encabezados()
        return JSONResponse(content=jsonable_encoder({"data": data}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/EmailEnvios/Detalle")
async def email_detalle(idEncabezado: int = Query(...)):
    try:
        data = listar_detalles_por_encabezado(idEncabezado)
        return JSONResponse(content=jsonable_encoder({"data": data}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))