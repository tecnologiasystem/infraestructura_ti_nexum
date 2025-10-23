from fastapi import APIRouter, HTTPException, Request
from services.auth_service import login_user
from models.user import UserLogin
from services.logs_service import registrar_login

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/login")
async def login(user_login: UserLogin, request: Request):
    auth_result = login_user(user_login.username, user_login.password)

    # Registrar log de login
    usuario = auth_result["usuario"]
    token = auth_result["token"]
    ip_cliente = request.client.host
    id_rol = usuario.get("idRol", None)
    nombre_usuario = usuario.get("nombre", "")

    registrar_login(usuario["idUsuario"], nombre_usuario, token, ip_cliente, id_rol)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": usuario
    }
