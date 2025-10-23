from collections import Counter
from app.dal.usuarioxrol_dal import fetch_roles, fetch_usuarios_roles

def obtener_distribucion_roles():
    """
    Esta función obtiene la distribución de usuarios por cada rol en el sistema.

    - Consulta la lista de roles y la relación usuario-rol desde la base de datos.
    - Usa un diccionario para mapear IDs de rol a sus nombres.
    - Cuenta cuántos usuarios hay por cada rol.
    - Devuelve dos listas: 
        - `labels` con los nombres de los roles.
        - `values` con el número de usuarios por cada uno.
    """

    """
    Consulta las listas necesarias desde la base de datos:
    - roles_data: lista de tuplas (id, nombre del rol)
    - usuarios_data: lista de tuplas con ID de rol asignado a cada usuario
    """
    roles_data = fetch_roles()
    usuarios_data = fetch_usuarios_roles()

    """
    Crear un diccionario que mapea el ID del rol con su nombre.
    Ejemplo: {1: "Administrador", 2: "Gestor"}
    """
    roles_dict = {rol[0]: rol[1] for rol in roles_data}

    """
    Crear un contador que cuente la cantidad de usuarios que tienen cada ID de rol.
    Esto se basa en la lista de asociaciones usuario-rol.
    """
    conteo_roles = Counter([usuario[0] for usuario in usuarios_data])

    """
    Construir la lista de nombres de roles (`labels`) usando el diccionario.
    Si algún ID no se encuentra en el diccionario, se le asigna "Rol {ID}" como nombre por defecto.
    """
    labels = [roles_dict.get(rol_id, f"Rol {rol_id}") for rol_id in conteo_roles.keys()]

    """
    Extraer las cantidades (valores) de usuarios por cada rol.
    """
    values = list(conteo_roles.values())

    """
    Devuelve dos listas:
    - labels: nombres de roles
    - values: número de usuarios por cada rol
    """
    return labels, values
