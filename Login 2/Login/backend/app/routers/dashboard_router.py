from fastapi import APIRouter, Depends
from security.security import get_current_user

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)

@router.get("/")
async def ver_dashboard(user: dict = Depends(get_current_user)):
    return {"message": f"Bienvenido {user['username']} al dashboard general"}
