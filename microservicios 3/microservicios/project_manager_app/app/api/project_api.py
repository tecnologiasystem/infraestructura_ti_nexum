from fastapi import APIRouter
from app.models import ProyectoModel, TareaModel, RecursoModel, AdjuntoModel, TareaCreateModel
from app.bll import project_bll

router = APIRouter()

# ====================
# RUTAS PARA PROYECTOS
# ====================
@router.post("/proyecto/crear", tags=["PROYECTOS"])
def crear_proyecto(data: ProyectoModel):
    """
    Crea un nuevo proyecto con la información recibida.
    """
    return project_bll.crear_proyecto(data)

@router.put("/proyecto/editar", tags=["PROYECTOS"])
def editar_proyecto(data: ProyectoModel):
    """
    Edita un proyecto existente con la información enviada.
    """
    return project_bll.editar_proyecto(data)

@router.delete("/proyecto/eliminar/{idProyecto}", tags=["PROYECTOS"])
def eliminar_proyecto(idProyecto: int):
    """
    Elimina un proyecto identificado por su ID.
    """
    return project_bll.eliminar_proyecto(idProyecto)

@router.get("/proyecto/listar", tags=["PROYECTOS"])
def listar_proyectos(idProyecto: int = None):
    """
    Lista proyectos; si se proporciona idProyecto, filtra por ese proyecto.
    """
    return project_bll.listar_proyectos(idProyecto)

# ====================
# RUTAS PARA TAREAS
# ====================
@router.post("/tarea/crear", tags=["TAREAS"])
def crear_tarea(data: TareaCreateModel):
    """
    Crea una nueva tarea con la información recibida.
    """
    return project_bll.crear_tarea(data)

@router.put("/tarea/editar", tags=["TAREAS"])
def editar_tarea(data: TareaModel):
    """
    Edita una tarea existente con la información enviada.
    """
    return project_bll.editar_tarea(data)

@router.delete("/tarea/eliminar/{idTarea}", tags=["TAREAS"])
def eliminar_tarea(idTarea: int):
    """
    Elimina una tarea identificada por su ID.
    """
    return project_bll.eliminar_tarea(idTarea)

@router.get("/tarea/listar", tags=["TAREAS"])
def listar_tareas(idTarea: int = None, idProyecto: int = None):
    """
    Lista tareas; si se proporciona idTarea, filtra por esa tarea,
    si se proporciona idProyecto, filtra por proyecto.
    Si no se proporciona ninguno, retorna todas las tareas.
    """
    return project_bll.listar_tareas(idTarea=idTarea, idProyecto=idProyecto)

# ====================
# RUTAS PARA RECURSOS
# ====================
@router.post("/recurso/crear", tags=["RECURSOS"])
def crear_recurso(data: RecursoModel):
    """
    Crea un nuevo recurso con la información recibida.
    """
    return project_bll.crear_recurso(data)

@router.put("/recurso/editar", tags=["RECURSOS"])
def editar_recurso(data: RecursoModel):
    """
    Edita un recurso existente con la información enviada.
    """
    return project_bll.editar_recurso(data)

@router.delete("/recurso/eliminar/{idRecurso}", tags=["RECURSOS"])
def eliminar_recurso(idRecurso: int):
    """
    Elimina un recurso identificado por su ID.
    """
    return project_bll.eliminar_recurso(idRecurso)

@router.get("/recurso/listar", tags=["RECURSOS"])
def listar_recursos(idRecurso: int = None):
    """
    Lista recursos; si se proporciona idRecurso, filtra por ese recurso.
    """
    return project_bll.listar_recursos(idRecurso)

# ====================
# RUTAS PARA ADJUNTOS
# ====================
@router.post("/adjunto/crear", tags=["ADJUNTOS"])
def crear_adjunto(data: AdjuntoModel):
    """
    Crea un nuevo adjunto con la información recibida.
    """
    return project_bll.crear_adjunto(data)

@router.put("/adjunto/editar", tags=["ADJUNTOS"])
def editar_adjunto(data: AdjuntoModel):
    """
    Edita un adjunto existente con la información enviada.
    """
    return project_bll.editar_adjunto(data)

@router.delete("/adjunto/eliminar/{idAdjunto}", tags=["ADJUNTOS"])
def eliminar_adjunto(idAdjunto: int):
    """
    Elimina un adjunto identificado por su ID.
    """
    return project_bll.eliminar_adjunto(idAdjunto)

@router.get("/adjunto/listar", tags=["ADJUNTOS"])
def listar_adjuntos(idAdjunto: int = None):
    """
    Lista adjuntos; si se proporciona idAdjunto, filtra por ese adjunto.
    """
    return project_bll.listar_adjuntos(idAdjunto)

