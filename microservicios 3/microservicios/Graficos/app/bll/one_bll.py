from app.dal.one_dal import load_csv_data

def get_accumulated_records():
    """
    Esta función procesa un archivo CSV cargado desde la capa DAL para identificar
    las 10 actuaciones (tipos de 'Actuación') más frecuentes registradas.
    """

    df = load_csv_data()

    """
    Imprime por consola los nombres de las columnas presentes en el DataFrame.
    Esto es útil para depuración si el archivo no tiene los nombres esperados.
    """
    print(df.columns)

    if "Actuación" not in df.columns:
        """
        Si la columna no está presente, retorna un diccionario con un mensaje de error
        indicando que no se puede continuar con el procesamiento.
        """
        return {"error": "La columna 'Actuación' no existe en el archivo CSV."}

    """
    Obtiene los valores únicos en la columna "Actuación" y cuenta cuántas veces
    aparece cada uno. Luego selecciona solo los 10 más frecuentes.
    """
    top_act = df["Actuación"].value_counts().head(10)

    """
    Convierte el resultado de conteo a un diccionario para que pueda ser retornado
    como una estructura serializable (por ejemplo, en una API JSON).
    """
    return top_act.to_dict()
