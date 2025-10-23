from app.config.database import get_connection
from app.models.gail_models import CampanaGail, ContactoGail

def insertar_campana_gail(campana: CampanaGail):
    """
    Inserta en la base de datos toda la información relacionada con una campaña GAIL:
    - Campaña principal
    - Lista de contactos
    - Secuencia
    - Regla de remarcado
    - Outcomes y acciones del sistema
    - Contactos asociados

    Si los registros ya existen (según su ID), primero los elimina para evitar duplicados.

    Parámetros:
        campana (CampanaGail): objeto con toda la información de la campaña a insertar.

    Retorna:
        dict: mensaje de éxito si todo fue insertado correctamente.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Identificadores clave sin convertir a string (se mantienen como UUID)
    id_campana = campana.idCampana
    id_lista = campana.contactList.id
    id_secuencia = campana.sequence.id
    id_regla = campana.redialingRule.id

    try:
        """
        Eliminación previa de registros existentes con los mismos IDs
        para evitar conflictos y asegurar consistencia de datos.
        """
        cursor.execute("DELETE FROM ReglasRemarcadoSystemActions WHERE idRegla = ?", (id_regla,))
        cursor.execute("DELETE FROM ReglasRemarcadoOutcomes WHERE idRegla = ?", (id_regla,))
        cursor.execute("DELETE FROM ReglasRemarcadoGail WHERE idRegla = ?", (id_regla,))
        cursor.execute("DELETE FROM SecuenciasGail WHERE idGail = ?", (id_secuencia,))
        cursor.execute("DELETE FROM ListasContactoGail WHERE idLista = ?", (id_lista,))
        cursor.execute("DELETE FROM CampañasGail WHERE idGail = ?", (id_campana,))
        cursor.execute("DELETE FROM ContactosGail_Nueva1 WHERE idLista = ?", (id_lista,))

        """ Inserción de la campaña principal """
        cursor.execute("""
            INSERT INTO CampañasGail (idGail, name, description, status, Pais)
            VALUES (?, ?, ?, ?, ?)
        """, (id_campana, campana.name, campana.description, campana.status, campana.pais))

        """ Inserción de la lista de contactos """
        cursor.execute("""
            INSERT INTO ListasContactoGail (idLista, name, description, idCampaña, Pais)
            VALUES (?, ?, ?, ?, ?)
        """, (id_lista, campana.contactList.name, campana.contactList.description, id_campana, campana.pais))

        """ Inserción de la secuencia asociada """
        cursor.execute("""
            INSERT INTO SecuenciasGail (idGail, name, idCampaña, Pais)
            VALUES (?, ?, ?, ?)
        """, (id_secuencia, campana.sequence.name, id_campana, campana.pais))

        """ Inserción de la regla de remarcado """
        cursor.execute("""
            INSERT INTO ReglasRemarcadoGail (id, idRegla, name, idCampaña, Pais)
            VALUES (?, ?, ?, ?, ?)
        """, (id_regla, id_regla, campana.redialingRule.name, id_campana, campana.pais))

        """ Inserción de los outcomes asociados a la regla """
        for outcome in campana.redialingRule.outcomes:
            cursor.execute("""
                INSERT INTO ReglasRemarcadoOutcomes (idRegla, outcomeName, definition, Pais)
                VALUES (?, ?, ?, ?)
            """, (id_regla, outcome["name"], outcome["definition"], campana.pais))

        """ Inserción de las acciones del sistema (por outcome) """
        for outcome_name, actions in campana.redialingRule.systemActions.items():
            for action in actions:
                cursor.execute("""
                    INSERT INTO ReglasRemarcadoSystemActions (idRegla, outcomeName, action, delay, maxAttempts, Pais)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (id_regla, outcome_name, action["action"], action["delay"], action["maxAttempts"], campana.pais))

        """ Inserción de cada contacto asociado a la campaña """
        for c in campana.contactos:
            contacto = c if isinstance(c, ContactoGail) else ContactoGail(**c)
            additional = contacto.additionalData or {}
            phone_numbers = contacto.phoneNumbers or []

            telefono = phone_numbers[0].number if phone_numbers else None
            tipo_telefono = phone_numbers[0].type if phone_numbers else None

            # Campos extraídos del diccionario additionalData
            cedula = additional.get("cedula") or additional.get("Cedula")
            banco = additional.get("banco")
            capital = additional.get("Capital")
            entidad = additional.get("entidad")
            oferta1 = additional.get("Oferta 1")
            oferta2 = additional.get("Oferta 2")
            oferta3 = additional.get("Oferta 3")
            producto = additional.get("Producto")
            intereses = additional.get("Intereses")
            nombre_hmlg = additional.get("nombre_HMLG")
            saldo_total = additional.get("Saldo total") or additional.get("Saldo Total")
            hasta6 = additional.get("Hasta 6 cuotas") or additional.get("hasta6Cuotas")
            hasta12 = additional.get("Hasta 12 cuotas") or additional.get("hasta12Cuotas")
            hasta18 = additional.get("hasta18Cuotas")
            ultimos_digitos = additional.get("Ultimos digitos") or additional.get("ultimosDigitos")
            tel2 = additional.get("TEL2")
            tel3 = additional.get("TEL3")
            pago_flexible = additional.get("Pago Flexible")

            # Inserción final del contacto
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
            """, (contacto.id, contacto.id, id_lista,
                contacto.firstName, contacto.lastName,
                contacto.businessName, contacto.source,
                contacto.status, telefono, tipo_telefono,
                banco, cedula, capital, entidad, oferta1, oferta2, oferta3,
                producto, intereses, nombre_hmlg, saldo_total,
                hasta6, hasta12, hasta18, ultimos_digitos,
                tel2, tel3, pago_flexible, campana.pais))

        """ Confirmación de todos los cambios """
        conn.commit()
        return {"mensaje": "Campaña GAIL registrada correctamente."}

    except Exception as e:
        """ En caso de error se hace rollback para evitar datos corruptos """
        conn.rollback()
        raise e
    finally:
        """ Cierre de recursos sin importar si falló o no """
        cursor.close()
        conn.close()
