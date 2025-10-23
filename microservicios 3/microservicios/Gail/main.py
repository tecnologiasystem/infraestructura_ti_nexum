from fastapi import FastAPI
from app.api.gail_api import router as gail_router
from app.api.datosGail_api import router as datosGail_router
from fastapi.middleware.cors import CORSMiddleware

"""
🎯 Punto de entrada principal para la aplicación FastAPI.

- Se configura la instancia principal de FastAPI.
- Se agrega el middleware de CORS para permitir peticiones desde cualquier origen.
- Se incluyen los routers de los módulos GAIL y datosGAIL.
"""

# 🚀 Instancia principal de la aplicación FastAPI
app = FastAPI()

"""
🛡️ Middleware de CORS (Cross-Origin Resource Sharing)
Permite que cualquier dominio haga peticiones a la API, lo cual es útil para desarrollo,
pero en producción deberías restringir los orígenes permitidos.
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔓 Permite todos los orígenes (en producción, usar una lista específica)
    allow_credentials=True,
    allow_methods=["*"],  # 🔁 Permite todos los métodos HTTP: GET, POST, etc.
    allow_headers=["*"],  # 📄 Permite todos los headers
)

"""
🧩 Inclusión de routers de los módulos:
- `gail_router`: contiene los endpoints relacionados con campañas GAIL.
- `datosGail_router`: contiene endpoints para sincronizar datos desde Lula hacia GAIL.
"""
app.include_router(gail_router)
app.include_router(datosGail_router)
