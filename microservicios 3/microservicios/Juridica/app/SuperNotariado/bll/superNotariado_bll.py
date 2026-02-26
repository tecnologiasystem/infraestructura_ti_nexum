from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.SuperNotariado.dal.superNotariado_dal import (
    insertar_encabezado,
    insertar_detalle,
    EncabezadoModel,
    crud_usuarios_consulta,
    insertar_detalle_resultado,
    insertar_usuarios_desde_excel_df,
    obtener_y_ocupar_usuario,
    obtener_correo_usuario, marcar_correo_enviado,
    obtener_idUsuario_por_encabezado, correo_ya_enviado,
    marcar_pausa_encabezado, pausar_detalle_encabezado,
    quitar_pausa_encabezado, reanudar_detalle_encabezado, obtener_correo_notificacion
)
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.email_config import REMITENTE, PASSWORD, SERVER, PORT

def procesar_archivo_excel(encabezado: EncabezadoModel) -> int:
    """
    """
    """
    Esta función recibe un objeto 'EncabezadoModel' que contiene la metadata 
    y una lista de detalles (filas de datos).
    Primero, intenta insertar el encabezado en la base de datos usando 
    la función 'insertar_encabezado'. Si falla, se lanza una excepción y 
    el proceso se detiene.
    Luego, para cada detalle en la lista, llama a 'insertar_detalle' para 
    insertar cada fila relacionada con el encabezado.
    Finalmente, devuelve el id generado para el encabezado, que sirve para 
    relacionar los detalles.
    """
    idEncabezado = insertar_encabezado(encabezado)
    if not idEncabezado or idEncabezado == -1:
        raise Exception("❌ Error al insertar encabezado. No se puede continuar con los detalles.")
    for detalle in encabezado.detalles:
        insertar_detalle(idEncabezado, detalle)
    return idEncabezado

class UsuarioConsultaModel(BaseModel):
    """
    """
    """
    Modelo de datos Pydantic que representa un usuario para consulta.
    Incluye campos opcionales y obligatorios, como usuario, contraseña,
    estado y fecha de uso.
    """
    idUsuarioConsulta: Optional[int] = None
    correo: Optional[str] = None
    usuario: str
    contraseña: str
    estado: Optional[bool] = True
    fechaUso: Optional[datetime] = None

class ResultadoModel(BaseModel):
    """
    """
    """
    Modelo de resultado para almacenar los datos procesados de la automatización.
    Incluye campos típicos asociados a un registro de SuperNotariado.
    """
    CC: str
    ciudad: Optional[str] = None
    matricula: Optional[str] = None
    direccion: Optional[str] = None
    vinculadoA: Optional[str] = None

def procesar_resultado_automatizacion(resultado: ResultadoModel) -> bool:
    """
    """
    """
    Función para procesar los resultados que llegan de la automatización.
    Recibe un objeto ResultadoModel y llama a la función 'insertar_detalle_resultado'
    que realiza la inserción o actualización en la base de datos.
    Devuelve True si la operación fue exitosa, False si falló.
    """
    return insertar_detalle_resultado(resultado)

def crear_usuario(usuario: UsuarioConsultaModel) -> int:
    """
    """
    """
    Función que crea un nuevo usuario en la base de datos.
    Si no se especifica el estado o la fechaUso, se asignan valores por defecto:
    estado True y fecha actual.
    Utiliza la función 'crud_usuarios_consulta' con acción 1 (crear).
    Retorna el id generado si tiene éxito o -1 en caso de error.
    """
    if usuario.estado is None:
        usuario.estado = True
    if usuario.fechaUso is None:
        usuario.fechaUso = datetime.now()
    result = crud_usuarios_consulta(1, usuario.dict())
    return result["idUsuarioConsulta"] if result else -1

def actualizar_usuario(usuario: UsuarioConsultaModel) -> bool:
    """
    """
    """
    Actualiza un usuario existente.
    Llama a 'crud_usuarios_consulta' con acción 2 (actualizar).
    Retorna True si se actualizó correctamente, False si no.
    """
    return crud_usuarios_consulta(2, usuario.dict()) is not None

def eliminar_usuario(id_usuario: int) -> bool:
    """
    """
    """
    Elimina un usuario dado su id.
    Usa 'crud_usuarios_consulta' con acción 3 (eliminar).
    Retorna True si fue exitoso, False en caso contrario.
    """
    return crud_usuarios_consulta(3, {"idUsuarioConsulta": id_usuario}) is not None

def obtener_usuario(id_usuario: int) -> Optional[dict]:
    """
    """
    """
    Obtiene un usuario específico por id.
    Llama a 'crud_usuarios_consulta' con acción 4 (obtener).
    Retorna un diccionario con datos del usuario o None si no existe.
    """
    resultado = crud_usuarios_consulta(4, {"idUsuarioConsulta": id_usuario})
    return resultado[0] if resultado else None

def listar_usuarios() -> List[dict]:
    """
    """
    """
    Obtiene la lista completa de usuarios.
    Llama a 'crud_usuarios_consulta' con acción 6 (listar).
    Devuelve una lista de diccionarios con los usuarios.
    """
    return crud_usuarios_consulta(6)

def cargar_usuarios_excel_desde_archivo(ruta_excel: str):
    """
    """
    """
    Lee un archivo Excel ubicado en 'ruta_excel' usando pandas.
    Limpia los valores nulos y llama a la función que inserta usuarios en base
    a un DataFrame.
    Devuelve un tuple (success: bool, mensaje: str).
    En caso de error, captura y muestra el traceback.
    """
    try:
        df = pd.read_excel(ruta_excel)
        df.fillna("", inplace=True)
        return insertar_usuarios_desde_excel_df(df)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)

def tomar_usuario_disponible() -> Optional[dict]:
    """
    """
    """
    Obtiene un usuario disponible para la automatización.
    Llama a la función 'obtener_y_ocupar_usuario' que marca al usuario
    como ocupado y retorna sus datos.
    Retorna None si no hay usuarios disponibles.
    """
    return obtener_y_ocupar_usuario()

def enviar_correo_finalizacionSuperNotariado(id_usuario: int):
    """
    Envía correo notificando la finalización del proceso Super Notariado para el usuario dado.

    - Obtiene el correo del usuario.
    - Arma un email simple con asunto y cuerpo.
    - Se conecta al servidor SMTP y envía el mensaje.
    - Retorna True si el correo se envió exitosamente, False si hubo error.
    """
    correo_destino = obtener_correo_usuario(id_usuario)
    if not correo_destino:
        print(f"❌ No se encontró correo para usuario {id_usuario}")
        return False

    asunto = "Automatización completada"
    cuerpo = f"""
    Hola,

    La automatización SUPER NOTARIADO ha finalizado exitosamente.

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

    enviado = enviar_correo_finalizacionSuperNotariado(id_usuario)
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

#--------- GET PARA NOTIFICACIONES ---------------------------------------------
def obtener_correoNotificacion():
    """
    Retorna la siguiente tupla (radicado, fechaInicial, fechaFinal) pendiente.
    Lanza excepción si hay un error, o devuelve None si no hay más radicados.
    """
    filas, error = obtener_correo_notificacion()
    if error:
        raise Exception(f"Error al consultar próximo radicado: {error}")
    if not filas:
        return None
    return filas[0]