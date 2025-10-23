"""
Capa de lógica de negocio (BLL) para la gestión de campañas.

Este módulo actúa como puente entre la API y la capa de acceso a datos (DAL),
delegando la ejecución de operaciones relacionadas con campañas.
"""

from app.dal.campanas_dal import (
    obtener_campanas_db,
    crear_campana_db,
    editar_campana_db,
    eliminar_campana_db,
    activar_campana_db
)


"""
Función que lista todas las campañas disponibles en el sistema.

Invoca:
    obtener_campanas_db() desde la capa DAL.

Retorna:
    Lista de campañas.
"""
def listar_campanas():
    return obtener_campanas_db()


"""
Función que crea una nueva campaña.

Parámetros:
    campana: Objeto o diccionario con los datos de la campaña a registrar.

Invoca:
    crear_campana_db(campana) desde la capa DAL.

Retorna:
    Resultado de la operación (puede incluir mensaje de éxito o ID generado).
"""
def crear_campana(campana):
    return crear_campana_db(campana)


"""
Función que edita una campaña existente.

Parámetros:
    campana: Objeto o diccionario con los datos actualizados de la campaña.

Invoca:
    editar_campana_db(campana) desde la capa DAL.

Retorna:
    Resultado de la operación (por ejemplo, True si fue exitosa).
"""
def editar_campana(campana):
    return editar_campana_db(campana)


"""
Función que elimina (o desactiva) una campaña por su ID.

Parámetros:
    id_campana: ID de la campaña a eliminar.

Invoca:
    eliminar_campana_db(id_campana) desde la capa DAL.

Retorna:
    Resultado de la operación.
"""
def eliminar_campana(id_campana):
    return eliminar_campana_db(id_campana)


"""
Función que reactiva una campaña previamente eliminada o desactivada.

Parámetros:
    id_campana: ID de la campaña a reactivar.

Invoca:
    activar_campana_db(id_campana) desde la capa DAL.

Retorna:
    Resultado de la operación.
"""
def activar_campana(id_campana):
    return activar_campana_db(id_campana)

