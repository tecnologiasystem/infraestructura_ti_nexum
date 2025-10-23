# app/main.py

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from API.embudo_api import router as contacto_router

"""Crear la instancia principal de la aplicación FastAPI"""
app = FastAPI(
    title="Contactabilidad API",
    description="Importación de llamadas y obtención de embudo de contactabilidad",
    version="1.0.0"
)

"""Configuración de CORS para permitir peticiones desde el frontend"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,                   # Permitir envío de cookies y credenciales
    allow_methods=["*"],                       # Permitir todos los métodos HTTP (GET, POST, etc.)
    allow_headers=["*"],                       # Permitir todos los encabezados HTTP
)

""" Montar el router con los endpoints definidos en embudo_api
Todos los endpoints quedarán accesibles con prefijo /Emb"""
app.include_router(contacto_router, prefix="/Emb", tags=["EMBUDO"])

"""Punto de entrada para ejecutar el servidor directamente con `python app/main.py`"""
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",    # Path a la aplicación (ajusta si tu estructura es diferente)
        host="0.0.0.0",    # Escuchar en todas las interfaces de red
        port=8019,         # Puerto para la API
        reload=True        # Recarga automática al cambiar código (solo para desarrollo)
    )
