from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.gateway_api_toki import router

app = FastAPI(
    title="Gateway Toki Nexum",
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

#3004
app.include_router(router, prefix="/gateway")

