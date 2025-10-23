from fastapi import APIRouter, Depends
from security.security import require_role

router = APIRouter(
    prefix="/reportes",
    tags=["reportes"]
)

@router.get("/")
async def listar_reportes(user: dict = Depends(require_role(["admin", "coordinador"]))):
    return {"message": f"Bienvenido {user['username']} al módulo de reportes"}
