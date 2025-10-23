from collections import Counter
from app.dal import usuarioxcampana_dal

def procesar_datos_campanas():
    """
    Esta función consulta las campañas y los usuarios asociados a ellas,
    y luego calcula cuántos usuarios tiene cada campaña.

    Retorna:
        - labels: Lista con los nombres de las campañas.
        - valores: Cantidad de usuarios por cada campaña.
    """

    """
    Consulta los datos crudos desde la capa DAL, obteniendo dos listas:
    - campanas_raw: lista de tuplas con ID y nombre de campaña.
    - usuarios_raw: lista de tuplas con ID de campaña por cada usuario.
    """
    campanas_raw, usuarios_raw = usuarioxcampana_dal.obtener_campanas()

    """
    Crea un diccionario donde la clave es el ID de campaña
    y el valor es el nombre correspondiente.
    Esto servirá para mapear luego los nombres desde los IDs.
    """
    campanas_dict = {campana[0]: campana[1] for campana in campanas_raw}

    """
    Cuenta cuántas veces aparece cada ID de campaña en la lista de usuarios.
    Cada aparición representa un usuario asociado a esa campaña.
    """
    conteo_campanas = Counter([usuario[0] for usuario in usuarios_raw])

    """
    Crea una lista de etiquetas (nombres de campaña) usando el diccionario de mapeo.
    Si algún ID no tiene nombre en el diccionario, se usa un nombre por defecto.
    """
    labels = [campanas_dict.get(camp_id, f"Campaña {camp_id}") for camp_id in conteo_campanas.keys()]

    """
    Obtiene los valores (cantidad de usuarios) asociados a cada campaña.
    El orden coincide con el de la lista de etiquetas.
    """
    valores = list(conteo_campanas.values())

    """
    Devuelve dos listas paralelas:
    - labels: nombres de las campañas.
    - valores: número de usuarios por campaña.
    Estas listas son útiles para construir gráficos o reportes.
    """
    return labels, valores
