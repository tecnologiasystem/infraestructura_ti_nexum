from app.dal.gateway_dal import crud_permisos_menuDAL

"""
Función: obtener_permisos_por_usuarioBLL

Descripción:
Obtiene todos los permisos asociados a un usuario específico a través de su ID de aplicación.

Parámetros:
    idUsuarioApp (int): Identificador del usuario.

Retorna:
    list: Lista de permisos del usuario.
"""
def obtener_permisos_por_usuarioBLL(idUsuarioApp):
    return crud_permisos_menuDAL(accion=4, idUsuarioApp=idUsuarioApp)
"""
Función: obtener_permisos_por_rolBLL

Descripción:
Consulta todos los permisos asignados a un rol específico.

Parámetros:
    idRol (int): Identificador del rol.

Retorna:
    list: Lista de permisos asociados al rol.
"""
def obtener_permisos_por_rolBLL(idRol):
    return crud_permisos_menuDAL(accion=5, idRol=idRol)
"""
Función: obtener_todos_los_permisosBLL

Descripción:
Obtiene todos los permisos disponibles en el sistema sin filtros.

Parámetros:
    Ninguno.

Retorna:
    list: Lista de todos los permisos registrados.
"""
def obtener_todos_los_permisosBLL():
    return crud_permisos_menuDAL(accion=1)
"""
Función: obtener_permiso_por_idBLL

Descripción:
Consulta la información de un permiso específico a partir de su ID.

Parámetros:
    id (int): Identificador del permiso.

Retorna:
    dict: Detalles del permiso.
"""
def obtener_permiso_por_idBLL(id):
    return crud_permisos_menuDAL(accion=6, id=id)
"""
Función: crear_permiso_menuBLL

Descripción:
Crea un nuevo permiso de menú en el sistema con los datos proporcionados.

Parámetros:
    data (dict): Diccionario con los campos requeridos para crear el permiso.

Retorna:
    dict: Resultado de la operación de creación.
"""
def crear_permiso_menuBLL(data):
    return crud_permisos_menuDAL(
        accion=2,
        ruta=data.get("ruta"),
        idRol=data.get("idRol"),
        descripcion=data.get("descripcion"),
        detalle=data.get("detalle"),
        permisoVer=data.get("permisoVer"),
        permisoCrear=data.get("permisoCrear"),
        permisoEditar=data.get("permisoEditar"),
        permisoEliminar=data.get("permisoEliminar"),
        estado=1
    )
"""
Función: editar_permiso_menuBLL

Descripción:
Edita los datos de un permiso de menú existente.

Parámetros:
    id (int): ID del permiso a editar.
    data (dict): Diccionario con los nuevos valores para el permiso.

Retorna:
    dict: Resultado de la operación de edición.
"""
def editar_permiso_menuBLL(id, data):
    # Elimina el id duplicado del payload si existe
    data.pop("id", None)
    return crud_permisos_menuDAL(
        accion=3,
        id=id,
        ruta=data.get("ruta"),
        idRol=data.get("idRol"),
        descripcion=data.get("descripcion"),
        detalle=data.get("detalle"),
        permisoVer=data.get("permisoVer"),
        permisoCrear=data.get("permisoCrear"),
        permisoEditar=data.get("permisoEditar"),
        permisoEliminar=data.get("permisoEliminar")
    )
"""
Función: eliminar_permiso_menuBLL

Descripción:
Elimina un permiso del sistema utilizando su identificador.

Parámetros:
    id (int): ID del permiso a eliminar.

Retorna:
    dict: Resultado de la operación de eliminación.
"""
def eliminar_permiso_menuBLL(id):
    return crud_permisos_menuDAL(accion=4, id=id)
