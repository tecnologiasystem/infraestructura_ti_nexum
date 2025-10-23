from app.dal.four_dal import load_csv_data

"""
📄 Módulo BLL: four_bll.py

Este módulo pertenece a la capa de lógica de negocio (Business Logic Layer).
Se encarga de procesar y devolver los 10 valores más frecuentes de la columna "RADICADO"
a partir de un archivo CSV leído desde la capa DAL.
"""

def get_top_radicados():
    """
    📌 Función que obtiene los 10 radicados más frecuentes desde un archivo CSV.

    Flujo de trabajo:
    1. Carga los datos del archivo CSV usando la función `load_csv_data()` de la capa DAL.
    2. Verifica si la columna "RADICADO" está presente en el DataFrame.
    3. Calcula los 10 valores más repetidos en dicha columna utilizando `value_counts().head(10)`.
    4. Devuelve el resultado como una serie de pandas (puede ser convertido a dict por la capa API).

    Returns:
        - pandas.Series con los 10 radicados más comunes (si todo va bien).
        - dict con clave `"error"` si la columna "RADICADO" no existe.
    """
    df = load_csv_data()
    
    if "RADICADO" not in df.columns:
        return {"error": "La columna 'RADICADO' no existe en el archivo."}
    
    radicados = df["RADICADO"].value_counts().head(10)
    return radicados
