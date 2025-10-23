""" 
Importa el enrutador principal de FastAPI, que permite agrupar rutas relacionadas
en un solo objeto (por ejemplo, para rutas del módulo de áreas).
"""
from fastapi import APIRouter

"""
Importa BaseModel de Pydantic, que se usa para definir los esquemas de entrada y salida
de datos, con validaciones automáticas para las solicitudes entrantes.
"""
from pydantic import BaseModel

"""
Se importan las funciones de la capa lógica del negocio (BLL), que contienen
la lógica para gestionar las áreas, como listar, crear, editar, eliminar o activar.
"""
from app.bll.areas_bll import (listar_areas,crear_area,editar_area,eliminar_area,activar_area)

"""
Se instancia el objeto router que se encargará de manejar todas las rutas
relacionadas con el módulo de áreas dentro del sistema.
"""
router = APIRouter()

"""
Modelo de datos para el objeto Área.

Este modelo representa la estructura que se espera enviar o recibir
al trabajar con áreas en la API, ya sea para crear, editar o consultar.

Atributos:
    idArea: Identificador único del área (puede ser nulo al crear una nueva).
    nombreArea: Nombre o descripción del área.
"""
class Area(BaseModel):
    idArea: int = None
    nombreArea: str = None


"""
Endpoint GET que retorna la lista completa de áreas registradas.

Este método invoca la función listar_areas() de la capa BLL, 
que consulta todas las áreas activas (o todas según lógica definida en BLL).
"""
@router.get("/dar")
async def dar_areas():
    return listar_areas()


"""
Endpoint POST que permite crear una nueva área.

Recibe un objeto tipo Area con los datos necesarios para registrar 
una nueva área en la base de datos.
"""
@router.post("/crear")
async def crear(area: Area):
    return crear_area(area)


"""
Endpoint PUT que permite editar los datos de un área existente.

Recibe un objeto tipo Area con el id del área a modificar y los nuevos datos.
"""
@router.put("/editar")
async def editar(area: Area):
    return editar_area(area)


"""
Endpoint PUT que permite eliminar o desactivar un área existente.

Recibe un objeto tipo Area, pero solo utiliza el campo idArea
para identificar el registro a eliminar.
"""
@router.put("/eliminar")
async def eliminar(area: Area):
    return eliminar_area(area.idArea)


"""
Endpoint PUT que permite reactivar un área que fue previamente desactivada.

Recibe un objeto tipo Area, usando únicamente el idArea para reactivarla.
"""
@router.put("/activar")
async def activar(area: Area):
    return activar_area(area.idArea)
