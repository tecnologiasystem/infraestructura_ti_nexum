from typing import Any, Dict, List, Optional
from app.config.database import get_connection
from datetime import datetime

def listar_mensajes_por_conversacion(conversacion_id: int) -> List[Dict[str, Any]]:
    """
    Action = 5 en sp_Mensajes_CRUD (SELECT list)
    Filtrando por conversacion_id
    """
    resultados: List[Dict[str, Any]] = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            EXEC dbo.sp_Mensajes_CRUD
                @Action = ?,
                @id = ?,
                @conversacion_id = ?,
                @tipo = ?,
                @texto = ?,
                @intencion = ?,
                @emocion = ?,
                @agente = ?,
                @confianza = ?,
                @necesita_humano = ?,
                @metadata = ?,
                @prompt_tokens = ?,
                @completion_tokens = ?,
                @total_tokens = ?,
                @processing_time_ms = ?
            """,
            5,               
            None,            
            conversacion_id, 
            None, None, None, None, None, None,
            None,            
            None, None, None, None, None
        )
        columns = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            resultados.append(dict(zip(columns, row)))
    return resultados

def exportar_mensajes_crm(
    campaign_id: Optional[int] = None,
    fecha_inicio: Optional[datetime] = None,
    fecha_fin: Optional[datetime] = None,
    intencion: Optional[str] = None,
    canal: Optional[str] = None,
    current_state: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Exporta mensajes + info de conversación usando sp_Conversaciones_ExportMensajes
    """
    resultados: List[Dict[str, Any]] = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            EXEC dbo.sp_Conversaciones_ExportMensajes
                @campaign_id = ?,
                @fecha_inicio = ?,
                @fecha_fin = ?,
                @intencion = ?,
                @canal = ?,
                @current_state = ?
            """,
            campaign_id,
            fecha_inicio,
            fecha_fin,
            intencion,
            canal,
            current_state,
        )
        columns = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            resultados.append(dict(zip(columns, row)))
    return resultados
