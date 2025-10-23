from app.dal.two_dal import load_csv_data

def get_top_radicados():
    """
    Esta función obtiene los 10 valores más frecuentes en la columna 'RADICADO'
    de un archivo CSV. Sirve para identificar los radicados con mayor número
    de registros o menciones.
    """

    df = load_csv_data()

    """
    Verifica si la columna 'RADICADO' existe en el DataFrame.
    Si no está, retorna un mensaje de error que será manejado por el API.
    """
    if "RADICADO" not in df.columns:
        return {"error": "La columna 'RADICADO' no existe en el archivo."}

    """
    Calcula los 10 radicados más frecuentes en el archivo
    usando la función `value_counts()` de pandas.
    """
    top_radicados = df["RADICADO"].value_counts().head(10)

    """
    Convierte la serie de pandas a un diccionario para que pueda
    ser devuelto en formato JSON por el endpoint correspondiente.
    """
    return top_radicados.to_dict()
