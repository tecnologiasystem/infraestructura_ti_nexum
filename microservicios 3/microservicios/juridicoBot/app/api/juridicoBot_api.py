from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.bll.juridicoBot_bll import (
obtener_automatizacionInfoJuridico
)
router = APIRouter()


@router.get("/automatizacionJuridico/porInfo", tags=["Automatizacion Juridico"])
def get_Info_aConsultar():
    """
    Obtiene la próxima cédula disponible para consulta.
    Si no hay cédulas disponibles retorna error 404.
    """
    try:
        resultado = obtener_automatizacionInfoJuridico()
        if not resultado:
            return JSONResponse(status_code=404, content={"error": "No hay cédulas disponibles"})
        id_enc, nombreCompleto, departamento, ciudad, especialidad= resultado
        return {"idEncabezado": id_enc, "nombreCompleto": nombreCompleto,"departamento": departamento, "ciudad": ciudad, "especialidad":especialidad}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})