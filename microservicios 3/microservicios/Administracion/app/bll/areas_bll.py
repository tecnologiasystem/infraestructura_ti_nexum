"""
Capa de lógica de negocio (BLL) para la gestión de áreas.

Este módulo actúa como intermediario entre la capa DAL (acceso a datos)
y la capa API, encapsulando la lógica de validación, transformación de datos
y manejo de errores para las operaciones sobre la entidad "área".
"""

from app.dal.areas_dal import (
    obtener_areas,
    crear_area_bd,
    editar_area_bd,
    eliminar_area_bd,
    activar_area_bd
)


"""
Función que lista todas las áreas registradas en la base de datos.

Invoca:
    obtener_areas() desde la capa DAL.

Retorna:
    Diccionario con la clave "areas" y la lista de resultados,
    o un diccionario con la clave "error" si hay excepción.
"""
def listar_areas():
    try:
        return {"areas": obtener_areas()}
    except Exception as e:
        return {"error": str(e)}


"""
Función que crea una nueva área.

Parámetros:
    area: Objeto o diccionario con los datos de la nueva área.

Invoca:
    crear_area_bd(area) desde la capa DAL.

Retorna:
    Resultado de la operación o mensaje de error.
"""
def crear_area(area):
    try:
        return crear_area_bd(area)
    except Exception as e:
        return {"error": str(e)}


"""
Función que edita una área existente.

Parámetros:
    area: Objeto o diccionario con los datos actualizados.

Invoca:
    editar_area_bd(area) desde la capa DAL.

Retorna:
    Resultado de la operación o mensaje de error.
"""
def editar_area(area):
    try:
        return editar_area_bd(area)
    except Exception as e:
        return {"error": str(e)}


"""
Función que elimina (o desactiva) una área.

Parámetros:
    idArea: ID de la área que se desea eliminar.

Invoca:
    eliminar_area_bd(idArea) desde la capa DAL.

Retorna:
    Resultado de la operación o mensaje de error.
"""
def eliminar_area(idArea):
    try:
        return eliminar_area_bd(idArea)
    except Exception as e:
        return {"error": str(e)}


"""
Función que reactiva una área previamente eliminada o desactivada.

Parámetros:
    idArea: ID de la área que se desea reactivar.

Invoca:
    activar_area_bd(idArea) desde la capa DAL.

Retorna:
    Resultado de la operación o mensaje de error.
"""
def activar_area(idArea):
    try:
        return activar_area_bd(idArea)
    except Exception as e:
        return {"error": str(e)}
