from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Form, Body
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
import pandas as pd
from io import BytesIO
import os
import numpy as np
from datetime import datetime
from app.CamaraComercio.bll.camaraComercio_bll import (
    procesar_archivo_excel,
    procesar_resultado_automatizacionCamaraComercio,
    ResultadoCamaraComercioModel, enviar_correo_finalizacion_por_encabezado,
    pausar_encabezado, reanudar_encabezado
)
from app.CamaraComercio.dal.camaraComercio_dal import DetalleModel, EncabezadoModel, obtener_detalles_agrupados_CamaraComercio, obtener_detalles_por_encabezado

router = APIRouter()

@router.get("/excel/plantilla", tags=["Excel"])
async def descargar_plantilla():
    plantilla_path = r"\\BITMXL94920DQ\Uipat Datos\Camara Comercio\Plantilla\plantilla_camaraComercio.xlsx"
    if not os.path.exists(plantilla_path):
        return JSONResponse(status_code=404, content={"error": "Plantilla no encontrada"})
    return FileResponse(
        path=plantilla_path,
        filename="plantilla_camaraComercio.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.post("/excel/guardarCamaraComercio", tags=["Camara Comercio"])
async def guardar_excel(
    file: UploadFile = File(...),
    idUsuario: int = Form(...)
    ):
    try:
        contents = await file.read()

        ruta_input = r"\\BITMXL94920DQ\Uipat Datos\Camara Comercio\Datos\Input"
        ruta_output = r"\\BITMXL94920DQ\Uipat Datos\Camara Comercio\Correos\Input"

        os.makedirs(ruta_input, exist_ok=True)
        os.makedirs(ruta_output, exist_ok=True)

        file_path = os.path.join(ruta_input, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)

        df = pd.read_excel(file_path)
        df.columns = [col.strip().upper() for col in df.columns]
        df.replace({np.nan: "", np.inf: None, -np.inf: None}, inplace=True) 

        df = df.drop_duplicates(subset=["CEDULA"], keep="first") 

        num_filas = len(df)

        resumen_filename = f"resumen_{file.filename}"
        resumen_path = os.path.join(ruta_output, resumen_filename)
        pd.DataFrame({"Cantidad de filas": [num_filas]}).to_excel(resumen_path, index=False) 

        detalles = []
        for _, row in df.iterrows():
            detalles.append(DetalleModel(
                cedula=str(row.get("CEDULA", "")).strip()
            ))

        encabezado = EncabezadoModel(
            automatizacion="Camara de Comercio",
            idUsuario=idUsuario,
            fechaCargue=datetime.now(),
            totalRegistros=num_filas,
            estado="En proceso",
            detalles=detalles
        )

        id_encabezado = procesar_archivo_excel(encabezado)

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

@router.get("/excel/listar", tags=["Excel"])
async def listar_archivos_excel():
    try:
        carpeta = r"\\BITMXL94920DQ\Uipat Datos\Camara Comercio\Datos\Output"
        archivos = [f for f in os.listdir(carpeta) if f.endswith(".xlsx") or f.endswith(".xls")]
        return {"archivos": archivos}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/ver_json", tags=["Excel"])
async def ver_contenido_excel_json(nombre: str):
    try:
        carpeta = r"\\BITMXL94920DQ\Uipat Datos\Camara Comercio\Datos\Output"
        file_path = os.path.join(carpeta, nombre)

        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"error": "Archivo no encontrado"})

        df = pd.read_excel(file_path)
        df.replace({np.nan: "", np.inf: None, -np.inf: None}, inplace=True)
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/ver", tags=["Excel"])
async def descargar_archivo_excel(nombre: str):
    try:
        carpeta = r"\\BITMXL94920DQ\Uipat Datos\Camara Comercio\Datos\Output"
        file_path = os.path.join(carpeta, nombre)
        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"error": "Archivo no encontrado"})
        return FileResponse(path=file_path, filename=nombre, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/automatizacion/resultadoCamaraComercio", tags=["Automatizacion Camara Comercio"])
def recibir_resultado(resultado: ResultadoCamaraComercioModel):
    print("📥 JSON recibido:", resultado.dict())

    try:
        updated = procesar_resultado_automatizacionCamaraComercio(resultado)
        if updated:
            return {"success": True, "mensaje": "Resultado guardado correctamente"}
        else:
            raise HTTPException(status_code=404, detail="No se encontró Detalle para la cédula enviada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/detalle/listar_agrupadoCamaraComercio", tags=["Camara Comercio"])
def listar_detalles_agrupados():
    try:
        datos = obtener_detalles_agrupados_CamaraComercio()
        return {"data": datos}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/exportar_resultados", tags=["Excel"])
def exportar_resultados_por_tanda(id_encabezado: int = Query(...)):
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

@router.post("/notificarFinalizacionCamaraComercio", tags=["Camara Comercio"])
def notificar_finalizacion(idEncabezado: int = Body(..., embed=True)):
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
@router.post("/pausar/{id_encabezado}", tags=["Camara Comercio"])
def api_pausar_encabezado(id_encabezado: int):
    success = pausar_encabezado(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo pausar el encabezado")
    return {"success": True}

@router.post("/reanudar/{id_encabezado}", tags=["Camara Comercio"])
def api_reanudar_encabezado(id_encabezado: int):
    success = reanudar_encabezado(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo reanudar el encabezado")
    return {"success": True}