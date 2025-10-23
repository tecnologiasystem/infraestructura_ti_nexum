from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.Runt.dal.runt_dal import insertar_encabezado, insertar_detalle, EncabezadoModel, insertar_detalle_resultadoRunt, obtener_correo_usuarioRunt, correo_ya_enviado, obtener_idUsuario_por_encabezado, marcar_correo_enviado, marcar_pausa_encabezado, pausar_detalle_encabezado, quitar_pausa_encabezado,reanudar_detalle_encabezado
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config.email_config import REMITENTE, PASSWORD, SERVER, PORT
import re
from typing import List

def procesar_archivo_excel(encabezado: EncabezadoModel) -> int:
    """
    Función principal que procesa la información del encabezado y sus detalles
    extraídos desde un archivo Excel para la automatización RUNT.

    Proceso detallado:
    1. Filtra solo los detalles que tengan cédula válida (no vacía ni nula). 
       Esto evita insertar registros incompletos o inválidos en la base de datos.
    2. Actualiza la propiedad `totalRegistros` del encabezado con el número real
       de detalles válidos, garantizando que el conteo sea correcto y consistente.
    3. Inserta el encabezado en la base de datos usando la función `insertar_encabezado`.
       Si esta operación falla (devuelve None o -1), lanza una excepción que detiene
       el flujo para evitar insertar detalles sin un encabezado válido.
    4. Itera sobre cada detalle válido y lo inserta en la base de datos asociado al
       `idEncabezado` obtenido.
    5. Finalmente, retorna el `idEncabezado` insertado para seguimiento o uso posterior.

    Este flujo es fundamental para mantener la integridad y trazabilidad de los datos
    en la automatización, asegurando que solo se procesen datos completos y correctamente
    agrupados bajo un encabezado.
    """
    detalles_validos = [d for d in encabezado.detalles if d.cedula and d.cedula.strip()]
    
    encabezado.totalRegistros = len(detalles_validos)

    idEncabezado = insertar_encabezado(encabezado)
    if not idEncabezado or idEncabezado == -1:
        raise Exception("❌ Error al insertar encabezado. No se puede continuar con los detalles.")
    
    for detalle in detalles_validos:
        insertar_detalle(idEncabezado, detalle)

    return idEncabezado


class ResultadoRuntModel(BaseModel):
    cedula: str
    placaVehiculo: Optional[str] = None
    tipoServicio: Optional[str] = None
    estadoVehiculo: Optional[str] = None
    claseVehiculo: Optional[str] = None
    marca: Optional[str] = None
    modelo: Optional[str] = None
    numeroSerie: Optional[str] = None
    numeroChasis: Optional[str] = None
    cilindraje: Optional[str] = None
    tipoCombustible: Optional[str] = None
    autoridadTransito: Optional[str] = None
    linea: Optional[str] = None
    color: Optional[str] = None
    numeroMotor: Optional[str] = None
    numeroVIN: Optional[str] = None
    tipoCarroceria: Optional[str] = None
    polizaSOAT: Optional[str] = None
    revisionTecnomecanica: Optional[str] = None
    limitacionesPropiedad: Optional[str] = None
    garantiasAFavorDe: Optional[str] = None

class PolizaSOATItem(BaseModel):
    numeroPoliza: str
    fechaExpedicion: str
    fechaInicio: str
    fechaFin: str
    codigoTarifa: str
    entidad: str
    estado: str

class RevisionRTMItem(BaseModel):
    tipoRevision: str
    fechaExpedicion: str
    fechaVigencia: str
    CDA: str
    vigente: str
    numeroCertificado: str
    infoConsistente: str

class LimitacionItem(BaseModel):
    tipo: str
    numeroOficio: str
    entidad: str
    departamento: str
    municipio: str
    fechaOficio: str
    fechaRegistro: str

class GarantiaItem(BaseModel):
    acreedor: str
    nit: str
    fechaInscripcion: str
    confecamaras: str

def procesar_resultado_automatizacionRunt(resultado: ResultadoRuntModel) -> bool:
    debug_parseo_completo(resultado)
    
    # Parsear todos los datos
    polizas = parsear_polizas(resultado.polizaSOAT)
    tecnomecanicas = parsear_tecnomecanica(resultado.revisionTecnomecanica)
    limitaciones = parsear_limitaciones(resultado.limitacionesPropiedad)
    garantias = parsear_garantias(resultado.garantiasAFavorDe)

    # Formatear como strings para almacenamiento
    resultado.polizaSOAT = formatear_polizas_str(polizas)
    resultado.revisionTecnomecanica = formatear_rtm_str(tecnomecanicas)
    resultado.limitacionesPropiedad = formatear_limitaciones_str(limitaciones)
    resultado.garantiasAFavorDe = formatear_garantias_str(garantias)
    
    print("📝 Strings formateados:")
    print(f"  - Pólizas SOAT: {len(polizas)} registros")
    print(f"  - Tecnomecánicas: {len(tecnomecanicas)} registros")
    print(f"  - Limitaciones: {len(limitaciones)} registros")
    print(f"  - Garantías: {len(garantias)} registros")

    resultado_guardado = insertar_detalle_resultadoRunt(resultado)
    print(f"✅ Resultado guardado: {resultado_guardado}")
    return resultado_guardado


def enviar_correo_finalizacionRunt(id_usuario: int):
    """
    Envía correo notificando la finalización del proceso Runt para el usuario dado.

    - Obtiene el correo del usuario.
    - Arma un email simple con asunto y cuerpo.
    - Se conecta al servidor SMTP y envía el mensaje.
    - Retorna True si el correo se envió exitosamente, False si hubo error.
    """
    correo_destino = obtener_correo_usuarioRunt(id_usuario)
    if not correo_destino:
        print(f"❌ No se encontró correo para usuario {id_usuario}")
        return False

    asunto = "Automatización completada"
    cuerpo = f"""
    Hola,

    La automatización RUNT ha finalizado exitosamente.

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

    enviado = enviar_correo_finalizacionRunt(id_usuario)
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

#------------PARSEAR--------------------------

def parsear_polizas(texto: str) -> List[PolizaSOATItem]:
    if not texto or "Número de poliza" not in texto:
        return []
    
    # Patrón mejorado que maneja mejor los saltos de línea y espacios en nombres de entidades
    patron = r'(\d{8,})\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(\d+)\s+(.+?)\s+(NO VIGENTE|VIGENTE)'
    
    bloques = re.findall(patron, texto, re.MULTILINE | re.DOTALL)
    
    polizas = []
    for match in bloques:
        # Limpiar el nombre de la entidad removiendo saltos de línea y espacios extra
        entidad_limpia = re.sub(r'\s+', ' ', match[5].strip())
        
        poliza = PolizaSOATItem(
            numeroPoliza=match[0].strip(),
            fechaExpedicion=match[1].strip(),
            fechaInicio=match[2].strip(),
            fechaFin=match[3].strip(),
            codigoTarifa=match[4].strip(),
            entidad=entidad_limpia,
            estado=match[6].strip()
        )
        polizas.append(poliza)
        print(f"  📋 Póliza {match[0].strip()}: {entidad_limpia} ({match[6].strip()})")
    
    print(f"✅ Parsed {len(polizas)} pólizas SOAT")
    return polizas


def parsear_tecnomecanica(texto: str) -> List[RevisionRTMItem]:
    """
    Parsea todas las revisiones tecnomecánicas del texto, no solo la primera.
    """
    if not texto or "REVISION TECNICO-MECANICO" not in texto:
        return []

    # Patrón mejorado para capturar todos los bloques de revisión tecnomecánica
    patron = r'REVISION TECNICO-MECANICO\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})\s+(.+?)\s+(SI|NO)\s+(\d+)\s+(SI|NO)'
    
    bloques = re.findall(patron, texto, re.MULTILINE | re.DOTALL)
    
    revisiones = []
    for match in bloques:
        # Limpiar el nombre del CDA removiendo saltos de línea y espacios extra
        cda_limpio = re.sub(r'\s+', ' ', match[2].strip())
        
        revision = RevisionRTMItem(
            tipoRevision="REVISION TECNICO-MECANICO",
            fechaExpedicion=match[0].strip(),
            fechaVigencia=match[1].strip(),
            CDA=cda_limpio,
            vigente=match[3].strip(),
            numeroCertificado=match[4].strip(),
            infoConsistente=match[5].strip()
        )
        revisiones.append(revision)
        print(f"  🔧 Revisión {match[0].strip()}: {cda_limpio} (Vigente: {match[3].strip()})")
    
    print(f"✅ Parsed {len(revisiones)} revisiones tecnomecánicas")
    return revisiones


def parsear_limitaciones(texto: str) -> List[LimitacionItem]:
    """
    Parsea todas las limitaciones de propiedad del texto, no solo la primera.
    """
    if not texto or "EMBARGO" not in texto:
        return []
    
    # Patrón mejorado para capturar todos los embargos
    patron = r'(EMBARGO)\s+(\d+)\s+(.+?)\s+([A-Za-z\s.]+?)\s+(BOGOTA|[A-Za-z\s]+?)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})'
    
    bloques = re.findall(patron, texto, re.MULTILINE | re.DOTALL)
    
    limitaciones = []
    for match in bloques:
        limitacion = LimitacionItem(
            tipo=match[0].strip(),
            numeroOficio=match[1].strip(),
            entidad=match[2].strip(),
            departamento=match[3].strip(),
            municipio=match[4].strip(),
            fechaOficio=match[5].strip(),
            fechaRegistro=match[6].strip()
        )
        limitaciones.append(limitacion)
    
    print(f"✅ Parsed {len(limitaciones)} limitaciones")
    return limitaciones


def parsear_garantias(texto: str) -> List[GarantiaItem]:
    """
    Parsea todas las garantías a favor de del texto, no solo la primera.
    """
    if not texto or "NIT" not in texto:
        return []
    
    # Patrón mejorado para capturar todos los bancos/garantías
    patron = r'NIT\s+(\d+)\s+(BANCO[^\n\r]+?|[A-Z\s&.]+?)\s+(\d{2}/\d{2}/\d{4})\s+(NO|SI)'
    
    bloques = re.findall(patron, texto, re.MULTILINE | re.DOTALL)
    
    garantias = []
    for match in bloques:
        # Limpiar el nombre del acreedor removiendo saltos de línea y espacios extra
        acreedor_limpio = re.sub(r'\s+', ' ', match[1].strip())
        
        garantia = GarantiaItem(
            nit=match[0].strip(),
            acreedor=acreedor_limpio,
            fechaInscripcion=match[2].strip(),
            confecamaras=match[3].strip()
        )
        garantias.append(garantia)
        print(f"  🏦 Garantía NIT {match[0].strip()}: {acreedor_limpio}")
    
    print(f"✅ Parsed {len(garantias)} garantías")
    return garantias


def formatear_polizas_str(lista: List[PolizaSOATItem]) -> str:
    if not lista:
        return "No se encontraron pólizas SOAT registradas."
    
    # Formato más compacto para evitar truncamiento en BD
    resultado = f"PÓLIZAS SOAT ({len(lista)} registros):\n"
    for i, p in enumerate(lista, 1):
        resultado += f"{i}. Nº{p.numeroPoliza} | {p.fechaExpedicion} → {p.fechaFin} | {p.entidad} | {p.estado}\n"
    
    print(f"📝 String de pólizas generado: {len(resultado)} caracteres")
    return resultado.strip()

def formatear_rtm_str(lista: List[RevisionRTMItem]) -> str:
    if not lista:
        return "No se encontraron revisiones tecnomecánicas registradas."
    
    # Formato más compacto para evitar truncamiento en BD
    resultado = f"REVISIONES TECNOMECÁNICAS ({len(lista)} registros):\n"
    for i, r in enumerate(lista, 1):
        resultado += f"{i}. {r.fechaExpedicion} → {r.fechaVigencia} | {r.CDA} | Vigente:{r.vigente} | Cert:{r.numeroCertificado}\n"
    
    print(f"📝 String de RTM generado: {len(resultado)} caracteres")
    return resultado.strip()

def formatear_limitaciones_str(lista: List[LimitacionItem]) -> str:
    if not lista:
        return "No se encontraron limitaciones de propiedad registradas."
    
    # Formato más compacto para evitar truncamiento en BD
    resultado = f"LIMITACIONES ({len(lista)} registros):\n"
    for i, l in enumerate(lista, 1):
        resultado += f"{i}. {l.tipo} Nº{l.numeroOficio} | {l.entidad} | {l.departamento},{l.municipio} | {l.fechaOficio}\n"
    
    print(f"📝 String de limitaciones generado: {len(resultado)} caracteres")
    return resultado.strip()

def formatear_garantias_str(lista: List[GarantiaItem]) -> str:
    if not lista:
        return "No se encontraron garantías registradas."
    
    # Formato más compacto para evitar truncamiento en BD
    resultado = f"GARANTÍAS ({len(lista)} registros):\n"
    for i, g in enumerate(lista, 1):
        resultado += f"{i}. {g.acreedor} | NIT:{g.nit} | {g.fechaInscripcion} | Confecámaras:{g.confecamaras}\n"
    
    print(f"📝 String de garantías generado: {len(resultado)} caracteres")
    return resultado.strip()


def debug_parseo_completo(resultado: ResultadoRuntModel):
    """
    Función para debuggear el parseo completo y ver cuántos registros se están capturando.
    """
    print("🔍 DEBUGGING PARSEO COMPLETO:")
    print(f"📋 Cédula: {resultado.cedula}")
    print(f"🚗 Placa: {resultado.placaVehiculo}")
    
    polizas = parsear_polizas(resultado.polizaSOAT)
    print(f"🛡️ Pólizas encontradas: {len(polizas)}")
    for i, p in enumerate(polizas, 1):
        print(f"    {i}. {p.numeroPoliza} - {p.entidad} - {p.estado}")
    
    tecnomecanicas = parsear_tecnomecanica(resultado.revisionTecnomecanica)
    print(f"🔧 Revisiones tecnomecánicas encontradas: {len(tecnomecanicas)}")
    for i, t in enumerate(tecnomecanicas, 1):
        print(f"    {i}. {t.fechaExpedicion} - {t.CDA} - Vigente: {t.vigente}")
    
    limitaciones = parsear_limitaciones(resultado.limitacionesPropiedad)
    print(f"⚖️ Limitaciones encontradas: {len(limitaciones)}")
    for i, l in enumerate(limitaciones, 1):
        print(f"    {i}. {l.tipo} - {l.entidad} - {l.fechaOficio}")
    
    garantias = parsear_garantias(resultado.garantiasAFavorDe)
    print(f"🏦 Garantías encontradas: {len(garantias)}")
    for i, g in enumerate(garantias, 1):
        print(f"    {i}. {g.acreedor} - NIT: {g.nit} - {g.fechaInscripcion}")
