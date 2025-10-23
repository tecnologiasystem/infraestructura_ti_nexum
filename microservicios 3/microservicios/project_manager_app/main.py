"""
Este es el archivo principal que inicia la aplicación FastAPI para el sistema de gestión de proyectos.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import project_api

""" Creamos la instancia principal de FastAPI con título y versión. """
app = FastAPI(
    title="Project Manager API",
    version="1.0.0"
)

""" Lista de orígenes permitidos para CORS, evitando problemas al hacer peticiones desde frontend en diferentes dominios. """
origins = [
    "http://localhost:3000",      # Desarrollo local típico React/Next.js
    "http://172.18.73.22:3000",  # IP local o servidor de desarrollo
    # Aquí se pueden agregar más URLs usadas en producción o staging
]

""" Configuramos el middleware CORS para controlar los permisos de acceso desde los orígenes definidos. """
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # Orígenes permitidos para solicitudes
    allow_credentials=True,       # Permite enviar cookies y credenciales
    allow_methods=["*"],          # Permite todos los métodos HTTP (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],          # Permite todos los headers (por ejemplo Authorization, Content-Type)
)

""" Incluimos el router del módulo project_api bajo el prefijo /api/project """
app.include_router(project_api.router, prefix="/api/project")

""" Ruta raíz para verificar que el servicio está activo """
@app.get("/")
def root():
    return {"status": "Project Manager API up and running"}

