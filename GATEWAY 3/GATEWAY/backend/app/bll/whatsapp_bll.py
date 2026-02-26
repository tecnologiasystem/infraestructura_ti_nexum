from app.dal.whatsapp_dal import (
    obtener_whatsapp_detalle_DAL,
    contar_whatsapp_vacios_DAL,
    obtener_estadisticas_whatsapp_DAL
)

"""
Función: obtener_whatsapp_detalle_BLL

Descripción:
Lógica de negocio para obtener los registros de WhatsAppDetalle con WhatsApp asignado.

Parámetros:
    idEncabezado (int): ID del encabezado para filtrar los registros.

Retorna:
    tuple: (resultado, error)
        resultado (list): Lista de registros con WhatsApp.
        error (str): Mensaje de error si ocurre alguna excepción.
"""
def obtener_whatsapp_detalle_BLL(idEncabezado):
    resultado, error = obtener_whatsapp_detalle_DAL(idEncabezado)
    
    if error:
        return None, f"Error al obtener datos de WhatsApp: {error}"
    
    return resultado, None


"""
Función: contar_whatsapp_vacios_BLL

Descripción:
Lógica de negocio para contar los registros de WhatsAppDetalle sin WhatsApp.

Parámetros:
    idEncabezado (int): ID del encabezado para filtrar los registros.

Retorna:
    tuple: (resultado, error)
        resultado (int): Cantidad de registros vacíos.
        error (str): Mensaje de error si ocurre alguna excepción.
"""
def contar_whatsapp_vacios_BLL(idEncabezado):
    resultado, error = contar_whatsapp_vacios_DAL(idEncabezado)
    
    if error:
        return None, f"Error al contar registros vacíos: {error}"
    
    return resultado, None


"""
Función: obtener_estadisticas_whatsapp_BLL

Descripción:
Lógica de negocio para obtener estadísticas completas de WhatsApp.

Parámetros:
    idEncabezado (int): ID del encabezado para filtrar los registros.

Retorna:
    tuple: (resultado, error)
        resultado (dict): Diccionario con las estadísticas.
        error (str): Mensaje de error si ocurre alguna excepción.
"""
def obtener_estadisticas_whatsapp_BLL(idEncabezado):
    resultado, error = obtener_estadisticas_whatsapp_DAL(idEncabezado)
    
    if error:
        return None, f"Error al obtener estadísticas: {error}"
    
    return resultado, None
