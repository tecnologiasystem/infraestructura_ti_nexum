from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.gateway_api_rpa import router
#from app.hilos.session_checker import iniciar_hilo_verificador
from api.monitor_rpa import router as monitor_rpa
from fastapi.staticfiles import StaticFiles
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(
    title="Gateway RPA Nexum",
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

#3003

app.include_router(router, prefix="/gateway")
app.include_router(monitor_rpa)

