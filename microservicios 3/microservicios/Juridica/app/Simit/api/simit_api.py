from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Form, Body
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
import pandas as pd
from io import BytesIO
import os
import numpy as np
from datetime import datetime
from app.Simit.bll.simit_bll import (
    procesar_archivo_excel,
    procesar_resultado_automatizacionSimit,
    ResultadoSimitModel, enviar_correo_finalizacion_por_encabezado,
    pausar_encabezado, reanudar_encabezado
)
from app.Simit.dal.simit_dal import DetalleModel, EncabezadoModel, obtener_detalles_agrupados_Simit, obtener_detalles_por_encabezado

router = APIRouter()

@router.get("/excel/plantilla", tags=["Excel"])
async def descargar_plantilla():
    """
    Función para descargar la plantilla Excel para cargar datos Simit.
    
    - Verifica si la plantilla existe en la ruta compartida de red.
    - Si no existe, retorna un error 404.
    - Si existe, retorna el archivo con tipo MIME para Excel, listo para descargar.
    """
    plantilla_path = r"\\BITMXL94920DQ\Uipat Datos\Simit\Plantilla\plantilla_simit.xlsx"
    if not os.path.exists(plantilla_path):
        return JSONResponse(status_code=404, content={"error": "Plantilla no encontrada"})
    return FileResponse(
        path=plantilla_path,
        filename="plantilla_simit.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.post("/excel/guardarSimit", tags=["Simit"])
async def guardar_excel(
    file: UploadFile = File(...),
    idUsuario: int = Form(...)
    ):
    """
    Esta función recibe el archivo Excel con los datos Simit subidos por el usuario y procesa su almacenamiento e inserción.
    
    Pasos que realiza:
    1. Lee el contenido del archivo subido y lo guarda en una ruta de red para procesamiento.
    2. Carga el archivo a un DataFrame de pandas para manejo de datos.
    3. Normaliza nombres de columnas y limpia datos NaN o infinitos.
    4. Genera un archivo resumen con la cantidad de filas procesadas.
    5. Por cada fila, crea un objeto DetalleModel con los datos limpios y procesados.
    6. Crea un EncabezadoModel que contiene metadatos del proceso (usuario, fecha, total registros).
    7. Llama a `procesar_archivo_excel` para insertar la información en la base de datos.
    8. Finalmente, limpia archivos temporales que quedan abiertos y devuelve resumen y datos procesados.
    
    Manejo de errores:
    - Captura excepciones e imprime trazas para depuración.
    - Retorna JSON con el error para informar al cliente.
    """
    try:
        contents = await file.read()

        ruta_input = r"\\BITMXL94920DQ\Uipat Datos\Simit\Datos\Input"
        ruta_output = r"\\BITMXL94920DQ\Uipat Datos\Simit\Correos\Input"

        os.makedirs(ruta_input, exist_ok=True)
        os.makedirs(ruta_output, exist_ok=True)

        file_path = os.path.join(ruta_input, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)

        df = pd.read_excel(file_path)
        df.columns = [col.strip().upper() for col in df.columns]  # Normaliza nombres para evitar errores por espacios o mayúsculas/minúsculas
        df.replace({np.nan: "", np.inf: None, -np.inf: None}, inplace=True)  # Limpia datos inválidos

        df = df.drop_duplicates(subset=["CEDULA"], keep="first") 

        num_filas = len(df)  #Total de registros procesados

        resumen_filename = f"resumen_{file.filename}" 
        resumen_path = os.path.join(ruta_output, resumen_filename)
        pd.DataFrame({"Cantidad de filas": [num_filas]}).to_excel(resumen_path, index=False) 

        detalles = []
        for _, row in df.iterrows():
            """Crea un objeto DetalleModel con los datos de cada fila, aplicando strip para limpiar espacios"""
            detalles.append(DetalleModel(
                cedula=str(row.get("CEDULA", "")).strip(),
                tipo=str(row.get("TIPO", "")).strip(),
                placa=str(row.get("PLACA", "")).strip(),
                secretaria=str(row.get("SECRETARIA", "")).strip()
            ))

        """Se crea el encabezado con metadata del proceso"""
        encabezado = EncabezadoModel(
            automatizacion="Simit",
            idUsuario=idUsuario,
            fechaCargue=datetime.now(),
            totalRegistros=num_filas,
            estado="En proceso",
            detalles=detalles
        )

        """Se llama al proceso que inserta todo en la base de datos"""
        id_encabezado = procesar_archivo_excel(encabezado)

        """Limpieza de archivos temporales generados por Excel (~$)"""
        for archivo in os.listdir(ruta_input):
            if archivo.startswith("~$") and archivo.endswith(".xlsx"):
                try:
                    os.remove(os.path.join(ruta_input, archivo))
                except Exception as e:
                    print(f"Error eliminando archivo temporal: {archivo}. Detalle: {e}")

        """Se devuelve la data en formato dict, nombre del resumen y cantidad de filas procesadas"""
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
    """
    Lista todos los archivos Excel (.xls y .xlsx) presentes en la carpeta de salida de datos RUNT.
    - Retorna un JSON con la lista de archivos.
    - En caso de error, captura excepción y retorna error 500 con detalle.
    """
    try:
        carpeta = r"\\BITMXL94920DQ\Uipat Datos\Simit\Datos\Output"
        archivos = [f for f in os.listdir(carpeta) if f.endswith(".xlsx") or f.endswith(".xls")]
        return {"archivos": archivos}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/ver_json", tags=["Excel"])
async def ver_contenido_excel_json(nombre: str):
    """
    Permite consultar el contenido de un archivo Excel en formato JSON.
    - Recibe el nombre del archivo como parámetro.
    - Verifica que el archivo exista.
    - Lee el archivo y reemplaza valores NaN e infinitos para evitar errores.
    - Retorna un JSON con los datos para mostrar en frontend.
    - Captura y reporta errores con código 500.
    """
    try:
        carpeta = r"\\BITMXL94920DQ\Uipat Datos\Simit\Datos\Output"
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
    """
    Permite descargar un archivo Excel desde la carpeta de salida.
    - Verifica existencia del archivo.
    - Si no existe retorna error 404.
    - Si existe, lo devuelve como FileResponse para descarga directa.
    - Maneja excepciones y retorna error 500 si falla.
    """
    try:
        carpeta = r"\\BITMXL94920DQ\Uipat Datos\Simit\Datos\Output"
        file_path = os.path.join(carpeta, nombre)
        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"error": "Archivo no encontrado"})
        return FileResponse(path=file_path, filename=nombre, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.post("/automatizacion/resultadoSimit", tags=["Automatizacion Simit"])
def recibir_resultado(resultado: ResultadoSimitModel):
    """
    Endpoint para recibir resultados de la automatización Simit.
    - Recibe un JSON validado contra el modelo ResultadoRuntModel.
    - Llama a la función para procesar el resultado y guardarlo en la base.
    - Si se guarda correctamente, devuelve mensaje de éxito.
    - Si no encuentra registro para la cédula, devuelve error 404.
    - Captura excepciones y devuelve error 500 en caso de falla.
    """
    print("📥 JSON recibido:", resultado.dict())

    try:
        updated = procesar_resultado_automatizacionSimit(resultado)
        if updated:
            return {"success": True, "mensaje": "Resultado guardado correctamente"}
        else:
            raise HTTPException(status_code=404, detail="No se encontró Detalle para la cédula enviada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/detalle/listar_agrupadoSimit", tags=["Simit"])
def listar_detalles_agrupados():
    """
    Obtiene todos los detalles agrupados por cédula de Simit para mostrar.
    - Llama a función DAL para traer datos agrupados.
    - Retorna JSON con los datos.
    - Captura y reporta errores con código 500.
    """
    try:
        datos = obtener_detalles_agrupados_Simit()
        return {"data": datos}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/exportar_resultados", tags=["Excel"])
def exportar_resultados_por_tanda(id_encabezado: int = Query(...)):
    """
    Exporta los resultados de la tanda indicada a un archivo Excel para descargar.
    - Obtiene detalles por encabezado desde DAL.
    - Si no hay datos, retorna error 404.
    - Crea DataFrame y lo convierte a Excel en memoria.
    - Retorna StreamingResponse para descarga directa del archivo Excel.
    - Captura excepciones y retorna error 500 en caso de fallo.
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

@router.post("/notificarFinalizacionSimit", tags=["Simit"])
def notificar_finalizacion(idEncabezado: int = Body(..., embed=True)):
    """
    Envía un correo notificando la finalización del proceso Simit al usuario que subió la base.
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
@router.post("/pausar/{id_encabezado}", tags=["Simit"])
def api_pausar_encabezado(id_encabezado: int):
    success = pausar_encabezado(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo pausar el encabezado")
    return {"success": True}

@router.post("/reanudar/{id_encabezado}", tags=["Simit"])
def api_reanudar_encabezado(id_encabezado: int):
    success = reanudar_encabezado(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo reanudar el encabezado")
    return {"success": True}