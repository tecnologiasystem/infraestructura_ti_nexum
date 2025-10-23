from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Form, Request, Body
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
import pandas as pd
from io import BytesIO
import os
import numpy as np
from datetime import datetime

from app.bll.mensajeWhatsapp_bll import (
    procesar_archivo_excel,
    obtener_automatizacionNumeroMensajeWhatsApp,
    listar_automatizaciones_estadoMensajeWhatsApp,
    obtener_automatizacionMensajeWhatsApp, enviar_correo_finalizacion_por_encabezado,
)

from app.dal.mensajeWhatsapp_dal import DetalleModel, EncabezadoModel, obtener_detalles_por_encabezado, obtener_detalles_agrupados_WhatsApp

router = APIRouter()


@router.get("/automatizacionesMensajeWhatsApp", tags=["Mensajes WhatsApp"])
def get_automatizaciones():
    return listar_automatizaciones_estadoMensajeWhatsApp()


@router.get("/automatizacionesMensajeWhatsApp/{id_encabezado}", tags=["Mensajes WhatsApp"])
def get_automatizacion_por_id(id_encabezado: int):
    """
    Obtiene los detalles de una automatización específica dado su id.
    Lanza error 404 si no existe la automatización.
    """
    resultado = obtener_automatizacionMensajeWhatsApp(id_encabezado)
    if not resultado:
        raise HTTPException(status_code=404, detail="Automatización no encontrada")
    return resultado


@router.get("/automatizacionMensajeWhatsApp/porNumero", tags=["Mensajes WhatsApp"])
def get_numero_aConsultar():
    try:
        resultado = obtener_automatizacionNumeroMensajeWhatsApp()
        if not resultado:
            return JSONResponse(status_code=404, content={"error": "No hay numeros disponibles"})
        id_enc, numero, mensaje = resultado
        return {"idEncabezado": id_enc, "numero": numero, "mensaje": mensaje}
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
    plantilla_path = r"\\BITMXL94920DQ\Uipat Datos\Mensajes WhatsApp\Plantilla\plantilla_Mensajes_WhatsApp.xlsx"
    if not os.path.exists(plantilla_path):
        return JSONResponse(status_code=404, content={"error": "Plantilla no encontrada"})
    return FileResponse(
        path=plantilla_path,
        filename="plantilla_Mensajes_WhatsApp.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.post("/excel/guardarWhatsApp", tags=["Mensajes WhatsApp"])
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

        ruta_input = r"\\BITMXL94920DQ\Uipat Datos\Mensajes WhatsApp\Datos\Input"
        ruta_output = r"\\BITMXL94920DQ\Uipat Datos\Mensajes WhatsApp\Correos\Input"

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
            mensaje_valor = row.get("MENSAJE", "")

            numero_str = numero_valor.strip() if numero_valor else ""
            mensaje_str = mensaje_valor.strip() if mensaje_valor else ""

            print(f"Numero Leido: {numero_str}")

            detalles.append(DetalleModel(
                numero=numero_str,
                indicativo=mensaje_str
            ))

        encabezado = EncabezadoModel(
            automatizacion="Mensaje WhatsApp",
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

@router.get("/detalle/listar_agrupadoMensajeWhatsApp", tags=["Mensaje WhatsApp"])
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


@router.post("/notificarFinalizacionMensajeWhatsApp", tags=["Mensaje WhatsApp"])
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
