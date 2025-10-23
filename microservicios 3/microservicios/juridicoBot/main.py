from fastapi import FastAPI
from app.api.juridicoBot_api import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Microservicio Juridica",
    description="juridica",
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
app.include_router(router, prefix="/juridicoBot_api")

"""
Ruta raíz simple para verificar que el microservicio está activo
"""
@app.get("/")
async def read_root():
    return {"message": "Microservicio Juridica activo"}
