from sqlalchemy import text
from database.connection import get_connection
from security.security import create_access_token

def listar_usuarios():
    conn = get_connection()
    try:
        query = text("EXEC sp_crud_usuarios @indicador = 1")
        result = conn.execute(query).fetchall()
        return [dict(row) for row in result]
    finally:
        conn.close()

def crear_usuario(usuario):
    conn = get_connection()
    try:
        query = text("""
            EXEC sp_crud_usuarios 
                @indicador = 2,
                @username = :username,
                @password = :password,
                @nombreCompleto = :nombreCompleto,
                @idRol = :idRol,
                @cedula = :cedula,
                @area = :area,
                @cargo = :cargo,
                @correo = :correo
        """)
        conn.execute(query, usuario)
        conn.commit()
    finally:
        conn.close()

def actualizar_usuario(usuario):
    conn = get_connection()
    try:
        query = text("""
            EXEC sp_crud_usuarios 
                @indicador = 3,
                @idUsuario = :idUsuario,
                @username = :username,
                @password = :password,
                @nombreCompleto = :nombreCompleto,
                @idRol = :idRol,
                @cedula = :cedula,
                @area = :area,
                @cargo = :cargo,
                @correo = :correo
        """)
        conn.execute(query, usuario)
        conn.commit()
    finally:
        conn.close()

def eliminar_usuario(idUsuario: int):
    conn = get_connection()
    try:
        query = text("""
            EXEC sp_crud_usuarios 
                @indicador = 4,
                @idUsuario = :idUsuario
        """)
        conn.execute(query, {"idUsuario": idUsuario})
        conn.commit()
    finally:
        conn.close()

def login_user(username: str, password: str):
    conn = get_connection()
    try:
        query = text("EXEC sp_crud_usuarios @indicador = 5, @username = :username, @password = :password")
        result = conn.execute(query, {"username": username, "password": password}).fetchone()

        if result and getattr(result, 'Error', None) != -1:
            # Usuario encontrado correctamente
            user_data = {
                "idUsuario": result.idUsuario,
                "nombre": result.nombre,
                "idRol": result.idRol,
                "nombreRol": result.nombreRol
            }
            # Crear JWT
            token_data = {
                "sub": str(result.idUsuario),
                "username": username,
                "rol": result.nombreRol
            }
            token = create_access_token(token_data)

            return {
                "token": token,
                "usuario": user_data
            }
        else:
            return None
    finally:
        conn.close()
