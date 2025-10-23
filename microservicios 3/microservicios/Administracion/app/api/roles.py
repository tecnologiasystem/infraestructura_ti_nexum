"""
Importa APIRouter desde FastAPI, que permite registrar rutas agrupadas
por módulo. En este caso, se usará para las rutas relacionadas con roles.
"""
from fastapi import APIRouter

"""
Importa BaseModel desde Pydantic, que se utiliza para definir modelos de datos
validables automáticamente en las rutas (request/response).
"""
from pydantic import BaseModel

"""
Importa las funciones desde la capa de lógica de negocio (BLL) del módulo de roles.

Estas funciones permiten:
- listar_roles: obtener todos los roles existentes.
- crear_rol: registrar un nuevo rol.
- editar_rol: modificar un rol existente.
- eliminar_rol: desactivarlo o eliminarlo lógicamente.
- activar_rol: reactivarlo si estaba desactivado.
"""
from app.bll.roles_bll import listar_roles, crear_rol, editar_rol, eliminar_rol, activar_rol

"""
Instancia del router para el módulo de roles. Aquí se registrarán
todas las rutas que gestionan roles dentro del sistema.
"""
router = APIRouter()

"""
Modelo de datos para representar un Rol dentro del sistema.

Atributos:
    idRol: Identificador numérico del rol (opcional en creación, requerido en edición).
    rol: Nombre del rol (por ejemplo: "Administrador", "Usuario", etc.).
"""
class Rol(BaseModel):
    idRol: int = None
    rol: str = None


"""
Ruta GET que retorna la lista de todos los roles existentes en el sistema.

Invoca la función listar_roles() de la capa BLL, que consulta y devuelve
todos los roles registrados (activos o no, según la lógica interna).

Retorna:
    Lista de objetos de tipo Rol.
"""
@router.get("/dar")
async def dar_roles():
    return listar_roles()


"""
Ruta POST que permite crear un nuevo rol en el sistema.

Parámetros:
    rol: Objeto de tipo Rol recibido en el cuerpo (Body) de la solicitud,
         que contiene el nombre del nuevo rol.

Invoca:
    crear_rol(rol) desde la capa BLL.
"""
@router.post("/crear")
async def crear(rol: Rol):
    return crear_rol(rol)


"""
Ruta PUT que permite editar un rol existente.

Parámetros:
    rol: Objeto de tipo Rol que incluye el ID del rol a modificar
         y su nuevo nombre.

Invoca:
    editar_rol(rol) desde la capa BLL.
"""
@router.put("/editar")
async def editar(rol: Rol):
    return editar_rol(rol)


"""
Ruta PUT que permite desactivar o eliminar un rol del sistema.

Parámetros:
    rol: Objeto de tipo Rol que contiene el idRol del rol a eliminar.

Invoca:
    eliminar_rol(idRol) desde la capa BLL.
"""
@router.put("/eliminar")
async def eliminar(rol: Rol):
    return eliminar_rol(rol.idRol)


"""
Ruta PUT que permite reactivar un rol previamente eliminado o desactivado.

Parámetros:
    rol: Objeto de tipo Rol que contiene el idRol a reactivar.

Invoca:
    activar_rol(idRol) desde la capa BLL.
"""
@router.put("/activar")
async def activar(rol: Rol):
    return activar_rol(rol.idRol)

