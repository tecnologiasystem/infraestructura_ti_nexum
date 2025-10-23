import pandas as pd
from app.config.database import CSV_PATH, DELIMITER

def load_csv_data():
    """
    Carga y procesa un archivo CSV desde una ruta y delimitador definidos en el archivo de configuración del sistema.
    
    Esta función realiza las siguientes tareas:
    
    1. `pd.read_csv(...)`:
        - Intenta leer el archivo CSV ubicado en la ruta `CSV_PATH` utilizando el delimitador `DELIMITER`.
        - Se emplea la codificación `cp1252`, que es adecuada para archivos que contienen caracteres especiales en español.

    2. `df.columns.str.strip()`:
        - Elimina cualquier espacio en blanco al inicio o final de los nombres de las columnas.
        - Esta limpieza evita errores comunes al acceder a columnas por nombre exacto.

    3. Conversión de fechas:
        - Se define una lista de columnas con fechas que podrían estar presentes en el archivo.
        - Para cada columna que exista en el DataFrame, se convierte su contenido a tipo `datetime`.
        - Si alguna celda tiene un valor inválido para fecha, se convierte a `NaT` (Not a Time) usando `errors='coerce'`.

    4. Manejo de errores:
        - Si ocurre cualquier excepción durante la carga del archivo (por ejemplo, archivo inexistente, formato incorrecto, etc.),
          el error se imprime en consola y se devuelve un DataFrame vacío para evitar que el programa se detenga.

    Retorna:
        Un `DataFrame` limpio y con columnas de fecha procesadas, o vacío si ocurre algún error.
    """

    try:
        df = pd.read_csv(CSV_PATH, delimiter=DELIMITER, encoding="cp1252")
        df.columns = df.columns.str.strip()

        date_columns = ["Fecha de Actuación", "Fecha de Registro", "Fecha inicia Término", "Fecha finaliza Término"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    except Exception as e:
        print(f"Error cargando el archivo CSV: {e}")
        return pd.DataFrame()
