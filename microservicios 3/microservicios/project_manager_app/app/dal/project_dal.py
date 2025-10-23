from app.config.database import get_connection

def execute_sp_proyecto(accion: int, data):
    """
    Ejecuta el procedimiento almacenado sp_CRUD_Proyectos con la acción y datos proporcionados.

    Parámetros:
        accion (int): Código de operación (1=crear, 2=editar, 3=eliminar, 4=listar).
        data: objeto con atributos necesarios para la operación.

    Retorna:
        Lista de diccionarios con los resultados (cuando accion=4).
        Diccionario con mensaje OK para otras acciones.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        EXEC sp_CRUD_Proyectos ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    """,
        accion,
        data.idProyecto,
        data.titulo,
        data.descripcion,
        data.responsable,
        data.fechaInicio,
        data.fechaFin,
        data.estado,
        data.unidadNegocio,
        data.observaciones
    )
    if accion == 4:
        # Obtener filas y convertir a lista de diccionarios para retorno JSON
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        result = [dict(zip(columns, row)) for row in rows]
        cursor.close()
        conn.close()
        return result
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "OK"}

def execute_sp_tarea(accion: int, data):
    """
    Ejecuta el procedimiento almacenado sp_CRUD_Tareas con la acción y datos proporcionados.

    Parámetros:
        accion (int): Código de operación (1=crear, 2=editar, 3=eliminar, 4=listar).
        data: objeto con atributos necesarios para la operación.

    Retorna:
        Lista de diccionarios con los resultados (cuando accion=4).
        Diccionario con mensaje OK para otras acciones.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Si data no tiene idTarea (creación), asumimos None
    id_tarea = getattr(data, 'idTarea', None)

    cursor.execute("""
        EXEC sp_CRUD_Tareas ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
    """,
        accion,
        id_tarea,
        data.idProyecto,
        data.titulo,
        data.descripcion,
        data.responsable,
        data.fechaInicio,
        data.fechaFin,
        data.estado,
        data.porcentajeCompletado,
        data.antecesoraId,
        data.unidadNegocio
    )

    if accion == 4:
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        result = [dict(zip(columns, row)) for row in rows]
        cursor.close()
        conn.close()
        return result

    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "OK"}


def execute_sp_recurso(accion: int, data):
    """
    Ejecuta el procedimiento almacenado sp_CRUD_Recursos con la acción y datos proporcionados.

    Parámetros:
        accion (int): Código de operación (1=crear, 2=editar, 3=eliminar, 4=listar).
        data: objeto con atributos necesarios para la operación.

    Retorna:
        Lista de diccionarios con los resultados (cuando accion=4).
        Diccionario con mensaje OK para otras acciones.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        EXEC sp_CRUD_Recursos ?, ?, ?, ?, ?, ?, ?, ?
    """,
        accion,
        data.idRecurso,
        data.nombre,
        data.correo,
        data.rol,
        data.capacidad,
        data.tasaHoras,
        data.Calendario
    )
    if accion == 4:
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        result = [dict(zip(columns, row)) for row in rows]
        cursor.close()
        conn.close()
        return result
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "OK"}

def execute_sp_adjunto(accion: int, data):
    """
    Ejecuta el procedimiento almacenado sp_CRUD_Adjuntos con la acción y datos proporcionados.

    Parámetros:
        accion (int): Código de operación (1=crear, 2=editar, 3=eliminar, 4=listar).
        data: objeto con atributos necesarios para la operación.

    Retorna:
        Lista de diccionarios con los resultados (cuando accion=4).
        Diccionario con mensaje OK para otras acciones.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        EXEC sp_CRUD_Adjuntos ?, ?, ?, ?, ?
    """,
        accion,
        data.idAdjunto,
        data.idTarea,
        data.nombreArchivo,
        data.rutaArchivo
    )
    if accion == 4:
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        result = [dict(zip(columns, row)) for row in rows]
        cursor.close()
        conn.close()
        return result
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "OK"}
