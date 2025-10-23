from fastapi import FastAPI
from app.api import focos_resultado, focos_trabajables

app = FastAPI(
    title="Microservicio Planeacion",
    description="Microservicio para creacion de focos",
    version="1.0.0"
)

# Montamos los routers para las rutas específicas
app.include_router(focos_resultado.router, prefix="/focos/resultado")
app.include_router(focos_trabajables.router, prefix="/focos/trabajable")

@app.get("/")
async def read_root():
    """
    Endpoint raíz para verificar que el microservicio está activo.
    """
    return {"message": "Microservicio Planeacion activo"}
