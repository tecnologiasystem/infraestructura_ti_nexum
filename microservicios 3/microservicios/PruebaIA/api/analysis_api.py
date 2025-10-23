# api/analysis_api.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import json
from typing import Optional

from bll.analysis_service import analyze_project,  generar_informe_ia
from dal import analytics_dal as dal

router = APIRouter(tags=["analítica"])

class AnalyzeResponse(BaseModel):
    run_id: int
    score_general: float | None = None
    semaforo: str | None = None
    resumen: str | None = None

@router.get("/healthz")
def healthz():
    return {"ok": True}

# api/analysis_api.py
@router.post("/analitica/proyecto/{proyecto_id}", response_model=AnalyzeResponse)
def crear_analisis_proyecto(proyecto_id: int, modoNarrativa: str = "extendida"):
    res = analyze_project(proyecto_id=proyecto_id, modo_narrativa=modoNarrativa)
    return res


@router.get("/analitica/run/{run_id}/progress")
def obtener_progreso(run_id: int):
    try:
        data = dal.progress_get(run_id)
        if not data:
            raise HTTPException(status_code=404, detail="Run no encontrado")
        return jsonable_encoder(data)   # 👈 convierte datetimes a strings
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/analitica/run/{run_id}/informe", response_class=HTMLResponse)
def obtener_informe(run_id: int):
    try:
        html = dal.get_informe_html(run_id)
        return HTMLResponse(content=html)
    except Exception as ex:
        raise HTTPException(status_code=400, detail=str(ex))

@router.get("/analitica/reportes")
def obtener_reportes(
    proyecto_id: Optional[int] = None,
    solo_activos: Optional[bool] = False,
    estado: Optional[str] = None,
    semaforo: Optional[str] = None,  # ✅ Parámetro directo
    desde: Optional[str] = None,
    hasta: Optional[str] = None,
    buscar: Optional[str] = None,
    top: Optional[int] = 50,
):
    try:
        reportes = dal.get_reportes(
            proyecto_id=proyecto_id,
            solo_activos=solo_activos,
            estado=estado,
            semaforo=semaforo,  # ✅ Pasar semáforo al DAL
            desde=desde,
            hasta=hasta,
            buscar=buscar,
            top=top,
        )
        return reportes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/proyectos")
def obtener_proyectos():
    try:
        # Lógica para obtener los proyectos desde la base de datos
        proyectos = dal.get_proyectos()  # Suponiendo que tienes una función para esto en el DAL
        return JSONResponse(content=proyectos)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analitica/run/{run_id}/informe-ia")
def obtener_informe_ia(
    run_id: int,
    audiencia: str = Query("ejecutiva", pattern="^(ejecutiva|operativa|ambas)$"),
    format: str = Query("html", pattern="^(html|json)$"),
):
    try:
        data, html = generar_informe_ia(run_id, audiencia=audiencia)
        return JSONResponse(content=data) if format == "json" else HTMLResponse(content=html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))