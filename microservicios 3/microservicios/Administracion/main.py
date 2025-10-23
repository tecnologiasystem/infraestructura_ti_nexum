from fastapi import FastAPI
from app.api import usuarios, campanas, areas, roles, usuariosCampanas, permisos, logs

"""
Inicializa la instancia principal de la aplicación FastAPI.

Se define la metadata del microservicio:
- title: Título visible en la documentación Swagger.
- description: Descripción general del microservicio.
- version: Versión actual del servicio.
"""
app = FastAPI(
    title="Microservicio Administración",
    description="Microservicio para administrar usuarios, campañas, áreas y roles",
    version="1.0.0"
)



"""
Se agregan los distintos routers del sistema.

Cada uno tiene un prefijo de ruta para agrupar endpoints por módulo:
- /usuarios
- /campanas
- /areas
- /roles
- /usuariosCampanas
- /permisos
- /logs
"""
app.include_router(usuarios.router, prefix="/usuarios")
app.include_router(campanas.router, prefix="/campanas")
app.include_router(areas.router, prefix="/areas")
app.include_router(roles.router, prefix="/roles")
app.include_router(usuariosCampanas.router, prefix="/usuariosCampanas")
app.include_router(permisos.router, prefix="/permisos")
app.include_router(logs.router, prefix="/logs")



"""
Ruta raíz de prueba para verificar que el microservicio está activo.
"""
@app.get("/")
async def read_root():
    return {"message": "Microservicio Administración activo"}
