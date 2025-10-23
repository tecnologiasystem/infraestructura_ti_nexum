import pandas as pd
from app.dal.three_dal import load_csv_data

def get_actuaciones_mensuales():
    """
    Esta función calcula cuántas actuaciones se realizaron por mes,
    basándose en la columna 'Fecha de Actuación' de un archivo CSV cargado desde la capa DAL.
    Devuelve un diccionario con claves como '2024-01', '2024-02', etc., y sus respectivas frecuencias.
    """

    df = load_csv_data()

    if "Fecha de Actuación" not in df.columns:
        """
        Si no se encuentra la columna 'Fecha de Actuación', se retorna un mensaje de error
        informando que no es posible continuar el análisis mensual.
        """
        return {"error": "La columna 'Fecha de Actuación' no existe en el archivo."}

    """
    Convierte los valores de la columna 'Fecha de Actuación' a formato datetime.
    Si hay valores inválidos o vacíos, se convierten en NaT (Not a Time).
    """
    df["Fecha de Actuación"] = pd.to_datetime(df["Fecha de Actuación"], errors='coerce')

    """
    Elimina las filas que no tienen una fecha válida (NaT) en la columna 'Fecha de Actuación'.
    Esto garantiza que solo se analicen registros con fechas correctas.
    """
    df = df.dropna(subset=["Fecha de Actuación"])

    """
    Extrae el mes y año de cada fecha como un período (por ejemplo, 2024-01)
    y lo almacena en una nueva columna llamada 'Mes'.
    """
    df["Mes"] = df["Fecha de Actuación"].dt.to_period("M")

    """
    Cuenta cuántas actuaciones ocurrieron en cada mes.
    Luego ordena cronológicamente los resultados usando `sort_index`.
    """
    time_series = df["Mes"].value_counts().sort_index()

    """
    Convierte el índice de tipo Period a string (por ejemplo, de Period('2024-01', 'M') a '2024-01')
    para facilitar la lectura en el diccionario de salida.
    """
    time_series.index = time_series.index.astype(str)

    """
    Devuelve la serie de tiempo como diccionario para uso externo (por ejemplo, en visualización).
    Las claves serán strings con el formato 'YYYY-MM' y los valores serán cantidades de registros.
    """
    return time_series.to_dict()
