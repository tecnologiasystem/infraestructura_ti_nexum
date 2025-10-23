from fastapi import APIRouter, HTTPException
from app.bll.focos_trabajable_bll import obtener_resultados_cargue

router = APIRouter()

@router.post("/consultar")
async def consultar_cargue_focos_api(filtros: dict):
    """
    Endpoint para consultar resultados de cargue de focos según filtros recibidos.

    :param filtros: Diccionario con parámetros para filtrar la consulta.
    :return: Resultados obtenidos desde la capa BLL mediante obtener_resultados_cargue.
    :raises HTTPException 500: En caso de error en la consulta.
    """
    try:
        resultados = obtener_resultados_cargue(filtros)
        return resultados
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
