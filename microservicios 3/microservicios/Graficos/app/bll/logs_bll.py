from app.dal.logs_dal import obtener_logs_por_dia

def procesar_logs_por_dia():
    """
    Esta función obtiene los logs agrupados por día desde la capa DAL (Data Access Layer)
    y transforma los datos en un formato más estructurado para enviar como respuesta JSON.
    """
    
    datos_raw = obtener_logs_por_dia()

    """
    Lista que almacenará los resultados ya formateados.
    Cada elemento será un diccionario con información por día.
    """
    resultado = []

    for row in datos_raw:
        """
        row[0]: fecha tipo datetime
        row[1]: total de registros/logs de esa fecha
        row[2]: string con los nombres de usuario separados por coma (ej: "juan, pedro, maria")
        """

        """
        Se formatea la fecha a un string "YYYY-MM-DD"
        para que sea legible al retornar por JSON.
        """
        fecha = row[0].strftime("%Y-%m-%d")

        """
        Se extrae el total de logs registrados en esa fecha.
        """
        total = row[1]

        """
        Si la lista de usuarios existe, se separa por coma y espacio ", ".
        Si viene vacía o NULL, se asigna una lista vacía.
        """
        usuarios = row[2].split(", ") if row[2] else []

        """
        Se construye un diccionario estructurado con la información de esa fecha,
        y se agrega a la lista de resultados.
        """
        resultado.append({
            "fecha": fecha,
            "total": total,
            "usuarios": usuarios
        })

    """
    Devuelve una lista de diccionarios, cada uno con:
    - fecha: string con el día
    - total: número de logs
    - usuarios: lista de nombres de usuario que registraron actividad ese día
    """
    return resultado
