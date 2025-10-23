import threading
import time
from datetime import datetime
from app.dal.gateway_dal import cerrar_sesiones_expiradas

def verificar_sesiones_activas():
    while True:
        try:
            print("🕵️ Revisando sesiones activas...")
            cerrar_sesiones_expiradas()
        except Exception as e:
            print(f"❌ Error al cerrar sesiones: {e}")
        time.sleep(60)  # Revisión cada 60 segundos

def iniciar_hilo_verificador():
    hilo = threading.Thread(target=verificar_sesiones_activas, daemon=True)
    hilo.start()
