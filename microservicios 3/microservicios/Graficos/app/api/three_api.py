from fastapi import APIRouter
from app.bll.three_bll import get_actuaciones_mensuales

"""
📄 Módulo API para obtener las actuaciones procesales mensuales.

Este archivo define un endpoint que retorna los registros agrupados por mes, según los datos 
cargados desde un origen definido en la capa BLL (`three_bll.py`).
"""

# 🔌 Instancia del router de FastAPI que permite organizar las rutas del módulo
router = APIRouter()

@router.get("/actuaciones_por_mes")
def actuaciones_por_mes():
    """
    📅 Endpoint GET que devuelve las actuaciones registradas agrupadas por mes.

    Esta función llama al método `get_actuaciones_mensuales()` de la capa BLL, 
    que se encarga de procesar los datos y retornar un DataFrame mensual.

    Returns:
        dict: Diccionario convertido desde el DataFrame con la información mensual.
              En caso de error, retorna un mensaje de error.
    """
    try:
        data = get_actuaciones_mensuales()
        return data.to_dict()
    except Exception as e:
        return {"error": str(e)}

