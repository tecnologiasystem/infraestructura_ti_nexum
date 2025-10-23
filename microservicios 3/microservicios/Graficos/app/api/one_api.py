from fastapi import APIRouter
from app.bll.one_bll import get_accumulated_records

"""
📄 Módulo de API para obtener los tipos de actuación más frecuentes.

Este archivo define un endpoint HTTP tipo GET que se conecta a la lógica de negocio para 
leer un archivo CSV y retornar los 10 tipos de 'Actuación' más comunes en los registros procesados.
"""

# 🔌 Instancia del router de FastAPI para agrupar los endpoints relacionados
router = APIRouter()

@router.get("/registros_acumulados", summary="Top 10 tipos de actuación")
def registros_acumulados():
    """
    📊 Endpoint GET que retorna los 10 tipos de actuación más frecuentes.

    Llama a la función `get_accumulated_records` ubicada en `one_bll.py`, que 
    procesa el archivo de datos y acumula las ocurrencias por tipo de actuación.

    Returns:
        dict: Diccionario con los 10 tipos de actuación más frecuentes.
    """
    return get_accumulated_records()
