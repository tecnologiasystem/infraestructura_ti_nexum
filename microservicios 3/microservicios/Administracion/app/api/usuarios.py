"""
Importa APIRouter desde FastAPI para definir y agrupar las rutas
relacionadas con el módulo de usuarios.
"""
from fastapi import APIRouter

"""
Importa BaseModel y Field desde Pydantic. BaseModel se utiliza para definir
la estructura de los modelos de entrada/salida. Field permite definir configuraciones
adicionales como valores por defecto o alias.
"""
from pydantic import BaseModel, Field

"""
Importa tipos auxiliares de typing:
- Optional: indica que un campo puede ser None.
- List: se utiliza para definir campos tipo lista (array).
"""
from typing import Optional, List 

"""
Importa funciones desde la capa de lógica de negocio (BLL) para usuarios.

Estas funciones permiten consultar, crear, editar, eliminar y activar usuarios.
"""
from app.bll.usuarios_bll import (
    obtener_usuarios,
    obtener_usuariosID,
    crear_usuario,
    editar_usuario,
    eliminar_usuario,
    activar_usuario
)

"""
Instancia del router para el módulo de usuarios.
Agrupa todas las rutas relacionadas con la administración de usuarios.
"""
router = APIRouter()


"""
Modelo de datos que representa un usuario dentro del sistema.

Atributos:
    idUsuarioApp: ID único del usuario (opcional, requerido solo para edición).
    nombre: Nombre completo del usuario.
    username: Nombre de usuario para iniciar sesión.
    correo: Correo electrónico del usuario.
    cargo: Cargo o título del usuario dentro de la empresa (opcional).
    idArea: ID del área a la que pertenece.
    idRol: ID del rol que define los permisos del usuario.
    activo: Indica si el usuario está activo (1) o inactivo (0). Por defecto está activo.
    campañas: Lista de IDs de campañas a las que el usuario está asignado. Se recibe con alias "campanas".
    password: Contraseña del usuario (opcional, requerida solo al crear o cambiar contraseña).
"""
class Usuario(BaseModel):
    idUsuarioApp: Optional[int] = None
    nombre: str
    username: str
    correo: str
    cargo: Optional[str] = ""
    idArea: int
    idRol: int
    activo: Optional[int] = Field(default=1)
    campañas: Optional[List[int]] = Field(default_factory=list, alias="campanas")  # <- 👈 aquí
    password: Optional[str] = None



"""
Modelo para recibir únicamente el ID del usuario.

Este modelo se usa en endpoints donde solo se necesita el identificador,
por ejemplo: eliminar o activar un usuario.
"""
class UsuarioID(BaseModel):
    idUsuarioApp: int


"""
Ruta GET que retorna todos los usuarios registrados en el sistema.

Esta función consulta la base de datos a través de la capa BLL,
utilizando la función obtener_usuarios().
"""
@router.get("/dar")
async def listar_usuarios():
    return obtener_usuarios()


"""
Ruta GET que retorna información detallada de un usuario específico por ID.

Parámetros:
    idUsuario: ID del usuario a consultar (se recibe por query string).

Invoca:
    obtener_usuariosID(idUsuario) desde la capa BLL.
"""
@router.get("/darConID")
async def listar_usuarios(idUsuario):
    return obtener_usuariosID(idUsuario)


"""
Ruta POST que permite crear un nuevo usuario en el sistema.

Parámetros:
    usuario: Objeto completo de tipo Usuario que contiene los datos a registrar.

Incluye manejo de excepciones para capturar y retornar errores del proceso.
"""
@router.post("/crear")
async def crear_usuario_api(usuario: Usuario):
    try:
        print("💬 Payload recibido:", usuario)
        return crear_usuario(usuario)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


"""
Ruta PUT que permite editar un usuario existente.

Parámetros:
    usuario: Objeto de tipo Usuario con todos los campos actualizados.

Invoca:
    editar_usuario(usuario) desde la capa BLL.
"""
@router.put("/editar")
async def editar_usuario_api(usuario: Usuario):
    return editar_usuario(usuario)


"""
Ruta PUT que permite eliminar o desactivar un usuario.

Parámetros:
    usuario: Objeto de tipo UsuarioID que contiene solo el idUsuarioApp.

Invoca:
    eliminar_usuario(idUsuarioApp) desde la capa BLL.
"""
@router.put("/eliminar")
async def eliminar_usuario_api(usuario: UsuarioID):
    return eliminar_usuario(usuario.idUsuarioApp)


"""
Ruta PUT que permite reactivar un usuario previamente eliminado o desactivado.

Parámetros:
    usuario: Objeto de tipo UsuarioID con el idUsuarioApp.

Invoca:
    activar_usuario(idUsuarioApp) desde la capa BLL.
"""
@router.put("/activar")
async def activar_usuario_api(usuario: UsuarioID):
    return activar_usuario(usuario.idUsuarioApp)
