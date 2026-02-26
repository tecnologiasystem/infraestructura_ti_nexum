from config.db_config import get_connection

"""
Función: obtener_whatsapp_detalle_DAL

Descripción:
Obtiene los registros de WhatsAppDetalle que tienen WhatsApp asignado.
Excluye registros vacíos y registros con estado "Pausado".

Parámetros:
    idEncabezado (int): ID del encabezado para filtrar los registros.

Retorna:
    tuple: (resultado, error)
        resultado (list): Lista de registros con WhatsApp (excluyendo "Pausado").
        error (str): Mensaje de error si ocurre alguna excepción.
"""
def obtener_whatsapp_detalle_DAL(idEncabezado):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        query = """
            SELECT *
            FROM [NEXUM].[dbo].[WhatsAppDetalle] WITH(NOLOCK)
            WHERE tiene_whatsApp <> ''
            AND tiene_whatsApp <> 'Pausado'
            AND idEncabezado = ?
        """
        
        cursor.execute(query, (idEncabezado,))
        columns = [column[0] for column in cursor.description]
        results = []
        
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        cursor.close()
        conn.close()
        
        return results, None
        
    except Exception as e:
        if conn:
            conn.close()
        return None, str(e)


"""
Función: contar_whatsapp_vacios_DAL

Descripción:
Cuenta los registros de WhatsAppDetalle que no tienen WhatsApp asignado.
Incluye registros vacíos y registros con estado "Pausado".

Parámetros:
    idEncabezado (int): ID del encabezado para filtrar los registros.

Retorna:
    tuple: (resultado, error)
        resultado (int): Cantidad de registros vacíos o pausados.
        error (str): Mensaje de error si ocurre alguna excepción.
"""
def contar_whatsapp_vacios_DAL(idEncabezado):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        query = """
            SELECT COUNT(*) as VACIOS
            FROM [NEXUM].[dbo].[WhatsAppDetalle] WITH(NOLOCK)
            WHERE (tiene_whatsApp = '' OR tiene_whatsApp = 'Pausado')
            AND idEncabezado = ?
        """
        
        cursor.execute(query, (idEncabezado,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        return result[0] if result else 0, None
        
    except Exception as e:
        if conn:
            conn.close()
        return None, str(e)


"""
Función: obtener_estadisticas_whatsapp_DAL

Descripción:
Obtiene estadísticas completas de WhatsApp (total, con WhatsApp, vacíos/pausados).
Los registros con estado "Pausado" se cuentan como vacíos.

Parámetros:
    idEncabezado (int): ID del encabezado para filtrar los registros.

Retorna:
    tuple: (resultado, error)
        resultado (dict): Diccionario con las estadísticas.
            - total: Total de registros
            - con_whatsapp: Registros con WhatsApp válido (excluyendo "Pausado")
            - vacios: Registros vacíos o con estado "Pausado"
        error (str): Mensaje de error si ocurre alguna excepción.
"""
def obtener_estadisticas_whatsapp_DAL(idEncabezado):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        query = """
            SELECT 
                COUNT(*) as TOTAL,
                SUM(CASE WHEN tiene_whatsApp <> '' AND tiene_whatsApp <> 'Pausado' THEN 1 ELSE 0 END) as CON_WHATSAPP,
                SUM(CASE WHEN tiene_whatsApp = '' OR tiene_whatsApp = 'Pausado' THEN 1 ELSE 0 END) as VACIOS
            FROM [NEXUM].[dbo].[WhatsAppDetalle] WITH(NOLOCK)
            WHERE idEncabezado = ?
        """
        
        cursor.execute(query, (idEncabezado,))
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if row:
            return {
                "total": row[0],
                "con_whatsapp": row[1],
                "vacios": row[2]
            }, None
        
        return {"total": 0, "con_whatsapp": 0, "vacios": 0}, None
        
    except Exception as e:
        if conn:
            conn.close()
        return None, str(e)
