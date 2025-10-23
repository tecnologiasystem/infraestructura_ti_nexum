from app.config.database import get_connection

def obtener_focos_resultado(accion: int, data: dict):
    """
    Ejecuta el procedimiento almacenado SP_CRUD_CARGUE_FOCOS con la acción y datos indicados.

    Para acción = 1 (SELECT):
    - Procesa rangos en campos tipo "valor1-valor2" para capital, saldoTotal, ofertas y cuotas.
    - Pasa como parámetros los valores mínimos y máximos para el filtro.

    Para otras acciones (INSERT, UPDATE, DELETE):
    - Pasa directamente los valores completos recibidos en 'data'.

    Retorna lista de resultados para consulta, o éxito/fallo para otras acciones.
    """
    conn = get_connection()
    cursor = conn.cursor()

    def parse_rango(campo):
        """
        Convierte un string rango 'valor1-valor2' en dos floats (mínimo, máximo).
        Si no es válido, retorna (None, None).
        """
        valor = data.get(campo)
        if valor and isinstance(valor, str) and '-' in valor:
            try:
                val_min, val_max = valor.split('-')
                return float(val_min.strip()), float(val_max.strip())
            except:
                return None, None
        return None, None

    if accion == 1:
        capital_min, capital_max = parse_rango("capital")
        saldo_min, saldo_max = parse_rango("saldoTotal")
        oferta1_min, oferta1_max = parse_rango("oferta1")
        oferta2_min, oferta2_max = parse_rango("oferta2")
        oferta3_min, oferta3_max = parse_rango("oferta3")
        cuotas3_min, cuotas3_max = parse_rango("cuotas3")
        cuotas6_min, cuotas6_max = parse_rango("cuotas6")
        cuotas12_min, cuotas12_max = parse_rango("cuotas12")

        query = """
            EXEC SP_CRUD_CARGUE_FOCOS 
                @accion = ?,
                @capitalMin = ?, @capitalMax = ?,
                @saldoTotalMin = ?, @saldoTotalMax = ?,
                @oferta1Min = ?, @oferta1Max = ?,
                @oferta2Min = ?, @oferta2Max = ?,
                @oferta3Min = ?, @oferta3Max = ?,
                @cuotas3Min = ?, @cuotas3Max = ?,
                @cuotas6Min = ?, @cuotas6Max = ?,
                @cuotas12Min = ?, @cuotas12Max = ?
        """

        params = [
            1,
            capital_min, capital_max,
            saldo_min, saldo_max,
            oferta1_min, oferta1_max,
            oferta2_min, oferta2_max,
            oferta3_min, oferta3_max,
            cuotas3_min, cuotas3_max,
            cuotas6_min, cuotas6_max,
            cuotas12_min, cuotas12_max,
        ]

    else:
        query = """
            EXEC SP_CRUD_CARGUE_FOCOS 
                @accion = ?, @id = ?, @nombreCliente = ?, @cedula = ?, @telefono = ?, @producto = ?, @entidad = ?,
                @saldoTotal = ?, @capital = ?, @oferta1 = ?, @oferta2 = ?, @oferta3 = ?,
                @cuotas3 = ?, @cuotas6 = ?, @cuotas12 = ?
        """

        params = [
            accion,
            data.get("id"),
            data.get("nombreCliente"),
            data.get("cedula"),
            data.get("telefono"),
            data.get("producto"),
            data.get("entidad"),
            data.get("saldoTotal"),
            data.get("capital"),
            data.get("oferta1"),
            data.get("oferta2"),
            data.get("oferta3"),
            data.get("cuotas3"),
            data.get("cuotas6"),
            data.get("cuotas12"),
        ]

    try:
        cursor.execute(query, params)
        if accion == 1:
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return results
        else:
            conn.commit()
            return {"success": True}
    except Exception as e:
        print("❌ Error CRUD:", e)
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


def insertar_foco_resultado(data: dict):
    """
    Inserta un nuevo foco en la tabla usando SP_CRUD_CARGUE_FOCOS con acción 2 (INSERT).
    Recibe un diccionario con todos los campos requeridos.

    Retorna éxito o detalle de error.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        EXEC SP_CRUD_CARGUE_FOCOS 
            @accion = ?, @id = ?, @nombreCliente = ?, @cedula = ?, @telefono = ?, @producto = ?, @entidad = ?,
            @saldoTotal = ?, @capital = ?, @oferta1 = ?, @oferta2 = ?, @oferta3 = ?,
            @cuotas3 = ?, @cuotas6 = ?, @cuotas12 = ?
    """

    params = [
        2,  # acción: INSERT
        None,
        data.get("nombreCliente"),
        data.get("cedula"),
        data.get("telefono"),
        data.get("producto"),
        data.get("entidad"),
        data.get("saldoTotal"),
        data.get("capital"),
        data.get("oferta1"),
        data.get("oferta2"),
        data.get("oferta3"),
        data.get("cuotas3"),
        data.get("cuotas6"),
        data.get("cuotas12"),
    ]

    try:
        cursor.execute(query, params)
        conn.commit()
        return {"success": True}
    except Exception as e:
        print("❌ Error al insertar en cargueFocos:", e)
        return {"success": False, "error": str(e)}
    finally:
        conn.close()
