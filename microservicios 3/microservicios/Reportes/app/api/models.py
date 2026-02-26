from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class FiltroRequest(BaseModel):
    tabla: str
    filtros: Optional[Dict[str, str]] = Field(default_factory=dict)  
    columnas: Optional[List[str]] = None
    offset: int = 0
    limit: int = 50
