from sqlalchemy import text
from fastapi import HTTPException
from database.connection import get_connection
from security.security import create_access_token

def login_user(username: str, password: str):
    conn = get_connection()
    try:
        query = text("EXEC SP_CRUD_USUARIOS @indicador = 5, @nombre = :username, @password = :password")
        result = conn.execute(query, {"username": username, "password": password}).fetchone()

        if result and getattr(result, 'Error', None) != -1:
            # Usuario encontrado correctamente
            user_data = {
                "idUsuario": result.idUsuario,
                "nombre": result.nombre,
            }
            # Crear JWT
            token_data = {
                "sub": str(result.idUsuario),
                "username": result.nombre,
            }
            token = create_access_token(token_data)

            return {
                "token": token,
                "usuario": user_data
            }
        
        else:
            # 👇 Lanzar excepción 401 aquí mismo
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")
        
    finally:
        conn.close()
