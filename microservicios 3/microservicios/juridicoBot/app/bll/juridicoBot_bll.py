from pydantic import BaseModel
from typing import Optional
from app.dal.juridicoBot_dal import  DetalleModel, procesar_juridico_nombre, procesar_juridico_detalle, procesar_juridico_actuaciones
from app.dal.juridicoBot_dal import obtener_Info_aConsultarJuridico, insertar_detalle_resultadoJuridico
import pandas as pd
from app.dal.juridicoBot_dal import obtener_Info_aConsultarJuridico
import requests
import time
import random
import urllib.parse
import pandas as pd
import sys

# --- COLORES ANSI Y PRINTS ESTILO "HACKER" ---
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"  

class ResultadoJuridicoModel(BaseModel):
    nombreCompleto: str
    departamento: Optional[str] = None
    ciudad: Optional[str] = None
    especialidad: Optional[str] = None
    idNombres: Optional[str] = None
    detalle: Optional[str]  = None
    actuaciones: Optional[str] = None

class ResultadoNombresJuridicoModel(BaseModel):
    idProceso: Optional[str] = None
    idConexion: Optional[str] = None
    llaveProceso: Optional[str] = None
    fechaProceso: Optional[str] = None
    fechaUltimaActuacion: Optional[str] = None
    despacho: Optional[str] = None
    departamento: Optional[str] = None
    sujetosProcesales: Optional[str] = None
    esPrivado: Optional[str] = None
    cantFilas: Optional[str] = None

class ResultadoDetalleJuridicoModel(BaseModel):
    idProceso: Optional[str] = None
    llaveProceso: Optional[str] = None
    idConexion: Optional[str] = None
    esPrivado: Optional[str] = None
    fechaProceso: Optional[str] = None
    codDespachoCompleto: Optional[str] = None
    despacho: Optional[str] = None
    ponente: Optional[str] = None
    tipoProceso: Optional[str] = None
    claseProceso: Optional[str] = None
    subclaseProceso: Optional[str] = None
    recurso: Optional[str] = None
    ubicacion: Optional[str] = None
    contenidoRadicacion: Optional[str] = None
    fechaConsulta: Optional[str] = None
    ultimaActualizacion: Optional[str] = None

class ResultadoActuacionesJuridicoModel(BaseModel):
    idProceso: Optional[str] = None
    idRegActuacion: Optional[str] = None
    llaveProceso: Optional[str] = None
    consActuacion: Optional[str] = None
    fechaActuacion: Optional[str] = None
    actuacion: Optional[str] = None
    anotacion: Optional[str] = None
    fechaInicial: Optional[str] = None
    fechaFinal: Optional[str] = None
    fechaRegistro: Optional[str] = None
    codRegla: Optional[str] = None
    conDocumentos: Optional[str] = None
    cant: Optional[str] = None
    
def hacker_print(text, color=GREEN, delay=0.003):
    for c in text:
        sys.stdout.write(color + c + RESET)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def progress_bar(idx, total, width=30):
    pct = idx / total
    fill = int(pct * width)
    bar = "|" + "#" * fill + "-" * (width - fill) + "|"
    return f"{bar} {pct*100:6.2f}%"

def hacker_separator():
    print(GREEN + BOLD + "="*60 + RESET)

def esperar_datos_juridico(reintentos=0, espera_segundos=60):
    while True:
        info, error = obtener_Info_aConsultarJuridico()

        if error:
            hacker_print(f"[X] Error al consultar la base de datos: {error}", RED)
            time.sleep(espera_segundos)
            continue

        if not info:
            reintentos += 1
            hacker_print(f"[⏳] Sin datos aún. Reintentando en {espera_segundos}s... (Intento #{reintentos})", YELLOW)
            time.sleep(espera_segundos)
            continue

        return info 
    
# -------- CONFIGURACIÓN --------
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36 Edg/126.0.2592.102"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "DNT": "1",
    "Origin": "https://consultaprocesos.ramajudicial.gov.co",
    "Referer": "https://consultaprocesos.ramajudicial.gov.co/",
    "sec-ch-ua": "\"Microsoft Edge\";v=\"126\", \"Chromium\";v=\"126\", \"Not(A:Brand\";v=\"99\"",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-ch-ua-mobile": "?0",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
}



sujetos_objetivo = [
    "PATRIMONIO AUTONOMO SYSTEMGROUP TUYA", "PATRIMONIO AUTONOMO SYSTEMGROUP",
    "PATRIMONIO  SYSTEMGROUP", "AUTONOMO SYSTEMGROUP", "SYSTEMGROUP",
    "PATRIMONIO AUTONOMO ADAMANTINE NPL", "PATRIMONIO AUTONOMO ADAMANTINE",
    "PATRIMONIO ADAMANTINE", "ADAMANTINE", "PATRIMONIO AUTONOMO DAVIVIENDA",
    "PATRIMONIO DAVIVIENDA", "DAVIVIENDA", "FIDUARIA COLPATRIA",
    "FIDUCIARIA COLPATRIA", "SISTEMCOBRO", "SYSTEMCOBRO", "PATRIMONIO AUTONOMO FC",
    "SISTEMGROUP","FIDUCIARIA SCOTIABANK", "ADMANTINE"
]

cols_detalle = ['idProceso', 'llaveProceso', 'idConexion', 'esPrivado', 'fechaProceso',
    'codDespachoCompleto', 'despacho', 'ponente', 'tipoProceso',
    'claseProceso', 'subclaseProceso', 'recurso', 'ubicacion',
    'contenidoRadicacion', 'fechaConsulta', 'ultimaActualizacion']
cols_sujeto = ['idProceso', 'idRegSujeto', 'tipoSujeto', 'esEmplazado',
    'identificacion', 'nombreRazonSocial', 'cant']
cols_actuacion = ['idProceso', 'idRegActuacion', 'llaveProceso', 'consActuacion',
    'fechaActuacion', 'actuacion', 'anotacion', 'fechaInicial',
    'fechaFinal', 'fechaRegistro', 'codRegla', 'conDocumentos', 'cant']


info = esperar_datos_juridico()

url_base = "https://consultaprocesos.ramajudicial.gov.co:448/api/v2"

def fetch_all_pages(url_without_pagina: str, headers, list_key: str, max_pages: int = 999):
    """
    Itera ?pagina=1..N hasta que el API no devuelva más elementos en list_key.
    url_without_pagina debe venir SIN el parámetro &pagina=.
    """
    resultados = []
    page = 1
    while page <= max_pages:
        sep = "&" if "?" in url_without_pagina else "?"
        url = f"{url_without_pagina}{sep}pagina={page}"
        r = robust_request(url, headers)
        if not r or r.status_code != 200:
            break
        data = r.json() or {}
        chunk = data.get(list_key, [])
        if not chunk:
            break
        resultados.extend(chunk)
        page += 1
        # pequeña pausa anti-rate limit
        time.sleep(random.uniform(0.5, 1.3))
    return resultados

def robust_request(url, headers, nombre=None, departamento=None, ciudad=None, especialidad=None, max_retries=5):
    for intento in range(1, max_retries + 1):
        session = requests.Session()
        try:
            r = session.get(url, headers=headers, timeout=30)
            if r.status_code == 200:
                return r
            elif r.status_code in [403, 429, 500, 504]:
                espera = 3 * intento
                hacker_print(f"[!] ERROR {r.status_code} (REINTENTO {intento}/{max_retries}), ESPERANDO {espera}s...", YELLOW)
                time.sleep(espera + random.randint(1, 3))
            elif r.status_code == 400:
                hacker_print(f"[X] ERROR 400 (BAD REQUEST): REVISA TU PETICIÓN.", RED)

                # Si recibimos contexto, registramos el error en BD para este nombre
                if nombre is not None:
                    resultado = DetalleModel(
                        nombreCompleto=nombre,
                        departamento=departamento,
                        ciudad=ciudad,
                        especialidad=especialidad,
                        idNombres="error",
                        idDetalleJuridico="error",
                        idActuaciones="error"
                    )
                    insertar_detalle_resultadoJuridico(resultado)
                    hacker_print(f"[✓] REGISTRO GUARDADO COMO 'ERROR' EN BD PARA {nombre.upper()}", RED)
                return None
            else:
                hacker_print(f"[X] HTTP INESPERADO: {r.status_code}, SKIPPING.", RED)
                return None
        except Exception as e:
            hacker_print(f"[!] RED: {e} (REINTENTO {intento}/{max_retries})", RED)
            time.sleep(3)
    hacker_print("[X] MAX REINTENTOS ALCANZADOS. SE DESCARTA LA CONSULTA.", RED)
    return None


# --------- CICLO PRINCIPAL ---------
while True:
    info = esperar_datos_juridico()
    for idx, fila in enumerate(info, 1):
        idEncabezado, nombre, departamento, ciudad, especialidad = fila
        hacker_separator()
        bar = progress_bar(idx, len(info))
        porcentaje = (idx / len(info)) * 100
        status = f"[>] CONSULTANDO ({idx}/{len(info)}) - {porcentaje:.2f}%"
        hacker_print(bar, CYAN, delay=0.001)
        hacker_print(status, CYAN, delay=0.002)
        hacker_print(f"[>] NOMBRE: {nombre.upper()}", CYAN, delay=0.002)
        time.sleep(random.uniform(0.01, 0.03))
        # ---- PROCESOS POR NOMBRE ----
        nombre_encoded = urllib.parse.quote(nombre)
        url_proc_base = (
            f"{url_base}/Procesos/Consulta/NombreRazonSocial"
            f"?nombre={nombre_encoded}&tipoPersona=nat&SoloActivos=false&codificacionDespacho="
        )

        # Obtén TODAS las páginas
        procesos = fetch_all_pages(url_proc_base, headers, list_key="procesos")
        if not procesos:
            hacker_print(f"[!] {nombre.upper()}: SIN COINCIDENCIAS", YELLOW)
            resultado = DetalleModel(
                nombreCompleto=nombre,
                departamento=departamento,
                ciudad=ciudad,
                especialidad=especialidad,
                idNombres="vacio",
                idDetalleJuridico="vacio",
                idActuaciones="vacio"
            )
            insertar_detalle_resultadoJuridico(resultado)
            hacker_print(f"[✓] REGISTRO GUARDADO COMO 'VACÍO' EN BD PARA {nombre.upper()}", YELLOW)
            time.sleep(random.randint(1, 3))
            continue

        # Filtra procesos que contengan alguno de los sujetos objetivo
        coincidencias = [
            p for p in procesos
            if any(suj.upper() in p.get("sujetosProcesales", "").upper() for suj in sujetos_objetivo)
        ]

        if not coincidencias:
            hacker_print(f"[!] {nombre.upper()}: SIN COINCIDENCIAS", YELLOW)

            resultado = DetalleModel(
                nombreCompleto=nombre,
                departamento=departamento,
                ciudad=ciudad,
                especialidad=especialidad,
                idNombres="vacio",
                idDetalleJuridico="vacio",
                idActuaciones="vacio"
            )
            insertar_detalle_resultadoJuridico(resultado)
            hacker_print(f"[✓] REGISTRO GUARDADO COMO 'VACÍO' EN BD PARA {nombre.upper()}", YELLOW)
            time.sleep(random.randint(1, 3))
            continue


        for proc in coincidencias:
            id_proceso = str(proc["idProceso"])
            hacker_print(f"[+] PROCESO {id_proceso} MATCH ENCONTRADO", GREEN, delay=0.001)

            # ---- DETALLE ----
            res_det = robust_request(f"{url_base}/Proceso/Detalle/{id_proceso}", headers)
            detalle = res_det.json() if res_det and res_det.status_code == 200 else {}

            detalle["idProceso"] = id_proceso

            print("🟡 Detalle a insertar:", detalle)

            for k in ['fechaProceso', 'fechaConsulta', 'ultimaActualizacion']:
                detalle[k] = pd.to_datetime(detalle.get(k), errors='coerce').strftime('%Y-%m-%d %H:%M:%S') if detalle.get(k) else ""
            idDetalleJuridico = procesar_juridico_detalle(detalle)

            # ---- SUJETOS ----
            url_sujetos_base = f"{url_base}/Proceso/Sujetos/{id_proceso}"
            sujetos_all = fetch_all_pages(url_sujetos_base, headers, list_key="sujetos")
            idNombres = None

            # Conservamos tu esquema: guardas UN registro en NombresJuridico por proceso,
            # usando los metadatos del 'proc' y el 'cantFilas' = total de sujetos.
            nombre_data = {
                "idProceso": proc.get("idProceso"),
                "idConexion": proc.get("idConexion"),
                "llaveProceso": proc.get("llaveProceso"),
                "fechaProceso": proc.get("fechaProceso"),
                "fechaUltimaActuacion": proc.get("fechaUltimaActuacion"),
                "despacho": proc.get("despacho"),
                "departamento": proc.get("departamento"),
                "sujetosProcesales": proc.get("sujetosProcesales"),
                "esPrivado": proc.get("esPrivado"),
                "cantFilas": len(sujetos_all)
            }
            idNombres = procesar_juridico_nombre(nombre_data)


            # ---- ACTUACIONES ----
            url_act_base = f"{url_base}/Proceso/Actuaciones/{id_proceso}"
            actuaciones_all = fetch_all_pages(url_act_base, headers, list_key="actuaciones")

            idActuaciones = None
            for act in actuaciones_all:
                act["idProceso"] = id_proceso
                # Normaliza fechas
                for fecha in ['fechaActuacion', 'fechaInicial', 'fechaFinal', 'fechaRegistro']:
                    act[fecha] = pd.to_datetime(act.get(fecha), errors='coerce').strftime('%Y-%m-%d %H:%M:%S') if act.get(fecha) else ""
                last_id = procesar_juridico_actuaciones(act)
                idActuaciones = last_id  # conserva el último id insertado (por si lo enlazas abajo)


            # ---- VINCULACIÓN EN BD
            resultado = DetalleModel(
                nombreCompleto=nombre,
                departamento=detalle.get("departamento", ""),
                ciudad=detalle.get("ubicacion", ""),
                especialidad=detalle.get("especialidad", ""),
                idNombres=str(id_proceso),
                idDetalleJuridico=str(id_proceso),
                idActuaciones=str(id_proceso),
            )

            insertar_detalle_resultadoJuridico(resultado)

            hacker_print(f"[✓] DATOS GUARDADOS EN BD ({id_proceso})", GREEN, delay=0.001)
            time.sleep(random.randint(2, 6))

    hacker_separator()
    hacker_print("[+] FIN DE LA CONSULTA. TODOS LOS DATOS HAN SIDO PROCESADOS.", GREEN, delay=0.002)
    hacker_separator()
    time.sleep(5)


    def obtener_automatizacionInfoJuridico():
        """
        Retorna la siguiente tupla (idEncabezado, cedula) pendiente.
        Lanza excepción si hay un error, o devuelve None si no hay más cédulas.
        """
        filas, error = obtener_Info_aConsultarJuridico()
        if error:
            raise Exception(f"Error al consultar próxima cédula: {error}")
        if not filas:
            return None
        # Convertir a lista si viene como tupla inmutable
        fila = list(filas[0])
        
        # Suponiendo que el nombre completo está en la segunda posición (índice 1)
        if fila:
            nombre = fila[1].lower()
            nombre = nombre.replace("ñ", "%C3%B1")
            nombre = nombre.replace(" ", "%20")
            fila[1] = nombre
        return fila
