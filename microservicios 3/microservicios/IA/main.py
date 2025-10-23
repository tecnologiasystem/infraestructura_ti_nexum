from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.digital_api import router as digital_router
from app.api.contactabilidad_api import router as contactabilidad_router

"""
Importación de módulos principales:
- FastAPI: framework ligero para construcción de APIs REST.
- CORSMiddleware: middleware que permite controlar las políticas de acceso entre dominios (CORS).
- Routers:
  - digital_api: contiene las rutas relacionadas con el procesamiento de hojas de vida (carga y análisis).
  - contactabilidad_api: contiene las rutas que manejan la lógica de predicción de contactabilidad.
"""

app = FastAPI()

"""
Instancia principal de la aplicación FastAPI.
Desde aquí se definen los middlewares, rutas y configuración general de la API.
"""

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    
)

"""
Se incluyen las rutas (routers) que encapsulan la lógica separada por módulos.
Esto mantiene la aplicación organizada y escalable.
"""

app.include_router(digital_router)
"""
Incluye el router del módulo digital, que maneja la carga de hojas de vida,
extracción de texto y almacenamiento de información relevante en base de datos.
"""

app.include_router(contactabilidad_router)
"""
Incluye el router del módulo de contactabilidad, responsable de procesar datos históricos
de llamadas y aplicar modelos predictivos para sugerir mejores horarios de contacto.
"""
