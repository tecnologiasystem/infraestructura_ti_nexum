from fastapi import APIRouter
from app.bll.datosGail_bll import sincronizar_campanas_lula

"""
Se crea un router de FastAPI para agrupar rutas relacionadas con integración Lula.
Este router será incluido luego en la aplicación principal.
"""
router = APIRouter()

@router.post("/lula/sincronizar-todo")
def sincronizar_todo():
    """
    Endpoint POST que se encarga de ejecutar la función de sincronización completa
    de campañas Lula. Esta función se encuentra en la capa BLL (Business Logic Layer).
    
    Retorna:
    - El resultado directo de la función `sincronizar_campanas_lula()`, que puede ser
      un mensaje de éxito, lista de campañas sincronizadas o errores capturados.
    """
    return sincronizar_campanas_lula()
