from fastapi import APIRouter, Request, UploadFile, File, Query
from fastapi.responses import JSONResponse, FileResponse
import os
import pandas as pd
from app.ImpulsoProcesal.bll.procesal_bll import (
    upload_excel_juridico_bll,
    guardar_carta_impulso_bll,
    exportar_cartas_impulso_bll,
    export_preforma_excel_impulso,
    export_preforma_carta_impulso
)

from Comun.rutas_archivos import UPLOAD_EXCEL_PREFORMA, UPLOAD_EXCEL_EJECUCION_IMPULSO

router = APIRouter()

"""
Endpoint POST /UploadPreformaImpulsoUno
- Recibe un archivo Excel (.xlsx) vía UploadFile.
- Valida que se reciba archivo y que sea .xlsx, si no devuelve error 400.
- Crea el directorio destino si no existe.
- Guarda el archivo recibido en disco en la ruta configurada.
- Devuelve mensaje de éxito con nombre del archivo.
- Captura y maneja excepciones retornando error 500 con mensaje.
"""
@router.post("/UploadPreformaImpulsoUno")
async def upload_preforma_impulso_uno(file: UploadFile = File(...)):
    try:
        if not file:
            return JSONResponse(content={"error": "No se recibió archivo."}, status_code=400)

        if not file.filename.endswith(".xlsx"):
            return JSONResponse(content={"error": "Solo se aceptan archivos .xlsx"}, status_code=400)

        os.makedirs(UPLOAD_EXCEL_EJECUCION_IMPULSO, exist_ok=True)
        file_path = os.path.join(UPLOAD_EXCEL_EJECUCION_IMPULSO, file.filename)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        return JSONResponse(content={
            "message": f"Archivo {file.filename} subido exitosamente",
            "excelFilename": file.filename
        }, status_code=200)

    except Exception as e:
        print(f"🔥 Error real capturado en UploadPreformaImpulsoUno: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


"""
Endpoint GET /ExportPreformaImpulso
- Exporta una plantilla Excel preformateada para impulso procesal.
- Busca el archivo en la ruta configurada.
- Si el archivo no existe, devuelve error 404.
- Si existe, retorna el archivo con el tipo MIME adecuado para Excel.
- Captura excepciones y retorna error 500 con mensaje.
"""
@router.get("/ExportPreformaImpulso")
async def export_preforma_impulso():
    try:
        file_path = os.path.join(UPLOAD_EXCEL_PREFORMA, 'Preforma_ImpulsoProcesal.xlsx')
        if not os.path.exists(file_path):
            return JSONResponse(content={"error": "El archivo Preforma_ImpulsoProcesal.xlsx no existe"}, status_code=404)
        return FileResponse(path=file_path, filename='Preforma_ImpulsoProcesal.xlsx', media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        print(f"🔥 Error en ExportPreformaImpulso: {str(e)}")
        return JSONResponse(content={"error": f"Error interno del servidor: {str(e)}"}, status_code=500)


"""
Endpoint GET /ExportPreformaCartaImpulso
- Exporta una plantilla Word para cartas de impulso procesal.
- Verifica existencia del archivo en ruta configurada.
- Devuelve error 404 si no se encuentra.
- Si existe, lo retorna con el tipo MIME para documentos Word.
- Maneja errores retornando mensaje de error 500.
"""
@router.get("/ExportPreformaCartaImpulso")
async def export_preforma_carta_impulso():
    try:
        file_path = os.path.join(UPLOAD_EXCEL_PREFORMA, 'SOLICITUD_AMPLIACION.docx')
        if not os.path.exists(file_path):
            return JSONResponse(content={"error": "El archivo SOLICITUD_AMPLIACION.docx no existe"}, status_code=404)
        return FileResponse(path=file_path, filename='SOLICITUD_AMPLIACION.docx', media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    except Exception as e:
        print(f"🔥 Error en ExportPreformaCartaImpulso: {str(e)}")
        return JSONResponse(content={"error": f"Error interno del servidor: {str(e)}"}, status_code=500)


"""
Endpoint POST /GuardarCartaImpulso
- Recibe datos JSON en el cuerpo de la petición y parámetros query.
- Imprime los datos y parámetros recibidos para seguimiento.
- Llama a la función BLL para guardar la carta de impulso.
- Devuelve el resultado en JSON con status 200 si todo va bien.
- Captura errores retornando error 500 con mensaje.
"""
@router.post("/GuardarCartaImpulso")
async def guardar_carta_impulso(request: Request):
    try:
        data = await request.json()
        params = dict(request.query_params)

        print("📥 Datos recibidos:", data)
        print("📥 Parámetros:", params)

        result = guardar_carta_impulso_bll(data, params)
        return JSONResponse(content=result, status_code=200)

    except Exception as e:
        print(f"🔥 Error en GuardarCartaImpulso: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


"""
Endpoint GET /ExportarCartasImpulso
- Recibe parámetro query 'processId' identificando el proceso a exportar.
- Valida que se envíe el processId, si no devuelve error 400.
- Llama a la función BLL para exportar las cartas en un archivo ZIP.
- Verifica existencia del archivo ZIP generado.
- Si no existe, retorna error 404.
- Si existe, devuelve el ZIP con el tipo MIME adecuado.
- Maneja errores retornando error 500 con mensaje.
"""
@router.get("/ExportarCartasImpulso")
async def exportar_cartas_impulso(processId: str = Query(None)):
    if not processId:
        return JSONResponse(content={"error": "Falta el identificador del proceso."}, status_code=400)
    try:
        zip_path = exportar_cartas_impulso_bll(processId)
        if not os.path.exists(zip_path):
            return JSONResponse(content={"error": "No se encontraron cartas para el proceso indicado."}, status_code=404)
        return FileResponse(path=zip_path, filename=os.path.basename(zip_path), media_type="application/zip")
    except Exception as e:
        print(f"🔥 Error en ExportarCartasImpulso: {str(e)}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

