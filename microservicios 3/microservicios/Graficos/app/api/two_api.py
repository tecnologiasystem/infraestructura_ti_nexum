from fastapi import APIRouter
from app.bll.two_bll import get_top_radicados

"""
📄 Módulo API para obtener el top 10 de radicados más frecuentes.

Este módulo expone un endpoint HTTP GET que consulta, a través de la capa BLL, los radicados
que aparecen con mayor frecuencia en el conjunto de datos.
"""

# 🔌 Se crea un router de FastAPI para registrar rutas relacionadas con radicados
router = APIRouter()

@router.get("/top_radicados", summary="Top 10 RADICADOS más frecuentes")
def top_radicados():
    """
    📊 Endpoint GET que retorna el top 10 de radicados más comunes.

    Este endpoint invoca la función `get_top_radicados()` definida en la capa de lógica de negocio (BLL).
    El resultado debe ser un diccionario o estructura serializable que represente los radicados
    más frecuentes en la fuente de datos.

    Returns:
        dict | JSONResponse: Diccionario con el top de radicados o mensaje de error.
    """
    return get_top_radicados()
