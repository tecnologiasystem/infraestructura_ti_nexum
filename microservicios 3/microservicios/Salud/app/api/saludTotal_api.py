from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Form, Request, Body
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
import pandas as pd
from io import BytesIO
import os
import numpy as np
from datetime import datetime

from app.bll.saludTotal_bll import (
    procesar_resultado_automatizacionSaludTotal,
    ResultadoSaludTotalModel,
    enviar_correo_finalizacionSaludTotal,
    procesar_archivo_excel,
    obtener_automatizacion_por_idSaludTotal,
    obtener_automatizacionCCSaludTotal,
    listar_automatizaciones_estadoSaludTotal,
    obtener_automatizacionSaludTotal, enviar_correo_finalizacion_por_encabezado
)

from app.dal.saludTotal_dal import DetalleModel, EncabezadoModel, obtener_detalles_agrupados_SaludTotal, obtener_detalles_por_encabezado

router = APIRouter()


@router.get("/automatizacionesSaludTotal", tags=["Salud Total"])
def get_automatizaciones():
    """
    Endpoint para listar todas las automatizaciones con su estado actual.
    Retorna la lista completa sin filtros.
    """
    return listar_automatizaciones_estadoSaludTotal()


@router.get("/automatizacionesSaludTotal/{id_encabezado}", tags=["Salud Total"])
def get_automatizacion_por_id(id_encabezado: int):
    """
    Obtiene los detalles de una automatización específica dado su id.
    Lanza error 404 si no existe la automatización.
    """
    resultado = obtener_automatizacionSaludTotal(id_encabezado)
    if not resultado:
        raise HTTPException(status_code=404, detail="Automatización no encontrada")
    return resultado


@router.get("/automatizacionSaludTotal/porCC", tags=["Automatizacion Salud Total"])
def get_CC_aConsultar():
    """
    Obtiene la próxima cédula disponible para consulta.
    Si no hay cédulas disponibles retorna error 404.
    """
    try:
        resultado = obtener_automatizacionCCSaludTotal()
        if not resultado or not resultado[0] or not resultado[0][0]:
            return JSONResponse(status_code=404, content={"error": "No hay cédulas disponibles"})
        return {"cedula": resultado[0][0]}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/excel/plantilla", tags=["Excel"])
def descargar_plantilla():
    """
    Permite descargar la plantilla Excel estándar para el proceso FamiSanar.
    Valida existencia del archivo antes de devolverlo.
    """
    plantilla_path = r"\\BITMXL94920DQ\Uipat Datos\Salud Total\Plantilla\plantilla_saludTotal.xlsx"
    if not os.path.exists(plantilla_path):
        return JSONResponse(status_code=404, content={"error": "Plantilla no encontrada"})
    return FileResponse(
        path=plantilla_path,
        filename="plantilla_saludTotal.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.post("/excel/guardarSaludTotal", tags=["Salud Total"])
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

        ruta_input = r"\\BITMXL94920DQ\Uipat Datos\Salud Total\Datos\Input"
        ruta_output = r"\\BITMXL94920DQ\Uipat Datos\Salud Total\Correos\Input"

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
            cedula_valor = row.get("CEDULA", "")
            cedula_str = cedula_valor.strip() if cedula_valor else ""

            print(f"Cédula leída: {cedula_str}")

            detalles.append(DetalleModel(
                cedula=cedula_str,
                nombres=row.get("NOMBRES") or None,
                apellidos=row.get("APELLIDOS") or None,
                estado=row.get("ESTADO") or None,
                IPS=row.get("IPS") or None,
                convenio=row.get("CONVENIO") or None,
                tipo=row.get("TIPO") or None,
                categoria=row.get("CATEGORIA") or None,
                semanas=row.get("SEMANAS") or None,
                fechaNacimiento=row.get("FECHA NACIMIENTO") or None,
                edad=row.get("EDAD") or None,
                sexo=row.get("SEXO") or None,
                direccion=row.get("DIRECCION") or None,
                telefono=row.get("TELEFONO") or None,
                departamento=row.get("DEPARTAMENTO") or None,
                municipio=row.get("MUNICIPIO") or None,
                causal=row.get("CAUSAL") or None,
            ))

        encabezado = EncabezadoModel(
            automatizacion="Salud Total",
            idUsuario=idUsuario,
            fechaCargue=datetime.now(),
            totalRegistros=num_filas,
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


@router.post("/automatizacion/resultadoSaludTotal", tags=["Automatizacion Salud Total"])
async def recibir_resultado(request: Request):
    """
    Recibe un JSON con resultado de automatización, valida datos, y llama a BLL para procesarlo.
    Retorna éxito o error 404 si no se encontró registro para actualizar.
    """
    raw = await request.json()
    print("📥 Payload crudo:", raw)
    try:
        resultado = ResultadoSaludTotalModel(**raw)
    except ValidationError as ve:
        print("❌ ValidationError:", ve.json())
        raise HTTPException(status_code=422, detail=ve.errors())

    updated = procesar_resultado_automatizacionSaludTotal(resultado)
    if not updated:
        raise HTTPException(status_code=404, detail="No se encontró Detalle para la cédula enviada")
    return {"success": True, "mensaje": "Resultado guardado correctamente"}


@router.get("/detalle/listar_agrupadoSaludTotal", tags=["Salud Total"])
def listar_detalles_agrupados():
    """
    Retorna la lista de detalles agrupados para Salud total.
    """
    try:
        datos = obtener_detalles_agrupados_SaludTotal()
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


@router.post("/notificarFinalizacionSaludTotal", tags=["Salud Total"])
def notificar_finalizacion(idEncabezado: int = Body(..., embed=True)):
    """
    Envía un correo notificando la finalización del proceso Salud total al usuario que subió la base.
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
