from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.dal.contelfinanciera_dal import insertar_detalle_Coltefinanciera

class ResultadoModel(BaseModel):
    CuentaDeposito: Optional[str]
    FechaTransaccion: Optional[str]
    FechaHoraAplicacion: Optional[str]
    Descripcion: Optional[str]
    Referencia: Optional[str]
    Debito: Optional[str]
    Credito: Optional[str]
    Tipo: Optional [str]

def procesar_resultado_automatizacionColtefinanciera(resultado: ResultadoModel) -> bool:
    """
    Inserta o actualiza el resultado de la automatización para una cédula específica.
    Retorna True si se actualizó correctamente, False si no se encontró el registro.
    """
    return insertar_detalle_Coltefinanciera(resultado)