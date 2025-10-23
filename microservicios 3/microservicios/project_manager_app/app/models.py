from pydantic import BaseModel
from typing import Optional

class ProyectoModel(BaseModel):
    """
    Modelo para un proyecto, que representa la estructura esperada de un proyecto en la API.
    """
    idProyecto: Optional[int]  # ID opcional, puede ser None para nuevos proyectos
    titulo: str                # Título obligatorio del proyecto
    descripcion: Optional[str] # Descripción opcional del proyecto
    responsable: int           # ID del responsable (obligatorio)
    fechaInicio: str           # Fecha de inicio en formato string (idealmente ISO 8601)
    fechaFin: str              # Fecha fin en formato string
    estado: str                # Estado actual del proyecto (e.g., "Activo", "Finalizado")
    unidadNegocio: str         # Unidad de negocio asociada
    observaciones: Optional[str] # Observaciones adicionales (opcional)

class TareaModel(BaseModel):
    """
    Modelo para una tarea dentro de un proyecto.
    """
    idTarea: Optional[int] = None    # ID de tarea, opcional para nuevas tareas
    idProyecto: Optional[int] = None          # ID del proyecto al que pertenece (obligatorio)
    titulo: str                # Título de la tarea (obligatorio)
    descripcion: Optional[str] # Descripción opcional
    responsable: int           # ID del responsable de la tarea
    fechaInicio: str           # Fecha inicio tarea
    fechaFin: str              # Fecha fin tarea
    estado: str                # Estado actual de la tarea
    porcentajeCompletado: int  # Porcentaje completado (ejemplo: 0-100)
    antecesoraId: Optional[int] # ID de tarea antecesora si aplica
    unidadNegocio: str         # Unidad de negocio

class RecursoModel(BaseModel):
    """
    Modelo para un recurso humano o similar.
    """
    idRecurso: Optional[int]   # ID recurso, opcional para nuevos registros
    nombre: str                # Nombre del recurso
    correo: str                # Correo electrónico
    rol: str                   # Rol asignado
    capacidad: Optional[float]
    tasaHoras: Optional[float]
    Calendario: Optional[int]


class AdjuntoModel(BaseModel):
    """
    Modelo para adjuntos relacionados a tareas.
    """
    idAdjunto: Optional[int]   # ID adjunto, opcional para nuevos registros
    idTarea: int               # ID de la tarea asociada
    nombreArchivo: str         # Nombre del archivo adjunto
    rutaArchivo: str           # Ruta donde se almacena el archivo


class TareaCreateModel(BaseModel):
    idProyecto: int
    titulo: str
    descripcion: Optional[str] = None
    responsable: int
    fechaInicio: str
    fechaFin: str
    estado: str
    porcentajeCompletado: int
    antecesoraId: Optional[int] = None
    unidadNegocio: Optional[str] = None