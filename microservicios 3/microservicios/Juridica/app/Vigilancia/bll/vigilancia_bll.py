from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.Vigilancia.dal.vigilancia_dal import insertar_encabezado, insertar_detalle, EncabezadoModel, insertar_detalle_resultadoVigilancia, obtener_correo_usuarioVigilancia, correo_ya_enviado, obtener_idUsuario_por_encabezado, marcar_correo_enviado, pausar_detalle_encabezado, reanudar_detalle_encabezado, quitar_pausa_encabezado, marcar_pausa_encabezado
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.email_config import REMITENTE, PASSWORD, SERVER, PORT

def procesar_archivo_excel(encabezado: EncabezadoModel) -> int:
    detalles_validos = [d for d in encabezado.detalles if d.radicado and d.radicado.strip()]
    
    encabezado.totalRegistros = len(detalles_validos)

    idEncabezado = insertar_encabezado(encabezado)
    if not idEncabezado or idEncabezado == -1:
        raise Exception("❌ Error al insertar encabezado. No se puede continuar con los detalles.")
    
    for detalle in detalles_validos:
        insertar_detalle(idEncabezado, detalle)

    return idEncabezado

class ResultadoVigilanciaModel(BaseModel):
    radicado: str
    fechaInicial: Optional[str]
    fechaFinal: Optional[str]
    fechaActuacion: Optional[str] = None
    actuacion: Optional[str] = None
    anotacion: Optional[str] = None
    fechaIniciaTermino: Optional[str] = None
    fechaFinalizaTermino: Optional[str] = None
    fechaRegistro: Optional[str] = None
    radicadoNuevo: Optional[str] = None

def procesar_resultado_automatizacionVigilancia(resultado: ResultadoVigilanciaModel) -> bool:
    return insertar_detalle_resultadoVigilancia(resultado)

def enviar_correo_finalizacionVigilancia(id_usuario: int):
    correo_destino = obtener_correo_usuarioVigilancia(id_usuario)
    if not correo_destino:
        print(f"❌ No se encontró correo para usuario {id_usuario}")
        return False

    asunto = "Automatización completada"
    cuerpo = f"""
    Hola,

    La automatización VIGILANCIA ha finalizado exitosamente.

    Puedes revisar los resultados en el sistema.

    Saludos,
    Sistema de Automatización.
    """

    mensaje = MIMEMultipart()
    mensaje["From"] = REMITENTE
    mensaje["To"] = correo_destino
    mensaje["Subject"] = asunto
    mensaje.attach(MIMEText(cuerpo, "plain"))

    try:
        with smtplib.SMTP(SERVER, PORT) as servidor:
            servidor.starttls()
            servidor.login(REMITENTE, PASSWORD)
            servidor.send_message(mensaje)
            print(f"📨 Correo enviado a {correo_destino}")
            return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False


def enviar_correo_finalizacion_por_encabezado(idEncabezado: int) -> bool:
    """
    Envía el correo de finalización solo si no se ha enviado previamente.
    """
    if correo_ya_enviado(idEncabezado):
        print(f"⚠️ Correo ya enviado previamente para encabezado {idEncabezado}")
        return True  

    id_usuario = obtener_idUsuario_por_encabezado(idEncabezado)
    if id_usuario is None:
        print(f"No se encontró idUsuario para encabezado {idEncabezado}")
        return False

    enviado = enviar_correo_finalizacionVigilancia(id_usuario)
    if enviado:
        marcar_correo_enviado(idEncabezado)
    return enviado

#---------- PAUSAR-------------------------------
def pausar_encabezado(id_encabezado: int) -> bool:
    ok1 = marcar_pausa_encabezado(id_encabezado, datetime.now())
    ok2 = pausar_detalle_encabezado(id_encabezado)
    return ok1 and ok2

def reanudar_encabezado(id_encabezado: int) -> bool:
    ok1 = quitar_pausa_encabezado(id_encabezado)
    ok2 = reanudar_detalle_encabezado(id_encabezado)
    return ok1 and ok2
