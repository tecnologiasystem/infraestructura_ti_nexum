from fastapi import APIRouter
from app.bll import usuarioxrol_bll
from fastapi.responses import JSONResponse

"""
📄 Módulo API: usuarios_por_rol

Este módulo define una ruta HTTP GET que expone la distribución de usuarios por rol del sistema.
La lógica de negocio es manejada en `usuarioxrol_bll.py`.
"""

# 🔌 Se crea una instancia del enrutador de FastAPI para registrar los endpoints asociados
router = APIRouter()

@router.get("/usuarios_por_rol")
def obtener_usuarios_por_rol():
    """
    📊 Endpoint GET que retorna la cantidad de usuarios agrupados por cada rol existente en el sistema.

    Utiliza la función `obtener_distribucion_roles()` de la capa de lógica de negocio (BLL)
    para extraer y procesar los datos relevantes.

    Returns:
        JSONResponse: Un JSON que contiene:
            - `labels`: una lista con los nombres de los roles.
            - `valores`: una lista con la cantidad de usuarios por cada rol.
        En caso de error, retorna un JSON con el mensaje de error y un status 500.
    """
    try:
        labels, valores = usuarioxrol_bll.obtener_distribucion_roles()
        return JSONResponse(content={"labels": labels, "valores": valores})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

