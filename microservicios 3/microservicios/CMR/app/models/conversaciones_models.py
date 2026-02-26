from typing import List, Optional, Union
from pydantic import BaseModel
from datetime import datetime

class Mensaje(BaseModel):
    id: int
    conversacion_id: int
    tipo: Optional[str] = None
    texto: Optional[str] = None
    intencion: Optional[str] = None
    emocion: Optional[str] = None
    agente: Optional[str] = None
    confianza: Optional[float] = None
    necesita_humano: Optional[bool] = None
    metadata: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    processing_time_ms: Optional[int] = None
    created_at: Optional[datetime] = None  

class Conversacion(BaseModel):
    id: int
    user_id: Optional[str]
    campaign_id: Optional[Union[int, str]] = None
    title: Optional[str]
    current_state: Optional[str]
    context_data: Optional[str]
    is_active: bool
    session_id: Optional[str]
    canal: Optional[str]
    metadata: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    closed_at: Optional[datetime]

class ResultadoConversacion(BaseModel):
    """Resumen tipo CRM/Auditoría para tablero."""
    resultado: str
    ultima_intencion: Optional[str]
    total_mensajes: int
    mensajes_cliente: int
    mensajes_agente: int
    necesita_humano: bool

class ConversacionDetalle(BaseModel):
    conversacion: Conversacion
    mensajes: List[Mensaje]
    resumen: ResultadoConversacion
