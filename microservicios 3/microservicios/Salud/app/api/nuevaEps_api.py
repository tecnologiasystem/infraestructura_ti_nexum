"""
Este archivo define el router FastAPI para el módulo NuevaEps, que gestiona automatizaciones,
procesamiento de archivos Excel, consulta y actualización de datos, y envío de notificaciones por correo.

Se integran modelos Pydantic para validación y la lógica de negocio se delega a la capa BLL.
"""

from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Form, Request, Body, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
import pandas as pd
from io import BytesIO
import os
import numpy as np
from datetime import datetime
from pydantic import ValidationError

from app.bll.nuevaEps_bll import (
    procesar_resultado_automatizacionNuevaEps,
    ResultadoNuevaEpsModel,
    enviar_correo_finalizacionNuevaEps,
    procesar_archivo_excel,
    obtener_automatizacion_por_idNuevaEps,
    obtener_automatizacionCCNuevaEps,
    listar_automatizaciones_estadoNuevaEps,
    obtener_automatizacionNuevaEps,  enviar_correo_finalizacion_por_encabezado,
    pausar_encabezado, reanudar_encabezado, resumen_encabezadoNuevaEpsBLL,
    listar_detalles_paginadosNuevaEpsBLL, listar_encabezados_paginadoNuevaEpsBLL
)

from app.dal.nuevaEps_dal import DetalleModel, EncabezadoModel, obtener_detalles_agrupados_NuevaEps, obtener_detalles_por_encabezado

router = APIRouter()

# -----------------------------------
# Función limpiar_encabezado general
# -----------------------------------
def limpiar_encabezado(valor: str) -> str:
    if not valor:
        return valor
    
    valor = valor.strip()
    patrones = ["Nombre", "Fecha de nacimiento", "Edad", "Sexo", "Fecha inicio vigencia afiliación",
                "EPS anterior", "Dirección de residencia", "Teléfono fijo", "Teléfono móvil",
                "Municipio de residencia", "Departamento de residencia", "Tipo de afiliado"]
    for p in patrones:
        if valor.lower().startswith(p.lower()):
            return valor[len(p):].strip()
    return valor


@router.get("/automatizacionesNuevaEps/{id_encabezado}", tags=["Nueva Eps"])
def get_automatizacion_por_id(id_encabezado: int):
    """
    Obtiene detalles de la automatización dada su ID.
    Retorna 404 si no existe.
    """
    resultado = obtener_automatizacionNuevaEps(id_encabezado)
    if not resultado:
        raise HTTPException(status_code=404, detail="Automatización no encontrada")
    return resultado


@router.get("/automatizacionNuevaEps/porCC", tags=["Automatizacion Nueva Eps"])
def get_CC_aConsultar():
    """
    Obtiene la próxima cédula disponible para consulta.
    Si no hay cédulas disponibles retorna error 404.
    """
    try:
        resultado = obtener_automatizacionCCNuevaEps()
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
    Permite descargar la plantilla Excel para Nueva Eps.
    Verifica existencia antes de enviar.
    """
    plantilla_path = r"\\BITMXL94920DQ\Uipat Datos\NuevaEps\Plantilla\plantilla_nuevaEps.xlsx"
    if not os.path.exists(plantilla_path):
        return JSONResponse(status_code=404, content={"error": "Plantilla no encontrada"})
    return FileResponse(
        path=plantilla_path,
        filename="plantilla_nuevaEps.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.post("/excel/guardarNuevaEps", tags=["Nueva Eps"])
async def guardar_excel(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    idUsuario: int = Form(...)
):
    """
    Recibe y guarda archivo Excel, procesa datos para la automatización,
    crea resumen con conteo de filas y elimina archivos temporales de Excel.
    """
    try:
        contents = await file.read()

        ruta_input = r"\\BITMXL94920DQ\Uipat Datos\NuevaEps\Datos\Input"
        ruta_output = r"\\BITMXL94920DQ\Uipat Datos\NuevaEps\Correos\Input"

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
                nombre=limpiar_encabezado (row.get("NOMBRE") or None),
                fechaNacimiento=limpiar_encabezado(row.get("FECHA NACIMIENTO") or None),
                edad=limpiar_encabezado (row.get("EDAD") or None),
                sexo=limpiar_encabezado (row.get("SEXO") or None),
                antiguedad=limpiar_encabezado (row.get("ANTIGUEDAD") or None),
                fechaAfiliacion=limpiar_encabezado (row.get("FECHA AFILIACION") or None),
                epsAnterior=limpiar_encabezado (row.get("EPS ANTERIOR") or None),
                direccion=limpiar_encabezado (row.get("DIRECCION") or None),
                telefono=limpiar_encabezado (row.get("TELEFONO") or None),
                celular=limpiar_encabezado (row.get("CELULAR") or None),
                email=limpiar_encabezado (row.get("EMAIL") or None),
                municipio=limpiar_encabezado (row.get("MUNICIPIO") or None),
                departamento=limpiar_encabezado (row.get("DEPARTAMENTO") or None),
                observacion=limpiar_encabezado (row.get("OBSERVACION") or None),
            ))

        encabezado = EncabezadoModel(
            automatizacion="Nueva Eps",
            idUsuario=idUsuario,
            fechaCargue=datetime.now(),
            totalRegistros=num_filas,
            estado="En proceso",
            detalles=detalles
        )

        background_tasks.add_task(procesar_archivo_excel, encabezado)

        # Limpieza archivos temporales iniciados por Excel
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


@router.post("/automatizacion/resultadoNuevaEps", tags=["Automatizacion Nueva Eps"])
async def recibir_resultado(request: Request):
    """
    Recibe JSON con resultado de automatización, limpia encabezados, valida el formato con Pydantic,
    y llama a la capa BLL para procesar el resultado.
    Retorna error 422 en validación, o 404 si no se encuentra registro a actualizar.
    """
    raw = await request.json()
    print("📥 Payload crudo:", raw)

    # Limpieza antes de validar con Pydantic
    for key in raw:
        if isinstance(raw[key], str):
            raw[key] = limpiar_encabezado(raw[key])

    try:
        resultado = ResultadoNuevaEpsModel(**raw)
    except ValidationError as ve:
        print("❌ ValidationError:", ve.json())
        raise HTTPException(status_code=422, detail=ve.errors())

    updated = procesar_resultado_automatizacionNuevaEps(resultado)
    if not updated:
        raise HTTPException(status_code=404, detail="No se encontró Detalle para la cédula enviada")
    return {"success": True, "mensaje": "Resultado guardado correctamente"}


@router.get("/detalle/listar_agrupadoNuevaEps", tags=["Nueva Eps"])
def listar_detalles_agrupados():
    """
    Retorna lista agrupada de detalles para Nueva Eps.
    """
    try:
        datos = obtener_detalles_agrupados_NuevaEps()
        return {"data": datos}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/excel/exportar_resultados", tags=["Excel"])
def exportar_resultados_por_tanda(id_encabezado: int = Query(...)):
    """
    Exporta resultados de una tanda automatizada a Excel para descarga.
    Retorna error 404 si no hay resultados.
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


@router.post("/notificarFinalizacionNuevaEps", tags=["Nueva Eps"])
def notificar_finalizacion(idEncabezado: int = Body(..., embed=True)):
    """
    Envía un correo notificando la finalización del proceso Nueva eps al usuario que subió la base.
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
@router.post("/pausar/{id_encabezado}", tags=["Nueva Eps"])
def api_pausar_encabezado(id_encabezado: int):
    success = pausar_encabezado(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo pausar el encabezado")
    return {"success": True}

@router.post("/reanudar/{id_encabezado}", tags=["Nueva Eps"])
def api_reanudar_encabezado(id_encabezado: int):
    success = reanudar_encabezado(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo reanudar el encabezado")
    return {"success": True}

@router.get("/automatizacionesNuevaEps/{id_encabezado}/resumen", tags=["Nueva Eps"])
def resumen_encabezado(id_encabezado: int):
    return resumen_encabezadoNuevaEpsBLL(id_encabezado)

@router.get("/automatizacionesNuevaEps/{id_encabezado}/detalles", tags=["Nueva Eps"])
def detalles_paginados(
    id_encabezado: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=500),
    cc: str = Query(None)
):
    return listar_detalles_paginadosNuevaEpsBLL(id_encabezado, offset, limit, cc)

@router.get("/automatizacionesNuevaEps", tags=["Nueva Eps"])
def get_automatizaciones(
    offset: int | None = Query(None, ge=0),
    limit: int  | None = Query(None, ge=1, le=200)
):
    if offset is None or limit is None:
        return listar_automatizaciones_estadoNuevaEps()
    return listar_encabezados_paginadoNuevaEpsBLL(offset, limit)