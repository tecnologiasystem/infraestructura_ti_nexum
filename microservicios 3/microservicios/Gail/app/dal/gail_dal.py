import pyodbc
from itertools import chain
from app.config.database import get_connection
from app.models.gail_models import CampanaGail, ContactoGail

"""
Este módulo contiene la lógica de acceso a datos (DAL) para insertar campañas GAIL completas,
incluyendo listas de contacto, secuencias, reglas de remarcado, outcomes, acciones del sistema
y contactos asociados.
"""

def insertar_campana_gail(campana: CampanaGail):
    """
    Inserta una campaña GAIL completa en la base de datos SQL Server, eliminando previamente cualquier dato con los mismos IDs.
    """

    conn = get_connection()
    cursor = conn.cursor()

    id_campana = str(campana.idCampana)
    id_lista = str(campana.contactList.id)
    id_secuencia = str(campana.sequence.id)
    id_regla = str(campana.redialingRule.id)

    # 🔴 Eliminación previa
    cursor.execute("DELETE FROM ReglasRemarcadoSystemActions WHERE idRegla = ?", id_regla)
    cursor.execute("DELETE FROM ReglasRemarcadoOutcomes WHERE idRegla = ?", id_regla)
    cursor.execute("DELETE FROM ReglasRemarcadoGail WHERE idRegla = ?", id_regla)
    cursor.execute("DELETE FROM SecuenciasGail WHERE idGail = ?", id_secuencia)
    cursor.execute("DELETE FROM ListasContactoGail WHERE idLista = ?", id_lista)
    cursor.execute("DELETE FROM CampañasGail WHERE idGail = ?", id_campana)
    cursor.execute("DELETE FROM ContactosGail_Nueva1 WHERE idLista = ?", id_lista)

    # 📌 Inserción de campaña
    cursor.execute("""
        INSERT INTO CampañasGail (idGail, name, description, status, Pais)
        VALUES (?, ?, ?, ?, ?)
    """, id_campana, campana.name, campana.description, campana.status, campana.pais)

    # 📌 Inserción de lista de contactos
    cursor.execute("""
        INSERT INTO ListasContactoGail (idLista, name, description, idCampaña, Pais)
        VALUES (?, ?, ?, ?, ?)
    """, id_lista, campana.contactList.name, campana.contactList.description, id_campana, campana.pais)

    # 📌 Inserción de secuencia
    cursor.execute("""
        INSERT INTO SecuenciasGail (idGail, name, idCampaña, Pais)
        VALUES (?, ?, ?, ?)
    """, id_secuencia, campana.sequence.name, id_campana, campana.pais)

    # 📌 Inserción de regla de remarcado
    cursor.execute("""
        INSERT INTO ReglasRemarcadoGail (id, idRegla, name, idCampaña, Pais)
        VALUES (?, ?, ?, ?, ?)
    """, id_regla, id_regla, campana.redialingRule.name, id_campana, campana.pais)

    # 📌 Outcomes
    for outcome in campana.redialingRule.outcomes:
        cursor.execute("""
            INSERT INTO ReglasRemarcadoOutcomes (idRegla, outcomeName, definition, Pais)
            VALUES (?, ?, ?, ?)
        """, id_regla, outcome["name"], outcome["definition"], campana.pais)

    # 📌 System Actions
    for outcome_name, actions in campana.redialingRule.systemActions.items():
        for action in actions:
            cursor.execute("""
                INSERT INTO ReglasRemarcadoSystemActions (idRegla, outcomeName, action, delay, maxAttempts, Pais)
                VALUES (?, ?, ?, ?, ?, ?)
            """, id_regla, outcome_name, action["action"], action["delay"], action["maxAttempts"], campana.pais)

    # 📌 Inserción de contactos
    for c in campana.contactos:
        contacto = c if isinstance(c, ContactoGail) else ContactoGail(**c)
        additional = contacto.additionalData or {}

        additional_normalized = {k.strip().lower().replace(" ", "").replace("_", ""): v for k, v in additional.items()}
        phone_numbers = contacto.phoneNumbers or []

        telefono = phone_numbers[0].number if phone_numbers else None
        tipo_telefono = phone_numbers[0].type if phone_numbers else None

        cedula = additional_normalized.get("cedula")
        banco = additional_normalized.get("banco")
        capital = additional_normalized.get("capital")
        entidad = additional_normalized.get("entidad")
        oferta1 = additional_normalized.get("oferta1")
        oferta2 = additional_normalized.get("oferta2")
        oferta3 = additional_normalized.get("oferta3")
        producto = additional_normalized.get("producto")
        intereses = additional_normalized.get("intereses")
        nombre_hmlg = additional_normalized.get("nombre_hmlg")
        saldo_total = additional_normalized.get("saldototal")
        hasta6 = additional_normalized.get("hasta6cuotas")
        hasta12 = additional_normalized.get("hasta12cuotas")
        hasta18 = additional_normalized.get("hasta18cuotas")
        ultimos_digitos = additional_normalized.get("ultimosdigitos")
        tel2 = additional_normalized.get("tel2")
        tel3 = additional_normalized.get("tel3")
        pago_flexible = additional_normalized.get("pagoflexible")

        cursor.execute("""
            INSERT INTO ContactosGail_Nueva1 (
                id, idGail, idLista, firstName, lastName, businessName,
                source, status, telefonoMovil, tipoTelefono, banco,
                cedula, capital, entidad, oferta1, oferta2, oferta3,
                producto, intereses, nombre_HMLG, saldoTotal,
                hasta6Cuotas, hasta12Cuotas, hasta18Cuotas, ultimosDigitos,
                tel2, tel3, pagoFlexible, Pais
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, contacto.id, contacto.id, id_lista,
            contacto.firstName, contacto.lastName,
            contacto.businessName, contacto.source,
            contacto.status, telefono, tipo_telefono,
            banco, cedula, capital, entidad, oferta1, oferta2, oferta3,
            producto, intereses, nombre_hmlg, saldo_total,
            hasta6, hasta12, hasta18, ultimos_digitos,
            tel2, tel3, pago_flexible, campana.pais)

    conn.commit()
    cursor.close()
    conn.close()

    return {"mensaje": "Campaña GAIL registrada correctamente."}
