from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.Rues.dal.rues_dal import (
    insertar_encabezado,        # Función para insertar un encabezado en BD
    insertar_detalle,           # Función para insertar un detalle asociado al encabezado
    EncabezadoModel,            # Modelo que representa el encabezado con detalles
    insertar_detalle_resultadoRues,  # Inserta resultado de automatización para un detalle
    obtener_correo_usuarioRues,  # Obtiene el correo electrónico de un usuario por su ID
    correo_ya_enviado,
    obtener_idUsuario_por_encabezado,
    marcar_correo_enviado,
    marcar_pausa_encabezado,
    pausar_detalle_encabezado,
    quitar_pausa_encabezado,
    reanudar_detalle_encabezado
)
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.email_config import REMITENTE, PASSWORD, SERVER, PORT


def procesar_archivo_excel(encabezado: EncabezadoModel) -> int:
    """
    Procesa un encabezado con sus detalles extraídos de un Excel para almacenarlos en la BD.

    Pasos:
    - Filtra solo detalles que tienen cédula no vacía (validación básica).
    - Actualiza el total de registros del encabezado con la cantidad válida.
    - Inserta el encabezado en la base y obtiene el ID generado.
    - Si no se puede insertar el encabezado, lanza excepción para evitar inconsistencias.
    - Inserta cada detalle válido en la base con el ID de encabezado.
    - Retorna el ID del encabezado insertado para seguimiento.
    """
    detalles_validos = [d for d in encabezado.detalles if d.cedula and d.cedula.strip()]
    
    encabezado.totalRegistros = len(detalles_validos)

    idEncabezado = insertar_encabezado(encabezado)
    if not idEncabezado or idEncabezado == -1:
        raise Exception("❌ Error al insertar encabezado. No se puede continuar con los detalles.")
    
    for detalle in detalles_validos:
        insertar_detalle(idEncabezado, detalle)

    return idEncabezado


class ResultadoRuesModel(BaseModel):
    """
    Modelo Pydantic que representa el resultado que llega de la automatización para actualizar detalles.

    Campos:
    - cedula (str): Identificador obligatorio para el detalle.
    - nombre, identificacion, categoria, camaraComercio, numeroMatricula, actividadEconomica (opcionales).
    """
    cedula: str
    nombre: Optional[str] = None
    identificacion: Optional[str] = None
    categoria: Optional[str] = None
    camaraComercio: Optional[str] = None
    numeroMatricula: Optional[str] = None
    actividadEconomica: Optional[str] = None


def procesar_resultado_automatizacionRues(resultado: ResultadoRuesModel) -> bool:
    """
    Llama al DAL para insertar o actualizar el detalle con la información procesada
    tras la automatización.

    Retorna True si la operación fue exitosa.
    """
    return insertar_detalle_resultadoRues(resultado)


def enviar_correo_finalizacionRues(id_usuario: int):
    """
    Envía correo notificando la finalización del proceso Rues para el usuario dado.

    - Obtiene el correo del usuario.
    - Arma un email simple con asunto y cuerpo.
    - Se conecta al servidor SMTP y envía el mensaje.
    - Retorna True si el correo se envió exitosamente, False si hubo error.
    """
    correo_destino = obtener_correo_usuarioRues(id_usuario)
    if not correo_destino:
        print(f"❌ No se encontró correo para usuario {id_usuario}")
        return False

    asunto = "Automatización completada"
    cuerpo = f"""
    Hola,

    La automatización RUES ha finalizado exitosamente.

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

    enviado = enviar_correo_finalizacionRues(id_usuario)
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
