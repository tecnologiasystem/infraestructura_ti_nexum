from fastapi import FastAPI
from app.api.usuarioxcampana_api import router as usuarioxcampana_api
from app.api.usuarioxrol_api import router as usuarioxrol_api
from app.api.logs_api import router as logs_api

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Microservicio Graficos",
    description="graficos",
    version="1.0.0"
)

"""
Middleware CORS para permitir peticiones cross-origin desde cualquier origen
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las URLs (orígenes)
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos HTTP (GET, POST, PUT, DELETE...)
    allow_headers=["*"],  # Permite todos los headers en las solicitudes
)

"""
Montaje de los routers con sus respectivos prefijos
"""
app.include_router(usuarioxcampana_api)
app.include_router(usuarioxrol_api)
app.include_router(logs_api)




