"""
Capa de lógica de negocio (BLL) para la gestión de usuarios.

Este módulo sirve de puente entre la API y la capa DAL, y permite realizar operaciones como:
- Consultar usuarios.
- Crear nuevos usuarios.
- Editar información de usuarios.
- Eliminar o reactivar usuarios.
"""

from app.dal.usuarios_dal import (
    crearUsuariosbd,
    obtenerUsuariosIDbd,
    obtenerUsuariosbd,
    editarUsuariosbd,
    eliminarUsuariosbd,
    activarUsuariosbd
)


"""
Función que retorna la lista de todos los usuarios registrados.

Invoca:
    obtenerUsuariosbd() desde la DAL.

Retorna:
    Lista de usuarios.
"""
def obtener_usuarios():
    return obtenerUsuariosbd()


"""
Función que obtiene los datos de un usuario específico por su ID.

Parámetros:
    idUsuario: ID del usuario que se desea consultar.

Invoca:
    obtenerUsuariosIDbd(idUsuario) desde la DAL.

Retorna:
    Datos del usuario correspondiente.
"""
def obtener_usuariosID(idUsuario):
    return obtenerUsuariosIDbd(idUsuario)


"""
Función que permite crear un nuevo usuario.

Parámetros:
    usuario: Objeto o diccionario con la información del nuevo usuario.

Invoca:
    crearUsuariosbd(usuario) desde la DAL.

Retorna:
    Resultado de la operación.
"""
def crear_usuario(usuario):
    return crearUsuariosbd(usuario)


"""
Función que permite editar los datos de un usuario existente.

Parámetros:
    usuario: Objeto o diccionario con la información actualizada.

Invoca:
    editarUsuariosbd(usuario) desde la DAL.

Retorna:
    Resultado de la operación.
"""
def editar_usuario(usuario):
    return editarUsuariosbd(usuario)


"""
Función que elimina o desactiva un usuario del sistema.

Parámetros:
    id_usuario: ID del usuario a eliminar.

Invoca:
    eliminarUsuariosbd(id_usuario) desde la DAL.

Retorna:
    Resultado de la operación.
"""
def eliminar_usuario(id_usuario):
    return eliminarUsuariosbd(id_usuario)


"""
Función que reactiva un usuario previamente eliminado o inactivo.

Parámetros:
    id_usuario: ID del usuario a reactivar.

Invoca:
    activarUsuariosbd(id_usuario) desde la DAL.

Retorna:
    Resultado de la operación.
"""
def activar_usuario(id_usuario):
    return activarUsuariosbd(id_usuario)
