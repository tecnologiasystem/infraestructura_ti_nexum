from fastapi import APIRouter, HTTPException
from app.bll.monitor_rpa_bll import actualizar_ultima_consulta, listar_detalles_rpa, listar_encabezados_rpa, listar_detalles_rpa_paginados, listar_todos_detalles_por_origen, obtener_resumen_vigencia
from app.dal.monitor_rpa_dal import obtener_datos_encabezado

router = APIRouter()

@router.post("/rpa/notificacion/{origen}/{id_encabezado}")
async def notificacion(origen: str, id_encabezado: int):
    """
    1) Actualiza en memoria y persiste el heartbeat en BD.
    2) Opcionalmente obtiene datos del encabezado para el mensaje de respuesta.
    3) Devuelve OK al Gateway.
    """
    actualizar_ultima_consulta(origen, id_encabezado)
    datos = obtener_datos_encabezado(origen, id_encabezado)
    nombre = datos["automatizacion"] if datos else f"{origen} {id_encabezado}"
    return {
        "status": "ok",
        "message": f"Heartbeat recibido de {nombre} (origen={origen}, idEncabezado={id_encabezado})"
    }

@router.get("/rpa/encabezados/{origen}/{id_encabezado}/detalles", tags=["MonitorRPA"])
async def api_rpa_detalles_paginados(
    origen: str,
    id_encabezado: int,
    offset: int = 0,
    limit: int = 8):

    try:
        return listar_detalles_rpa_paginados(origen, id_encabezado, offset, limit)
    except ValueError as e:
        raise HTTPException(400, str(e))
    
@router.get("/rpa/encabezados/{origen}/{id_encabezado}/resumen", tags=["MonitorRPA"])
async def api_resumen_generico(origen: str, id_encabezado: int):
    if origen.upper() != "VIGENCIA":
        raise HTTPException(404, f"No hay resumen para {origen}")
    try:
        return obtener_resumen_vigencia(id_encabezado)
    except Exception as e:
        raise HTTPException(500, str(e))