from app.config.database import get_connection

"""
Importa la función de conexión a la base de datos principal.

Esta conexión es utilizada para ejecutar procedimientos almacenados relacionados con la gestión
de permisos de menú asociados a roles.
"""



"""
Función: obtener_permisos_por_rolDAL

Obtiene los permisos de menú asociados a un rol específico.

Parámetros:
    idRol (int): ID del rol.

Ejecuta:
    EXEC SP_CRUD_PERMISOS_MENU con acción 5 (consultar permisos por rol)

Retorna:
    - Lista de permisos si fue exitoso.
    - None y mensaje de error si ocurre una excepción.
"""
def obtener_permisos_por_rolDAL(idRol: int):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("EXEC SP_CRUD_PERMISOS_MENU @accion=?, @idRol=?", 5, idRol)
        columns = [col[0] for col in cursor.description]
        permisos = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return permisos, None
    except Exception as e:
        return None, str(e)



"""
Función: crear_permiso_menuDAL

Crea un nuevo permiso de menú utilizando los datos proporcionados.

Parámetros:
    data (dict): Diccionario con la información del permiso (ruta, idRol, descripción, etc.).

Ejecuta:
    EXEC SP_CRUD_PERMISOS_MENU con acción 2 (INSERT)

Retorna:
    - True si fue exitoso.
    - None y mensaje de error si falla.
"""
def crear_permiso_menuDAL(data: dict):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            EXEC SP_CRUD_PERMISOS_MENU @accion=?, @ruta=?, @idRol=?, @descripcion=?, @detalle=?, 
            @permisoVer=?, @permisoCrear=?, @permisoEditar=?, @permisoEliminar=?, @estado=?
        """, 2, data["ruta"], data["idRol"], data["descripcion"], data.get("detalle", ""),
             data["permisoVer"], data["permisoCrear"], data["permisoEditar"], data["permisoEliminar"], 1)
        conn.commit()
        return True, None
    except Exception as e:
        return None, str(e)



"""
Función: editar_permiso_menuDAL

Edita un permiso de menú existente con el ID dado y nuevos datos.

Parámetros:
    id (int): ID del permiso a editar.
    data (dict): Diccionario con la nueva información del permiso.

Ejecuta:
    EXEC SP_CRUD_PERMISOS_MENU con acción 3 (UPDATE)

Retorna:
    - True si fue exitoso.
    - None y mensaje de error si ocurre un fallo.
"""
def editar_permiso_menuDAL(id: int, data: dict):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            EXEC SP_CRUD_PERMISOS_MENU @accion=?, @id=?, @ruta=?, @idRol=?, @descripcion=?, @detalle=?, 
            @permisoVer=?, @permisoCrear=?, @permisoEditar=?, @permisoEliminar=?
        """, 3, id, data["ruta"], data["idRol"], data["descripcion"], data.get("detalle", ""),
             data["permisoVer"], data["permisoCrear"], data["permisoEditar"], data["permisoEliminar"])
        conn.commit()
        return True, None
    except Exception as e:
        return None, str(e)



"""
Función: eliminar_permiso_menuDAL

Elimina un permiso de menú con el ID especificado.

Parámetros:
    id (int): ID del permiso a eliminar.

Ejecuta:
    EXEC SP_CRUD_PERMISOS_MENU con acción 4 (DELETE)

Retorna:
    - True si se eliminó correctamente.
    - None y mensaje de error si hubo un problema.
"""
def eliminar_permiso_menuDAL(id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("EXEC SP_CRUD_PERMISOS_MENU @accion=?, @id=?", 4, id)
        conn.commit()
        return True, None
    except Exception as e:
        return None, str(e)



"""
Función: obtener_permiso_por_idDAL

Obtiene los datos de un permiso de menú por su ID.

Parámetros:
    id (int): ID del permiso.

Ejecuta:
    EXEC SP_CRUD_PERMISOS_MENU con acción 6 (SELECT por ID)

Retorna:
    - Diccionario con los datos del permiso.
    - None y mensaje de error si falla.
"""
def obtener_permiso_por_idDAL(id: int):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("EXEC SP_CRUD_PERMISOS_MENU @accion=?, @id=?", 6, id)
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return data[0] if data else None, None
    except Exception as e:
        return None, str(e)



"""
Función: obtener_todos_los_permisosDAL

Obtiene todos los permisos de menú registrados en el sistema.

Ejecuta:
    EXEC SP_CRUD_PERMISOS_MENU con acción 1 (SELECT general)

Retorna:
    - Lista de permisos si fue exitoso.
    - None y mensaje de error si ocurre una excepción.
"""
def obtener_todos_los_permisosDAL():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("EXEC SP_CRUD_PERMISOS_MENU @accion=?", 1)
        columns = [col[0] for col in cursor.description]
        permisos = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return permisos, None
    except Exception as e:
        return None, str(e)

