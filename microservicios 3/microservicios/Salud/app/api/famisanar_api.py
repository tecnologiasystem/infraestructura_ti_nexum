"""
Este archivo define el router FastAPI para el módulo FamiSanar, con endpoints para gestión de automatizaciones,
manejo de archivos Excel, consulta y actualización de datos, y notificaciones por correo.

Se integran modelos Pydantic para validación, y la lógica de negocio se delega a la capa BLL.
"""

from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Form, Request, Body, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from app.bll.famisanar_bll import procesar_archivo_excel_background 
import pandas as pd
from io import BytesIO
import os
import numpy as np
from datetime import datetime

from app.bll.famisanar_bll import (
    procesar_resultado_automatizacionFamiSanar,
    ResultadoFamiSanarModel,
    enviar_correo_finalizacionFamiSanar,
    procesar_archivo_excel,
    obtener_automatizacion_por_idFamiSanar,
    obtener_automatizacionCCFamiSanar,
    listar_automatizaciones_estadoFamiSanar,
    obtener_automatizacionFamiSanar, enviar_correo_finalizacion_por_encabezado,
    pausar_encabezado,reanudar_encabezado, listar_detalles_por_encabezado_paginadoBLL,
    resumen_encabezadoBLL, listar_encabezados_paginado_famisanar_bll
)

from app.dal.famisanar_dal import DetalleModel, EncabezadoModel, obtener_detalles_agrupados_FamiSanar, obtener_detalles_por_encabezado

router = APIRouter()

@router.get("/automatizacionesFamiSanar/{id_encabezado}", tags=["FamiSanar"])
def get_automatizacion_por_id(id_encabezado: int):
    """
    Obtiene los detalles de una automatización específica dado su id.
    Lanza error 404 si no existe la automatización.
    """
    resultado = obtener_automatizacionFamiSanar(id_encabezado)
    if not resultado:
        raise HTTPException(status_code=404, detail="Automatización no encontrada")
    return resultado


@router.get("/automatizacionFamiSanar/porCC", tags=["Automatizacion FamiSanar"])
def get_CC_aConsultar():
    """
    Obtiene la próxima cédula disponible para consulta.
    Si no hay cédulas disponibles retorna error 404.
    """
    try:
        resultado = obtener_automatizacionCCFamiSanar()
        if not resultado:
            return JSONResponse(status_code=404, content={"error": "No hay cédulas disponibles"})
        id_enc, cedula = resultado
        return {"idEncabezado": id_enc, "cedula": cedula}
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
    plantilla_path = r"\\BITMXL94920DQ\Uipat Datos\FamiSanar\Plantilla\plantilla_famisanar.xlsx"
    if not os.path.exists(plantilla_path):
        return JSONResponse(status_code=404, content={"error": "Plantilla no encontrada"})
    return FileResponse(
        path=plantilla_path,
        filename="plantilla_famisanar.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.post("/excel/guardarFamiSanar", tags=["FamiSanar"])
async def guardar_excel(
    background_tasks: BackgroundTasks,
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

        ruta_input = r"\\BITMXL94920DQ\Uipat Datos\FamiSanar\Datos\Input"
        ruta_output = r"\\BITMXL94920DQ\Uipat Datos\FamiSanar\Correos\Input"

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
            automatizacion="FamiSanar",
            idUsuario=idUsuario,
            fechaCargue=datetime.now(),
            totalRegistros=num_filas,
            estado="En proceso", 
            detalles=detalles
        )

        background_tasks.add_task(procesar_archivo_excel_background, encabezado)

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


@router.post("/automatizacion/resultadoFamiSanar", tags=["Automatizacion FamiSanar"])
async def recibir_resultado(request: Request):
    """
    Recibe un JSON con resultado de automatización, valida datos, y llama a BLL para procesarlo.
    Retorna éxito o error 404 si no se encontró registro para actualizar.
    """
    raw = await request.json()
    print("📥 Payload crudo:", raw)
    try:
        resultado = ResultadoFamiSanarModel(**raw)
    except ValidationError as ve:
        print("❌ ValidationError:", ve.json())
        raise HTTPException(status_code=422, detail=ve.errors())

    updated = procesar_resultado_automatizacionFamiSanar(resultado)
    if not updated:
        raise HTTPException(status_code=404, detail="No se encontró Detalle para la cédula enviada")
    return {"success": True, "mensaje": "Resultado guardado correctamente"}


@router.get("/detalle/listar_agrupadoFamiSanar", tags=["FamiSanar"])
def listar_detalles_agrupados():
    """
    Retorna la lista de detalles agrupados para FamiSanar.
    """
    try:
        datos = obtener_detalles_agrupados_FamiSanar()
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


@router.post("/notificarFinalizacionFamiSanar", tags=["FamiSanar"])
def notificar_finalizacion(idEncabezado: int = Body(..., embed=True)):
    """
    Envía un correo notificando la finalización del proceso FamiSanar al usuario que subió la base.
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
@router.post("/pausar/{id_encabezado}", tags=["FamiSanar"])
def api_pausar_encabezado(id_encabezado: int):
    success = pausar_encabezado(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo pausar el encabezado")
    return {"success": True}

@router.post("/reanudar/{id_encabezado}", tags=["FamiSanar"])
def api_reanudar_encabezado(id_encabezado: int):
    success = reanudar_encabezado(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo reanudar el encabezado")
    return {"success": True}

@router.get("/automatizacionesFamiSanar/{id_encabezado}/detalles", tags=["FamiSanar"])
def get_detalles_paginados(
    id_encabezado: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    cc: str | None = Query(None)
):
    """
    Detalles de un encabezado, paginados. Filtro opcional por cédula exacta.
    Retorna: {"rows": [...], "total": N}
    """
    return listar_detalles_por_encabezado_paginadoBLL(id_encabezado, offset, limit, cc)

@router.get("/automatizacionesFamiSanar/{id_encabezado}/resumen", tags=["FamiSanar"])
def api_resumen_encabezado(id_encabezado: int):
    return resumen_encabezadoBLL(id_encabezado)

@router.get("/automatizacionesFamiSanar", tags=["FamiSanar"])
def get_automatizaciones(
    offset: int | None = Query(None, ge=0),
    limit: int  | None = Query(None, ge=1, le=200)
):
    if offset is None or limit is None:
        return listar_automatizaciones_estadoFamiSanar()
    return listar_encabezados_paginado_famisanar_bll(offset, limit)