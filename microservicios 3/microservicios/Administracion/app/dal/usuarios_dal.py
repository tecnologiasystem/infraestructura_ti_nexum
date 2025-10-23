from app.config.database import get_connection, get_connection2

"""
Importa funciones de conexión a las bases de datos:
- get_connection: conexión a la base principal NEXUM.
- get_connection2: conexión a la base secundaria de login (autenticación).
"""



"""
Función: obtenerUsuariosbd

Obtiene todos los usuarios registrados en la base de datos principal.

Ejecuta:
    EXEC sp_crud_usuariosApp @accion = 1

Retorna:
    Lista de diccionarios con la información de cada usuario.
"""
def obtenerUsuariosbd():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_crud_usuariosApp @accion = 1")
        columnas = [column[0] for column in cursor.description]
        resultados = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
        return resultados
    finally:
        conn.close()



"""
Función: obtenerUsuariosIDbd

Obtiene un usuario específico por su ID.

Parámetros:
    idUsuario (str): ID del usuario.

Ejecuta:
    EXEC sp_crud_usuariosApp @accion = 5, @idUsuarioApp = ?

Retorna:
    Lista con el usuario encontrado (generalmente 1 o ningún resultado).
"""
def obtenerUsuariosIDbd(idUsuario):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "EXEC sp_crud_usuariosApp @accion = 5, @idUsuarioApp = ?",
            (idUsuario,)
        )
        columnas = [column[0] for column in cursor.description]
        resultados = [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
        return resultados
    finally:
        conn.close()



"""
Función: crearUsuariosbd

Crea un nuevo usuario en la base principal y lo asocia a campañas.

Parámetros:
    usuario (Usuario): Objeto con los datos del usuario a registrar.

Ejecuta:
    - sp_crud_usuariosApp con @accion = 2
    - Inserta campañas en UsuariosCampanas
    - Crea usuario en base de login

Retorna:
    Diccionario con mensaje y el ID generado.
"""
def crearUsuariosbd(usuario):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "EXEC sp_crud_usuariosApp @accion = 2, @nombre=?, @username=?, @correo=?, @cargo=?, @idArea=?, @idRol=?, @activo=1",
            (usuario.nombre, usuario.username, usuario.correo, usuario.cargo, usuario.idArea, usuario.idRol)
        )
        nuevo_id = cursor.fetchone()[0]
        usuario.idUsuarioApp = nuevo_id

        if usuario.campañas:
            for campana_id in usuario.campañas:
                cursor.execute(
                    "INSERT INTO UsuariosCampanas (idUsuarioApp, idCampana) VALUES (?, ?)",
                    (nuevo_id, campana_id)
                )

        conn.commit()
        crearUsuarioLogin(usuario)
        return {
            "success": True,
            "mensaje": "Usuario creado correctamente",
            "idUsuarioApp": nuevo_id
        }
    finally:
        conn.close()



"""
Función: crearUsuarioLogin

Registra un usuario en la base de datos de login.

Parámetros:
    usuario (Usuario): Objeto con idUsuarioApp, username y password.

Ejecuta:
    SP_CRUD_USUARIOS con @indicador = 1
"""
def crearUsuarioLogin(usuario):
    conn = get_connection2()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "EXECUTE SP_CRUD_USUARIOS @indicador=1, @idusuario=?, @nombre=?, @password=?",
            (usuario.idUsuarioApp, usuario.username, usuario.password)
        )
        conn.commit()
        return {"mensaje": "Usuario creado correctamente"}
    finally:
        conn.close()



"""
Función: editarUsuariosbd

Edita la información de un usuario existente, incluyendo sus campañas y contraseña.

Parámetros:
    usuario (Usuario): Objeto con datos actualizados.

Ejecuta:
    - sp_crud_usuariosApp con @accion = 3
    - Elimina e inserta campañas
    - Actualiza contraseña si se proporciona
"""
def editarUsuariosbd(usuario):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "EXEC sp_crud_usuariosApp @accion = 3, @idUsuarioApp=?, @nombre=?, @username=?, @correo=?, @cargo=?, @idArea=?, @idRol=?",
            (usuario.idUsuarioApp, usuario.nombre, usuario.username, usuario.correo, usuario.cargo, usuario.idArea, usuario.idRol)
        )

        cursor.execute(
            "DELETE FROM UsuariosCampanas WHERE idUsuarioApp = ?",
            (usuario.idUsuarioApp,)
        )

        if usuario.campañas:
            for campana_id in usuario.campañas:
                cursor.execute(
                    "INSERT INTO UsuariosCampanas (idUsuarioApp, idCampana) VALUES (?, ?)",
                    (usuario.idUsuarioApp, campana_id)
                )

        if usuario.password:
            actualizarUsuarioLogin(usuario)

        conn.commit()
        return {"mensaje": "Usuario actualizado correctamente"}
    finally:
        conn.close()



"""
Función: eliminarUsuariosbd

Desactiva lógicamente un usuario.

Parámetros:
    id_usuario (int): ID del usuario a eliminar.

Ejecuta:
    sp_crud_usuariosApp con @accion = 4
"""
def eliminarUsuariosbd(id_usuario):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "EXEC sp_crud_usuariosApp @accion = 4, @idUsuarioApp=?",
            (id_usuario,)
        )
        conn.commit()
        return {"mensaje": "Usuario desactivado correctamente"}
    finally:
        conn.close()



"""
Función: activarUsuariosbd

Activa un usuario previamente desactivado.

Parámetros:
    id_usuario (int): ID del usuario a activar.

Ejecuta:
    UPDATE sobre UsuariosApp
"""
def activarUsuariosbd(id_usuario):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE UsuariosApp SET activo = 1 WHERE idUsuarioApp = ?",
            (id_usuario,)
        )
        conn.commit()
        return {"mensaje": "Usuario activado correctamente"}
    finally:
        conn.close()



"""
Función: actualizarUsuarioLogin

Actualiza la contraseña de un usuario en la base de login.

Parámetros:
    usuario (Usuario): Objeto con idUsuarioApp, username y password.

Ejecuta:
    SP_CRUD_USUARIOS con @indicador = 2
"""
def actualizarUsuarioLogin(usuario):
    conn = get_connection2()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "EXECUTE SP_CRUD_USUARIOS @indicador=2, @idusuario=?, @nombre=?, @password=?",
            (usuario.idUsuarioApp, usuario.username, usuario.password)
        )
        conn.commit()
        return {"mensaje": "Contraseña actualizada correctamente"}
    finally:
        conn.close()
