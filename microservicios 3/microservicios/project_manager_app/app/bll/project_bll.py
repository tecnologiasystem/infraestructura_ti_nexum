from app.dal import project_dal

# =====================
# FUNCIONES PARA PROYECTOS
# =====================
def crear_proyecto(data):
    """
    Llama al procedimiento almacenado para crear un proyecto.
    :param data: objeto con datos del proyecto
    :return: resultado del SP
    """
    return project_dal.execute_sp_proyecto(1, data)

def editar_proyecto(data):
    """
    Llama al procedimiento almacenado para editar un proyecto.
    :param data: objeto con datos actualizados del proyecto
    :return: resultado del SP
    """
    return project_dal.execute_sp_proyecto(2, data)

def eliminar_proyecto(idProyecto):
    """
    Construye un objeto dummy con idProyecto para eliminar un proyecto por ID.
    Llama al SP con acción 3 (eliminar).
    :param idProyecto: ID del proyecto a eliminar
    :return: resultado del SP
    """
    dummy = type('obj', (object,), {
        'idProyecto': idProyecto, 'titulo': None, 'descripcion': None,
        'responsable': None, 'fechaInicio': None, 'fechaFin': None,
        'estado': None, 'unidadNegocio': None, 'observaciones': None
    })
    return project_dal.execute_sp_proyecto(3, dummy)

def listar_proyectos(idProyecto=None):
    """
    Construye un objeto dummy con idProyecto opcional para listar proyectos.
    Llama al SP con acción 4 (consultar).
    :param idProyecto: ID del proyecto a listar (opcional)
    :return: lista de proyectos o uno específico
    """
    dummy = type('obj', (object,), {
        'idProyecto': idProyecto, 'titulo': None, 'descripcion': None,
        'responsable': None, 'fechaInicio': None, 'fechaFin': None,
        'estado': None, 'unidadNegocio': None, 'observaciones': None
    })
    return project_dal.execute_sp_proyecto(4, dummy)

# =====================
# FUNCIONES PARA TAREAS
# =====================
def crear_tarea(data):
    """
    Crea una tarea llamando al SP con acción 1.
    """
    return project_dal.execute_sp_tarea(1, data)

def editar_tarea(data):
    """
    Edita una tarea llamando al SP con acción 2.
    """
    return project_dal.execute_sp_tarea(2, data)

def eliminar_tarea(idTarea):
    """
    Construye dummy para eliminar tarea por ID con acción 3.
    """
    dummy = type('obj', (object,), {
        'idTarea': idTarea, 'idProyecto': None, 'titulo': None, 'descripcion': None,
        'responsable': None, 'fechaInicio': None, 'fechaFin': None,
        'estado': None, 'porcentajeCompletado': None, 'antecesoraId': None,
        'unidadNegocio': None
    })
    return project_dal.execute_sp_tarea(3, dummy)

def listar_tareas(idTarea=None, idProyecto=None):
    dummy = type('obj', (object,), {
        'idTarea': idTarea,
        'idProyecto': idProyecto,
        'titulo': None,
        'descripcion': None,
        'responsable': None,
        'fechaInicio': None,
        'fechaFin': None,
        'estado': None,
        'porcentajeCompletado': None,
        'antecesoraId': None,
        'unidadNegocio': None
    })
    return project_dal.execute_sp_tarea(4, dummy)



# =====================
# FUNCIONES PARA RECURSOS
# =====================
def crear_recurso(data):
    """
    Crea un recurso llamando al SP con acción 1.
    """
    return project_dal.execute_sp_recurso(1, data)

def editar_recurso(data):
    """
    Edita un recurso llamando al SP con acción 2.
    """
    return project_dal.execute_sp_recurso(2, data)

def eliminar_recurso(idRecurso):
    """
    Construye dummy para eliminar recurso por ID con acción 3.
    """
    dummy = type('obj', (object,), {
        'idRecurso': idRecurso, 
        'nombre': None, 
        'correo': None, 
        'rol': None, 
        'capacidad': None,
        'tasaHoras': None,
        'Calendario': None
    })
    return project_dal.execute_sp_recurso(3, dummy)

def listar_recursos(idRecurso=None):
    """
    Lista recursos, con filtro opcional por idRecurso, usando acción 4.
    """
    dummy = type('obj', (object,), {
        'idRecurso': idRecurso, 
        'nombre': None, 
        'correo': None, 
        'rol': None, 
        'capacidad': None,
        'tasaHoras': None,
        'Calendario': None
    })
    return project_dal.execute_sp_recurso(4, dummy)

# =====================
# FUNCIONES PARA ADJUNTOS
# =====================
def crear_adjunto(data):
    """
    Crea un adjunto llamando al SP con acción 1.
    """
    return project_dal.execute_sp_adjunto(1, data)

def editar_adjunto(data):
    """
    Edita un adjunto llamando al SP con acción 2.
    """
    return project_dal.execute_sp_adjunto(2, data)

def eliminar_adjunto(idAdjunto):
    """
    Construye dummy para eliminar adjunto por ID con acción 3.
    """
    dummy = type('obj', (object,), {
        'idAdjunto': idAdjunto, 'idTarea': None, 'nombreArchivo': None, 'rutaArchivo': None
    })
    return project_dal.execute_sp_adjunto(3, dummy)

def listar_adjuntos(idAdjunto=None):
    """
    Lista adjuntos, con filtro opcional por idAdjunto, usando acción 4.
    """
    dummy = type('obj', (object,), {
        'idAdjunto': idAdjunto, 'idTarea': None, 'nombreArchivo': None, 'rutaArchivo': None
    })
    return project_dal.execute_sp_adjunto(4, dummy)
