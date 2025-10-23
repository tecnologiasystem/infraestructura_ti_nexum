from fastapi import APIRouter, HTTPException
from app.bll.focos_resultado_bll import consultar_focos, insertar_focos
from typing import Dict

router = APIRouter()

@router.post("/consultar")
async def consultar_focos_resultado(filtros: Dict[str, str]):
    """
    Endpoint para consultar focos resultado basado en filtros recibidos.

    :param filtros: Diccionario con filtros para consulta (ejemplo: {"fecha": "2025-07-04"})
    :return: Resultado de la consulta devuelto por la función consultar_focos
    """
    """
    📥 Filtros recibidos: debug que muestra filtros recibidos
    """
    print("📥 Filtros recibidos:", filtros)
    try:
        resultado = consultar_focos(filtros)
        return resultado
    except Exception as e:
        """
        ❌ Error al consultar: debug que muestra el error
        """
        print("❌ Error al consultar:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/insertar")
async def insertar_focos_resultado(filtros: dict):
    """
    Endpoint para insertar focos resultado usando datos recibidos.

    :param filtros: Diccionario con datos para insertar
    :return: Resultado de la inserción devuelto por la función insertar_focos
    """
    """
    📥 Filtros recibidos: debug que muestra datos recibidos
    """
    print("📥 Filtros recibidos:", filtros)
    try:
        resultado = insertar_focos(filtros)
        return resultado
    except Exception as e:
        """
        ❌ Error al insertar: debug que muestra el error
        """
        print("❌ Error al insertar:", str(e))
        raise HTTPException(status_code=500, detail=str(e))

