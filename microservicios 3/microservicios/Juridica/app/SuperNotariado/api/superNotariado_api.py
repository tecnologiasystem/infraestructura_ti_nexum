from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Body, Form
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
import pandas as pd
from pydantic import BaseModel
from io import BytesIO
import os
import numpy as np
from datetime import datetime
from app.SuperNotariado.bll.superNotariado_bll import (
    crear_usuario,
    actualizar_usuario,
    eliminar_usuario,
    obtener_usuario,
    listar_usuarios,
    UsuarioConsultaModel,
    procesar_archivo_excel, 
    procesar_resultado_automatizacion,
    ResultadoModel, pausar_encabezado,
    reanudar_encabezado
)
from app.SuperNotariado.dal.superNotariado_dal import DetalleModel, EncabezadoModel, obtener_detalles_agrupados, obtener_detalles_por_encabezado
from app.SuperNotariado.bll.superNotariado_bll import cargar_usuarios_excel_desde_archivo, tomar_usuario_disponible
from app.SuperNotariado.bll.superNotariado_bll import enviar_correo_finalizacion_por_encabezado

router = APIRouter()

@router.get("/excel/plantilla", tags=["Excel"])
def descargar_plantilla():
    """
    """
    """ 
    Se define una ruta GET para descargar la plantilla Excel.
    Se especifica la ruta del archivo en un recurso compartido.
    Si el archivo no existe, responde con error 404.
    Si existe, devuelve el archivo para descarga con el tipo MIME correcto.
    """
    plantilla_path = r"\\BITMXL94920DQ\Uipat Datos\Super Notariado\Plantilla\plantilla_superNotariado.xlsx"
    if not os.path.exists(plantilla_path):
        return JSONResponse(status_code=404, content={"error": "Plantilla no encontrada"})
    return FileResponse(
        path=plantilla_path,
        filename="plantilla_superNotariado.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.post("/excel/guardar")
async def guardar_excel(
    file: UploadFile = File(...),
    idUsuario: int = Form(...)):
    """
    """
    """
    Recibe un archivo Excel desde una petición POST junto con el idUsuario.
    Guarda el archivo en una carpeta de entrada.
    Lee el Excel y limpia datos nulos o infinitos.
    Cuenta filas para resumen.
    Guarda un archivo resumen con la cantidad de filas procesadas.
    Convierte cada fila en un objeto DetalleModel para su inserción.
    Crea un EncabezadoModel con metadata y lista de detalles.
    Llama a la función para procesar e insertar datos en base de datos.
    Elimina archivos temporales que empiezan con "~$" en la carpeta input.
    Devuelve en JSON los datos, resumen, número de filas y el idEncabezado generado.
    """
    try:
        # Lee bytes del archivo enviado
        contents = await file.read()

        # Define rutas para entrada y salida en red
        ruta_input = r"\\BITMXL94920DQ\Uipat Datos\Super Notariado\Datos\Input"
        ruta_output = r"\\BITMXL94920DQ\Uipat Datos\Super Notariado\Correos\Input"

        # Crea carpetas si no existen
        os.makedirs(ruta_input, exist_ok=True)
        os.makedirs(ruta_output, exist_ok=True)

        # Guarda archivo físicamente en carpeta input
        file_path = os.path.join(ruta_input, file.filename)
        with open(file_path, "wb") as f:
            f.write(contents)

        # Lee archivo Excel a DataFrame pandas
        df = pd.read_excel(file_path)
        # Limpia valores NaN o infinitos
        df.replace({np.nan: "", np.inf: None, -np.inf: None}, inplace=True)

        # Cuenta filas para resumen
        num_filas = len(df)

        # Crea DataFrame resumen con número de filas
        df_resumen = pd.DataFrame({"Cantidad de filas": [num_filas]})

        # Guarda resumen en carpeta output
        resumen_filename = f"resumen_{file.filename}"
        resumen_path = os.path.join(ruta_output, resumen_filename)
        df_resumen.to_excel(resumen_path, index=False, sheet_name="Hoja1")

        # Convierte filas a lista de detalles con campos vacíos excepto cédula
        detalles = []
        for _, row in df.iterrows():
            detalles.append(DetalleModel(
                CC=str(row.get("CEDULA", "")).strip(),
                ciudad="",
                matricula="",
                direccion="",
                vinculadoA=""
            ))

        # Crea encabezado con metadata y detalles
        encabezado = EncabezadoModel(
            automatizacion="SuperNotariado",
            idUsuario=idUsuario,
            fechaCargue=datetime.now(),  
            totalRegistros=num_filas,
            estado="En proceso",
            detalles=detalles
        )
        # Imprime idUsuario recibido (debug)
        print(f"📥 idUsuario recibido en microservicio: {idUsuario}")

        # Llama función para insertar encabezado y detalles en base
        id_encabezado = procesar_archivo_excel(encabezado)

        # Elimina archivos temporales que comienzan con "~$"
        for archivo in os.listdir(ruta_input):
            if archivo.startswith("~$") and archivo.endswith(".xlsx"):
                try:
                    os.remove(os.path.join(ruta_input, archivo))
                except Exception as e:
                    print(f"Error eliminando archivo temporal: {archivo}. Detalle: {e}")
        
        # Retorna los datos en JSON: filas, resumen y idEncabezado
        return {
            "data": df.to_dict(orient="records"),
            "resumen": resumen_filename,
            "filas": num_filas,
            "idEncabezado": id_encabezado
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        # En caso de error retorna JSON con status 500 y mensaje de error
        return JSONResponse(status_code=500, content={"error": str(e)})


@router.get("/excel/descargar_pdf", tags=["Excel"])
async def descargar_pdf_por_cedula(Cedula: str = Query(...)):
    """
    """
    """
    Ruta GET que permite descargar un archivo PDF dado un número de cédula.
    Busca el archivo PDF en la carpeta de descargas.
    Si no existe retorna error 404.
    Si existe, devuelve el archivo con tipo media pdf.
    """
    try:
        carpeta_pdf = r"\\BITMXL94920DQ\Uipat Datos\Super Notariado\Datos\Output\Descargas"
        archivo_pdf = f"{Cedula}.pdf"
        ruta_pdf = os.path.join(carpeta_pdf, archivo_pdf)

        if not os.path.exists(ruta_pdf):
            return JSONResponse(status_code=404, content={"error": f"PDF para matrícula {Cedula} no encontrado"})

        return FileResponse(
            path=ruta_pdf,
            filename=archivo_pdf,
            media_type="application/pdf"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    

@router.get("/darUsuario", tags=["Automatizacion SuperNotariado"])
def dar_usuario():
    """
    """
    """
    Ruta GET para obtener un usuario disponible para automatización.
    Si no hay usuarios disponibles devuelve error 404.
    """
    usuario = tomar_usuario_disponible()
    if not usuario:
        raise HTTPException(status_code=404, detail="No hay usuarios disponibles")
    return usuario


@router.get("/{id_usuario}", tags=["Automatizacion SuperNotariado"])
def obtener(id_usuario: int):
    """
    """
    """
    Ruta GET para obtener datos de usuario por id.
    Si no se encuentra el usuario devuelve error 404.
    """
    usuario = obtener_usuario(id_usuario)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.post("/", tags=["Automatizacion SuperNotariado"])
def crear(usuario: UsuarioConsultaModel):
    """
    """
    """
    Ruta POST para crear un nuevo usuario.
    Llama a función que inserta usuario en base de datos.
    Si falla, devuelve error 500.
    Si tiene éxito, devuelve id generado.
    """
    id_nuevo = crear_usuario(usuario)
    if id_nuevo == -1:
        raise HTTPException(status_code=500, detail="No se pudo crear el usuario")
    return {"idUsuarioConsulta": id_nuevo}


@router.put("/{id_usuario}", tags=["Automatizacion SuperNotariado"])
def actualizar(id_usuario: int, usuario: UsuarioConsultaModel):
    """
    """
    """
    Ruta PUT para actualizar un usuario dado el id.
    Si falla la actualización responde con error 400.
    """
    usuario.idUsuarioConsulta = id_usuario
    if not actualizar_usuario(usuario):
        raise HTTPException(status_code=400, detail="Error al actualizar")
    return {"success": True}


@router.delete("/{id_usuario}", tags=["Automatizacion SuperNotariado"])
def eliminar(id_usuario: int):
    """
    """
    """
    Ruta DELETE para eliminar usuario por id.
    Si falla la eliminación responde error 400.
    """
    if not eliminar_usuario(id_usuario):
        raise HTTPException(status_code=400, detail="Error al eliminar")
    return {"success": True}


@router.post("/automatizacion/resultado", tags=["Automatizacion SuperNotariado"])
def recibir_resultado(resultado: ResultadoModel):
    """
    """
    """
    Ruta POST para recibir resultados de la automatización.
    Intenta procesar resultado y actualizar la base.
    Si no se encuentra detalle para la cédula enviada responde error 404.
    En caso de error interno responde error 500.
    """
    try:
        updated = procesar_resultado_automatizacion(resultado)
        if updated:
            return {"success": True, "mensaje": "Resultado guardado correctamente"}
        else:
            raise HTTPException(status_code=404, detail="No se encontró Detalle para la cédula enviada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/usuariosConsulta/cargar_excel", tags=["Usuarios Consulta"])
def cargar_usuarios_excel():
    """
    """
    """
    Ruta POST para cargar usuarios desde archivo Excel predefinido.
    Llama a función que inserta datos en base.
    Retorna cantidad de registros insertados o error 500 si falla.
    """
    ruta_excel = r"\\BITMXL94920DQ\Uipat Datos\Super Notariado\Correos\Output\Usuarios.xlsx"
    success, resultado = cargar_usuarios_excel_desde_archivo(ruta_excel)
    if success:
        return {"success": True, "registros_insertados": resultado}
    else:
        raise HTTPException(status_code=500, detail=f"Error al insertar: {resultado}")


@router.post("/automatizacion/usuariosConsulta", tags=["Usuarios Consulta"])
def recibir_usuario_automatizacion(usuario: UsuarioConsultaModel = Body(...)):
    """
    """
    """
    Ruta POST para recibir un usuario para la automatización.
    Valida que usuario y contraseña no estén vacíos.
    Inserta usuario nuevo en base.
    Retorna éxito y id nuevo o error 500 si falla.
    """
    try:
        if not usuario.usuario or not usuario.contraseña:
            raise HTTPException(status_code=400, detail="Usuario y contraseña son obligatorios")

        usuario.estado = True
        usuario.fechaUso = datetime.now()

        id_nuevo = crear_usuario(usuario)
        if id_nuevo == -1:
            raise HTTPException(status_code=500, detail="No se pudo insertar el usuario")
        
        return {"success": True, "idUsuarioConsulta": id_nuevo}

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/detalle/listar_agrupado", tags=["SuperNotariado"])
def listar_detalles_agrupados():
    """
    """
    """
    Ruta GET para listar detalles agrupados por cédula.
    Devuelve datos para mostrar resultados.
    En caso de error responde error 500.
    """
    try:
        datos = obtener_detalles_agrupados()
        return {"data": datos}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})
    

@router.get("/excel/exportar_resultados", tags=["Excel"])
def exportar_resultados_por_tanda(id_encabezado: int = Query(...)):
    """
    """
    """
    Ruta GET para exportar resultados de una tanda a un archivo Excel.
    Obtiene datos de base, los convierte a DataFrame y genera archivo Excel en memoria.
    Lo envía en Streaming para descarga directa.
    Si no hay datos para la tanda retorna error 404.
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
    

@router.post("/notificarFinalizacionSuperNotariado", tags=["SuperNotariado"])
def notificar_finalizacion(idEncabezado: int = Body(..., embed=True)):
    """
    Envía un correo notificando la finalización del proceso Super Notariado al usuario que subió la base.
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


class CCModel(BaseModel):
    CC: str

#------------- PAUSAR----------------------------
@router.post("/pausar/{id_encabezado}", tags=["SuperNotariado"])
def api_pausar_encabezado(id_encabezado: int):
    success = pausar_encabezado(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo pausar el encabezado")
    return {"success": True}

@router.post("/reanudar/{id_encabezado}", tags=["SuperNotariado"])
def api_reanudar_encabezado(id_encabezado: int):
    success = reanudar_encabezado(id_encabezado)
    if not success:
        raise HTTPException(status_code=500, detail="No se pudo reanudar el encabezado")
    return {"success": True}