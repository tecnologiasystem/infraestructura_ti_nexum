from app.dal.focos_resultado_dal import obtener_focos_resultado, insertar_foco_resultado

def consultar_focos(filtros: dict):
    """
    Consulta focos resultado aplicando los filtros dados.

    :param filtros: Diccionario con parámetros para filtrar la consulta.
    :return: Resultado de la función DAL obtener_focos_resultado con acción 1 (SELECT).
    """
    return obtener_focos_resultado(1, filtros)  # acción 1 = SELECT

def insertar_focos(filtros: dict):
    """
    Inserta un nuevo foco resultado usando los datos proporcionados en filtros.

    :param filtros: Diccionario con datos para insertar.
    :return: Resultado de la función DAL insertar_foco_resultado, que incluye la acción 2 internamente.
    """
    return insertar_foco_resultado(filtros)     # ya tiene acción 2 adentro
