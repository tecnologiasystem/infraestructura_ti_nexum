"""
Importa APIRouter desde FastAPI para agrupar las rutas relacionadas
con la asignación de usuarios a campañas.
"""
from fastapi import APIRouter, HTTPException

"""
Importa funciones desde la capa de lógica de negocio (BLL) para el módulo
de usuariosCampañas. Estas funciones permiten consultar, insertar,
actualizar, eliminar y asignar campañas a usuarios.
"""
from app.bll.usuariosCampanas_bll import (
    obtener_todosbll,   # Lista todas las asignaciones usuario-campaña
    insertarbll,        # Crea una nueva asignación
    actualizarbll,      # Edita una asignación existente
    eliminarbll,        # Elimina una asignación
    asignarbll          # Asigna múltiples campañas a un usuario
)

"""
Importa BaseModel de Pydantic para definir los modelos de entrada de datos
con validación automática.
"""
from pydantic import BaseModel

"""
Instancia del router para el módulo de usuariosCampañas.

Este objeto agrupará todas las rutas que permiten gestionar
la relación entre usuarios y campañas.
"""
router = APIRouter()


"""
Modelo utilizado para crear una nueva relación entre usuario y campaña.

Atributos:
    idUsuarioApp: ID del usuario que se desea asignar.
    idCampana: ID de la campaña a la que se desea asignar el usuario.
"""
class RelacionCreate(BaseModel):
    idUsuarioApp: int
    idCampana: int


"""
Modelo utilizado para actualizar la campaña asignada a un usuario.

Atributos:
    idUsuarioApp: ID del usuario que tiene la asignación.
    idCampanaActual: ID de la campaña actual que se desea reemplazar.
    idCampanaNuevo: ID de la nueva campaña que se asignará.
"""
class RelacionUpdate(BaseModel):
    idUsuarioApp: int
    idCampanaActual: int
    idCampanaNuevo: int


"""
Modelo utilizado para asignar múltiples campañas a un solo usuario.

Atributos:
    idUsuarioApp: ID del usuario que recibirá las asignaciones.
    idCampanas: Lista de IDs de campañas a asignar al usuario (plural).
"""
class AsignarCampanasInput(BaseModel):
    idUsuarioApp: int
    idCampanas: list[int]  # plural, arreglo de IDs



"""
Ruta GET que lista todas las relaciones usuario-campaña registradas en el sistema.
"""
@router.get("/listar")
def listar():
    return obtener_todosbll()


"""
Ruta POST que crea una nueva asignación entre usuario y campaña.
"""
@router.post("/crear")
def crear(rel: RelacionCreate):
    try:
        insertarbll(rel.idUsuarioApp, rel.idCampana)
        return {"mensaje": "Relación creada correctamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


"""
Ruta PUT que actualiza la campaña asignada a un usuario específico.
"""
@router.put("/actualizar")
def actualizar(rel: RelacionUpdate):
    try:
        actualizarbll(rel.idUsuarioApp, rel.idCampanaActual, rel.idCampanaNuevo)
        return {"mensaje": "Relación actualizada correctamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


"""
Ruta DELETE que elimina una relación entre usuario y campaña.
"""
@router.delete("/eliminar")
def eliminar(rel: RelacionCreate):
    try:
        eliminarbll(rel.idUsuarioApp, rel.idCampana)
        return {"mensaje": "Relación eliminada correctamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


"""
Ruta PUT que permite asignar múltiples campañas a un mismo usuario.
"""
@router.put("/asignar")
def asignar(rel: AsignarCampanasInput):
    try:
        asignarbll(rel.idUsuarioApp, rel.idCampanas)
        return {"mensaje": "Campañas asignadas correctamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))