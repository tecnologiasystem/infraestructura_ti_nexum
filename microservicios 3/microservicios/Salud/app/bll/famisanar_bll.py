"""
Este archivo contiene la lógica de negocio para el módulo FamiSanar.
Define modelos Pydantic para validación, funciones para consultar automatizaciones,
procesar datos, insertar resultados y enviar correos de notificación.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.dal.famisanar_dal import (
    insertar_encabezado,
    insertar_detalle,
    EncabezadoModel,
    insertar_detalle_resultadoFamiSanar,
    obtener_correo_usuarioFamiSanar,
    obtener_automatizacion_por_idFamiSanar,
    obtener_automatizacionesFamiSanar,
    obtener_CC_aConsultarFamiSanar, obtener_idUsuario_por_encabezado,
    correo_ya_enviado, marcar_correo_enviado, marcar_pausa_encabezado, pausar_detalle_encabezado,
    quitar_pausa_encabezado, reanudar_detalle_encabezado, contar_detalles_por_encabezado, obtener_detalles_por_encabezado_paginado,
    contar_total_por_encabezado, contar_procesados_por_encabezado, obtener_encabezados_paginado_famisanar,
    contar_encabezados_famisanar
)
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.email_config import REMITENTE, PASSWORD, SERVER, PORT


class ResultadoFamiSanarModel(BaseModel):
    """
    Modelo Pydantic para validar la estructura del resultado recibido de la automatización FamiSanar.
    """
    cedula: str
    nombres: Optional[str]
    apellidos: Optional[str]
    estado: Optional[str]
    IPS: Optional[str]
    convenio: Optional[str]
    tipo: Optional[str]
    categoria: Optional[str]
    semanas: Optional[str]
    fechaNacimiento: Optional[str]
    edad: Optional[str]
    sexo: Optional[str]
    direccion: Optional[str]
    telefono: Optional[str]
    departamento: Optional[str]
    municipio: Optional[str]
    causal: Optional[str]


def listar_automatizaciones_estadoFamiSanar():
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
    rows, error = obtener_automatizacionesFamiSanar()
    
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


def obtener_automatizacionFamiSanar(id_encabezado: int):
    """
    Obtiene los detalles completos de una automatización según su id_encabezado.
    Retorna None si no existen resultados.
    """
    rows = obtener_automatizacion_por_idFamiSanar(id_encabezado)
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
                "nombres": row.nombres,
                "apellidos": row.apellidos,
                "estado": row.estado,
                "IPS": row.IPS,
                "convenio": row.convenio,
                "tipo": row.tipo,
                "categoria": row.categoria,
                "semanas": row.semanas,
                "fechaNacimiento": row.fechaNacimiento,
                "edad": row.edad,
                "sexo": row.sexo,
                "direccion": row.direccion,
                "telefono": row.telefono,
                "departamento": row.departamento,
                "municipio": row.municipio,
                "causal": row.causal,
            })

    return encabezado


def obtener_automatizacionCCFamiSanar():
    """
    Retorna la siguiente tupla (idEncabezado, cedula) pendiente.
    Lanza excepción si hay un error, o devuelve None si no hay más cédulas.
    """
    filas, error = obtener_CC_aConsultarFamiSanar()
    if error:
        raise Exception(f"Error al consultar próxima cédula: {error}")
    if not filas:
        return None
    return filas[0]

import time

def procesar_archivo_excel_background(encabezado: EncabezadoModel, chunk_size: int = 500):
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


def procesar_archivo_excel(encabezado: EncabezadoModel) -> int:
    """
    Procesa el archivo Excel recibido: inserta encabezado y detalles en base de datos.

    - Imprime las cédulas detectadas en consola para debug.
    - Filtra detalles con cédula válida (no vacía).
    - Inserta encabezado en BD y devuelve su ID.
    - Inserta cada detalle asociado a dicho encabezado.
    """
    for d in encabezado.detalles:

        detalles_validos = [d for d in encabezado.detalles if d.cedula and str(d.cedula).strip()]
        encabezado.totalRegistros = len(detalles_validos)

    idEncabezado = insertar_encabezado(encabezado)
    if not idEncabezado or idEncabezado == -1:
        raise Exception("❌ Error al insertar encabezado. No se puede continuar con los detalles.")
    
    for detalle in detalles_validos:
        insertar_detalle(idEncabezado, detalle)

    return idEncabezado


def procesar_resultado_automatizacionFamiSanar(resultado: ResultadoFamiSanarModel) -> bool:
    """
    Inserta o actualiza el resultado de la automatización para una cédula específica.
    Retorna True si se actualizó correctamente, False si no se encontró el registro.
    """
    return insertar_detalle_resultadoFamiSanar(resultado)


def enviar_correo_finalizacionFamiSanar(id_usuario: int):
    """
    Envía correo notificando la finalización del proceso FamiSanar para el usuario dado.

    - Obtiene el correo del usuario.
    - Arma un email simple con asunto y cuerpo.
    - Se conecta al servidor SMTP y envía el mensaje.
    - Retorna True si el correo se envió exitosamente, False si hubo error.
    """
    correo_destino = obtener_correo_usuarioFamiSanar(id_usuario)
    if not correo_destino:
        print(f"❌ No se encontró correo para usuario {id_usuario}")
        return False

    asunto = "Automatización completada"
    cuerpo = f"""
    Hola,

    La automatización FAMISANAR ha finalizado exitosamente.

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

    enviado = enviar_correo_finalizacionFamiSanar(id_usuario)
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

def listar_detalles_por_encabezado_paginadoBLL(id_encabezado: int, offset: int = 0, limit: int = 50, cc: str | None = None):
    total = contar_detalles_por_encabezado(id_encabezado, cc)
    rows = obtener_detalles_por_encabezado_paginado(id_encabezado, offset, limit, cc)
    return {"rows": rows, "total": total}

def resumen_encabezadoBLL(id_encabezado: int):
    total = contar_total_por_encabezado(id_encabezado)
    procesados = contar_procesados_por_encabezado(id_encabezado)
    return {"idEncabezado": id_encabezado, "totalRegistros": total, "procesados": procesados}

def listar_encabezados_paginado_famisanar_bll(offset: int, limit: int):
    rows = obtener_encabezados_paginado_famisanar(offset, limit)
    if rows is None:
        raise Exception("Error al obtener encabezados paginados")

    resultados = []
    for row in rows:
        if not row:
            continue
        total = getattr(row, "totalRegistros", 0) or 0
        ingresados = getattr(row, "detallesIngresados", 0) or 0
        if getattr(row, "estado", None) == "Pausado":
            estado = "Pausado"
        else:
            porcentaje = (ingresados / total * 100) if total else 0
            estado = (
                "No iniciada" if ingresados == 0 else
                "Finalizada" if ingresados >= total else
                f"En progreso ({int(porcentaje)}%)"
            )

        resultados.append({
            "idEncabezado": row.idEncabezado,
            "automatizacion": row.automatizacion,
            "fechaCargue": str(row.fechaCargue),
            "totalRegistros": total,
            "detallesIngresados": ingresados,
            "estado": estado,
            "nombreUsuario": getattr(row, "nombreUsuario", "Desconocido")
        })

    total_enc = contar_encabezados_famisanar()
    return {"rows": resultados, "total": total_enc}