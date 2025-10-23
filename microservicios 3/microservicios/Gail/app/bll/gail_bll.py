import requests
import uuid
from app.models.gail_models import ContactoGail, CampanaGail
from dotenv import load_dotenv
import os
from app.dal.gail_dal import insertar_campana_gail

"""Carga las variables del archivo .env para acceder a las API Keys"""
load_dotenv()

# ====================================================================================
"""Devuelve la API Key correspondiente según el país indicado"""
def obtener_api_key_por_pais(pais: str) -> str:
    mapping = {
        "Dominicana": os.getenv("API_KEY_GAIL_DOMINICANA"),
        "SystemGroup": os.getenv("API_KEY_GAIL_SYSTEMGROUP"),
        "SystemGroup Cobro": os.getenv("API_KEY_GAIL_COBRO"),
    }
    return mapping.get(pais, "")

# ====================================================================================
"""Función principal para registrar una campaña GAIL.
   Esta función consulta los contactos de la lista asociada a la campaña 
   y construye los objetos necesarios antes de insertarla en la base de datos."""
def registrar_campana_gail(campana: CampanaGail):
    id_lista = campana.contactList.id
    pais = campana.pais or "Desconocido"
    api_key = obtener_api_key_por_pais(pais)

    if not api_key:
        campana.contactos = []
        return {"error": f"No se encontró API Key para el país '{pais}'"}

    url = f"https://api.lula.com/v1/contact_lists/{id_lista}/contacts"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            
            """Determina si la respuesta viene como lista o diccionario con clave 'data'"""
            if isinstance(response_data, list):
                contactos_json = response_data
            elif isinstance(response_data, dict) and "data" in response_data:
                contactos_json = response_data["data"]
            else:
                contactos_json = []

            campana.contactos = []
            for c in contactos_json:
                if not c.get("id"):
                    c["id"] = str(uuid.uuid4())

                contacto = ContactoGail(**c)
                """Se puede registrar también el país directamente en el contacto"""
                contacto.additionalData["pais"] = pais
                campana.contactos.append(contacto)

            print(f"✅ TOTAL CONTACTOS: {len(campana.contactos)} para país {pais}")
        else:
            campana.contactos = []

    except Exception as e:
        campana.contactos = []

    return insertar_campana_gail(campana)

# ====================================================================================
"""Obtiene todas las listas de contacto disponibles para el país"""
def obtener_contact_lists_por_pais(pais: str):
    api_key = obtener_api_key_por_pais(pais)
    if not api_key:
        return []
    url = "https://api.lula.com/v1/contact_lists"
    response = requests.get(url, headers={"X-API-Key": api_key})
    return response.json() if response.ok else []

# ====================================================================================
"""Obtiene todas las secuencias disponibles para el país"""
def obtener_secuencias_por_pais(pais: str):
    api_key = obtener_api_key_por_pais(pais)
    if not api_key:
        return []
    url = "https://api.lula.com/v1/sequences"
    response = requests.get(url, headers={"X-API-Key": api_key})
    return response.json() if response.ok else []

# ====================================================================================
"""Obtiene todas las reglas de remarcado disponibles para el país"""
def obtener_reglas_por_pais(pais: str):
    api_key = obtener_api_key_por_pais(pais)
    if not api_key:
        return []
    url = "https://api.lula.com/v1/redialing_rules"
    response = requests.get(url, headers={"X-API-Key": api_key})
    return response.json() if response.ok else []
