from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Union
from datetime import date, datetime
import io
import pandas as pd
from fastapi.responses import StreamingResponse

from app.bll.conversaciones_bll import (
    listar_conversaciones,
    obtener_detalle_conversacion,
    exportar_conversaciones_mensajes,
)
from app.models.conversaciones_models import Conversacion, ConversacionDetalle

router = APIRouter(prefix="/crm", tags=["CRM - Conversaciones"])

@router.get("/conversaciones", response_model=List[Conversacion])
def get_conversaciones(
    user_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    canal: Optional[str] = Query(None),
    campaign_id: Optional[Union[int, str]] = Query(None),
):
    return listar_conversaciones(
        user_id=user_id,
        is_active=is_active,
        canal=canal,
        campaign_id=campaign_id,
    )

@router.get("/conversaciones/export")
def export_conversaciones(
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    campaign_id: Optional[Union[int, str]] = Query(None),
    intencion: Optional[str] = Query(None),
    canal: Optional[str] = Query(None),
    pais: Optional[str] = Query(None),
    current_state: Optional[str] = Query(None),
):
    """
    Exporta a Excel todas las filas (conversación + mensaje) filtradas
    por fecha de mensaje, campaña, canal e intención.
    """
    datos = exportar_conversaciones_mensajes(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        campaign_id=campaign_id,
        intencion=intencion,
        canal=canal,
        pais=pais,
        current_state=current_state,
    )

    if not datos:
        # Excel vacío pero válido
        df = pd.DataFrame()
    else:
        df = pd.DataFrame(datos)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Conversaciones")
    output.seek(0)

    filename = f"crm_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename=\"{filename}\"'}
    )

@router.get("/conversaciones/detalle/{conversacion_id}", response_model=ConversacionDetalle)
def get_conversacion_detalle(conversacion_id: int):
    detalle = obtener_detalle_conversacion(conversacion_id)
    if not detalle:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return detalle

