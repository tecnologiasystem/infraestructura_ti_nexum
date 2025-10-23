"""
Importa el enrutador principal de FastAPI para definir las rutas relacionadas
con la gestión de campañas. Cada grupo de rutas se agrupa usando APIRouter.
"""
from fastapi import APIRouter

"""
Importa BaseModel desde Pydantic, utilizado para validar y estructurar
los datos de entrada/salida en la API.
"""
from pydantic import BaseModel

"""
Importa las funciones de la capa de lógica de negocio (BLL) para la entidad Campaña.
Estas funciones manejan operaciones como listar, crear, editar, eliminar o activar campañas.
"""
from app.bll.campanas_bll import (
    listar_campanas,
    crear_campana,
    editar_campana,
    eliminar_campana,
    activar_campana
)

"""
Instancia del router para el módulo de campañas. Este objeto se utilizará
para registrar las rutas relacionadas con campañas dentro de la aplicación.
"""
router = APIRouter()

"""
Modelo de datos para representar una campaña.

Atributos:
    idCampana: Identificador único de la campaña (opcional, usado en edición/eliminación).
    descripcionCampana: Nombre o descripción asignada a la campaña.
"""
class Campana(BaseModel):
    idCampana: int = None
    descripcionCampana: str = None

"""
Endpoint GET que retorna la lista de campañas registradas.

Invoca la función listar_campanas() desde la capa de negocio,
que consulta y devuelve todas las campañas (según el estado definido en BLL).
"""
@router.get("/dar")
async def listar():
    return listar_campanas()


"""
Endpoint POST que permite crear una nueva campaña.

Recibe un objeto Campana con la descripción necesaria para registrar una campaña nueva.
"""
@router.post("/crear")
async def crear(campana: Campana):
    return crear_campana(campana)


"""
Endpoint PUT que permite editar una campaña existente.

Recibe un objeto Campana con el ID y la nueva descripción para actualizar los datos.
"""
@router.put("/editar")
async def editar(campana: Campana):
    return editar_campana(campana)


"""
Endpoint PUT que permite eliminar (o desactivar) una campaña específica.

Recibe un objeto Campana y utiliza únicamente el idCampana para identificar qué campaña eliminar.
"""
@router.put("/eliminar")
async def eliminar(campana: Campana):
    return eliminar_campana(campana.idCampana)


"""
Endpoint PUT que permite reactivar una campaña previamente eliminada o desactivada.

Recibe un objeto Campana y usa el idCampana para volver a activarla.
"""
@router.put("/activar")
async def activar(campana: Campana):
    return activar_campana(campana.idCampana)

