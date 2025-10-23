"""
Capa de lógica de negocio (BLL) para la gestión de roles.

Este módulo actúa como intermediario entre la API y la capa DAL (acceso a datos),
encargándose de orquestar las operaciones de consulta, creación, edición,
eliminación y activación de roles dentro del sistema.
"""

from app.dal.roles_dal import (
    obtener_roles_db,
    crear_rol_db,
    editar_rol_db,
    eliminar_rol_db,
    activar_rol_db
)


"""
Función que lista todos los roles registrados en el sistema.

Invoca:
    obtener_roles_db() desde la capa DAL.

Retorna:
    Diccionario con la clave "roles" que contiene la lista completa.
"""
def listar_roles():
    return {"roles": obtener_roles_db()}


"""
Función que crea un nuevo rol.

Parámetros:
    rol: Objeto o diccionario con los datos del nuevo rol (por ejemplo, nombre).

Invoca:
    crear_rol_db(rol) desde la capa DAL.

Retorna:
    Resultado de la operación.
"""
def crear_rol(rol):
    return crear_rol_db(rol)


"""
Función que edita un rol existente.

Parámetros:
    rol: Objeto o diccionario con los datos actualizados del rol.

Invoca:
    editar_rol_db(rol) desde la capa DAL.

Retorna:
    Resultado de la operación.
"""
def editar_rol(rol):
    return editar_rol_db(rol)


"""
Función que elimina (o desactiva) un rol específico.

Parámetros:
    idRol: ID del rol que se desea eliminar.

Invoca:
    eliminar_rol_db(idRol) desde la capa DAL.

Retorna:
    Resultado de la operación.
"""
def eliminar_rol(idRol):
    return eliminar_rol_db(idRol)


"""
Función que reactiva un rol previamente eliminado o desactivado.

Parámetros:
    idRol: ID del rol que se desea volver a activar.

Invoca:
    activar_rol_db(idRol) desde la capa DAL.

Retorna:
    Resultado de la operación.
"""
def activar_rol(idRol):
    return activar_rol_db(idRol)

