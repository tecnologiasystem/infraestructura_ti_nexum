from fastapi import FastAPI
from app.api.contacto_api import router as contacto_router
from fastapi.middleware.cors import CORSMiddleware

"""
Instancia principal de la aplicación FastAPI.
Aquí es donde se define toda la configuración central del microservicio.
"""
app = FastAPI()

"""
Configuración del middleware CORS (Cross-Origin Resource Sharing).
Esto permite que otros dominios puedan hacer peticiones a este backend (por ejemplo, desde el frontend en otro servidor).

Parámetros:
- allow_origins=["*"]: Permite todas las URLs de origen (útil para desarrollo; en producción es mejor restringirlo).
- allow_credentials=True: Permite el uso de cookies o headers de autenticación.
- allow_methods=["*"]: Permite todos los métodos HTTP (GET, POST, PUT, DELETE, etc.).
- allow_headers=["*"]: Permite cualquier header en las solicitudes.
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""
Se incluye el router de contacto_api.
Esto carga todas las rutas definidas en ese módulo y las expone en la API principal.
"""
app.include_router(contacto_router)
