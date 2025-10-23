import pandas as pd
from app.config.database import CSV_PATH, DELIMITER

def load_csv_data():
    """
    Esta función carga un archivo CSV utilizando la configuración definida en el módulo `database`.
    
    Pasos detallados:
    1. Utiliza `pandas.read_csv` para leer el archivo ubicado en la ruta `CSV_PATH`.
        - `sep=DELIMITER`: se usa el delimitador definido para separar las columnas.
        - `quotechar='"'`: los textos entre comillas dobles se respetan como un solo valor.
        - `on_bad_lines='skip'`: ignora automáticamente líneas que estén mal formateadas o corruptas.
        - `encoding='utf-8'`: asegura la correcta interpretación de caracteres especiales como tildes, ñ, etc.

    2. Limpia los nombres de las columnas quitando espacios al inicio o al final con `.str.strip()`.

    3. Verifica si existen columnas relacionadas con fechas y las convierte al tipo `datetime`:
        - Si hay errores en los datos (como fechas mal escritas), estos se transforman en `NaT` (Not a Time).

    Columnas que intenta convertir a fecha:
        - "Fecha de Actuación"
        - "Fecha de Registro"
        - "Fecha inicia Término"
        - "Fecha finaliza Término"

    Retorna:
        Un `pandas.DataFrame` ya procesado y limpio, listo para análisis posteriores.
    """
    
    df = pd.read_csv(CSV_PATH, sep=DELIMITER, quotechar='"', on_bad_lines='skip', encoding='utf-8')
    df.columns = df.columns.str.strip()

    date_columns = [
        "Fecha de Actuación", 
        "Fecha de Registro", 
        "Fecha inicia Término", 
        "Fecha finaliza Término"
    ]

    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df

