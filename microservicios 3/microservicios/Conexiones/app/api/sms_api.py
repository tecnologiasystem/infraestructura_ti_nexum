from fastapi import APIRouter, Request, HTTPException, UploadFile, File

"""
Importaciones desde FastAPI:
- APIRouter: Permite crear un grupo de rutas (endpoints) que luego se puede incluir en el proyecto principal.
- Request: Representa una solicitud HTTP entrante, útil para obtener datos JSON o headers.
- HTTPException: Se usa para lanzar errores personalizados con código y mensaje.
- UploadFile: Representa un archivo cargado en una petición POST (por ejemplo, un Excel).
- File: Marca que un parámetro debe recibirse como archivo, especialmente en formularios multipart/form-data.
"""

from app.bll.sms_bll import enviar_sms_360nrs

"""
Importa desde la capa BLL (Business Logic Layer) la función `enviar_sms_360nrs`,
que contiene la lógica necesaria para interactuar con el proveedor de envío de SMS (360NRS en este caso).
"""

from io import BytesIO

"""
BytesIO permite trabajar con archivos en memoria como si fueran archivos físicos.
Aquí se usa para convertir el archivo subido por el usuario a un buffer legible por pandas.
"""

import pandas as pd

"""
Pandas se utiliza para leer y procesar archivos Excel (.xlsx).
El contenido se transforma en un DataFrame, que permite recorrer las filas y extraer datos fácilmente.
"""



"""
Configuración del router.

Se define un router FastAPI. Esto permite organizar los endpoints relacionados con SMS
en un módulo separado, manteniendo el código limpio y modular.
Más adelante, este `router` se incluirá en la aplicación principal (`main.py` o `api.py`)
usando `app.include_router(router)`.
"""
router = APIRouter()



"""
ENDPOINT: /sms_send

Endpoint para enviar un mensaje SMS individual.

Método:
    POST

Entrada (JSON):
    - telefono (str): número al que se quiere enviar el SMS.
    - mensaje (str): contenido del mensaje.

Retorna:
    - Un diccionario con el resultado del envío: {"resultado": ...}

Lógica:
    1. Se extraen los datos del request.
    2. Se validan los campos requeridos.
    3. Se llama a la lógica de negocio `enviar_sms_360nrs`.
    4. Se retorna el resultado del intento de envío.
"""
@router.post("/sms_send")
async def sms_send(request: Request):
    data = await request.json()

    numero = data.get("telefono")
    mensaje = data.get("mensaje")

    if not numero or not mensaje:
        raise HTTPException(status_code=400, detail="Faltan datos")

    resultado = enviar_sms_360nrs(numero, mensaje)
    return {"resultado": resultado}



"""
ENDPOINT: /sms/send_excel

Endpoint para enviar mensajes SMS a múltiples destinatarios desde un archivo Excel.

Método:
    POST

Entrada:
    - archivo (UploadFile): Excel (.xlsx) con columnas:
        - "TEL1": número de teléfono
        - "SMS": contenido del mensaje

Retorna:
    - Lista de resultados por cada fila procesada, indicando número, mensaje y estado (OK / ERROR)

Lógica:
    1. Se lee el archivo cargado y se transforma en un DataFrame con pandas.
    2. Se recorren las filas para enviar cada mensaje individualmente.
    3. Se convierte el número a formato internacional si no empieza con "+".
    4. Se guarda el resultado por fila, dependiendo del éxito del envío.
    5. Si ocurre un error global al leer el archivo o procesarlo, se lanza un error HTTP 500.
"""
@router.post("/sms/send_excel")
async def sms_send_excel(archivo: UploadFile = File(...)):
    try:
        content = await archivo.read()
        df = pd.read_excel(BytesIO(content))  # Lectura directa desde memoria

        resultados_totales = []

        for _, row in df.iterrows():
            numero = str(row.get("TEL1"))
            mensaje = str(row.get("SMS"))

            if not numero or not mensaje:
                continue  # Omitir filas incompletas

            if not numero.startswith("+"):
                numero = f"+{numero}"  # Añadir prefijo internacional si falta

            resultado_envio = enviar_sms_360nrs(numero, mensaje)

            resultados_totales.append({
                "telefono": numero,
                "mensaje": mensaje,
                "estado": "OK" if all(res['status'] == 200 for res in resultado_envio) else "ERROR"
            })

        return {"resultado": resultados_totales}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")
