from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.bll.vigenciaJuridico_bll import (
obtener_automatizacionCCVigencia
)
router = APIRouter()


@router.get("/automatizacionVigencia/porInfo", tags=["Automatizacion Vigencia"])
def get_Info_aConsultar():
    """
    Obtiene la próxima cédula disponible para consulta.
    Si no hay cédulas disponibles retorna error 404.
    """
    try:
        resultado = obtener_automatizacionCCVigencia()
        if not resultado:
            return JSONResponse(status_code=404, content={"error": "No hay cédulas disponibles"})
        id_enc, cedula= resultado
        return {"idEncabezado": id_enc, "cedula": cedula}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": str(e)})