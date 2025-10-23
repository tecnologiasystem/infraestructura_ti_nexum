from fastapi import APIRouter, Query
"""
Se importan:
- `APIRouter`: para definir un conjunto de rutas específicas que luego se pueden incluir en `main.py`.
- `Query`: permite definir parámetros de consulta (query params) en endpoints GET, y controlar su validación.
"""

from datetime import datetime
"""
Se importa el tipo `datetime`, necesario para interpretar las fechas que llegan como parámetros.
"""

from app.bll.contacto_bll import procesar_llamadas_por_rango
"""
Importa desde la capa BLL (Business Logic Layer) la función que se encarga de procesar llamadas
entre un rango de fechas. Toda la lógica de negocio vive ahí, no en este archivo.
"""

# Se crea un router independiente para este módulo, que luego se puede registrar en el `main.py`
router = APIRouter()


@router.get("/importar")
async def importar_llamadas(
    fecha_inicio: datetime = Query(...),
    fecha_fin: datetime = Query(...)
):
    """
    Endpoint GET que permite importar o procesar llamadas dentro de un rango de fechas específico.

    Parámetros de entrada:
    - fecha_inicio (datetime): fecha inicial del rango (obligatoria). Se obtiene por query param.
    - fecha_fin (datetime): fecha final del rango (obligatoria). Se obtiene por query param.

    Ejemplo de uso desde el frontend o navegador:
    /importar?fecha_inicio=2025-07-01T00:00:00&fecha_fin=2025-07-03T23:59:59

    Flujo:
    - Los parámetros `fecha_inicio` y `fecha_fin` se validan automáticamente como fechas.
    - Luego se llama a la función `procesar_llamadas_por_rango()` con estas fechas.
    - El resultado es retornado como respuesta del endpoint.

    Este endpoint es útil para:
    - Importar registros de llamadas de una base externa.
    - Ejecutar tareas programadas con rangos definidos.
    - Usar desde frontend para refrescar o procesar datos recientes.
    """

    return await procesar_llamadas_por_rango(fecha_inicio, fecha_fin)
