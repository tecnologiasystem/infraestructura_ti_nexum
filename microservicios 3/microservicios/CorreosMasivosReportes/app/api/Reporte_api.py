from fastapi import APIRouter
from fastapi import HTTPException, Query
from fastapi.responses import JSONResponse
from app.dal.Reporte_dal import (
    listar_encabezados,
    listar_detalles_por_encabezado,
    dashboard_resumen,
    dashboard_por_remitente,
    dashboard_por_dia,
    dashboard_top_errores,
)
from fastapi.encoders import jsonable_encoder
import io, pandas as pd
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.get("/EmailEnvios/Encabezados")
async def email_encabezados():
    try:
        data = listar_encabezados()
        return JSONResponse(content=jsonable_encoder({"data": data}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/EmailEnvios/Detalle")
async def email_detalle(idEncabezado: int = Query(...)):
    try:
        data = listar_detalles_por_encabezado(idEncabezado)
        return JSONResponse(content=jsonable_encoder({"data": data}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/EmailEnvios/ExportarExcelPorEncabezado")
async def exportar_excel_por_encabezado(idEncabezado: int = Query(...)):
    try:
        data = listar_detalles_por_encabezado(idEncabezado)
        if not data:
            raise HTTPException(status_code=404, detail="No hay detalles para exportar")

        df = pd.DataFrame(data)

        # Elimina columnas que no quiere exportar
        df = df.drop(columns=["idDetalle", "cuerpo", "adjuntos"], errors="ignore")

        columnas_preferidas = [
            "email_destinatario", "asunto", "estado_envio",
            "fecha_registro", "fecha_envio", "error_detalle", "adjuntos"
        ]
        cols_final = [c for c in columnas_preferidas if c in df.columns]
        if cols_final:
            df = df[cols_final]

        bio = io.BytesIO()
        with pd.ExcelWriter(bio, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=f"Detalle_{idEncabezado}")
        bio.seek(0)

        return StreamingResponse(
            bio,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="detalle_{idEncabezado}.xlsx"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- DASHBOARD / TABLERO --------------------

@router.get("/EmailEnvios/Dashboard/PorRemitente")
async def email_dashboard_por_remitente(
    fecha_inicio: str | None = Query(default=None, description="YYYY-MM-DD"),
    fecha_fin: str | None = Query(default=None, description="YYYY-MM-DD"),
    idUsuario: int | None = Query(default=None),
):
    try:
        data = dashboard_por_remitente(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            idUsuario=idUsuario,
        )
        return JSONResponse(content=jsonable_encoder({"data": data}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/EmailEnvios/Dashboard/PorDia")
async def email_dashboard_por_dia(
    fecha_inicio: str | None = Query(default=None, description="YYYY-MM-DD"),
    fecha_fin: str | None = Query(default=None, description="YYYY-MM-DD"),
    idUsuario: int | None = Query(default=None),
    remitente: str | None = Query(default=None),
):
    try:
        data = dashboard_por_dia(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            idUsuario=idUsuario,
            remitente=remitente,
        )
        return JSONResponse(content=jsonable_encoder({"data": data}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/EmailEnvios/Dashboard/TopErrores")
async def email_dashboard_top_errores(
    fecha_inicio: str | None = Query(default=None, description="YYYY-MM-DD"),
    fecha_fin: str | None = Query(default=None, description="YYYY-MM-DD"),
    idUsuario: int | None = Query(default=None),
    remitente: str | None = Query(default=None),
    top: int = Query(default=20, ge=1, le=200),
):
    try:
        data = dashboard_top_errores(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            idUsuario=idUsuario,
            remitente=remitente,
            top=top,
        )
        return JSONResponse(content=jsonable_encoder({"data": data}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------- DASHBOARD / TABLERO ---------------------------

@router.get("/EmailEnvios/Dashboard/Resumen")
async def email_dashboard_resumen(
    fecha_inicio: str | None = Query(None, description="YYYY-MM-DD"),
    fecha_fin: str | None = Query(None, description="YYYY-MM-DD"),
    idUsuario: int | None = Query(None),
    remitente: str | None = Query(None, description="Descripción/Remitente"),
):
    """KPIs globales: enviados, errores, tasa de error, tiempos de envío."""
    try:
        data = dashboard_resumen(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, idUsuario=idUsuario, remitente=remitente)
        return JSONResponse(content=jsonable_encoder({"data": data}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/EmailEnvios/Dashboard/PorRemitente")
async def email_dashboard_por_remitente(
    fecha_inicio: str | None = Query(None, description="YYYY-MM-DD"),
    fecha_fin: str | None = Query(None, description="YYYY-MM-DD"),
    idUsuario: int | None = Query(None),
):
    """Agregado por remitente (el 'correo' o la descripción que uses)."""
    try:
        data = dashboard_por_remitente(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, idUsuario=idUsuario)
        return JSONResponse(content=jsonable_encoder({"data": data}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/EmailEnvios/Dashboard/PorDia")
async def email_dashboard_por_dia(
    fecha_inicio: str | None = Query(None, description="YYYY-MM-DD"),
    fecha_fin: str | None = Query(None, description="YYYY-MM-DD"),
    idUsuario: int | None = Query(None),
    remitente: str | None = Query(None),
):
    """Serie diaria para ver tendencia de envíos/errores."""
    try:
        data = dashboard_por_dia(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, idUsuario=idUsuario, remitente=remitente)
        return JSONResponse(content=jsonable_encoder({"data": data}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/EmailEnvios/Dashboard/TopErrores")
async def email_dashboard_top_errores(
    fecha_inicio: str | None = Query(None, description="YYYY-MM-DD"),
    fecha_fin: str | None = Query(None, description="YYYY-MM-DD"),
    idUsuario: int | None = Query(None),
    remitente: str | None = Query(None),
    top: int = Query(20, ge=1, le=100),
):
    """Top de errores (para el 'margen de error' + causas)."""
    try:
        data = dashboard_top_errores(fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, idUsuario=idUsuario, remitente=remitente, top=top)
        return JSONResponse(content=jsonable_encoder({"data": data}))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    