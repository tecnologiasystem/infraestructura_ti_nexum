from pydantic import BaseModel
from typing import Optional
from app.dal.vigenciaJuridico_dal import insertar_detalle_resultadoVigencia, obtener_CC_aConsultarVigencia
import requests
import time
import random
from datetime import datetime
import sys

# --- COLORES ANSI Y PRINTS ESTILO "HACKER" ---
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"  

class ResultadoJVigenciaModel(BaseModel):
    nombre: str
    cedula: str
    vigencia: Optional[str]
    fechaConsulta: Optional[str]

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

def esperar_datos_vigencia(reintentos=0, espera_segundos=60):
    while True:
        info, error = obtener_CC_aConsultarVigencia()

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

# ---------------------------------------------
# Consulta a Registraduría
# ---------------------------------------------
def consultar_vigencia_por_cedula(cedula: str) -> Optional[dict]:
    url = "https://defunciones.registraduria.gov.co:8443/VigenciaCedula/consulta"
    payload = {
        "nuip": int(cedula),
        "ip": "190.60.206.29"
    }
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "es-419,es;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://defunciones.registraduria.gov.co",
        "Referer": "https://defunciones.registraduria.gov.co/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error HTTP {response.status_code} al consultar la cédula {cedula}")
            return None
    except Exception as e:
        print(f"❌ Excepción al consultar vigencia: {e}")
        return None

# ---------------------------------------------
# Ciclo de consulta y guardado
# ---------------------------------------------
def ejecutar_consulta_y_guardado():
    info = esperar_datos_vigencia()

    for idx, fila in enumerate(info, 1):
        if len(fila) == 3:
            idEncabezado, nombre, cedula = fila[0], fila[1], fila[2]
        else:  
            idEncabezado, cedula = fila[0], fila[1]
            nombre = "" 

        hacker_separator()
        hacker_print(progress_bar(idx, len(info)), CYAN, delay=0.001)
        hacker_print(f"[🔎] Consultando vigencia para: {nombre} ({cedula})", CYAN)

        respuesta = consultar_vigencia_por_cedula(cedula)
        if not respuesta:
            hacker_print("[X] No se pudo obtener la respuesta de la Registraduría", RED)
            continue

        vigencia = respuesta.get("vigencia")
        fecha_str = respuesta.get("fecha")
        if not vigencia or not fecha_str:
            hacker_print("[X] Respuesta incompleta: falta 'vigencia' o 'fecha'", RED)
            continue

        try:
            fecha_consulta = datetime.strptime(fecha_str, "%d/%m/%Y").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            hacker_print(f"[X] Error al convertir la fecha: {fecha_str}", RED)
            continue

        resultado = ResultadoJVigenciaModel(
            nombre=nombre,           
            cedula=cedula,
            vigencia=vigencia,
            fechaConsulta=fecha_consulta
        )

        ok = insertar_detalle_resultadoVigencia(resultado)
        if ok:
            hacker_print(f"[✓] Guardado correctamente: {cedula} → {vigencia}", GREEN)
        else:
            hacker_print(f"[X] Falló el guardado para {cedula}", RED)

        time.sleep(random.uniform(1, 3))

# --------- LOOP PRINCIPAL ---------
while True:
    try:
        hacker_separator()
        hacker_print("[▶] Iniciando ciclo de consulta y guardado de Vigencia...", CYAN)
        ejecutar_consulta_y_guardado()

        hacker_separator()
        hacker_print("[+] FIN DE LA CONSULTA. TODOS LOS DATOS HAN SIDO PROCESADOS.", GREEN)
        hacker_separator()

        time.sleep(5)

    except KeyboardInterrupt:
        hacker_print("\n[■] Proceso detenido por el usuario.", YELLOW)
        break

    except Exception as e:
        hacker_print(f"[X] Error no controlado: {e}", RED)
        time.sleep(10)


def obtener_automatizacionCCVigencia():
    filas = esperar_datos_vigencia()
    if not filas:
        return None
    return filas[0]


