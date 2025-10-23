from fastapi import FastAPI
from app.api.excel_api import router as conversor_router
from app.api.productividad_api import router as productividad_router
from fastapi.middleware.cors import CORSMiddleware
import threading
import time
import os

"""
Inicializa una instancia de la aplicación FastAPI.
"""
app = FastAPI()

"""
Agrega el middleware CORS (Cross-Origin Resource Sharing), permitiendo que cualquier origen
haga peticiones (útil para pruebas locales o microservicios separados).
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""
Incluye el router de conversión de columnas numéricas y nombres a texto,
accesible mediante el prefijo "/conversor".
"""
app.include_router(conversor_router, prefix="/conversor", tags=["Conversión"])

"""
Incluye el router de análisis de productividad,
accesible mediante el prefijo "/productividad".
"""
app.include_router(productividad_router, prefix="/productividad", tags=["Productividad"])


# =========================================================
# 🔁 LIMPIEZA AUTOMÁTICA DE ARCHIVOS TEMPORALES EN /temp
# =========================================================

"""
Función que se ejecuta en segundo plano:
- Revisa periódicamente (cada 120 segundos)
- Elimina archivos en la carpeta 'temp' que tengan más de 10 minutos de antigüedad
- Esto evita que se acumulen archivos grandes y se llene el disco
"""
def limpiar_archivos_temporales():
    temp_dir = "temp"
    tiempo_limite = 10 * 60  # 🕒 10 minutos en segundos

    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    print("🟢 Monitor de limpieza automática iniciado.")

    while True:
        ahora = time.time()
        for archivo in os.listdir(temp_dir):
            ruta = os.path.join(temp_dir, archivo)
            if os.path.isfile(ruta):
                if ahora - os.path.getctime(ruta) > tiempo_limite:
                    try:
                        os.remove(ruta)
                        print(f"🧹 Archivo temporal eliminado: {archivo}")
                    except Exception as e:
                        print(f"❌ Error al eliminar {archivo}: {e}")
        time.sleep(120)  # Espera 2 minutos antes de revisar nuevamente

"""
Se lanza la función de limpieza automática en un hilo daemon.
Esto permite que se ejecute en paralelo sin bloquear la aplicación principal.
"""
threading.Thread(target=limpiar_archivos_temporales, daemon=True).start()
