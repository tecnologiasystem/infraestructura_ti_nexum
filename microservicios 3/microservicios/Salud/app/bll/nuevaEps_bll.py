"""
Este módulo contiene la lógica de negocio para la automatización "Nueva EPS".
Incluye modelos Pydantic para validar datos, funciones para listar automatizaciones,
obtener detalles específicos, procesar archivos Excel, manejar resultados, y enviar
correos electrónicos notificando finalización.
"""
import time
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.dal.nuevaEps_dal import (
    insertar_encabezado,
    insertar_detalle,
    EncabezadoModel,
    insertar_detalle_resultadoNuevaEps,
    obtener_correo_usuarioNuevaEps,
    obtener_automatizacion_por_idNuevaEps,
    obtener_automatizacionesNuevaEps,
    obtener_CC_aConsultarNuevaEps, correo_ya_enviado,
    obtener_idUsuario_por_encabezado, marcar_correo_enviado,
    marcar_pausa_encabezado, pausar_detalle_encabezado,
    quitar_pausa_encabezado, reanudar_detalle_encabezado, contar_total_por_encabezadoNuevaEps,
    contar_procesados_por_encabezadoNuevaEps, obtener_detalles_paginados_por_encabezadoNuevaEps,
    obtener_encabezados_paginadoNuevaEps, contar_encabezadosNuevaEps
)
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.email_config import REMITENTE, PASSWORD, SERVER, PORT


class ResultadoNuevaEpsModel(BaseModel):
    """
    Modelo que representa los datos del resultado de la automatización de Nueva EPS.
    Todos los campos son opcionales excepto la cédula, que es requerida.
    """
    cedula: str
    nombre: Optional[str]
    fechaNacimiento: Optional[str]
    edad: Optional[str]
    sexo: Optional[str]
    antiguedad: Optional[str]
    fechaAfiliacion: Optional[str]
    epsAnterior: Optional[str]
    direccion: Optional[str]
    telefono: Optional[str]
    celular: Optional[str]
    email: Optional[str]
    municipio: Optional[str]
    departamento: Optional[str]
    observacion: Optional[str]


def listar_automatizaciones_estadoNuevaEps():
    """
    Obtiene el listado de automatizaciones con su estado de avance.

    Para cada automatización calcula:
    - porcentaje de detalles ingresados
    - estado ("No iniciada", "Finalizada" o "En progreso (XX%)")
    Retorna una lista con esta información para mostrar en la UI.
    """
    rows, error = obtener_automatizacionesNuevaEps()
    
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


def obtener_automatizacionNuevaEps(id_encabezado: int):
    """
    Obtiene la información completa de una automatización específica por su ID.

    Retorna un diccionario con encabezado y lista de detalles relacionados.
    """
    rows = obtener_automatizacion_por_idNuevaEps(id_encabezado)
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
                "cedula": row.cedula,
                "nombre": row.nombre,
                "fechaNacimiento": row.fechaNacimiento,
                "edad": row.edad,
                "sexo": row.sexo,
                "antiguedad": row.antiguedad,
                "fechaAfiliacion": row.fechaAfiliacion,
                "epsAnterior": row.epsAnterior,
                "direccion": row.direccion,
                "telefono": row.telefono,
                "celular": row.celular,
                "email": row.email,
                "municipio": row.municipio,
                "departamento": row.departamento,
                "observacion": row.observacion,
            })

    return encabezado


def obtener_automatizacionCCNuevaEps():

    filas, error = obtener_CC_aConsultarNuevaEps()
    if error:
        raise Exception(f"Error al consultar próxima cédula: {error}")
    if not filas:
        return None
    return filas[0]


def procesar_archivo_excel(encabezado: EncabezadoModel, chunk_size: int = 500):
    """
    Procesa el archivo Excel en segundo plano, en bloques para evitar saturar el servidor.
    """
    print("🚀 Iniciando procesamiento en segundo plano...")

    detalles_validos = [d for d in encabezado.detalles if d.cedula and str(d.cedula).strip()]
    encabezado.totalRegistros = len(detalles_validos)

    idEncabezado = insertar_encabezado(encabezado)
    if not idEncabezado or idEncabezado == -1:
        print("❌ Error al insertar encabezado. Abortando.")
        return

    for i in range(0, len(detalles_validos), chunk_size):
        bloque = detalles_validos[i:i + chunk_size]
        print(f"🧩 Insertando bloque {i} a {i + len(bloque) - 1}...")
        for detalle in bloque:
            insertar_detalle(idEncabezado, detalle)
        time.sleep(0.1)  # espera opcional para liberar CPU

    print(f"✅ Finalizado: {len(detalles_validos)} detalles insertados para encabezado {idEncabezado}")



def procesar_resultado_automatizacionNuevaEps(resultado: ResultadoNuevaEpsModel) -> bool:
    """
    Inserta o actualiza el resultado de la automatización para una cédula en particular.
    Retorna True si se actualizó correctamente, False si no se encontró registro.
    """
    return insertar_detalle_resultadoNuevaEps(resultado)


def enviar_correo_finalizacionNuevaEps(id_usuario: int):
    """
    Envía correo notificando la finalización del proceso FamiSanar para el usuario dado.

    - Obtiene el correo del usuario.
    - Arma un email simple con asunto y cuerpo.
    - Se conecta al servidor SMTP y envía el mensaje.
    - Retorna True si el correo se envió exitosamente, False si hubo error.
    """
    correo_destino = obtener_correo_usuarioNuevaEps(id_usuario)
    if not correo_destino:
        print(f"❌ No se encontró correo para usuario {id_usuario}")
        return False

    asunto = "Automatización completada"
    cuerpo = f"""
    Hola,

    La automatización NUEVA EPS ha finalizado exitosamente.

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

    enviado = enviar_correo_finalizacionNuevaEps(id_usuario)
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


def resumen_encabezadoNuevaEpsBLL(id_encabezado: int):
    total = contar_total_por_encabezadoNuevaEps(id_encabezado)
    procesados = contar_procesados_por_encabezadoNuevaEps(id_encabezado)
    return {"idEncabezado": id_encabezado, "totalRegistros": total, "procesados": procesados}

def listar_detalles_paginadosNuevaEpsBLL(
    id_encabezado: int, offset: int, limit: int, cc: Optional[str]
):
    rows, total = obtener_detalles_paginados_por_encabezadoNuevaEps(id_encabezado, offset, limit, cc)
    return {"rows": rows, "total": total}

def listar_encabezados_paginadoNuevaEpsBLL(offset: int, limit: int):
    rows = obtener_encabezados_paginadoNuevaEps(offset, limit)
    if rows is None:
        raise Exception("Error al obtener encabezados paginados")

    resultados = []
    for row in rows:
        total = getattr(row, "totalRegistros", 0) or 0
        ingresados = getattr(row, "detallesIngresados", 0) or 0
        if getattr(row, "estado", None) == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (ingresados / total * 100) if total else 0
            estado = ("No iniciada" if ingresados == 0 else
                      "Finalizada" if ingresados >= total else
                      f"En progreso ({int(porcentaje)}%)")

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": total,
            "detallesIngresados": ingresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    total_enc = contar_encabezadosNuevaEps()
    return {"rows": resultados, "total": total_enc}