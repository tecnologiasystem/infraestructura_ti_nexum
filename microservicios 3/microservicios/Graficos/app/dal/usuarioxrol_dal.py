from app.config.database import get_connectionGraficos

def fetch_roles():
    """
    Recupera todos los roles definidos en el sistema desde la tabla `roles`.

    Conexión:
        - Utiliza la función `get_connectionGraficos()` para conectarse a la base de datos 'NEXUM'.

    Consulta:
        - `SELECT IdRol, Rol FROM roles`:
            - `IdRol`: identificador único del rol.
            - `Rol`: nombre o descripción textual del rol.

    Flujo:
        1. Ejecuta la consulta SQL.
        2. Obtiene todos los registros mediante `fetchall()`.
        3. Cierra la conexión para liberar recursos.

    Retorna:
        - Lista de tuplas con la forma `(IdRol, Rol)` representando todos los roles disponibles en la aplicación.
    """
    conn = get_connectionGraficos()
    cursor = conn.cursor()
    cursor.execute("SELECT IdRol, Rol FROM roles")
    roles = cursor.fetchall()
    conn.close()
    return roles

def fetch_usuarios_roles():
    """
    Recupera los roles asignados a los usuarios desde la tabla `UsuariosApp`.

    Conexión:
        - Se conecta a la base de datos 'NEXUM' mediante `get_connectionGraficos()`.

    Consulta:
        - `SELECT IdRol FROM UsuariosApp`:
            - Extrae únicamente el ID del rol (`IdRol`) asignado a cada usuario.
            - Esto permite luego contar cuántos usuarios pertenecen a cada rol.

    Flujo:
        1. Ejecuta la consulta SQL.
        2. Recupera los resultados con `fetchall()`.
        3. Cierra la conexión a la base de datos.

    Retorna:
        - Lista de tuplas con el identificador del rol para cada usuario.
        - Este resultado es útil para construir un contador de usuarios por rol.
    """
    conn = get_connectionGraficos()
    cursor = conn.cursor()
    cursor.execute("SELECT IdRol FROM UsuariosApp")
    usuarios = cursor.fetchall()
    conn.close()
    return usuarios
