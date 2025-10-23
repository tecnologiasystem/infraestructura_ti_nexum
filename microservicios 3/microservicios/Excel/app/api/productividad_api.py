from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from app.bll.productividad_bll import calcular_productividad

"""
Se define un router de FastAPI que agrupará las rutas relacionadas con el análisis de productividad.
"""
router = APIRouter()

@router.post("/analizar_productividad", tags=["Productividad"])
async def analizar_productividad(archivo: UploadFile = File(...)):
    """
    Endpoint que recibe un archivo (generalmente Excel o CSV) para calcular métricas de productividad
    y genera una gráfica a partir de los resultados.

    Parámetros:
    - archivo: archivo subido por el usuario (esperado en formato compatible con pandas)

    Flujo:
    1. Se lee el contenido binario del archivo.
    2. Se llama a `calcular_productividad()` que retorna:
       - una imagen (grafico en bytes)
       - un diccionario con los resultados del análisis.
    3. La imagen se guarda localmente como 'ultima_grafica.png' para ser accedida por otro endpoint.
    4. Se incluye en el resultado una URL relativa para descargar el gráfico generado.
    5. Se devuelve la respuesta en formato JSON.
    """
    contenido = await archivo.read()  # Leer el contenido del archivo subido
    imagen, resultado = calcular_productividad(contenido)  # Procesar y generar imagen

    # Guardamos el gráfico generado localmente
    with open("ultima_grafica.png", "wb") as f:
        f.write(imagen.read())

    imagen.seek(0)  # Volvemos al inicio del buffer por si se quiere reutilizar

    # Agregamos URL para que el cliente pueda descargar la imagen si quiere visualizarla aparte
    resultado["grafico_url"] = "/productividad/descargar_grafico"

    return JSONResponse(content=resultado)  # Devolvemos el análisis con enlace al gráfico


@router.get("/descargar_grafico")
def descargar_grafico():
    """
    Endpoint que permite descargar la última imagen de productividad generada.
    Este archivo es generado por el endpoint `analizar_productividad`.

    Retorna:
    - StreamingResponse con la imagen PNG del gráfico.
    """
    return StreamingResponse(open("ultima_grafica.png", "rb"), media_type="image/png")
