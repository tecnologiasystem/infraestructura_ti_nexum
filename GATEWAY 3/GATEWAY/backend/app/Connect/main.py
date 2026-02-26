from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.gateway_api_connect import router
#from app.hilos.session_checker import iniciar_hilo_verificador
from api.monitor_rpa import router as monitor_rpa
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
from bll.monitor_rpa_bll import verificar_inactividad

app = FastAPI(
    title="Gateway Connect Nexum",
    description="API Gateway que redirige peticiones a microservicios",
    version="1.0.0"
)

# 🔥 Permitir CORS mientras pruebas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#3002

app.include_router(router, prefix="/gateway")
app.include_router(monitor_rpa)

scheduler = BackgroundScheduler()
scheduler.add_job(lambda: asyncio.run(verificar_inactividad()), "interval", minutes=10)
scheduler.start()