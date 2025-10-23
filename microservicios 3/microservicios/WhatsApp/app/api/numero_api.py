from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Form, Request, Body
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
import pandas as pd
from io import BytesIO
import os
import numpy as np
from datetime import datetime

from app.bll.numero_bll import (
    procesar_resultado_automatizacionWhatsApp,
    ResultadoWhatsAppModel,
    enviar_correo_finalizacionWhatsApp,
    procesar_archivo_excel,
    obtener_automatizacion_por_idWhatsApp,
    obtener_automatizacionNumeroWhatsApp,
    listar_automatizaciones_estadoWhatsApp,
    obtener_automatizacionWhatsApp, enviar_correo_finalizacion_por_encabezado,
    pausar_encabezado,reanudar_encabezado
)

from app.dal.numero_dal import DetalleModel, EncabezadoModel, obtener_detalles_agrupados_WhatsApp, obtener_detalles_por_encabezado

router = APIRouter()


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
def get_numero_aConsultar():
    """
    Obtiene la próxima cédula disponible para consulta.
    Si no hay cédulas disponibles retorna error 404.
    """
    try:
        resultado = obtener_automatizacionNumeroWhatsApp()
        if not resultado:
            return JSONResponse(status_code=404, content={"error": "No hay cédulas disponibles"})
        id_enc, indicativo, numero = resultado
        return {"idEncabezado": id_enc, "indicativo": indicativo, "numero": numero}
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
    plantilla_path = r"\\BITMXL94920DQ\Uipat Datos\WhatsApp\Plantilla\plantilla_whatsApp.xlsx"
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
    Recibe un archivo Excel cargado, lo guarda en carpeta de input, procesa sus datos
    y genera un resumen de cantidad de filas. También limpia archivos temporales.

    Retorna los datos leídos, nombre del resumen generado y total de filas.
    """
    try:
        contents = await file.read()

        ruta_input = r"\\BITMXL94920DQ\Uipat Datos\WhatsApp\Datos\Input"
        ruta_output = r"\\BITMXL94920DQ\Uipat Datos\WhatsApp\Correos\Input"

        os.makedirs(ruta_input, exist_ok=True)
        os.makedirs(ruta_output, exist_ok=True)

        file_path = os.path.join(ruta_input, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)

        df = pd.read_excel(file_path, dtype=str)
        df.columns = [col.strip().upper() for col in df.columns]
        df.replace({np.nan: "", np.inf: None, -np.inf: None}, inplace=True)

        num_filas = len(df)

        resumen_filename = f"resumen_{file.filename}"
        resumen_path = os.path.join(ruta_output, resumen_filename)
        pd.DataFrame({"Cantidad de filas": [num_filas]}).to_excel(resumen_path, index=False)

        detalles = []
        for _, row in df.iterrows():
            numero_valor = row.get("NUMERO", "")
            indicativo_valor = row.get("INDICATIVO", "")

            numero_str = numero_valor.strip() if numero_valor else ""
            indicativo_str = indicativo_valor.strip() if indicativo_valor else ""

            print(f"Numero Leido: {numero_str}")

            detalles.append(DetalleModel(
                indicativo=indicativo_str,
                numero=numero_str
            ))

        encabezado = EncabezadoModel(
            automatizacion="WhatsApp",
            idUsuario=idUsuario,
            fechaCargue=datetime.now(),
            totalRegistros=num_filas,
            estado="En proceso", 
            detalles=detalles
        )

        id_encabezado = procesar_archivo_excel(encabezado)

        # Limpieza de archivos temporales iniciados por Excel
        for archivo in os.listdir(ruta_input):
            if archivo.startswith("~$") and archivo.endswith(".xlsx"):
                try:
                    os.remove(os.path.join(ruta_input, archivo))
                except Exception as e:
                    print(f"Error eliminando archivo temporal: {archivo}. Detalle: {e}")

        return {
            "data": df.to_dict(orient="records"),
            "resumen": resumen_filename,
            "filas": num_filas
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/automatizacion/resultadoWhatsApp", tags=["Automatizacion WhatsApp"])
async def recibir_resultado(request: Request):
    """
    Recibe un JSON con resultado de automatización, valida datos, y llama a BLL para procesarlo.
    Retorna éxito o error 404 si no se encontró registro para actualizar.
    """
    raw = await request.json()
    print("📥 Payload crudo:", raw)
    try:
        resultado = ResultadoWhatsAppModel(**raw)
    except ValidationError as ve:
        print("❌ ValidationError:", ve.json())
        raise HTTPException(status_code=422, detail=ve.errors())

    updated = procesar_resultado_automatizacionWhatsApp(resultado)
    if not updated:
        raise HTTPException(status_code=404, detail="No se encontró Detalle para la cédula enviada")
    return {"success": True, "mensaje": "Resultado guardado correctamente"}


@router.get("/detalle/listar_agrupadoWhatsApp", tags=["WhatsApp"])
def listar_detalles_agrupados():
    """
    Retorna la lista de detalles agrupados para WhatsApp.
    """
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
    Exporta los resultados de una tanda (automatización) a un archivo Excel para descarga.

    Si no hay resultados, retorna error 404.
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
    """
    Envía un correo notificando la finalización del proceso WhatsApp al usuario que subió la base.
    """
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

#------------- PAUSAR----------------------------
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