from app.dal.focos_trabajable_dal import consultar_cargue_focos_expandible

def obtener_resultados_cargue(filtros: dict):
    """
    Obtiene resultados de cargue de focos según los filtros proporcionados.

    :param filtros: Diccionario con los parámetros para filtrar la consulta.
    :return: Resultado de la función DAL consultar_cargue_focos_expandible.
    """
    return consultar_cargue_focos_expandible(filtros)
