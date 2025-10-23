from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List
from BLL.embudo_bll import (
    obtener_embudo_llamadas, 
    obtener_efectividad_por_hora, 
    obtener_commitments_acumulados, 
    obtener_assignments_campaign
)

router = APIRouter(prefix="/embudo", tags=["Embudo"])

@router.get("/funnel", response_model=list[dict])
def embudo_llamadas():
    """
    Endpoint que retorna los datos del embudo de llamadas.
    """
    return obtener_embudo_llamadas()

@router.get("/efectividad-por-hora", response_model=list[dict])
def efectividad_por_hora():
    """
    Endpoint que retorna la efectividad de llamadas segmentada por hora.
    """
    return obtener_efectividad_por_hora()

@router.get("/commitments-acumulados", response_model=list[dict])
def commitments_acumulados():
    """
    Endpoint que retorna los commitments acumulados en el tiempo.
    """
    return obtener_commitments_acumulados()

class AssignmentCampaign(BaseModel):
    """
    Modelo Pydantic que representa el resultado de assignments agrupados por campaña.
    """
    name: str
    value: int

@router.get("/by-campaign", response_model=List[AssignmentCampaign])
def assignments_by_campaign(idUsuario: int = Query(...), rol: str = Query(...)):
    """
    Endpoint que retorna la cantidad de assignments para un usuario y rol dados, agrupados por campaña.

    :param idUsuario: ID del usuario que realiza la consulta
    :param rol: Rol del usuario (string)
    :return: Lista de campañas con sus respectivos valores de assignments
    """
    return obtener_assignments_campaign(idUsuario, rol)
