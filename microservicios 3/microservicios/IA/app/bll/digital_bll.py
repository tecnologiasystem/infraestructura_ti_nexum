import os
import json
import logging
from app.services.gpt import extraer_datos_hv
from app.services.utils import procesar_pdf, procesar_word, procesar_imagen
from app.dal.digital_dal import insertar_candidato

"""
Convierte cualquier tipo de valor a string.
Si el valor es lista o diccionario, lo convierte a JSON.
Si ocurre algún error durante la conversión, retorna una cadena vacía.
"""
def obtener_str(value):
    try:
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        return str(value).strip()
    except Exception as e:
        logging.error(f"Error al convertir el valor a cadena: {e}")
        return ""

"""
Procesa un archivo (PDF, Word o imagen) para extraer datos de una hoja de vida.
Devuelve una respuesta con los campos extraídos y los guarda en base de datos.
"""
async def procesar_archivo(file):
    filename = file.name
    extension = os.path.splitext(filename)[1].lower()

    """
    Determina el tipo de archivo y extrae el texto utilizando la función correspondiente.
    """
    if extension == ".pdf":
        texto = await procesar_pdf(file)
    elif extension == ".docx":
        texto = await procesar_word(file)
    elif extension in [".jpg", ".jpeg", ".png"]:
        texto = await procesar_imagen(file)
    else:
        return {"error": "Formato de archivo no soportado"}

    """
    Usa GPT para extraer información estructurada del texto leído.
    """
    datos_extraidos = extraer_datos_hv(texto)
    if not isinstance(datos_extraidos, dict):
        return {"error": "Datos extraídos no son un diccionario"}

    """
    Se arma la respuesta con los campos requeridos, haciendo limpieza de datos y control de errores.
    También se hace conversión segura para evitar advertencias.
    """
    datos = datos_extraidos.get("datos", {})
    respuesta = {
        "nombre_completo": obtener_str(datos.get("nombre_completo") or ""),
        "cedula": obtener_str(datos.get("cedula") or ""),
        "telefono": obtener_str(datos.get("telefono") or ""),
        "correo_electronico": obtener_str(datos.get("correo_electronico") or ""),
        "experiencia_laboral": datos.get("experiencia_laboral", []),
        "habilidades": obtener_str(datos.get("habilidades") or []),
        "formacion_academica": datos.get("formacion_academica", []),
        "ciudad": obtener_str(datos.get("ciudad") or ""),
        "direccion": obtener_str(datos.get("direccion") or ""),
        "profesion": obtener_str(datos.get("profesion") or "")
    }

    """
    Guarda los datos extraídos en la base de datos.
    Devuelve éxito o error dependiendo del resultado de la inserción.
    """
    exito = insertar_candidato(respuesta)
    if exito:
        return {"status": "Procesado correctamente"}
    else:
        return {"error": "Error al guardar en la base de datos"}
