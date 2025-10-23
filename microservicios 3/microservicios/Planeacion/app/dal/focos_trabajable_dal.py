import pyodbc
from app.config.database import get_connection

def consultar_cargue_focos_expandible(filtros: dict):
    """
    Ejecuta el procedimiento almacenado SP_CARGUE_FOCOS_EXPANDIBLE con los filtros dados
    para obtener datos relacionados con cargue de focos.

    Parámetros esperados en filtros (opcionalmente pueden ser None):
    - capital
    - SaldoCapital
    - InteresesCorrientes
    - pago
    - pago2
    - valor_recaudo
    - Juridico
    - Insolvencia

    Retorna:
    - Lista de diccionarios con las columnas y filas obtenidas de la consulta.
    - En caso de error, retorna lista vacía.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        EXEC dbo.SP_CARGUE_FOCOS_EXPANDIBLE 
            @capital = ?, 
            @SaldoCapital = ?, 
            @InteresesCorrientes = ?, 
            @pago = ?, 
            @pago2 = ?, 
            @valor_recaudo = ?, 
            @juridico = ?, 
            @insolvencia = ?
    """

    params = [
        filtros.get("capital"),
        filtros.get("SaldoCapital"),
        filtros.get("InteresesCorrientes"),
        filtros.get("pago"),
        filtros.get("pago2"),
        filtros.get("valor_recaudo"),
        filtros.get("Juridico"),
        filtros.get("Insolvencia"),
    ]

    try:
        cursor.execute(query, params)
        # Obtener nombres de columnas del resultado
        columns = [col[0] for col in cursor.description]
        # Crear lista de diccionarios con resultado
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        print("❌ Error al ejecutar el SP:", e)
        results = []
    finally:
        conn.close()

    return results

