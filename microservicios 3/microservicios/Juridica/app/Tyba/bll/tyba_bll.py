from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.Tyba.dal.tyba_dal import insertar_encabezado, insertar_detalle, EncabezadoModel, insertar_detalle_resultadoTyba, obtener_correo_usuarioTyba, correo_ya_enviado, obtener_idUsuario_por_encabezado, marcar_correo_enviado, marcar_pausa_encabezado, pausar_detalle_encabezado, quitar_pausa_encabezado,reanudar_detalle_encabezado
import pandas as pd
import re
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.email_config import REMITENTE, PASSWORD, SERVER, PORT

def procesar_archivo_excel(encabezado: EncabezadoModel) -> int:
    detalles_validos = [d for d in encabezado.detalles if d.cedula and d.cedula.strip()]
    
    encabezado.totalRegistros = len(detalles_validos)

    idEncabezado = insertar_encabezado(encabezado)
    if not idEncabezado or idEncabezado == -1:
        raise Exception("❌ Error al insertar encabezado. No se puede continuar con los detalles.")
    
    for detalle in detalles_validos:
        insertar_detalle(idEncabezado, detalle)

    return idEncabezado


class ResultadoTybaModel(BaseModel):
    cedula: str
    radicado: Optional[str]
    proceso: Optional[str]
    departamento: Optional[str]
    coorporacion: Optional[str]
    distrito: Optional[str]
    despacho: Optional[str]
    telefono: Optional[str]
    correo: Optional[str]
    fechaProvidencia: Optional[str]
    tipoProceso: Optional[str]
    subclaseProceso: Optional[str]
    ciudad: Optional[str]
    especialidad: Optional[str]
    numeroDespacho: Optional[str]
    direccion: Optional[str]
    celular: Optional[str]
    fechaPublicacion: Optional[str]
    sujetos: Optional[str]
    actuaciones: Optional[str]

def parsear_sujetos(sujetos_raw: str) -> str:
    sujetos = []

    if not sujetos_raw or len(sujetos_raw.strip()) < 20:
        return "[]"

    try:
        texto = sujetos_raw.strip()

        # ✅ 1. Agregar espacios después de los roles conocidos si están pegados
        texto = re.sub(r'(Demandado/indiciado/causante)', r'\1 ', texto)
        texto = re.sub(r'(Demandante/accionante)', r'\1 ', texto)
        texto = re.sub(r'(Defensor Privado)', r'\1 ', texto)

        # ✅ 2. Agregar espacios antes de fechas que están pegadas
        texto = re.sub(r'(\d{2}-\d{2}-\d{4})', r' \1 ', texto)

        # ✅ 3. Separar en bloques por cada rol
        bloques = re.findall(r'(Demandado/indiciado/causante.*?\d{2}-\d{2}-\d{4}|Demandante/accionante.*?\d{2}-\d{2}-\d{4}|Defensor Privado.*?\d{2}-\d{2}-\d{4})', texto)

        for bloque in bloques:
            partes = bloque.strip().split()
            rol = partes[0]
            tipo_doc = " ".join(partes[1:4])
            cedula = partes[4].replace(".", "")
            nombre = " ".join(partes[5:-1])
            fecha = partes[-1]

            sujetos.append({
                "rol": rol.strip(),
                "tipo_documento": tipo_doc.strip(),
                "cedula": cedula.strip(),
                "nombre": nombre.strip(),
                "fecha_registro": fecha.strip()
            })

    except Exception as e:
        print("❌ Error parseando sujetos:", e)
        return "[]"

    return json.dumps(sujetos, ensure_ascii=False)


def parsear_actuaciones(actuaciones_raw: str) -> str:

    actuaciones = []

    if not actuaciones_raw or len(actuaciones_raw.strip()) < 15:
        return "[]"

    try:
        texto = actuaciones_raw.strip()

        # ✅ 1. Eliminar encabezados basura si están presentes
        texto = re.sub(r'CicloTipo\s+ActuaciónFecha\s+ActuaciónFecha de Registro', '', texto, flags=re.IGNORECASE)

        # ✅ 2. Insertar espacios antes de fechas
        texto = re.sub(r'(\d{2}/\d{2}/\d{4})', r' \1 ', texto)
        texto = re.sub(r'(\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} [ap]\. ?m\.)', r' \1 ', texto)

        # ✅ 3. Regex final para extraer actuaciones
        patron = re.compile(
            r'(?P<ciclo>[A-ZÁÉÍÓÚÑ]{3,})\s+'
            r'(?P<tipo_actuacion>.*?)\s+'
            r'(?P<fecha_actuacion>\d{2}/\d{2}/\d{4})\s+'
            r'(?P<fecha_registro>\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{2}:\d{2} [ap]\. ?m\.)',
            re.IGNORECASE
        )

        for match in patron.finditer(texto):
            actuaciones.append({
                "ciclo": match.group("ciclo").strip(),
                "tipo_actuacion": match.group("tipo_actuacion").strip(),
                "fecha_actuacion": match.group("fecha_actuacion").strip(),
                "fecha_registro": match.group("fecha_registro").strip()
            })

    except Exception as e:
        print("❌ Error parseando actuaciones:", e)
        return "[]"

    return json.dumps(actuaciones, ensure_ascii=False)



def procesar_resultado_automatizacionTyba(resultado: ResultadoTybaModel) -> bool:
    resultado.sujetos = parsear_sujetos(resultado.sujetos)
    resultado.actuaciones = parsear_actuaciones(resultado.actuaciones)
    return insertar_detalle_resultadoTyba(resultado)

def enviar_correo_finalizacionTyba(id_usuario: int):
    correo_destino = obtener_correo_usuarioTyba(id_usuario)
    if not correo_destino:
        print(f"❌ No se encontró correo para usuario {id_usuario}")
        return False

    asunto = "Automatización completada"
    cuerpo = f"""
    Hola,

    La automatización TYBA ha finalizado exitosamente.

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
    if correo_ya_enviado(idEncabezado):
        print(f"⚠️ Correo ya enviado previamente para encabezado {idEncabezado}")
        return True  

    id_usuario = obtener_idUsuario_por_encabezado(idEncabezado)
    if id_usuario is None:
        print(f"No se encontró idUsuario para encabezado {idEncabezado}")
        return False

    enviado = enviar_correo_finalizacionTyba(id_usuario)
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
