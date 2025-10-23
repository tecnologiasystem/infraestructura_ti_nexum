from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.dal.numero_dal import (
    insertar_encabezado,
    insertar_detalle,
    EncabezadoModel,
    insertar_detalle_resultadoWhatsApp,
    obtener_correo_usuarioWhatsApp,
    obtener_automatizacion_por_idWhatsApp,
    obtener_automatizacionesWhatsApp,
    obtener_numero_aConsultarWhatsApp, obtener_idUsuario_por_encabezado,
    correo_ya_enviado, marcar_correo_enviado, marcar_pausa_encabezado, pausar_detalle_encabezado,
    quitar_pausa_encabezado, reanudar_detalle_encabezado
)
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.email_config import REMITENTE, PASSWORD, SERVER, PORT


class ResultadoWhatsAppModel(BaseModel):
    indicativo: str
    numero: str
    tiene_whatsApp: Optional[str]

def listar_automatizaciones_estadoWhatsApp():
    """
    Consulta la lista de automatizaciones disponibles con su estado.

    Retorna una lista con cada automatización incluyendo:
    - idEncabezado
    - automatizacion
    - fechaCargue
    - totalRegistros
    - detallesIngresados
    - estado calculado según porcentaje completado
    """
    rows, error = obtener_automatizacionesWhatsApp()
    
    if rows is None:
        raise Exception(f"Error al obtener automatizaciones: {error}")

    resultados = []
    for row in rows:
        if not row or row.totalRegistros is None or row.detallesIngresados is None:
            continue

        if row.estado and row.estado == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (row.detallesIngresados / row.totalRegistros) * 100 if row.totalRegistros else 0
            estado = (
                "No iniciada" if row.detallesIngresados == 0 else
                "Finalizada" if row.detallesIngresados >= row.totalRegistros else
                f"En progreso ({int(porcentaje)}%)"
        )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": row.totalRegistros,
            "detallesIngresados": row.detallesIngresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    return resultados


def obtener_automatizacionWhatsApp(id_encabezado: int):
    """
    Obtiene los detalles completos de una automatización según su id_encabezado.
    Retorna None si no existen resultados.
    """
    rows = obtener_automatizacion_por_idWhatsApp(id_encabezado)
    if not rows:
        return None

    encabezado = {
        "idEncabezado": rows[0].idEncabezado,
        "automatizacion": rows[0].automatizacion,
        "fechaCargue": str(rows[0].fechaCargue),
        "totalRegistros": rows[0].totalRegistros,
        "detalles": []
    }

    for row in rows:
        if row.idDetalle is not None:
            encabezado["detalles"].append({
                "idDetalle": row.idDetalle,
                "indicativo": row.indicativo,
                "numero": row.numero,
                "tiene_whatsApp": row.tiene_whatsApp,
            })

    return encabezado


def obtener_automatizacionNumeroWhatsApp():
    filas, error = obtener_numero_aConsultarWhatsApp()
    if error:
        raise Exception(f"Error al consultar próxima cédula: {error}")
    if not filas:
        return None
    return filas[0]


def procesar_archivo_excel(encabezado: EncabezadoModel) -> int:
    print("🧪 NUMEROS DETECTADOS:")
    for d in encabezado.detalles:
        print(f" - {d.numero!r}")

    detalles_validos = [d for d in encabezado.detalles if d.numero and str(d.numero).strip()]
    print(f"🔎 Detalles válidos encontrados: {len(detalles_validos)}")
    encabezado.totalRegistros = len(detalles_validos)

    idEncabezado = insertar_encabezado(encabezado)
    if not idEncabezado or idEncabezado == -1:
        raise Exception("❌ Error al insertar encabezado. No se puede continuar con los detalles.")
    
    for detalle in detalles_validos:
        insertar_detalle(idEncabezado, detalle)

    return idEncabezado


def procesar_resultado_automatizacionWhatsApp(resultado: ResultadoWhatsAppModel) -> bool:
    """
    Inserta o actualiza el resultado de la automatización para una cédula específica.
    Retorna True si se actualizó correctamente, False si no se encontró el registro.
    """
    return insertar_detalle_resultadoWhatsApp(resultado)


def enviar_correo_finalizacionWhatsApp(id_usuario: int):
    """
    Envía correo notificando la finalización del proceso FamiSanar para el usuario dado.

    - Obtiene el correo del usuario.
    - Arma un email simple con asunto y cuerpo.
    - Se conecta al servidor SMTP y envía el mensaje.
    - Retorna True si el correo se envió exitosamente, False si hubo error.
    """
    correo_destino = obtener_correo_usuarioWhatsApp(id_usuario)
    if not correo_destino:
        print(f"❌ No se encontró correo para usuario {id_usuario}")
        return False

    asunto = "Automatización completada"
    cuerpo = f"""
    Hola,

    La automatización WHATSAPP ha finalizado exitosamente.

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

    enviado = enviar_correo_finalizacionWhatsApp(id_usuario)
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
