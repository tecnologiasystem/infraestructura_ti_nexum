from datetime import datetime, timedelta
from collections import defaultdict
import smtplib
from email.mime.text import MIMEText
from app.dal.monitor_rpa_dal import registrar_caida_rpa, obtener_datos_encabezado, registrar_reactivacion_rpa, existe_caida_sin_reactivacion, obtener_ultima_fecha_caida
from app.dal.monitor_rpa_dal import obtener_dashboard as dal_obtener_dashboard, obtener_encabezados, obtener_detalles, obtener_detalles_paginados, obtener_todos_detalles_por_origen, buscar_detalle_por_cedula
from app.dal.monitor_rpa_dal import resumen_vigencia as dal_resumen_vigencia

from dotenv import load_dotenv
import os

load_dotenv()

SERVER = os.getenv("SERVER")
PORT = int(os.getenv("PORT"))
REMITENTE = os.getenv("REMITENTE")
PASSWORD = os.getenv("PASSWORD")
DESTINATARIOS = ["j.castillo@sgnpl.com", "j.salgar@sgnpl.com", "b.paloma@sgnpl.com"]

ultima_consulta: dict[str, datetime] = defaultdict(lambda: datetime.min)
alerta_enviada: dict[str, bool] = defaultdict(bool)


def enviar_correo(asunto: str, mensaje: str) -> None:
    msg = MIMEText(mensaje)
    msg["Subject"] = asunto
    msg["From"] = REMITENTE
    msg["To"] = ", ".join(DESTINATARIOS)

    try:
        with smtplib.SMTP(SERVER, PORT) as server:
            server.starttls()
            server.login(REMITENTE, PASSWORD)
            server.sendmail(REMITENTE, DESTINATARIOS, msg.as_string())
        print("✅ Correo enviado:", asunto)
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")

async def verificar_inactividad():
    ahora = datetime.now()
    for clave, ts in list(ultima_consulta.items()):
        origen, id_str = clave.split("_", 1)
        id_encabezado = int(id_str)

        if (ahora - ts) > timedelta(minutes=5) and not alerta_enviada[clave]:
            datos = obtener_datos_encabezado(origen, id_encabezado)
            if not datos:
                print(f"ℹ️ No existe encabezado para {origen}/{id_encabezado}. Limpio y continúo.")
                ultima_consulta.pop(clave, None)
                alerta_enviada.pop(clave, None)
                continue

            # si ya finalizó, también limpia
            if datos.get("fechaFinalizacion") is not None:
                print(f"ℹ️ {origen}-{id_encabezado} finalizado. Limpio para no re-chequear.")
                ultima_consulta.pop(clave, None)
                alerta_enviada.pop(clave, None)
                continue

            nombre = datos["automatizacion"]
            asunto = f"⚠️ Alerta: RPA {nombre} inactivo"
            mensaje = (
                f"El RPA '{nombre}' (idEncabezado={id_encabezado}) "
                f"no registra actividad desde {ts:%Y-%m-%d %H:%M:%S}"
            )

            enviar_correo(asunto, mensaje)

            registrar_caida_rpa(
                id_encabezado,                    
                ahora,                            
                mensaje,                       
                datos["automatizacion"],          
                datos["idUsuario"],          
                datos["fechaCargue"],             
                datos["totalRegistros"],         
            )
            alerta_enviada[clave] = True


def obtener_dashboard():
    return dal_obtener_dashboard()

def listar_encabezados_rpa(origen: str):
    return obtener_encabezados(origen)

def listar_detalles_rpa(origen: str, id_encabezado: int):
    return obtener_detalles(origen, id_encabezado)

def listar_detalles_rpa_paginados(
    origen: str,
    id_enc: int,
    offset: int,
    limit:  int,
    cc:     str | None = None
) -> dict:

    return obtener_detalles_paginados(origen, id_enc, offset, limit, cc)

def listar_todos_detalles_por_origen(origen: str) -> list[dict]:
    return obtener_todos_detalles_por_origen(origen)

def actualizar_ultima_consulta(origen: str, id_encabezado: int):
    clave = f"{origen}_{id_encabezado}"
    ts_anterior = ultima_consulta.get(clave, datetime.min)
    ultima_consulta[clave] = datetime.now()
    alerta_enviada[clave] = False

    if existe_caida_sin_reactivacion(id_encabezado):
        fecha_caida     = obtener_ultima_fecha_caida(id_encabezado)
        tiempo_delta    = datetime.now() - fecha_caida
        segundos_inactivo = int(tiempo_delta.total_seconds())
        registrar_reactivacion_rpa(
            id_encabezado,          
            datetime.now(),         
            segundos_inactivo  
        )
        
def buscar_detalle_por_cedulaBLL(origen: str, id_encabezado: int, cedula: str):
    return buscar_detalle_por_cedula(origen, id_encabezado, cedula)

def obtener_resumen_vigencia(id_encabezado: int) -> dict:
    return dal_resumen_vigencia(id_encabezado)