"""
Capa de lógica de negocio (BLL) para la gestión de asignaciones entre usuarios y campañas.

Este módulo coordina las operaciones necesarias para consultar, asignar,
actualizar o eliminar relaciones entre usuarios y campañas.
"""

from app.dal.usuariosCampanas_dal import (
    obtener_todosdb,
    insertardb,
    actualizardb,
    eliminardb,
    eliminar_todasdb
)


"""
Función que retorna todas las asignaciones existentes entre usuarios y campañas.

Invoca:
    obtener_todosdb() desde la DAL.

Retorna:
    Lista de relaciones usuario-campaña.
"""
def obtener_todosbll():
    return obtener_todosdb()


"""
Función que crea una nueva relación entre un usuario y una campaña.

Parámetros:
    id_usuario: ID del usuario a asignar.
    id_campana: ID de la campaña que se desea asignar al usuario.

Invoca:
    insertardb() desde la DAL.
"""
def insertarbll(id_usuario: int, id_campana: int):
    insertardb(id_usuario, id_campana)


"""
Función que actualiza la campaña asignada a un usuario.

Parámetros:
    id_usuario: ID del usuario.
    id_campana_actual: ID de la campaña que actualmente está asignada.
    id_campana_nuevo: ID de la nueva campaña a asignar.

Invoca:
    actualizardb() desde la DAL.
"""
def actualizarbll(id_usuario: int, id_campana_actual: int, id_campana_nuevo: int):
    actualizardb(id_usuario, id_campana_actual, id_campana_nuevo)


"""
Función que elimina una relación específica entre usuario y campaña.

Parámetros:
    id_usuario: ID del usuario.
    id_campana: ID de la campaña que se desea desvincular del usuario.

Invoca:
    eliminardb() desde la DAL.
"""
def eliminarbll(id_usuario: int, id_campana: int):
    eliminardb(id_usuario, id_campana)


"""
Función que asigna múltiples campañas a un usuario.

Este proceso:
    1. Elimina todas las asignaciones anteriores del usuario.
    2. Inserta las nuevas campañas seleccionadas.

Parámetros:
    id_usuario: ID del usuario.
    id_campanas: Lista de IDs de campañas a asignar.

Invoca:
    eliminar_todasdb() y luego insertardb() para cada campaña.
"""
def asignarbll(id_usuario: int, id_campanas: list[int]):
    # Elimina todas las campañas previas del usuario
    eliminar_todasdb(id_usuario)
    
    # Inserta todas las nuevas campañas
    for id_campana in id_campanas:
        insertardb(id_usuario, id_campana)
