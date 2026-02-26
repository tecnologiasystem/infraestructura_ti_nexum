from typing import Any, Dict, List, Optional, Union
from app.config.database import get_connection

def listar_conversaciones(
    user_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    canal: Optional[str] = None,
    campaign_id: Optional[Union[int, str]] = None,
) -> List[Dict[str, Any]]:
    """
    Action = 5 en sp_Conversaciones_CRUD (SELECT list)
    """
    from datetime import datetime

    resultados: List[Dict[str, Any]] = []
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            EXEC dbo.sp_Conversaciones_CRUD
                @Action = ?,
                @id = ?,
                @user_id = ?,
                @campaign_id = ?,
                @title = ?,
                @current_state = ?,
                @context_data = ?,
                @is_active = ?,
                @session_id = ?,
                @canal = ?,
                @metadata = ?
            """,
            5,              
            None,           
            user_id,
            campaign_id,
            None,           
            None,           
            None,          
            is_active,
            None,         
            canal,
            None,          
        )
        columns = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            resultados.append(dict(zip(columns, row)))
    return resultados


def obtener_conversacion_por_id(conversacion_id: int) -> Optional[Dict[str, Any]]:
    """
    Action = 4 en sp_Conversaciones_CRUD (SELECT single)
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            EXEC dbo.sp_Conversaciones_CRUD
                @Action = ?,
                @id = ?,
                @user_id = ?,
                @campaign_id = ?,
                @title = ?,
                @current_state = ?,
                @context_data = ?,
                @is_active = ?,
                @session_id = ?,
                @canal = ?,
                @metadata = ?
            """,
            4,             
            conversacion_id,
            None, None, None, None, None, None, None, None, None
        )
        row = cursor.fetchone()
        if not row:
            return None
        columns = [col[0] for col in cursor.description]
        return dict(zip(columns, row))
