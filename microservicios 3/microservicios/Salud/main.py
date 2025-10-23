from fastapi import FastAPI
from app.api.famisanar_api import router as famisanar_router
from app.api.nuevaEps_api import router as nuevaeps_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Microservicio Salud",
    description="juridica",
    version="1.0.0"
)

""" 
Agrega middleware CORS para permitir que el frontend realice peticiones a esta API sin restricciones de origen. 
Esto es especialmente útil durante el desarrollo cuando frontend y backend corren en dominios diferentes.
Parámetros:
- allow_origins=["*"]: Permite solicitudes desde cualquier origen (ideal en desarrollo, cuidado en producción).
- allow_credentials=True: Permite enviar cookies y credenciales.
- allow_methods=["*"]: Permite todos los métodos HTTP (GET, POST, PUT, DELETE, etc).
- allow_headers=["*"]: Permite todos los headers HTTP.
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""
Incluye los routers de los módulos 'famisanar' y 'nuevaeps'.
Cada router agrupa las rutas relacionadas y se monta con un prefijo para evitar conflictos
y mantener orden en la estructura de la API.

- famisanar_router: Maneja rutas bajo /famisanar_api
- nuevaeps_router: Maneja rutas bajo /nuevaeps_api
"""
app.include_router(famisanar_router, prefix="/famisanar_api")
app.include_router(nuevaeps_router, prefix="/nuevaeps_api")

"""
Ruta raíz ("/") para verificar que el microservicio está activo.
Devuelve un mensaje simple confirmando el estado del servicio.
"""
@app.get("/")
async def read_root():
    return {"message": "Microservicio Salud activo"}
