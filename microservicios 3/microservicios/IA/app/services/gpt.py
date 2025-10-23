import openai
import json
import os

"""
Se importan las librerías necesarias:
- openai: para interactuar con la API de OpenAI (ChatGPT).
- json: para procesar y validar respuestas en formato JSON.
- os: para acceder a variables de entorno como la clave de API.
"""

"""
Clave de API de OpenAI.
Se recomienda obtenerla desde una variable de entorno por seguridad.
"""
openai.api_key = os.getenv("OPENAI_API_KEY")

def limpiar_respuesta(respuesta):
    """
    Esta función limpia la respuesta del modelo de OpenAI.
    Elimina etiquetas como ```json o ``` que muchas veces vienen en el contenido,
    además de caracteres de nueva línea y tabulación innecesarios.
    
    Esto facilita luego el parseo a JSON.
    """
    respuesta = respuesta.strip()

    if respuesta.startswith("```json") and respuesta.endswith("```"):
        respuesta = respuesta[7:-3].strip()
    elif respuesta.startswith("```") and respuesta.endswith("```"):
        respuesta = respuesta[3:-3].strip()

    respuesta = respuesta.replace("\n", "").replace("\r", "").replace("\t", "")
    return respuesta

def procesar_respuesta(respuesta):
    """
    Esta función toma la respuesta del modelo, la limpia y luego intenta convertirla a un objeto JSON.
    
    Si la respuesta no empieza con { y termina con }, se asume que no tiene formato JSON válido.
    Si falla el intento de `json.loads`, se devuelve información útil para saber por qué falló.
    """
    respuesta_limpia = limpiar_respuesta(respuesta)

    if not respuesta_limpia.startswith("{") or not respuesta_limpia.endswith("}"):
        return {
            "error": "La respuesta no tiene formato JSON válido.",
            "respuesta_limpia": respuesta_limpia
        }

    try:
        return json.loads(respuesta_limpia)
    except json.JSONDecodeError as e:
        return {
            "error": "No se pudo decodificar el JSON.",
            "detalle_error": str(e),
            "respuesta_limpia": respuesta_limpia
        }

def extraer_datos_hv(texto_hv):
    """
    Esta es la función principal que se conecta con la API de OpenAI y envía el contenido
    de una hoja de vida para que el modelo extraiga los campos solicitados.

    El prompt indica explícitamente qué datos buscar:
    - nombre_completo, cedula, telefono, correo, experiencia_laboral, habilidades, formacion_academica,
      ciudad, direccion y profesion.

    También especifica sinónimos comunes que el modelo debe reconocer para cada campo,
    lo cual aumenta la tasa de éxito de extracción aunque el texto esté mal estructurado.

    Si la extracción tiene éxito, se procesa la respuesta con `procesar_respuesta`.
    En caso de error (por red, API, etc.), se captura la excepción y se devuelve con mensaje.
    """
    prompt = f"""
    Eres un asistente encargado de extraer información de hojas de vida.
    Extrae y organiza los siguientes campos en formato JSON

    - Nombre completo
    - Cedula o también puedes buscar número de identificación, número de documento o documento
    - Teléfono o celular también puedes buscar número de contacto, móvil o contacto
    - Correo electrónico también puedes buscar email, correo
    - Experiencia laboral también puedes buscar experiencia profesional, trabajo, historial laboral,
      lo que va acompañado del nombre de la empresa, qué función o tarea asumió y las fechas
    - Habilidades también puedes buscar competencias, destrezas
    - Formación académica también puedes buscar educación, titulación, indicando institución, año y título
    - Ciudad también puedes buscar ubicación o localidad
    - Dirección también puedes buscar lugar de residencia o vivienda
    - Profesión también puedes buscar puesto, trabajo, rol, cargo o empleo

    Asegúrate de que todos estos campos estén presentes en los datos extraídos.

    Los campos deben ir con los nombres que se usan en la base de datos:
    - nombre_completo
    - cedula
    - telefono
    - correo_electronico 
    - experiencia_laboral 
    - habilidades 
    - formacion_academica 
    - ciudad 
    - direccion
    - profesion

    Si alguna información está ausente, devuelve un valor vacío o 'No disponible'.

    HV: {texto_hv}
    Devuelve solo el json
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres un asistente de procesamiento de hojas de vida."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=3000,
        )

        respuesta = response['choices'][0]['message']['content']
        print("Respuesta del modelo:", respuesta)
        return procesar_respuesta(respuesta)
    
    except Exception as e:
        """
        Si ocurre cualquier error al hacer la petición a la API (timeout, clave inválida, etc.),
        se devuelve un diccionario con la clave "error" explicando qué pasó.
        """
        return {"error": f"Error al generar la respuesta: {str(e)}"}
