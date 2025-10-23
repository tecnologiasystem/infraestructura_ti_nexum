from typing import List, Optional
from pydantic import BaseModel
from app.config.database import get_connection
from datetime import datetime

class DetalleModel(BaseModel):
    CuentaDeposito: Optional[str]
    FechaTransaccion: Optional[str]
    FechaHoraAplicacion: Optional[str]
    Descripcion: Optional[str]
    Referencia: Optional[str]
    Debito: Optional[str]
    Credito: Optional[str]
    Tipo: Optional[str]

def insertar_detalle_Coltefinanciera(detalle: DetalleModel):

    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            EXEC SP_CRUD_ColtefinancieraDatos
                @Accion=1,
                @CuentaDeposito = ?,
                @FechaTransaccion = ?,
                @FechaHoraAplicacion = ?,
                @Descripcion = ? ,
                @Referencia = ?,
                @Debito = ?,
                @Credito = ?,
                @Tipo = ?                       
        """, (
            detalle.CuentaDeposito,
            detalle.FechaTransaccion,
            detalle.FechaHoraAplicacion,
            detalle.Descripcion,
            detalle.Referencia,
            detalle.Debito,
            detalle.Credito,
            detalle.Tipo
        ))

        conn.commit()
        return True, None 
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, str(e)
    finally:
        cursor.close()
        conn.close()
