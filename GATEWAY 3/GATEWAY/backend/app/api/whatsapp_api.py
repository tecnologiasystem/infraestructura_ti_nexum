from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.bll.whatsapp_bll import (
    obtener_whatsapp_detalle_BLL,
    contar_whatsapp_vacios_BLL,
    obtener_estadisticas_whatsapp_BLL
)
import pandas as pd
import io
from datetime import datetime
import traceback

"""
Instancia de APIRouter para registrar rutas relacionadas con WhatsApp.
"""
router = APIRouter()


def sanitizar_datos_para_excel(datos):
    """
    Sanitiza los datos para evitar problemas al crear el Excel.
    Convierte datetime, None y otros tipos problemáticos.
    """
    if not datos or len(datos) == 0:
        return datos
    
    datos_sanitizados = []
    for row in datos:
        row_sanitizada = {}
        for key, value in row.items():
            # Convertir datetime a string
            if hasattr(value, 'strftime'):
                row_sanitizada[key] = value.strftime('%Y-%m-%d %H:%M:%S')
            # Convertir None a string vacío
            elif value is None:
                row_sanitizada[key] = ''
            # Convertir bytes a string
            elif isinstance(value, bytes):
                try:
                    row_sanitizada[key] = value.decode('utf-8')
                except:
                    row_sanitizada[key] = str(value)
            else:
                row_sanitizada[key] = value
        datos_sanitizados.append(row_sanitizada)
    
    return datos_sanitizados


"""
Endpoint: GET /whatsapp/detalle

Descripción:
Obtiene los registros de WhatsAppDetalle que tienen WhatsApp asignado.
Excluye registros vacíos y registros con estado "Pausado".

Parámetros de consulta:
    - idEncabezado (int): ID del encabezado para filtrar los registros.

Respuestas:
    - 200: Lista de registros con WhatsApp (excluyendo "Pausado").
    - 400: Error en la solicitud.
    - 500: Error interno del servidor.
"""
@router.get("/whatsapp/detalle")
async def obtener_whatsapp_detalle(
    idEncabezado: int = Query(..., description="ID del encabezado")
):
    try:
        resultado, error = obtener_whatsapp_detalle_BLL(idEncabezado)
        
        if error:
            raise HTTPException(status_code=500, detail=error)
        
        return {
            "success": True,
            "data": resultado,
            "total": len(resultado) if resultado else 0
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


"""
Endpoint: GET /whatsapp/vacios

Descripción:
Cuenta los registros de WhatsAppDetalle que no tienen WhatsApp asignado.
Incluye registros vacíos y registros con estado "Pausado".

Parámetros de consulta:
    - idEncabezado (int): ID del encabezado para filtrar los registros.

Respuestas:
    - 200: Cantidad de registros vacíos o pausados.
    - 400: Error en la solicitud.
    - 500: Error interno del servidor.
"""
@router.get("/whatsapp/vacios")
async def contar_whatsapp_vacios(
    idEncabezado: int = Query(..., description="ID del encabezado")
):
    try:
        resultado, error = contar_whatsapp_vacios_BLL(idEncabezado)
        
        if error:
            raise HTTPException(status_code=500, detail=error)
        
        return {
            "success": True,
            "vacios": resultado
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


"""
Endpoint: GET /whatsapp/estadisticas

Descripción:
Obtiene estadísticas completas de WhatsApp (total, con WhatsApp, vacíos/pausados).
Los registros con estado "Pausado" se cuentan como vacíos.

Parámetros de consulta:
    - idEncabezado (int): ID del encabezado para filtrar los registros.

Respuestas:
    - 200: Estadísticas completas.
    - 400: Error en la solicitud.
    - 500: Error interno del servidor.
"""
@router.get("/whatsapp/estadisticas")
async def obtener_estadisticas_whatsapp(
    idEncabezado: int = Query(..., description="ID del encabezado")
):
    try:
        resultado, error = obtener_estadisticas_whatsapp_BLL(idEncabezado)
        
        if error:
            raise HTTPException(status_code=500, detail=error)
        
        return {
            "success": True,
            "estadisticas": resultado
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")


"""
Endpoint: GET /whatsapp/descargar-excel

Descripción:
Genera y descarga un archivo Excel con los registros de WhatsApp.
Incluye una pestaña con los datos y otra con las estadísticas.

Parámetros de consulta:
    - idEncabezado (int): ID del encabezado para filtrar los registros.

Respuestas:
    - 200: Archivo Excel para descargar.
    - 400: Error en la solicitud.
    - 500: Error interno del servidor.
"""
@router.get("/whatsapp/descargar-excel")
async def descargar_excel_whatsapp(
    idEncabezado: int = Query(..., description="ID del encabezado")
):
    try:
        # Obtener datos
        datos, error_datos = obtener_whatsapp_detalle_BLL(idEncabezado)
        if error_datos:
            raise HTTPException(status_code=500, detail=error_datos)
        
        # Obtener estadísticas
        estadisticas, error_stats = obtener_estadisticas_whatsapp_BLL(idEncabezado)
        if error_stats:
            raise HTTPException(status_code=500, detail=error_stats)
        
        # Sanitizar datos para evitar problemas con tipos de SQL Server
        datos_sanitizados = sanitizar_datos_para_excel(datos)
        
        # Crear Excel en memoria
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja 1: Datos de WhatsApp
            if datos_sanitizados and len(datos_sanitizados) > 0:
                df_datos = pd.DataFrame(datos_sanitizados)
                df_datos.to_excel(writer, sheet_name='Datos WhatsApp', index=False)
            else:
                # Si no hay datos, crear un DataFrame vacío con un mensaje
                df_vacio = pd.DataFrame({'Mensaje': ['No hay datos disponibles']})
                df_vacio.to_excel(writer, sheet_name='Datos WhatsApp', index=False)
            
            # Hoja 2: Estadísticas
            df_estadisticas = pd.DataFrame([estadisticas])
            df_estadisticas.to_excel(writer, sheet_name='Estadísticas', index=False)
        
        # Preparar el archivo para descarga
        output.seek(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"whatsapp_detalle_{idEncabezado}_{timestamp}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        error_detail = f"Error al generar Excel: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Para ver el error completo en los logs
        raise HTTPException(status_code=500, detail=f"Error al generar Excel: {str(e)}")
