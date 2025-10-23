import pandas as pd

def leer_excel(path: str) -> pd.DataFrame:
    """
    Lee un archivo de Excel (.xlsx) desde la ruta especificada y lo convierte en un DataFrame de pandas.

    Parámetros:
    - path (str): Ruta completa al archivo Excel que se desea leer.

    Retorna:
    - DataFrame con el contenido del archivo Excel.

    Nota:
    - Si el archivo no existe o está corrupto, lanzará una excepción que debe ser controlada donde se llame esta función.
    """
    return pd.read_excel(path)


def guardar_excel(df: pd.DataFrame, path: str):
    """
    Guarda un DataFrame de pandas como un archivo Excel (.xlsx) en la ruta especificada.

    Parámetros:
    - df (pd.DataFrame): El DataFrame que se desea guardar.
    - path (str): Ruta completa donde se desea guardar el archivo Excel.

    Comportamiento:
    - El archivo se guardará sin el índice de pandas (index=False) para que solo se exporten las columnas de datos.

    Nota:
    - Si la carpeta de destino no existe, se lanzará una excepción.
    """
    df.to_excel(path, index=False)
