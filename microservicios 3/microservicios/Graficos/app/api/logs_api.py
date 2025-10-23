from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.bll.logs_bll import procesar_logs_por_dia

"""
📄 Módulo de API para exponer información de logs agrupados por día.

Este archivo define un endpoint HTTP tipo GET que se conecta a la capa de lógica de negocio 
para procesar archivos o registros de logs y retornarlos estructurados por día.
"""

# 🔌 Instancia de router de FastAPI para este grupo de endpoints
router = APIRouter()

@router.get("/logs_por_dia")
def obtener_logs_por_dia():
    """
    📊 Endpoint GET que retorna los logs agrupados por día.

    Llama a la función `procesar_logs_por_dia` definida en `logs_bll.py` que contiene 
    la lógica para leer, procesar y agrupar los logs.

    Returns:
        JSONResponse: Diccionario con el resumen por día o un error si ocurre una excepción.
    """
    try:
        # ✅ Procesa y obtiene el resumen de logs por día
        datos = procesar_logs_por_dia()
        return JSONResponse(content=datos)
    except Exception as e:
        # ⚠️ Captura cualquier error inesperado y lo retorna en la respuesta
        return JSONResponse(status_code=500, content={"error": str(e)})
