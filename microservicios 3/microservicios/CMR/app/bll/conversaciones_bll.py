from typing import List, Optional, Union, Dict, Any
from datetime import datetime, date, time
from app.models.conversaciones_models import (
    Conversacion,
    Mensaje,
    ConversacionDetalle,
    ResultadoConversacion,
)
from app.dal.conversaciones_dal import (
    listar_conversaciones as dal_listar_conversaciones,
    obtener_conversacion_por_id,
)
from app.dal.mensajes_dal import (
    listar_mensajes_por_conversacion,
    exportar_mensajes_crm,
)

INTENCIONES_ACUERDO = {"acuerdo_pago", "promesa_pago", "cuota_acordada"}
INTENCIONES_RECHAZO = {"rechazo_pago", "no_interesado", "no_puede_pagar"}

def _es_peru(row: Dict[str, Any]) -> bool:
    camp = str(row.get("campaign_id", "")).upper()
    user = str(row.get("user_id", "")).replace("+", "").replace(" ", "")
    return ("PERU" in camp) or user.startswith("51")

def _es_colombia(row: Dict[str, Any]) -> bool:
    camp = str(row.get("campaign_id", "")).upper()
    user = str(row.get("user_id", "")).replace("+", "").replace(" ", "")
    return ("NPL" in camp) or user.startswith("57")


def _inferir_resultado(mensajes: List[Mensaje]) -> ResultadoConversacion:
    if not mensajes:
        return ResultadoConversacion(
            resultado="SIN_MENSAJES",
            ultima_intencion=None,
            total_mensajes=0,
            mensajes_cliente=0,
            mensajes_agente=0,
            necesita_humano=False,
        )

    total = len(mensajes)
    mensajes_cliente = sum(1 for m in mensajes if (m.agente or "").lower() in ("cliente", "user", "usuario"))
    mensajes_agente = sum(1 for m in mensajes if (m.agente or "").lower() not in ("cliente", "user", "usuario"))

    # Tomamos la última intención no nula
    intenciones = [m.intencion for m in mensajes if m.intencion]
    ultima_int = intenciones[-1] if intenciones else None
    ultima_int_lower = (ultima_int or "").lower()

    if ultima_int_lower in INTENCIONES_ACUERDO:
        resultado = "ACUERDO_PAGO"
    elif ultima_int_lower in INTENCIONES_RECHAZO:
        resultado = "RECHAZO"
    else:
        resultado = "EN_CONVERSACION"

    # Si en algún mensaje se marcó necesita_humano = 1
    necesita_humano = any(m.necesita_humano for m in mensajes if m.necesita_humano is not None)

    return ResultadoConversacion(
        resultado=resultado,
        ultima_intencion=ultima_int,
        total_mensajes=total,
        mensajes_cliente=mensajes_cliente,
        mensajes_agente=mensajes_agente,
        necesita_humano=necesita_humano,
    )


def obtener_detalle_conversacion(conversacion_id: int) -> Optional[ConversacionDetalle]:
    conv_dict = obtener_conversacion_por_id(conversacion_id)
    if not conv_dict:
        return None

    mensajes_dict = listar_mensajes_por_conversacion(conversacion_id)

    conv = Conversacion(**conv_dict)
    mensajes = [Mensaje(**m) for m in mensajes_dict]

    resumen = _inferir_resultado(mensajes)

    return ConversacionDetalle(
        conversacion=conv,
        mensajes=mensajes,
        resumen=resumen,
    )


def listar_conversaciones(
    user_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    canal: Optional[str] = None,
    campaign_id: Optional[Union[int, str]] = None,
) -> List[Conversacion]:
    filas = dal_listar_conversaciones(
        user_id=user_id,
        is_active=is_active,
        canal=canal,
        campaign_id=campaign_id,
    )
    return [Conversacion(**f) for f in filas]

def exportar_conversaciones_mensajes(
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    campaign_id: Optional[Union[int, str]] = None,
    intencion: Optional[str] = None,
    canal: Optional[str] = None,
    pais: Optional[str] = None,
    current_state: Optional[str] = None,

) -> List[Dict[str, Any]]:
    """
    Prepara parámetros y delega al DAL de exportar_mensajes_crm
    """
    fi_dt = datetime.combine(fecha_inicio, time.min) if fecha_inicio else None
    ff_dt = datetime.combine(fecha_fin, time.max) if fecha_fin else None

    campaign_id_int: Optional[int] = None

    if isinstance(campaign_id, int):
        campaign_id_int = campaign_id

    elif isinstance(campaign_id, str) and campaign_id.strip():
        # Solo convertir si es estrictamente numérica
        if campaign_id.isdigit():
            campaign_id_int = int(campaign_id)
        else:
            # Si NO es numérica (ej: "NPL"), no filtrar por campaña
            campaign_id_int = None


    result = exportar_mensajes_crm(
        campaign_id=campaign_id_int,
        fecha_inicio=fi_dt,
        fecha_fin=ff_dt,
        intencion=intencion,
        canal=canal,
        current_state=current_state,
    )
    if pais:
        pais_lower = pais.lower().strip()

        if pais_lower in ("perú", "peru"):
            result = [r for r in result if _es_peru(r)]
            return result

        elif pais_lower == "colombia":
            result = [r for r in result if _es_colombia(r)]
    return result


            