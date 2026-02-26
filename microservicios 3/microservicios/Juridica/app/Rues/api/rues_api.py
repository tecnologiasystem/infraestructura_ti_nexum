from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Form, Request, Body
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
import pandas as pd
import os
from io import BytesIO
import numpy as np
from datetime import datetime
from app.Rues.bll.rues_bll import (
    procesar_archivo_excel,
    procesar_resultado_automatizacionRues,
    ResultadoRuesModel, enviar_correo_finalizacion_por_encabezado, pausar_encabezado, reanudar_encabezado, obtener_correoNotificacion
)
from app.Rues.dal.rues_dal import DetalleModel, EncabezadoModel, obtener_detalles_agrupados_Rues, obtener_detalles_por_encabezado

router = APIRouter()

@router.get("/excel/plantilla", tags=["Excel"])
def descargar_plantilla():
    """
    Endpoint GET para descargar la plantilla Excel que los usuarios deben usar para cargar datos de Rues.

    - Se define la ruta UNC donde está almacenada la plantilla.
    - Se verifica si el archivo existe en disco.
    - Si no existe, retorna un JSON con error 404.
    - Si existe, devuelve un FileResponse para que el cliente descargue la plantilla Excel.
    - El media_type es el MIME type para archivos Excel modernos (.xlsx).
    """
    plantilla_path = r"\\172.18.73.76\Uipat Datos\Rues\Plantilla\plantilla_rues.xlsx"
    if not os.path.exists(plantilla_path):
        return JSONResponse(status_code=404, content={"error": "Plantilla no encontrada"})
    return FileResponse(
        path=plantilla_path,
        filename="plantilla_rues.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.post("/excel/guardarRues", tags=["Rues"])
async def guardar_excel(
    file: UploadFile = File(...), # Esperamos un archivo Excel cargado por el cliente
    idUsuario: int = Form(...)    # También un idUsuario enviado como formulario para saber quién sube el archivo
    ):
    """
    Endpoint POST para subir un archivo Excel con datos de Rues.

    Pasos detallados:

    1. Lee el contenido del archivo cargado con await file.read()
    2. Define rutas de entrada y salida UNC para guardar archivos y resultados.
    3. Crea esas carpetas si no existen (para evitar errores).
    4. Guarda el archivo Excel físicamente en la ruta de entrada.
    5. Carga el Excel con pandas, normalizando los nombres de columnas (quita espacios y pasa a mayúsculas).
    6. Reemplaza valores NaN y infinitos para limpiar datos.
    7. Cuenta la cantidad de filas del DataFrame.
    8. Genera un archivo resumen con la cantidad de filas y lo guarda en la carpeta salida.
    9. Recorre cada fila y crea un objeto DetalleModel con los campos correspondientes.
    10. Crea un objeto EncabezadoModel con datos generales y la lista de detalles.
    11. Llama a la función de lógica de negocio procesar_archivo_excel para guardar o procesar esta info.
    12. Elimina archivos temporales creados por Excel que empiezan con "~$" para mantener limpio el directorio.
    13. Retorna un JSON con:
        - Los datos del Excel en formato lista de diccionarios,
        - El nombre del archivo resumen generado,
        - La cantidad de filas procesadas.

    Si ocurre cualquier error en el proceso, captura la excepción, imprime el traceback para debugging
    y retorna un error 500 con la descripción del problema.
    """
    try:
        contents = await file.read()

        # Definición de rutas UNC donde se guardan los archivos cargados y resultados
        ruta_input = r"\\172.18.73.76\Uipat Datos\Rues\Datos\Input"
        ruta_output = r"\\172.18.73.76\Uipat Datos\Rues\Correos\Input"

        # Creación de carpetas si no existen para evitar errores al guardar archivos
        os.makedirs(ruta_input, exist_ok=True)
        os.makedirs(ruta_output, exist_ok=True)

        # Ruta física donde se guardará el archivo cargado
        file_path = os.path.join(ruta_input, file.filename)
        # Guardamos el contenido en disco
        with open(file_path, "wb") as f:
            f.write(contents)

        # Leemos el Excel con pandas para cargar los datos en memoria
        df = pd.read_excel(file_path)
        # Normalizamos nombres de columnas (sin espacios y en mayúsculas) para evitar errores de referencia
        df.columns = [col.strip().upper() for col in df.columns]
        # Reemplazamos valores NaN o infinitos para facilitar procesamiento posterior
        df.replace({np.nan: "", np.inf: None, -np.inf: None}, inplace=True)

        df = df.drop_duplicates(subset=["CEDULA O DOCUMENTO A CONSULTAR"], keep="first")
        # Número total de filas del Excel
        num_filas = len(df)

        # Creamos un archivo resumen en Excel con la cantidad de filas procesadas
        resumen_filename = f"resumen_{file.filename}"
        resumen_path = os.path.join(ruta_output, resumen_filename)
        pd.DataFrame({"Cantidad de filas": [num_filas]}).to_excel(resumen_path, index=False)

        # Convertimos cada fila en un objeto DetalleModel, que representa un registro en el dominio de Rues
        detalles = []
        for _, row in df.iterrows():
            detalles.append(DetalleModel(
                cedula=str(row.get("CEDULA O DOCUMENTO A CONSULTAR", "")).strip(),
                nombre=str(row.get("NOMBRE", "")).strip(),
                identificacion=str(row.get("IDENTIFICACION", "")).strip(),
                categoria=str(row.get("CATEGORIA", "")).strip(),
                camaraComercio=str(row.get("CAMARA DE COMERCIO", "")).strip(),
                numeroMatricula=str(row.get("NUMERO DE MATRICULA", "")).strip(),
                estado=str(row.get("ESTADO", "")).strip(),
                actividadEconomica=str(row.get("ACTIVIDAD ECONOMICA", "")).strip(),
            ))

        # Creamos un EncabezadoModel que agrupa toda la información, con fecha actual y total de registros
        encabezado = EncabezadoModel(
            automatizacion="Rues",
            idUsuario=idUsuario,
            fechaCargue=datetime.now(),
            totalRegistros=num_filas,
            estado="En proceso", 
            detalles=detalles
        )

        # Llamamos a la lógica de negocio para procesar esta estructura y persistirla en BD o lo que corresponda
        id_encabezado = procesar_archivo_excel(encabezado)

        # Limpiamos archivos temporales de Excel que empiezan con "~$" para evitar acumulación
        for archivo in os.listdir(ruta_input):
            if archivo.startswith("~$") and archivo.endswith(".xlsx"):
                try:
                    os.remove(os.path.join(ruta_input, archivo))
                except Exception as e:
                    print(f"Error eliminando archivo temporal: {archivo}. Detalle: {e}")

        # Retornamos el contenido leído para confirmación junto con el resumen y el conteo de filas
        return {
            "data": df.to_dict(orient="records"),
            "resumen": resumen_filename,
            "filas": num_filas
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        # Retornamos error 500 con el mensaje capturado para informar al cliente
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/excel/listar", tags=["Excel"])
async def listar_archivos_excel():
    """
    Endpoint GET para listar los archivos Excel disponibles en la carpeta de salida.
    - Lee los archivos en el directorio configurado para output.
    - Filtra para devolver solo archivos con extensión .xlsx o .xls.
    - En caso de error retorna un JSON con error 500.
    """
    try:
        carpeta = r"\\172.18.73.76\Uipat Datos\Rues\Datos\Output"
        archivos = [f for f in os.listdir(carpeta) if f.endswith(".xlsx") or f.endswith(".xls")]
        return {"archivos": archivos}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/excel/ver_json", tags=["Excel"])
async def ver_contenido_excel_json(nombre: str):
    """
    Endpoint GET para leer un archivo Excel específico y devolver su contenido en JSON.
    - Recibe como parámetro el nombre del archivo.
    - Verifica existencia, y si no existe devuelve error 404.
    - Lee el archivo con pandas y limpia valores nulos e infinitos.
    - Devuelve los datos en formato lista de diccionarios JSON.
    - Maneja errores retornando 500 con el mensaje.
    """
    try:
        carpeta = r"\\172.18.73.76\Uipat Datos\Rues\Datos\Output"
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
    Endpoint GET para descargar un archivo Excel específico.
    - Recibe el nombre del archivo.
    - Valida existencia y si no está devuelve error 404.
    - Devuelve el archivo con el content type para Excel.
    - Maneja excepciones retornando error 500.
    """
    try:
        carpeta = r"\\172.18.73.76\Uipat Datos\Rues\Datos\Output"
        file_path = os.path.join(carpeta, nombre)
        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"error": "Archivo no encontrado"})
        return FileResponse(path=file_path, filename=nombre, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.post("/automatizacion/resultadoRues", tags=["Automatizacion Rues"])
async def recibir_resultado(request: Request):
    """
    Endpoint POST que recibe el resultado de una automatización de Rues en formato JSON.
    - Lee el body crudo y lo imprime para debug.
    - Intenta validar el JSON con el modelo Pydantic ResultadoRuesModel.
    - Si la validación falla, retorna error 422 con detalles.
    - Si es válido, llama a la función para procesar y guardar el resultado.
    - Si no se encontró el detalle correspondiente, retorna error 404.
    - Finalmente devuelve confirmación de éxito.
    """
    raw = await request.json()
    print("📥 Payload crudo:", raw)
    try:
        resultado = ResultadoRuesModel(**raw)
    except ValidationError as ve:
        print("❌ ValidationError:", ve.json())
        raise HTTPException(status_code=422, detail=ve.errors())

    updated = procesar_resultado_automatizacionRues(resultado)
    if not updated:
        raise HTTPException(status_code=404, detail="No se encontró Detalle para la cédula enviada")
    return {"success": True, "mensaje": "Resultado guardado correctamente"}


@router.get("/detalle/listar_agrupadoRues", tags=["Rues"])
def listar_detalles_agrupados():
    """
    Endpoint GET para obtener detalles agrupados de Rues.
    - Llama a la función DAL que obtiene los datos agrupados.
    - En caso de error retorna 500 con el detalle.
    """
    try:
        datos = obtener_detalles_agrupados_Rues()
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

@router.post("/notificarFinalizacionRues", tags=["Rues"])
def notificar_finalizacion(idEncabezado: int = Body(..., embed=True)):
    """
    Envía un correo notificando la finalización del proceso Rues al usuario que subió la base.
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
@router.post("/pausar/{id_encabezado}", tags=["Vigilancia"])
def api_pausar_encabezado(id_encabezado: int):
    success = pausar_encabezado(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo pausar el encabezado")
    return {"success": True}

@router.post("/reanudar/{id_encabezado}", tags=["Vigilancia"])
def api_reanudar_encabezado(id_encabezado: int):
    success = reanudar_encabezado(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo reanudar el encabezado")
    return {"success": True}

#--------- GET PARA NOTIFICACIONES ---------------------------------------------
@router.get("/automatizacionRues/correo", tags=["Rues"])
def get_correo():
    try:
        resultado = obtener_correoNotificacion()
        if not resultado:
            return JSONResponse(status_code=404, content={"error": "No hay cédulas disponibles"})
        id_enc, fechaCargue, correo = resultado
        return {"idEncabezado": id_enc, "fechaCargue": fechaCargue, "correo": correo}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})