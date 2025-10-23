from pydantic import BaseModel
from typing import Optional

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    nombreCompleto: str
    idRol: int
    cedula: Optional[str] = None
    area: Optional[str] = None
    cargo: Optional[str] = None
    correo: Optional[str] = None

class UserUpdate(UserCreate):
    idUsuario: int

class UserResponse(BaseModel):
    idUsuario: int
    username: str
    nombre: str
    idRol: int
    nombreRol: str
