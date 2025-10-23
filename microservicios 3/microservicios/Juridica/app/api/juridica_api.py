from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Form, Body
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
import pandas as pd
import os
from datetime import datetime
import numpy as np
from io import BytesIO
from app.bll.juridica_bll import (
    listar_automatizaciones_estado, obtener_automatizacion, obtener_automatizacionCC,
    obtener_automatizacionCCRunt, listar_automatizaciones_estadoRunt, obtener_automatizacionRunt,
    listar_automatizaciones_estadoRues, obtener_automatizacionRues, obtener_automatizacionCCRues,
    refrescar_automatizacion_estado_por_id, listar_automatizaciones_estadoSimit,
    obtener_automatizacionSimit, obtener_automatizacionCCSimit, listar_automatizaciones_estadoVigilancia,
    obtener_automatizacionVigilancia, obtener_automatizacionRadicadoVigilancia, listar_automatizaciones_estadoCamaraComercio,
    obtener_automatizacionCamaraComercio, obtener_automatizacionCCCamaraComercio, listar_automatizaciones_estadoJuridico,
    obtener_automatizacionJuridico, procesar_archivo_excel, enviar_correo_finalizacion_por_encabezado, pausar_encabezado,
    reanudar_encabezado, listar_automatizaciones_estadoTyba, obtener_automatizacionTyba, obtener_automatizacionCCTyba, procesar_archivo_excelVigencia,
    enviar_correo_finalizacion_por_encabezadoVigencia, pausar_encabezadoVigencia, reanudar_encabezadoVigencia, listar_automatizaciones_estadoVigencia,
    obtener_automatizacionVigencia, listar_detalles_por_encabezado_paginadoBLLSuperNotariado, resumen_encabezadoBLLSuperNotariado,
    listar_encabezados_paginado_SuperNotariado_bll, listar_detalles_por_encabezado_paginadoBLLRunt, resumen_encabezadoBLLRunt,
    listar_encabezados_paginado_Runt_bll, listar_detalles_por_encabezado_paginadoBLLRues, resumen_encabezadoBLLRues, listar_encabezados_paginado_Rues_bll,
    listar_detalles_por_encabezado_paginadoBLLSimit, resumen_encabezadoBLLSimit, listar_encabezados_paginado_Simit_bll,
    listar_detalles_por_encabezado_paginadoBLLVigilancia, resumen_encabezadoBLLVigilancia, listar_encabezados_paginado_Vigilancia_bll,
    listar_detalles_por_encabezado_paginadoBLLCamaraComercio, resumen_encabezadoBLLCamaraComercio, listar_encabezados_paginado_CamaraComercio_bll,
      listar_detalles_por_encabezado_paginadoBLLTyba, resumen_encabezadoBLLTyba, listar_encabezados_paginado_Tyba_bll


)
from app.dal.juridica_dal import DetalleModel, EncabezadoModel, obtener_detalles_agrupados_Juridico, obtener_detalles_por_encabezado
from app.dal.juridica_dal import DetalleModelVigencia, EncabezadoModelVigencia, obtener_detalles_por_encabezadoVigencia


router = APIRouter()

#--------------- SUPERNOTARIADO
@router.get("/automatizaciones", tags=["SuperNotariado"])
def get_automatizaciones():
    """
    Endpoint para listar todas las automatizaciones activas o relevantes de SuperNotariado.
    Retorna la lista completa directamente desde la función BLL `listar_automatizaciones_estado()`.

    Explicación detallada:
    - Este endpoint responde a solicitudes GET sin parámetros para obtener el listado completo
      de automatizaciones del módulo SuperNotariado.
    - Utiliza la función de la capa de negocio (BLL) para abstraer la lógica y el acceso a datos,
      manteniendo el router limpio.
    - No contempla paginación ni filtros adicionales en esta versión.
    - El resultado se envía en el cuerpo de la respuesta HTTP con código 200 implícito.
    """
    return listar_automatizaciones_estado()

@router.get("/automatizaciones/{id_encabezado}", tags=["SuperNotariado"])
def get_automatizacion_por_id(id_encabezado: int):
    """
    Obtiene una automatización específica por su ID (id_encabezado).

    Explicación detallada:
    - Parámetro obligatorio: id_encabezado (int), recibido en la ruta URL.
    - Se llama a la función BLL `obtener_automatizacion` para buscar el registro.
    - Si no se encuentra el registro (resultado vacío o None), se lanza un HTTPException 404,
      indicando que la automatización no existe.
    - Si se encuentra, se retorna el objeto o estructura con los datos para el cliente.
    - Buen manejo de errores para evitar respuestas vacías o ambiguas.
    """
    resultado = obtener_automatizacion(id_encabezado)
    if not resultado:
        raise HTTPException(status_code=404, detail="Automatización no encontrada")
    return resultado

@router.get("/automatizacion/porCC", tags=["Automatizacion"])
def get_CC_aConsultar():
    """
    Obtiene la próxima cédula disponible para consulta.
    Si no hay cédulas disponibles retorna error 404.
    """
    try:
        resultado = obtener_automatizacionCC()
        if not resultado:
            return JSONResponse(status_code=404, content={"error": "No hay cédulas disponibles"})
        id_enc, cedula = resultado
        return {"idEncabezado": id_enc, "CC": cedula}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/automatizacionesSuperNotariado/{id_encabezado}/detalles", tags=["SuperNotariado"])
def get_detalles_paginados(
    id_encabezado: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    CC: str | None = Query(None)
):
    """
    Detalles de un encabezado, paginados. Filtro opcional por cédula exacta.
    Retorna: {"rows": [...], "total": N}
    """
    return listar_detalles_por_encabezado_paginadoBLLSuperNotariado(id_encabezado, offset, limit, CC)

@router.get("/automatizacionesSuperNotariado/{id_encabezado}/resumen", tags=["SuperNotariado"])
def api_resumen_encabezado(id_encabezado: int):
    return resumen_encabezadoBLLSuperNotariado(id_encabezado)

@router.get("/automatizacionesSuperNotariado", tags=["SuperNotariado"])
def get_automatizaciones(
    offset: int | None = Query(None, ge=0),
    limit: int  | None = Query(None, ge=1, le=200)
):
    if offset is None or limit is None:
        return listar_automatizaciones_estado()
    return listar_encabezados_paginado_SuperNotariado_bll(offset, limit)

#---------- RUNT -----------------
@router.get("/automatizacionesRunt", tags=["Runt"])
def get_automatizaciones():
    """
    Lista todas las automatizaciones activas o relevantes para Runt.

    Explicación detallada:
    - Endpoint GET para obtener todas las automatizaciones relacionadas con Runt.
    - Utiliza función BLL específica para Runt para aislar lógica.
    - Devuelve la lista completa sin filtros adicionales.
    """
    return listar_automatizaciones_estadoRunt()

@router.get("/automatizacionesRunt/{id_encabezado}", tags=["Runt"])
def get_automatizacion_por_id(id_encabezado: int):
    """
    Obtiene la automatización Runt específica por ID.

    Explicación detallada:
    - Parámetro `id_encabezado` en URL para consulta directa.
    - Llama a BLL para obtener el registro.
    - Si no existe, lanza error 404.
    - Retorna datos si existe.
    """
    resultado = obtener_automatizacionRunt(id_encabezado)
    if not resultado:
        raise HTTPException(status_code=404, detail="Automatización no encontrada")
    return resultado

@router.get("/automatizacionRunt/porCC", tags=["Automatizacion Runt"])
def get_CC_aConsultar():
    """
    Obtiene la próxima cédula disponible para consulta.
    Si no hay cédulas disponibles retorna error 404.
    """
    try:
        resultado = obtener_automatizacionCCRunt()
        if not resultado:
            return JSONResponse(status_code=404, content={"error": "No hay cédulas disponibles"})
        id_enc, cedula = resultado
        return {"idEncabezado": id_enc, "cedula": cedula}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/automatizacionesRunt/{id_encabezado}/detalles", tags=["Runt"])
def get_detalles_paginados(
    id_encabezado: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    cedula: str | None = Query(None)
):
    """
    Detalles de un encabezado, paginados. Filtro opcional por cédula exacta.
    Retorna: {"rows": [...], "total": N}
    """
    return listar_detalles_por_encabezado_paginadoBLLRunt(id_encabezado, offset, limit, cedula)

@router.get("/automatizacionesRunt/{id_encabezado}/resumen", tags=["Runt"])
def api_resumen_encabezado(id_encabezado: int):
    return resumen_encabezadoBLLRunt(id_encabezado)

@router.get("/automatizacionesRunt", tags=["Runt"])
def get_automatizaciones(
    offset: int | None = Query(None, ge=0),
    limit: int  | None = Query(None, ge=1, le=200)
):
    if offset is None or limit is None:
        return listar_automatizaciones_estadoRunt()
    return listar_encabezados_paginado_Runt_bll(offset, limit)

#-------- RUES ---------
@router.get("/automatizacionesRues", tags=["Rues"])
def get_automatizaciones():
    """
    Lista automatizaciones activas para Rues.

    Explicación detallada:
    - Similar a otros listados, pero para módulo Rues.
    """
    return listar_automatizaciones_estadoRues()

@router.get("/automatizacionesRues/{id_encabezado}", tags=["Rues"])
def get_automatizacion_por_id(id_encabezado: int):
    """
    Obtiene automatización Rues específica por ID.

    Explicación detallada:
    - Parámetro en URL.
    - Llamada a BLL.
    - Error 404 si no existe.
    """
    resultado = obtener_automatizacionRues(id_encabezado)
    if not resultado:
        raise HTTPException(status_code=404, detail="Automatización no encontrada")
    return resultado

@router.get("/automatizacionRues/porCC", tags=["Automatizacion Rues"])
def get_CC_aConsultar():
    """
    Obtiene la próxima cédula disponible para consulta.
    Si no hay cédulas disponibles retorna error 404.
    """
    try:
        resultado = obtener_automatizacionCCRues()
        if not resultado:
            return JSONResponse(status_code=404, content={"error": "No hay cédulas disponibles"})
        id_enc, cedula = resultado
        return {"idEncabezado": id_enc, "cedula": cedula}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/listarAutomatizacionesDetalleResumido")
def listar_automatizacion_detalle_resumido(id_encabezado: int):
    """
    Refresca y devuelve un resumen del estado de automatización por id_encabezado.

    Explicación detallada:
    - Parámetro id_encabezado obligatorio.
    - Llama a BLL para refrescar datos.
    - Si no encuentra registro lanza 404.
    - Si ocurre error lanza HTTP 500 con mensaje.
    - Permite a clientes consultar estado resumido actualizado.
    """
    try:
        resultado = refrescar_automatizacion_estado_por_id(id_encabezado)
        if resultado is None:
            raise HTTPException(status_code=404, detail="No se encontró automatización con ese ID.")
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/automatizacionesRues/{id_encabezado}/detalles", tags=["Rues"])
def get_detalles_paginados(
    id_encabezado: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    cedula: str | None = Query(None)
):
    """
    Detalles de un encabezado, paginados. Filtro opcional por cédula exacta.
    Retorna: {"rows": [...], "total": N}
    """
    return listar_detalles_por_encabezado_paginadoBLLRues(id_encabezado, offset, limit, cedula)

@router.get("/automatizacionesRues/{id_encabezado}/resumen", tags=["Rues"])
def api_resumen_encabezado(id_encabezado: int):
    return resumen_encabezadoBLLRues(id_encabezado)

@router.get("/automatizacionesRues", tags=["Rues"])
def get_automatizaciones(
    offset: int | None = Query(None, ge=0),
    limit: int  | None = Query(None, ge=1, le=200)
):
    if offset is None or limit is None:
        return listar_automatizaciones_estadoRues()
    return listar_encabezados_paginado_Rues_bll(offset, limit)

#---------- SIMIT --------------------------------------------------
@router.get("/automatizacionesSimit", tags=["Simit"])
def get_automatizaciones():
    """
    Lista automatizaciones activas o relevantes para Simit.

    Explicación detallada:
    - Mismo patrón que otros listados.
    """
    return listar_automatizaciones_estadoSimit()

@router.get("/automatizacionesSimit/{id_encabezado}", tags=["Simit"])
def get_automatizacion_por_id(id_encabezado: int):
    """
    Obtiene automatización Simit específica o error 404.

    Explicación detallada:
    - Parámetro obligatorio.
    - Consulta BLL.
    - Manejo de error 404.
    """
    resultado = obtener_automatizacionSimit(id_encabezado)
    if not resultado:
        raise HTTPException(status_code=404, detail="Automatización no encontrada")
    return resultado

@router.get("/automatizacionSimit/porCC", tags=["Automatizacion Simit"])
def get_CC_aConsultar():
    """
    Obtiene la próxima cédula disponible para consulta.
    Si no hay cédulas disponibles retorna error 404.
    """
    try:
        resultado = obtener_automatizacionCCSimit()
        if not resultado:
            return JSONResponse(status_code=404, content={"error": "No hay cédulas disponibles"})
        id_enc, cedula = resultado
        return {"idEncabezado": id_enc, "cedula": cedula}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/automatizacionesSimit/{id_encabezado}/detalles", tags=["Simit"])
def get_detalles_paginados(
    id_encabezado: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    cedula: str | None = Query(None)
):
    """
    Detalles de un encabezado, paginados. Filtro opcional por cédula exacta.
    Retorna: {"rows": [...], "total": N}
    """
    return listar_detalles_por_encabezado_paginadoBLLSimit(id_encabezado, offset, limit, cedula)

@router.get("/automatizacionesSimit/{id_encabezado}/resumen", tags=["Simit"])
def api_resumen_encabezado(id_encabezado: int):
    return resumen_encabezadoBLLSimit(id_encabezado)

@router.get("/automatizacionesSimit", tags=["Simit"])
def get_automatizaciones(
    offset: int | None = Query(None, ge=0),
    limit: int  | None = Query(None, ge=1, le=200)
):
    if offset is None or limit is None:
        return listar_automatizaciones_estadoSimit()
    return listar_encabezados_paginado_Simit_bll(offset, limit)

#---------- VIGILANCIA -----------------
@router.get("/automatizacionesVigilancia", tags=["Vigilancia"])
def get_automatizaciones():
    return listar_automatizaciones_estadoVigilancia()

@router.get("/automatizacionesVigilancia/{id_encabezado}", tags=["Vigilancia"])
def get_automatizacion_por_id(id_encabezado: int):
    resultado = obtener_automatizacionVigilancia(id_encabezado)
    if not resultado:
        raise HTTPException(status_code=404, detail="Automatización no encontrada")
    return resultado

@router.get("/automatizacionVigilancia/porRadicado", tags=["Vigilancia"])
def get_radicado_aConsultar():
    """
    Obtiene la próxima cédula disponible para consulta.
    Si no hay cédulas disponibles retorna error 404.
    """
    try:
        resultado = obtener_automatizacionRadicadoVigilancia()
        if not resultado:
            return JSONResponse(status_code=404, content={"error": "No hay cédulas disponibles"})
        id_enc, fecha_ini, fecha_fin, radicado = resultado
        return {"idEncabezado": id_enc, "fechaInicial": fecha_ini, "fechaFinal": fecha_fin, "radicado": radicado}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/automatizacionesVigilancia/{id_encabezado}/detalles", tags=["Vigilancia"])
def get_detalles_paginados(
    id_encabezado: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    radicado: str | None = Query(None)
):
    """
    Detalles de un encabezado, paginados. Filtro opcional por cédula exacta.
    Retorna: {"rows": [...], "total": N}
    """
    return listar_detalles_por_encabezado_paginadoBLLVigilancia(id_encabezado, offset, limit, radicado)

@router.get("/automatizacionesVigilancia/{id_encabezado}/resumen", tags=["Vigilancia"])
def api_resumen_encabezado(id_encabezado: int):
    return resumen_encabezadoBLLVigilancia(id_encabezado)

@router.get("/automatizacionesVigilancia", tags=["Vigilancia"])
def get_automatizaciones(
    offset: int | None = Query(None, ge=0),
    limit: int  | None = Query(None, ge=1, le=200)
):
    if offset is None or limit is None:
        return listar_automatizaciones_estadoVigilancia()
    return listar_encabezados_paginado_Vigilancia_bll(offset, limit)

#---------- CAMARA COMERCIO -----------------
@router.get("/automatizacionesCamaraComercio", tags=["Camara Comercio"])
def get_automatizaciones():
    return listar_automatizaciones_estadoCamaraComercio()

@router.get("/automatizacionesCamaraComercio/{id_encabezado}", tags=["Camara Comercio"])
def get_automatizacion_por_id(id_encabezado: int):

    resultado = obtener_automatizacionCamaraComercio(id_encabezado)
    if not resultado:
        raise HTTPException(status_code=404, detail="Automatización no encontrada")
    return resultado

@router.get("/automatizacionCamaraComercio/porCC", tags=["Automatizacion Camara Comercio"])
def get_CC_aConsultar():
    """
    Obtiene la próxima cédula disponible para consulta.
    Si no hay cédulas disponibles retorna error 404.
    """
    try:
        resultado = obtener_automatizacionCCCamaraComercio()
        if not resultado:
            return JSONResponse(status_code=404, content={"error": "No hay cédulas disponibles"})
        id_enc, cedula = resultado
        return {"idEncabezado": id_enc, "cedula": cedula}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/automatizacionesCamaraComercio/{id_encabezado}/detalles", tags=["Camara Comercio"])
def get_detalles_paginados(
    id_encabezado: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    cedula: str | None = Query(None)
):
    """
    Detalles de un encabezado, paginados. Filtro opcional por cédula exacta.
    Retorna: {"rows": [...], "total": N}
    """
    return listar_detalles_por_encabezado_paginadoBLLCamaraComercio(id_encabezado, offset, limit, cedula)

@router.get("/automatizacionesCamaraComercio/{id_encabezado}/resumen", tags=["Camara Comercio"])
def api_resumen_encabezado(id_encabezado: int):
    return resumen_encabezadoBLLCamaraComercio(id_encabezado)

@router.get("/automatizacionesCamaraComercio", tags=["Camara Comercio"])
def get_automatizaciones(
    offset: int | None = Query(None, ge=0),
    limit: int  | None = Query(None, ge=1, le=200)
):
    if offset is None or limit is None:
        return listar_automatizaciones_estadoCamaraComercio()
    return listar_encabezados_paginado_CamaraComercio_bll(offset, limit)

#------------- JURIDICO----------------------------
@router.get("/excel/plantilla", tags=["Excel"])
async def descargar_plantilla():
    plantilla_path = r"\\BITMXL94920DQ\Uipat Datos\Juridico\Plantilla\plantilla_juridico.xlsx"
    if not os.path.exists(plantilla_path):
        return JSONResponse(status_code=404, content={"error": "Plantilla no encontrada"})
    return FileResponse(
        path=plantilla_path,
        filename="plantilla_juridico.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.post("/excel/guardarJuridico", tags=["Juridico"])
async def guardar_excel(
    file: UploadFile = File(...),
    idUsuario: int = Form(...)
):
    try:
        contents = await file.read()

        ruta_input = r"\\BITMXL94920DQ\Uipat Datos\Juridico\Datos\Input"
        ruta_output = r"\\BITMXL94920DQ\Uipat Datos\Juridico\Correos\Input"
        os.makedirs(ruta_input, exist_ok=True)
        os.makedirs(ruta_output, exist_ok=True)

        file_path = os.path.join(ruta_input, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)

        df = pd.read_excel(file_path)
        df.columns = [col.strip().upper() for col in df.columns]
        df.replace({np.nan: "", np.inf: None, -np.inf: None}, inplace=True)

        num_filas = len(df)

        resumen_filename = f"resumen_{os.path.splitext(file.filename)[0]}.xlsx"
        resumen_path = os.path.join(ruta_output, resumen_filename)
        pd.DataFrame({"Cantidad de filas": [num_filas]}).to_excel(resumen_path, index=False)

        # Crear detalles con valores por defecto si la columna no está presente
        detalles = []
        for _, row in df.iterrows():
            detalles.append(DetalleModel(
                nombreCompleto=str(row.get("NOMBRE COMPLETO", "")).strip(),
                departamento=str(row.get("DEPARTAMENTO", "")).strip(),
                ciudad=str(row.get("CIUDAD", "")).strip(),
                especialidad=str(row.get("ESPECIALIDAD", "")).strip(),
                idNombres=str(row.get("idNombres", "")).strip(),
                idDetalleJuridico=str(row.get("idDetalleJuridico", "")).strip(),
                idActuaciones=str(row.get("idActuaciones", "")).strip()
            ))

        encabezado = EncabezadoModel(
            automatizacion="Juridico",
            idUsuario=idUsuario,
            fechaCargue=datetime.now(),
            totalRegistros=num_filas,
            estado="En proceso",
            detalles=detalles
        )

        id_encabezado = procesar_archivo_excel(encabezado)

        # Limpieza de archivos temporales Excel (~$)
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
        carpeta = r"\\BITMXL94920DQ\Uipat Datos\Juridico\Datos\Output"
        archivos = [f for f in os.listdir(carpeta) if f.endswith(".xlsx") or f.endswith(".xls")]
        return {"archivos": archivos}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/ver_json", tags=["Excel"])
async def ver_contenido_excel_json(nombre: str):
    try:
        carpeta = r"\\BITMXL94920DQ\Uipat Datos\Juridico\Datos\Output"
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
        carpeta = r"\\BITMXL94920DQ\Uipat Datos\Juridico\Datos\Output"
        file_path = os.path.join(carpeta, nombre)
        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"error": "Archivo no encontrado"})
        return FileResponse(path=file_path, filename=nombre, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})



@router.get("/detalle/listar_agrupadoJuridico", tags=["Juridico"])
def listar_detalles_agrupados():
    try:
        datos = obtener_detalles_agrupados_Juridico()
        return {"data": datos}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/exportar_resultados", tags=["Excel"])
def descargar_acciones(id_encabezado: int = Query(..., description="ID del encabezado Juridico")):
    try:
        data_acc4 = obtener_detalles_por_encabezado(id_encabezado, 4)
        data_acc5 = obtener_detalles_por_encabezado(id_encabezado, 5)
        data_acc6 = obtener_detalles_por_encabezado(id_encabezado, 6)
        data_acc7 = obtener_detalles_por_encabezado(id_encabezado, 7)

        if not any([data_acc4, data_acc5, data_acc6, data_acc7]):
            return JSONResponse(status_code=404, content={"error": "No se encontraron resultados para este id_encabezado"})

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            if data_acc4:
                pd.DataFrame(data_acc4).to_excel(writer, sheet_name="Detalles", index=False)
            else:
                pd.DataFrame([{"mensaje": "Sin datos"}]).to_excel(writer, sheet_name="Detalles", index=False)

            if data_acc5:
                pd.DataFrame(data_acc5).to_excel(writer, sheet_name="Resumen", index=False)
            else:
                pd.DataFrame([{"mensaje": "Sin datos"}]).to_excel(writer, sheet_name="Resumen", index=False)

            if data_acc6:
                pd.DataFrame(data_acc6).to_excel(writer, sheet_name="Vacios", index=False)
            else:
                pd.DataFrame([{"mensaje": "Sin datos"}]).to_excel(writer, sheet_name="Vacios", index=False)

            if data_acc7:
                pd.DataFrame(data_acc7).to_excel(writer, sheet_name="Error", index=False)
            else:
                pd.DataFrame([{"mensaje": "Sin datos"}]).to_excel(writer, sheet_name="Error", index=False)

        output.seek(0)

        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="juridico_{id_encabezado}_acciones_4_5_6_7.xlsx"'}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/acciones/{id_encabezado}/accion5", tags=["Juridico"])
def accion5_resumen_personas(id_encabezado: int):
    from app.dal.juridica_dal import obtener_accion5_por_encabezado
    data = obtener_accion5_por_encabezado(id_encabezado)
    # Normaliza nombres de campos por si el SP cambia capitalización
    return {"data": [{"nombreCompleto": r.get("nombreCompleto"),
                      "NumeroProcesos": r.get("NumeroProcesos", r.get("NumeroProcesos".lower()))}
                     for r in data]}

@router.get("/acciones/{id_encabezado}/accion4", tags=["Juridico"])
def accion4_detalles(id_encabezado: int):
    from app.dal.juridica_dal import obtener_accion4_por_encabezado
    data = obtener_accion4_por_encabezado(id_encabezado)
    return {"data": data}


@router.post("/notificarFinalizacionJuridico", tags=["Juridico"])
def notificar_finalizacion(idEncabezado: int = Body(..., embed=True)):
    """
    Envía un correo notificando la finalización del proceso Juridico al usuario que subió la base.
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
@router.post("/pausar/{id_encabezado}", tags=["Juridico"])
def api_pausar_encabezado(id_encabezado: int):
    success = pausar_encabezado(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo pausar el encabezado")
    return {"success": True}

@router.post("/reanudar/{id_encabezado}", tags=["Juridico"])
def api_reanudar_encabezado(id_encabezado: int):
    success = reanudar_encabezado(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo reanudar el encabezado")
    return {"success": True}

@router.get("/automatizacionesJuridico", tags=["Juridico"])
def get_automatizaciones():
    return listar_automatizaciones_estadoJuridico()

@router.get("/automatizacionesJuridico/{id_encabezado}", tags=["Juridico"])
def get_automatizacion_por_id(id_encabezado: int):

    resultado = obtener_automatizacionJuridico(id_encabezado)
    if not resultado:
        raise HTTPException(status_code=404, detail="Automatización no encontrada")
    return resultado

#---------- TYBA -----------------
@router.get("/automatizacionesTyba", tags=["Tyba"])
def get_automatizaciones():
    return listar_automatizaciones_estadoTyba()

@router.get("/automatizacionesTyba/{id_encabezado}", tags=["Tyba"])
def get_automatizacion_por_id(id_encabezado: int):
    resultado = obtener_automatizacionTyba(id_encabezado)
    if not resultado:
        raise HTTPException(status_code=404, detail="Automatización no encontrada")
    return resultado

@router.get("/automatizacionTyba/porCC", tags=["Automatizacion Tyba"])
def get_CC_aConsultar():
    try:
        resultado = obtener_automatizacionCCTyba()
        if not resultado:
            return JSONResponse(status_code=404, content={"error": "No hay cédulas disponibles"})
        id_enc, cedula = resultado
        return {"idEncabezado": id_enc, "cedula": cedula}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    
@router.get("/automatizacionesTyba/{id_encabezado}/detalles", tags=["Tyba"])
def get_detalles_paginados(
    id_encabezado: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    cedula: str | None = Query(None)
):
    """
    Detalles de un encabezado, paginados. Filtro opcional por cédula exacta.
    Retorna: {"rows": [...], "total": N}
    """
    return listar_detalles_por_encabezado_paginadoBLLTyba(id_encabezado, offset, limit, cedula)

@router.get("/automatizacionesTyba/{id_encabezado}/resumen", tags=["Tyba"])
def api_resumen_encabezado(id_encabezado: int):
    return resumen_encabezadoBLLTyba(id_encabezado)

@router.get("/automatizacionesTyba", tags=["Tyba"])
def get_automatizaciones(
    offset: int | None = Query(None, ge=0),
    limit: int  | None = Query(None, ge=1, le=200)
):
    if offset is None or limit is None:
        return listar_automatizaciones_estadoTyba()
    return listar_encabezados_paginado_Tyba_bll(offset, limit)

#------------- VIGENCIA----------------------------
@router.get("/excel/plantillaVigencia", tags=["Excel"])
async def descargar_plantilla():
    plantilla_path = r"\\BITMXL94920DQ\Uipat Datos\Vigencia\Plantilla\plantilla_vigencia.xlsx"
    if not os.path.exists(plantilla_path):
        return JSONResponse(status_code=404, content={"error": "Plantilla no encontrada"})
    return FileResponse(
        path=plantilla_path,
        filename="plantilla_vigencia.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.post("/excel/guardarVigencia", tags=["Vigencia"])
async def guardar_excel(
    file: UploadFile = File(...),
    idUsuario: int = Form(...)
):
    try:
        contents = await file.read()

        ruta_input = r"\\BITMXL94920DQ\Uipat Datos\Vigencia\Datos\Input"
        ruta_output = r"\\BITMXL94920DQ\Uipat Datos\Vigencia\Correos\Input"
        os.makedirs(ruta_input, exist_ok=True)
        os.makedirs(ruta_output, exist_ok=True)

        file_path = os.path.join(ruta_input, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)

        df = pd.read_excel(file_path)
        df.columns = [col.strip().upper() for col in df.columns]
        df.replace({np.nan: "", np.inf: None, -np.inf: None}, inplace=True)

        num_filas = len(df)

        resumen_filename = f"resumen_{os.path.splitext(file.filename)[0]}.xlsx"
        resumen_path = os.path.join(ruta_output, resumen_filename)
        pd.DataFrame({"Cantidad de filas": [num_filas]}).to_excel(resumen_path, index=False)

        # Crear detalles con valores por defecto si la columna no está presente
        detalles = []
        for _, row in df.iterrows():
            detalles.append(DetalleModelVigencia(
                nombre=str(row.get("NOMBRE", "")).strip(),
                cedula=str(row.get("CEDULA", "")).strip()
            ))

        encabezado = EncabezadoModelVigencia(
            automatizacion="Vigencia",
            idUsuario=idUsuario,
            fechaCargue=datetime.now(),
            totalRegistros=num_filas,
            estado="En proceso",
            detalles=detalles
        )

        id_encabezado = procesar_archivo_excelVigencia(encabezado)

        # Limpieza de archivos temporales Excel (~$)
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
        carpeta = r"\\BITMXL94920DQ\Uipat Datos\Vigencia\Datos\Output"
        archivos = [f for f in os.listdir(carpeta) if f.endswith(".xlsx") or f.endswith(".xls")]
        return {"archivos": archivos}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/excel/ver_json", tags=["Excel"])
async def ver_contenido_excel_json(nombre: str):
    try:
        carpeta = r"\\BITMXL94920DQ\Uipat Datos\Vigencia\Datos\Output"
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
        carpeta = r"\\BITMXL94920DQ\Uipat Datos\Vigencia\Datos\Output"
        file_path = os.path.join(carpeta, nombre)
        if not os.path.exists(file_path):
            return JSONResponse(status_code=404, content={"error": "Archivo no encontrado"})
        return FileResponse(path=file_path, filename=nombre, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/excel/exportar_resultadosVigencia", tags=["Excel"])
def exportar_resultados_por_tanda(id_encabezado: int = Query(...)):

    try:
        data = obtener_detalles_por_encabezadoVigencia(id_encabezado)

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

@router.post("/notificarFinalizacionVigencia", tags=["Vigencia"])
def notificar_finalizacion(idEncabezado: int = Body(..., embed=True)):
    try:
        enviado = enviar_correo_finalizacion_por_encabezadoVigencia(idEncabezado)
        if enviado:
            return {"success": True, "mensaje": "Correo enviado"}
        else:
            return {"success": False, "mensaje": "No se pudo enviar el correo"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

#------------- PAUSAR----------------------------
@router.post("/pausarVigencia/{id_encabezado}", tags=["Vigencia"])
def api_pausar_encabezado(id_encabezado: int):
    success = pausar_encabezadoVigencia(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo pausar el encabezado")
    return {"success": True}

@router.post("/reanudarVigencia/{id_encabezado}", tags=["Vigencia"])
def api_reanudar_encabezado(id_encabezado: int):
    success = reanudar_encabezadoVigencia(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo reanudar el encabezado")
    return {"success": True}

@router.get("/automatizacionesVigencia", tags=["Vigencia"])
def get_automatizaciones():
    return listar_automatizaciones_estadoVigencia()

@router.get("/automatizacionesVigencia/{id_encabezado}", tags=["Vigencia"])
def get_automatizacion_por_id(id_encabezado: int):

    resultado = obtener_automatizacionVigencia(id_encabezado)
    if not resultado:
        raise HTTPException(status_code=404, detail="Automatización no encontrada")
    return resultado