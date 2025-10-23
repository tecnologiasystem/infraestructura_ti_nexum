import pyodbc
from app.config.database import get_connection

"""
Importa pyodbc para conectarse a SQL Server
y la función `get_connection` desde la capa de configuración.

Este módulo contiene funciones para gestionar la relación entre usuarios y campañas.
"""



"""
Función: obtener_todosdb

Obtiene todas las relaciones entre usuarios y campañas registradas en la base de datos.

Ejecuta:
    EXEC sp_CRUD_UsuariosCampanas @accion = 1

Retorna:
    Lista de diccionarios con las relaciones encontradas.
"""
def obtener_todosdb():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_CRUD_UsuariosCampanas @accion = 1")
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    finally:
        conn.close()



"""
Función: insertardb

Inserta una nueva relación entre un usuario y una campaña.

Parámetros:
    id_usuario (int): ID del usuario.
    id_campana (int): ID de la campaña.

Ejecuta:
    EXEC sp_CRUD_UsuariosCampanas @accion = 2
"""
def insertardb(id_usuario: int, id_campana: int):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "EXEC sp_CRUD_UsuariosCampanas @accion = 2, @idUsuarioApp = ?, @idCampana = ?",
            (id_usuario, id_campana)
        )
        conn.commit()
    finally:
        conn.close()



"""
Función: actualizardb

Actualiza la campaña asignada a un usuario.

Parámetros:
    id_usuario (int): ID del usuario.
    id_campana_actual (int): Campaña actual asignada.
    id_campana_nuevo (int): Nueva campaña a asignar.

Ejecuta:
    EXEC sp_CRUD_UsuariosCampanas @accion = 3
"""
def actualizardb(id_usuario: int, id_campana_actual: int, id_campana_nuevo: int):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "EXEC sp_CRUD_UsuariosCampanas @accion = 3, @idUsuarioApp = ?, @idCampana = ?, @idCampanaNuevo = ?",
            (id_usuario, id_campana_actual, id_campana_nuevo)
        )
        conn.commit()
    finally:
        conn.close()



"""
Función: eliminardb

Elimina una relación específica entre un usuario y una campaña.

Parámetros:
    id_usuario (int): ID del usuario.
    id_campana (int): ID de la campaña.

Ejecuta:
    EXEC sp_CRUD_UsuariosCampanas @accion = 4
"""
def eliminardb(id_usuario: int, id_campana: int):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "EXEC sp_CRUD_UsuariosCampanas @accion = 4, @idUsuarioApp = ?, @idCampana = ?",
            (id_usuario, id_campana)
        )
        conn.commit()
    finally:
        conn.close()



"""
Función: eliminar_todasdb

Elimina todas las campañas asociadas a un usuario.

Parámetros:
    id_usuario (int): ID del usuario.

Ejecuta:
    EXEC sp_crud_usuariosCampanas @accion = 99
"""
def eliminar_todasdb(id_usuario: int):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "EXEC sp_crud_usuariosCampanas @accion = 99, @idUsuarioApp = ?",
            (id_usuario,)
        )
        conn.commit()
    finally:
        conn.close()

