from fastapi import FastAPI
from app.ImpulsoProcesal.api import procesal_api
from app.Vigilancia.api import vigilancia_api
from app.SuperNotariado.api import superNotariado_api
from app.Simit.api import simit_api
from app.Runt.api import runt_api
from app.Rues.api import rues_api
from app.Tyba.api import tyba_api
from app.CamaraComercio.api import camaraComercio_api
from app.api import juridica_api
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
app.include_router(procesal_api.router, prefix="/impulsoProcesal")
app.include_router(vigilancia_api.router, prefix="/vigilancia_api")
app.include_router(superNotariado_api.router, prefix="/superNotariado_api")
app.include_router(runt_api.router, prefix="/runt_api")
app.include_router(rues_api.router, prefix="/rues_api")
app.include_router(juridica_api.router, prefix="/juridica_api")
app.include_router(simit_api.router, prefix="/simit_api")
app.include_router(camaraComercio_api.router, prefix="/camaraComercio_api")
app.include_router(tyba_api.router, prefix="/tyba_api")

"""
Ruta raíz simple para verificar que el microservicio está activo
"""
@app.get("/")
async def read_root():
    return {"message": "Microservicio Juridica activo"}
