from fastapi import APIRouter, Depends
from models.user import UserCreate, UserUpdate
from services.usuarios_service import listar_usuarios, crear_usuario, actualizar_usuario, eliminar_usuario
from security.security import require_role

router = APIRouter(
    prefix="/usuarios",
    tags=["usuarios"]
)

@router.get("/")
async def listar(user: dict = Depends(require_role(["admin"]))):
    return listar_usuarios()

@router.post("/crear")
async def crear(usuario: UserCreate, user: dict = Depends(require_role(["admin"]))):
    crear_usuario(usuario.dict())
    return {"message": "Usuario creado exitosamente"}

@router.put("/editar/{idUsuario}")
async def editar(idUsuario: int, usuario: UserUpdate, user: dict = Depends(require_role(["admin"]))):
    data = usuario.dict()
    data["idUsuario"] = idUsuario
    actualizar_usuario(data)
    return {"message": "Usuario actualizado exitosamente"}

@router.delete("/eliminar/{idUsuario}")
async def eliminar(idUsuario: int, user: dict = Depends(require_role(["admin"]))):
    eliminar_usuario(idUsuario)
    return {"message": "Usuario eliminado exitosamente"}
