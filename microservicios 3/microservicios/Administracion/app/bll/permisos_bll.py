"""
Capa de lógica de negocio (BLL) para la gestión de permisos de menú.

Este módulo actúa como intermediario entre la API y la capa DAL,
delegando las operaciones relacionadas con la consulta, creación,
edición, eliminación y lectura de permisos.
"""

from app.dal.permisos_dal import (
    obtener_permisos_por_rolDAL,
    crear_permiso_menuDAL,
    editar_permiso_menuDAL,
    eliminar_permiso_menuDAL,
    obtener_permiso_por_idDAL,
    obtener_todos_los_permisosDAL,
)


"""
Función que obtiene todos los permisos asignados a un rol específico.

Parámetros:
    idRol: ID del rol que se desea consultar.

Retorna:
    Lista de permisos asociados a ese rol.
"""
def obtener_permisos_por_rolBLL(idRol: int):
    return obtener_permisos_por_rolDAL(idRol)


"""
Función que crea un nuevo permiso de menú.

Parámetros:
    data: Diccionario con los datos necesarios para registrar el permiso.

Retorna:
    Resultado de la operación desde la DAL.
"""
def crear_permiso_menuBLL(data: dict):
    return crear_permiso_menuDAL(data)


"""
Función que edita un permiso de menú existente.

Parámetros:
    id: ID del permiso a modificar.
    data: Diccionario con los nuevos datos del permiso.

Retorna:
    Resultado de la operación desde la DAL.
"""
def editar_permiso_menuBLL(id: int, data: dict):
    return editar_permiso_menuDAL(id, data)


"""
Función que elimina un permiso de menú por su ID.

Parámetros:
    id: ID del permiso que se desea eliminar.

Retorna:
    Resultado de la operación desde la DAL.
"""
def eliminar_permiso_menuBLL(id: int):
    return eliminar_permiso_menuDAL(id)


"""
Función que consulta un permiso específico por su ID.

Parámetros:
    id: ID del permiso a consultar.

Retorna:
    Detalle del permiso si existe.
"""
def obtener_permiso_por_idBLL(id: int):
    return obtener_permiso_por_idDAL(id)


"""
Función que retorna todos los permisos del sistema.

Invoca:
    obtener_todos_los_permisosDAL() desde la capa DAL.

Retorna:
    Lista completa de permisos registrados.
"""
def obtener_todos_los_permisosBLL():
    return obtener_todos_los_permisosDAL()
