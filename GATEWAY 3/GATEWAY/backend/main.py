from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.gateway_api import router
#from app.hilos.session_checker import iniciar_hilo_verificador
from app.api.monitor_rpa import router as monitor_rpa
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio
from app.bll.monitor_rpa_bll import verificar_inactividad
from app.api.parametros_api import router as parametro_router
from app.api.gateway_rpa_api import router as gateway_rpa

app = FastAPI(
    title="Gateway Nexum",
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



app.include_router(router, prefix="/gateway")
app.include_router(monitor_rpa)
app.include_router(parametro_router, prefix="/parametro")
app.include_router(gateway_rpa, prefix="/gateway-rpa")

scheduler = BackgroundScheduler()
scheduler.add_job(lambda: asyncio.run(verificar_inactividad()), "interval", minutes=10)
scheduler.start()