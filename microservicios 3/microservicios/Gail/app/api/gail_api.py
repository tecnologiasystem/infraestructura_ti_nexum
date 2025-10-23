from fastapi import APIRouter
from app.models.gail_models import CampanaGail
from app.bll.gail_bll import registrar_campana_gail
from app.bll.gail_bll import obtener_contact_lists_por_pais, obtener_secuencias_por_pais, obtener_reglas_por_pais

"""
Se define un enrutador específico para las rutas relacionadas con campañas Gail.
Este router permite registrar campañas y consultar listas, secuencias y reglas
según el país correspondiente.
"""
router = APIRouter()

@router.post("/campanas/registrar-gail")
def registrar_campana(campana: CampanaGail):
    """
    Registra una nueva campaña Gail en el sistema.

    Parámetros:
    - campana (CampanaGail): Objeto recibido en formato JSON con los datos de la campaña.

    Retorna:
    - Resultado de la función `registrar_campana_gail`, que contiene el estado del registro.
    """
    return registrar_campana_gail(campana)

@router.get("/campanas/contact_lists/{pais}")
def contact_lists_por_pais(pais: str):
    """
    Obtiene las listas de contacto disponibles para un país específico.

    Parámetros:
    - pais (str): Nombre o código del país.

    Retorna:
    - Listado de listas de contacto disponibles para el país indicado.
    """
    return obtener_contact_lists_por_pais(pais)

@router.get("/campanas/secuencias/{pais}")
def secuencias_por_pais(pais: str):
    """
    Obtiene las secuencias configuradas para campañas en un país específico.

    Parámetros:
    - pais (str): Nombre o código del país.

    Retorna:
    - Lista de secuencias configuradas según el país.
    """
    return obtener_secuencias_por_pais(pais)

@router.get("/campanas/reglas/{pais}")
def reglas_por_pais(pais: str):
    """
    Obtiene las reglas de campañas para un país específico.

    Parámetros:
    - pais (str): Nombre o código del país.

    Retorna:
    - Lista de reglas configuradas para campañas del país indicado.
    """
    return obtener_reglas_por_pais(pais)
