from app.config.database import get_connection

"""
Importa la función de conexión a la base de datos principal.

Esta conexión será utilizada por cada función para ejecutar el procedimiento 
almacenado relacionado con la gestión de roles.
"""



"""
Función: obtener_roles_db

Obtiene todos los roles existentes desde la base de datos.

Ejecuta:
    EXEC sp_crud_roles @operacion = 1

Retorna:
    Lista de roles en formato de diccionario con id, nombre y estado.
"""
def obtener_roles_db():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_crud_roles @operacion = 1")
        roles = cursor.fetchall()
        return [{"idRol": r[0], "rol": r[1], "activo": r[2]} for r in roles]
    finally:
        conn.close()



"""
Función: crear_rol_db

Crea un nuevo rol en la base de datos.

Parámetros:
    rol: Objeto con el atributo 'rol' (nombre del rol).

Ejecuta:
    EXEC sp_crud_roles @operacion = 2, @rol = ?

Retorna:
    Mensaje de éxito.
"""
def crear_rol_db(rol):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_crud_roles @operacion = 2, @rol = ?", (rol.rol,))
        conn.commit()
        return {"mensaje": "Rol creado exitosamente"}
    finally:
        conn.close()



"""
Función: editar_rol_db

Edita un rol existente en la base de datos.

Parámetros:
    rol: Objeto con 'idRol' y 'rol' (nombre nuevo).

Ejecuta:
    EXEC sp_crud_roles @operacion = 3, @idRol = ?, @rol = ?

Retorna:
    Mensaje de éxito.
"""
def editar_rol_db(rol):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_crud_roles @operacion = 3, @idRol = ?, @rol = ?", (rol.idRol, rol.rol))
        conn.commit()
        return {"mensaje": "Rol actualizado exitosamente"}
    finally:
        conn.close()



"""
Función: eliminar_rol_db

Desactiva (elimina lógicamente) un rol en la base de datos.

Parámetros:
    idRol: ID del rol a desactivar.

Ejecuta:
    EXEC sp_crud_roles @operacion = 4, @idRol = ?

Retorna:
    Mensaje de éxito.
"""
def eliminar_rol_db(idRol):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_crud_roles @operacion = 4, @idRol = ?", (idRol,))
        conn.commit()
        return {"mensaje": "Rol desactivado exitosamente"}
    finally:
        conn.close()



"""
Función: activar_rol_db

Activa un rol previamente desactivado en la base de datos.

Parámetros:
    idRol: ID del rol a activar.

Ejecuta:
    EXEC sp_crud_roles @operacion = 5, @idRol = ?

Retorna:
    Mensaje de éxito.
"""
def activar_rol_db(idRol):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_crud_roles @operacion = 5, @idRol = ?", (idRol,))
        conn.commit()
        return {"mensaje": "Rol activado exitosamente"}
    finally:
        conn.close()

