from fastapi import APIRouter
from app.bll import usuarioxcampana_bll
from fastapi.responses import JSONResponse

"""
📄 Módulo API: usuarios_por_campana

Este módulo expone un endpoint HTTP GET que permite consultar la cantidad de usuarios asociados a cada campaña.
Se basa en la lógica definida en el archivo `usuarioxcampana_bll.py`, el cual debe contener el procesamiento
y agregación de estos datos.
"""

# 🔌 Se instancia el router de FastAPI para registrar las rutas de esta sección
router = APIRouter()

@router.get("/usuarios_por_campana")
def obtener_usuarios_por_campana():
    """
    📊 Endpoint GET que retorna la cantidad de usuarios por cada campaña registrada.

    Utiliza la función `procesar_datos_campanas()` de la capa BLL para obtener dos listas:
    - `labels`: nombres o identificadores de campañas.
    - `valores`: cantidad de usuarios asociados a cada campaña.

    Returns:
        JSONResponse: Respuesta JSON con dos arreglos `labels` y `valores`, o un error si ocurre una excepción.
    """
    try:
        labels, valores = usuarioxcampana_bll.procesar_datos_campanas()
        return JSONResponse(content={"labels": labels, "valores": valores})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
