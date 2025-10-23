import requests
import uuid
from app.models.gail_models import CampanaGail, ContactoGail, ContactListGail, SequenceGail, RedialingRuleGail
from app.dal.gail_dal import insertar_campana_gail
from dotenv import load_dotenv
import os

# ============================================================
"""Carga las variables de entorno del archivo .env"""
load_dotenv()
print("🔐 API_KEY_GAIL_SYSTEMGROUP leída:", os.getenv("API_KEY_GAIL_DOMINICANA"))

# ============================================================
"""Función principal que sincroniza las campañas desde la API de Lula"""
def sincronizar_campanas_lula():
    url = "https://api.lula.com/v1/campaigns"
    headers = {
        "X-API-Key": os.getenv("API_KEY_GAIL_DOMINICANA"),
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {"error": f"Error al obtener campañas: {response.status_code}"}

    campañas = response.json()
    total = 0
    errores = []

    for c in campañas:
        try:
            # ============================
            """Validación de campos requeridos"""
            required_fields = ['contactLists', 'sequences', 'redialingRules']
            missing_fields = []

            if not c.get('contactLists') or len(c['contactLists']) == 0:
                missing_fields.append('contactLists')

            if not c.get('sequences') or len(c['sequences']) == 0:
                missing_fields.append('sequences')

            if not c.get('redialingRules'):
                missing_fields.append('redialingRules')

            if missing_fields:
                print(f"⚠️ Saltando campaña '{c.get('name')}' - Campos faltantes: {', '.join(missing_fields)}")
                continue

            # ============================
            """Extracción de IDs y consulta detallada de cada recurso"""
            contact_list_id = c['contactLists'][0]['id']
            sequence_id = c['sequences'][0]['sequenceId']
            redialing_rule_id = c['redialingRules']

            contact_list_data = get_contact_list(contact_list_id, headers)
            sequence_data = get_sequence(sequence_id, headers)
            regla_data = get_redialing_rule(redialing_rule_id, headers)
            contactos = get_contactos(contact_list_id, headers)

            # ============================
            """Validaciones para datos detallados"""
            if not contact_list_data or contact_list_data.get('id') == 'N/A':
                print(f"⚠️ No se pudo obtener lista de contactos para campaña '{c.get('name')}'")
                continue

            if not sequence_data or sequence_data.get('id') == 'N/A':
                print(f"⚠️ No se pudo obtener secuencia para campaña '{c.get('name')}'")
                continue

            if not regla_data or regla_data.get('id') == 'N/A':
                print(f"⚠️ No se pudo obtener regla de remarcado para campaña '{c.get('name')}'")
                continue

            # ============================
            """Construcción del objeto CampanaGail completo"""
            campana = CampanaGail(
                idCampana=c["id"],
                name=c["name"],
                description=c.get("description", ""),
                status=c["status"],
                pais=c.get("pais", "Desconocido"),
                contactList=ContactListGail(**contact_list_data),
                sequence=SequenceGail(**sequence_data),
                redialingRule=RedialingRuleGail(**regla_data),
                contactos=[ContactoGail(**con) for con in contactos]
            )

            # ============================
            """Insertar campaña en la base de datos"""
            insertar_campana_gail(campana)
            print(f"✅ Campaña '{campana.name}' insertada correctamente.")
            total += 1

        except Exception as e:
            error_msg = f"❌ Error con campaña '{c.get('name')}': {str(e)}"
            print(error_msg)
            errores.append(error_msg)

    # ============================
    """Resumen del proceso"""
    result = {"mensaje": f"Se insertaron {total} campañas correctamente."}
    if errores:
        result["errores"] = errores

    return result


# ============================================================
"""Obtiene los datos de una lista de contactos específica"""
def get_contact_list(id_lista, headers):
    try:
        r = requests.get(f"https://api.lula.com/v1/contact_lists/{id_lista}", headers=headers)
        if r.ok:
            return r.json()
        else:
            print(f"Error al obtener contact list {id_lista}: {r.status_code}")
            return None
    except Exception as e:
        print(f"Excepción al obtener contact list {id_lista}: {e}")
        return None


# ============================================================
"""Obtiene los datos de una secuencia específica"""
def get_sequence(id_seq, headers):
    try:
        r = requests.get(f"https://api.lula.com/v1/sequences/{id_seq}", headers=headers)
        if r.ok:
            return r.json()
        else:
            print(f"Error al obtener sequence {id_seq}: {r.status_code}")
            return None
    except Exception as e:
        print(f"Excepción al obtener sequence {id_seq}: {e}")
        return None


# ============================================================
"""Obtiene los datos de una regla de remarcado específica"""
def get_redialing_rule(id_regla, headers):
    try:
        r = requests.get(f"https://api.lula.com/v1/redialing_rules/{id_regla}", headers=headers)
        if r.ok:
            regla = r.json()
            return {
                "id": regla["id"],
                "name": regla["name"],
                "outcomes": regla.get("outcomes", []),
                "systemActions": regla.get("systemActions", {})
            }
        else:
            print(f"Error al obtener redialing rule {id_regla}: {r.status_code}")
            return None
    except Exception as e:
        print(f"Excepción al obtener redialing rule {id_regla}: {e}")
        return None


# ============================================================
"""Obtiene todos los contactos asociados a una lista"""
def get_contactos(id_lista, headers):
    try:
        r = requests.get(f"https://api.lula.com/v1/contact_lists/{id_lista}/contacts", headers=headers)
        if r.ok:
            res = r.json()
            return res["data"] if isinstance(res, dict) and "data" in res else res
        else:
            print(f"Error al obtener contactos para lista {id_lista}: {r.status_code}")
            return []
    except Exception as e:
        print(f"Excepción al obtener contactos para lista {id_lista}: {e}")
        return []
