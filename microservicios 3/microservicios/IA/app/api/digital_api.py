from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
import os
from app.bll.digital_bll import procesar_archivo

"""
Se instancia un enrutador para este módulo, que incluye un sistema de rate-limiting.
"""
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

"""
Ruta fija en donde se encuentran las hojas de vida a procesar.
"""
DIRECTORIO_HV = "C:\\Users\\j.salgar\\Documents\\hojas"

@router.post("/procesar_y_guardar/")
@limiter.limit("5 per minute")
async def procesar_y_guardar(request: Request):
    """
    Endpoint POST /procesar_y_guardar/

    Este endpoint se encarga de:
    - Verificar que exista el directorio con los archivos.
    - Leer todos los archivos del directorio.
    - Procesar cada archivo de forma asíncrona con la función `procesar_archivo`.
    - Retornar un JSON con los resultados de cada archivo procesado.

    Además, se aplica un límite de 5 solicitudes por minuto por IP.
    """
    if not os.path.exists(DIRECTORIO_HV):
        """
        Si el directorio no existe, retorna un error 400.
        """
        return JSONResponse(status_code=400, content={"error": "Directorio no encontrado"})

    """
    Se listan todos los archivos dentro del directorio especificado.
    """
    archivos = os.listdir(DIRECTORIO_HV)
    resultados = []

    """
    Se recorre cada archivo del directorio para procesarlo uno por uno.
    """
    for archivo in archivos:
        ruta_archivo = os.path.join(DIRECTORIO_HV, archivo)

        """
        Se abre el archivo en modo binario y se envía a la función `procesar_archivo`,
        que ejecuta la lógica de análisis del contenido.
        """
        with open(ruta_archivo, "rb") as file:
            resultado = await procesar_archivo(file)

            """
            Se guarda el nombre del archivo y el resultado del procesamiento.
            """
            resultados.append({"archivo": archivo, **resultado})

    """
    Se retorna una respuesta JSON con los resultados de todos los archivos.
    """
    return JSONResponse(content={"resultados": resultados})
