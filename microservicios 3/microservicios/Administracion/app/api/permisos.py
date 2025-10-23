"""
Importa APIRouter desde FastAPI para agrupar las rutas relacionadas
con la gestión de permisos en el sistema.
"""
from fastapi import APIRouter, HTTPException, Body, Query

"""
Importa las funciones desde la capa de lógica del negocio (BLL) 
relacionadas con la entidad Permisos. Estas funciones manejan operaciones
como obtener, crear, editar y eliminar permisos de menú.
"""
from app.bll.permisos_bll import (
    obtener_permisos_por_rolBLL,        # Consulta los permisos asignados a un rol específico
    crear_permiso_menuBLL,              # Crea un nuevo permiso de menú
    editar_permiso_menuBLL,             # Modifica un permiso existente
    eliminar_permiso_menuBLL,           # Elimina un permiso del menú
    obtener_permiso_por_idBLL,          # Consulta un permiso específico por ID
    obtener_todos_los_permisosBLL       # Lista todos los permisos existentes
)

"""
Instancia del router para el módulo de permisos.

Este objeto agrupará todas las rutas que gestionan la administración
de accesos y permisos dentro de la aplicación.
"""
router = APIRouter()

 
"""
Ruta GET que obtiene todos los permisos registrados en el sistema.

Invoca la función obtener_todos_los_permisosBLL() desde la capa de negocio,
y retorna la lista completa de permisos disponibles para todos los roles.
"""
@router.get("/permisos")
def get_all_permisos():
    data, error = obtener_todos_los_permisosBLL()
    if error:
        raise HTTPException(status_code=500, detail=error)
    return data


"""
Ruta GET que retorna los permisos asignados a un rol específico.

Parámetros:
    idRol: ID del rol a consultar (requerido por query string).

Invoca la función obtener_permisos_por_rolBLL(idRol), y si hay error
retorna una excepción HTTP 500.
"""
@router.get("/permisos/porRol")
def get_permisos_por_rol(idRol: int = Query(...)):
    data, error = obtener_permisos_por_rolBLL(idRol)
    if error:
        raise HTTPException(status_code=500, detail=error)
    return data


"""
Ruta GET que obtiene un permiso específico por su ID.

Parámetros:
    id: ID numérico del permiso (vía path).

Retorna el detalle del permiso si existe, o error 500 en caso de fallo.
"""
@router.get("/permisos/{id}")
def get_permiso_por_id(id: int):
    data, error = obtener_permiso_por_idBLL(id)
    if error:
        raise HTTPException(status_code=500, detail=error)
    return data


"""
Ruta POST que permite crear un nuevo permiso de menú.

Parámetros:
    data: Diccionario recibido en el cuerpo (Body) de la solicitud,
    con los datos requeridos para crear el permiso.

Retorna:
    {"success": True} si la operación fue exitosa, o error HTTP 500 si falló.
"""
@router.post("/permisos")
def crear_permiso(data: dict = Body(...)):
    ok, error = crear_permiso_menuBLL(data)
    if error:
        raise HTTPException(status_code=500, detail=error)
    return {"success": True}


"""
Ruta PUT que permite editar un permiso existente.

Parámetros:
    id: ID del permiso a editar (vía path).
    data: Diccionario con los nuevos valores a actualizar (en el Body).

Retorna:
    {"success": True} si fue exitoso, o error HTTP 500 en caso contrario.
"""
@router.put("/permisos/{id}")
def editar_permiso(id: int, data: dict = Body(...)):
    ok, error = editar_permiso_menuBLL(id, data)
    if error:
        raise HTTPException(status_code=500, detail=error)
    return {"success": True}


"""
Ruta DELETE que permite eliminar un permiso específico.

Parámetros:
    id: ID del permiso a eliminar (vía path).

Retorna:
    {"success": True} si la eliminación fue exitosa, o error HTTP 500 si falló.
"""
@router.delete("/permisos/{id}")
def eliminar_permiso(id: int):
    ok, error = eliminar_permiso_menuBLL(id)
    if error:
        raise HTTPException(status_code=500, detail=error)
    return {"success": True}
