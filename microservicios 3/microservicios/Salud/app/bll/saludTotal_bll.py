from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.dal.saludTotal_dal import (
    insertar_encabezado,
    insertar_detalle,
    EncabezadoModel,
    insertar_detalle_resultadoSaludTotal,
    obtener_correo_usuarioSaludTotal,
    obtener_automatizacion_por_idSaludTotal,
    obtener_automatizacionesSaludTotal,
    obtener_CC_aConsultarSaludTotal, obtener_idUsuario_por_encabezado,
    correo_ya_enviado, marcar_correo_enviado
)
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.email_config import REMITENTE, PASSWORD, SERVER, PORT


class ResultadoSaludTotalModel(BaseModel):
    """
    Modelo Pydantic para validar la estructura del resultado recibido de la automatización Salud Total.
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


def listar_automatizaciones_estadoSaludTotal():
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
    rows, error = obtener_automatizacionesSaludTotal()
    
    if rows is None:
        raise Exception(f"Error al obtener automatizaciones: {error}")

    resultados = []
    for row in rows:
        # Evitar filas nulas o con datos incompletos
        if not row or row.totalRegistros is None or row.detallesIngresados is None:
            continue

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
            "estado": estado
        })

    return resultados


def obtener_automatizacionSaludTotal(id_encabezado: int):
    """
    Obtiene los detalles completos de una automatización según su id_encabezado.
    Retorna None si no existen resultados.
    """
    rows = obtener_automatizacion_por_idSaludTotal(id_encabezado)
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


def obtener_automatizacionCCSaludTotal():
    """
    Obtiene la próxima cédula disponible para procesar en la automatización.
    """
    return obtener_CC_aConsultarSaludTotal()


def procesar_archivo_excel(encabezado: EncabezadoModel) -> int:
    """
    Procesa el archivo Excel recibido: inserta encabezado y detalles en base de datos.

    - Imprime las cédulas detectadas en consola para debug.
    - Filtra detalles con cédula válida (no vacía).
    - Inserta encabezado en BD y devuelve su ID.
    - Inserta cada detalle asociado a dicho encabezado.
    """
    print("🧪 CÉDULAS DETECTADAS:")
    for d in encabezado.detalles:
        print(f" - {d.cedula!r}")

    detalles_validos = [d for d in encabezado.detalles if d.cedula and str(d.cedula).strip()]
    print(f"🔎 Detalles válidos encontrados: {len(detalles_validos)}")
    encabezado.totalRegistros = len(detalles_validos)

    idEncabezado = insertar_encabezado(encabezado)
    if not idEncabezado or idEncabezado == -1:
        raise Exception("❌ Error al insertar encabezado. No se puede continuar con los detalles.")
    
    for detalle in detalles_validos:
        insertar_detalle(idEncabezado, detalle)

    return idEncabezado


def procesar_resultado_automatizacionSaludTotal(resultado: ResultadoSaludTotalModel) -> bool:
    """
    Inserta o actualiza el resultado de la automatización para una cédula específica.
    Retorna True si se actualizó correctamente, False si no se encontró el registro.
    """
    return insertar_detalle_resultadoSaludTotal(resultado)


def enviar_correo_finalizacionSaludTotal(id_usuario: int):
    """
    Envía correo notificando la finalización del proceso Salud total para el usuario dado.

    - Obtiene el correo del usuario.
    - Arma un email simple con asunto y cuerpo.
    - Se conecta al servidor SMTP y envía el mensaje.
    - Retorna True si el correo se envió exitosamente, False si hubo error.
    """
    correo_destino = obtener_correo_usuarioSaludTotal(id_usuario)
    if not correo_destino:
        print(f"❌ No se encontró correo para usuario {id_usuario}")
        return False

    asunto = "Automatización completada"
    cuerpo = f"""
    Hola,

    La automatización SALUD TOTAL ha finalizado exitosamente.

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

    enviado = enviar_correo_finalizacionSaludTotal(id_usuario)
    if enviado:
        marcar_correo_enviado(idEncabezado)
    return enviado
