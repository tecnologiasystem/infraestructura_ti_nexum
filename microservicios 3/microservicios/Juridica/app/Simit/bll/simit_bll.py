from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.Simit.dal.simit_dal import insertar_encabezado, insertar_detalle, EncabezadoModel, insertar_detalle_resultadoSimit, obtener_correo_usuarioSimit, marcar_correo_enviado, correo_ya_enviado, obtener_idUsuario_por_encabezado, marcar_pausa_encabezado, pausar_detalle_encabezado, quitar_pausa_encabezado, reanudar_detalle_encabezado
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.email_config import REMITENTE, PASSWORD, SERVER, PORT

def procesar_archivo_excel(encabezado: EncabezadoModel) -> int:
    """
    Esta función procesa un encabezado que contiene detalles extraídos de un archivo Excel para la automatización Simit.
    - Filtra únicamente los detalles que tienen una cédula válida, ignorando los vacíos o nulos.
    - Actualiza el campo totalRegistros con la cantidad real de detalles válidos.
    - Inserta el encabezado en la base de datos y obtiene su ID generado.
    - Si la inserción del encabezado falla (retorna -1 o None), lanza una excepción para detener el proceso.
    - Luego, para cada detalle válido, inserta el detalle asociado al encabezado en la base de datos.
    - Finalmente, retorna el ID del encabezado insertado, que puede usarse para futuras referencias o seguimiento.
    """
    detalles_validos = [d for d in encabezado.detalles if d.cedula and d.cedula.strip()]
    encabezado.totalRegistros = len(detalles_validos)
    idEncabezado = insertar_encabezado(encabezado)
    if not idEncabezado or idEncabezado == -1:
        raise Exception("❌ Error al insertar encabezado. No se puede continuar con los detalles.")
    for detalle in detalles_validos:
        insertar_detalle(idEncabezado, detalle)
    return idEncabezado


class ResultadoSimitModel(BaseModel):
    """
    Define la estructura esperada para los resultados que devuelve la automatización Simit.
    Contiene:
    - cedula: Obligatorio, representa la cédula del registro.
    - tipo: Opcional, tipo asociado al registro.
    - placa: Opcional, placa del vehículo o registro.
    - secretaria: Opcional, entidad responsable o relacionada.
    """
    cedula: str
    tipo: Optional[str] = None
    placa: Optional[str] = None
    secretaria: Optional[str] = None


def procesar_resultado_automatizacionSimit(resultado: ResultadoSimitModel) -> bool:
    """
    Recibe un objeto resultado con la información de la automatización.
    Su función es insertar o actualizar los detalles de ese resultado en la base de datos.
    Retorna:
    - True si la operación fue exitosa.
    - False en caso de error o si no se pudo insertar/actualizar.
    """
    return insertar_detalle_resultadoSimit(resultado)


def enviar_correo_finalizacionSimit(id_usuario: int):
    """
    Envía correo notificando la finalización del proceso Simit para el usuario dado.

    - Obtiene el correo del usuario.
    - Arma un email simple con asunto y cuerpo.
    - Se conecta al servidor SMTP y envía el mensaje.
    - Retorna True si el correo se envió exitosamente, False si hubo error.
    """
    correo_destino = obtener_correo_usuarioSimit(id_usuario)
    if not correo_destino:
        print(f"❌ No se encontró correo para usuario {id_usuario}")
        return False

    asunto = "Automatización completada"
    cuerpo = f"""
    Hola,

    La automatización SIMIT ha finalizado exitosamente.

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

    enviado = enviar_correo_finalizacionSimit(id_usuario)
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