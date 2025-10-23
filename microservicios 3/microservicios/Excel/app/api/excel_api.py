from typing import List
from fastapi import APIRouter, UploadFile, Form, BackgroundTasks
from fastapi.responses import FileResponse
from app.bll.excel_bll import procesar_columnas_numericas_mejorado
import shutil
import os
import uuid

"""
Se define un router de FastAPI que agrupará las rutas relacionadas con el procesamiento de archivos Excel.
"""
router = APIRouter()

@router.post("/procesar_excel/")
async def procesar_excel(
    archivo: UploadFile,
    background: BackgroundTasks,
    columnas: str = Form("Saldo total, Capital, Oferta 1, Oferta 2, Oferta 3, Hasta 3 cuotas, Hasta 6 cuotas, Hasta 12 Cuotas, Pago Flexible, Cap consolidado, Saldo Total Cons, 6 Cuotas, 12 cuotas, Intereses"),
    modo: str = Form("numerico")
):
    """
    Endpoint que recibe un archivo Excel y procesa columnas específicas indicadas por el usuario.

    Parámetros:
    - archivo: archivo Excel subido por el cliente (tipo .xlsx)
    - background: instancia para ejecutar tareas en segundo plano (como eliminar archivos temporales)
    - columnas: string separado por comas que indica las columnas a procesar
    - modo: indica el tipo de limpieza (por defecto "numerico")

    Flujo:
    1. Se convierte el string de columnas en una lista.
    2. Se guarda el archivo temporalmente con un nombre aleatorio.
    3. Se llama a la función de limpieza de columnas.
    4. Se devuelve el archivo procesado como descarga.
    5. Se eliminan los archivos temporales, tanto de entrada como de salida.
    """
    print(f"String de columnas recibido: '{columnas}'")

    """
    Convertimos el string de columnas a una lista, eliminando espacios sobrantes
    """
    columnas_list = [col.strip() for col in columnas.split(",")]
    print(f"Lista de columnas después del split: {columnas_list}")
    print(f"Cantidad de columnas en la lista: {len(columnas_list)}")

    """
    Creamos la carpeta 'temp' si no existe, donde se guardarán archivos temporales
    """
    if not os.path.exists("temp"):
        os.makedirs("temp")

    """
    Generamos nombres únicos para los archivos de entrada y salida, usando uuid para evitar colisiones
    """
    temp_input = f"temp/temp_input_{uuid.uuid4().hex}.xlsx"
    temp_output = f"temp/temp_output_{uuid.uuid4().hex}.xlsx"

    """
    Guardamos el archivo recibido por el usuario en el disco temporalmente
    """
    with open(temp_input, "wb") as buffer:
        shutil.copyfileobj(archivo.file, buffer)

    try:
        """
        Procesamos el archivo llamando a la lógica BLL que limpia las columnas numéricas
        """
        procesar_columnas_numericas_mejorado(temp_input, temp_output, columnas_list, modo=modo)

        """
        Eliminamos el archivo de entrada ya que ya fue procesado
        """
        if os.path.exists(temp_input):
            os.remove(temp_input)

        """
        Programamos eliminación del archivo de salida en segundo plano (cuando se complete la respuesta)
        """
        background.add_task(os.remove, temp_output)

        """
        Devolvemos el archivo procesado como descarga
        """
        return FileResponse(
            path=temp_output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="archivo_procesado.xlsx",
            background=background
        )

    except Exception as e:
        """
        En caso de error, eliminamos los archivos temporales si existen y devolvemos detalle del error
        """
        import traceback
        if os.path.exists(temp_input):
            os.remove(temp_input)
        if os.path.exists(temp_output):
            os.remove(temp_output)

        return {
            "error": str(e).encode("ascii", errors="ignore").decode(),
            "trace": traceback.format_exc().encode("ascii", errors="ignore").decode()
        }
