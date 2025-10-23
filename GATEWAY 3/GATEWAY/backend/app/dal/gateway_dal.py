from config.db_config import get_connection, get_connection2

"""
Función: crud_permisos_menuDAL

Descripción:
Función de acceso a datos que ejecuta el procedimiento almacenado SP_CRUD_PERMISOS_MENU.
Permite realizar operaciones CRUD (Crear, Leer, Actualizar, Eliminar) sobre los permisos de menú.

Parámetros:
    accion (int): Acción a ejecutar en el procedimiento almacenado.
    id (int, opcional): ID del permiso.
    idRol (int, opcional): ID del rol al que pertenece el permiso.
    ruta (str, opcional): Ruta del menú.
    descripcion (str, opcional): Descripción del permiso.
    detalle (str, opcional): Detalles adicionales del permiso.
    estado (int, opcional): Estado del permiso (1=activo).
    permisoVer (int, opcional): Permiso para ver.
    permisoCrear (int, opcional): Permiso para crear.
    permisoEditar (int, opcional): Permiso para editar.
    permisoEliminar (int, opcional): Permiso para eliminar.
    idUsuarioApp (int, opcional): ID del usuario para permisos específicos.

Retorna:
    tuple: (resultado, error)
        resultado (list): Lista de resultados del procedimiento.
        error (str): Mensaje de error si ocurre alguna excepción.
"""
def crud_permisos_menuDAL(
    accion,
    id=None,
    idRol=None,
    ruta=None,
    descripcion=None,
    detalle=None,
    estado=1,
    permisoVer=None,
    permisoCrear=None,
    permisoEditar=None,
    permisoEliminar=None,
    idUsuarioApp=None
):
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("""
            EXEC SP_CRUD_PERMISOS_MENU 
                @accion = ?, 
                @id = ?, 
                @idRol = ?, 
                @ruta = ?, 
                @descripcion = ?, 
                @detalle = ?, 
                @estado = ?, 
                @permisoVer = ?, 
                @permisoCrear = ?, 
                @permisoEditar = ?, 
                @permisoEliminar = ?, 
                @idUsuarioApp = ?
        """, (
            accion, id, idRol, ruta, descripcion, detalle,
            estado, permisoVer, permisoCrear, permisoEditar, permisoEliminar,
            idUsuarioApp
        ))

        resultados = []
        
        while True:
            if cursor.description:
                columnas = [col[0] for col in cursor.description]
                resultados.extend([dict(zip(columnas, row)) for row in cursor.fetchall()])
            if not cursor.nextset():
                break

        conn.commit()

        return resultados, None

    except Exception as e:
        return None, str(e)
    finally:
        conn.close()
"""
Función: cerrar_sesiones_expiradas

Descripción:
Elimina de la base de datos todos los registros de sesión vencidos en la tabla logins.
Utiliza la conexión alternativa configurada para limpieza de sesiones.

Parámetros:
    Ninguno.

Retorna:
    None
"""
def cerrar_sesiones_expiradas():
    conn = get_connection2()
    cursor = conn.cursor()

    # Puedes hacer DELETE o UPDATE dependiendo de tu lógica
    query = """
    DELETE FROM logins
    WHERE vencimiento < GETDATE()
    """
    cursor.execute(query)
    conn.commit()
    cursor.close()
    conn.close()