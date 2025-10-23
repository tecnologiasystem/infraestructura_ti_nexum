import pandas as pd
from app.config.database import CSV_PATH, DELIMITER

def load_csv_data():
    """
    Carga un archivo CSV definido por la configuración del sistema y devuelve
    un DataFrame de pandas con las fechas procesadas correctamente.

    Proceso detallado:
    1. Se intenta leer el archivo CSV utilizando la ruta definida en la variable `CSV_PATH`
       y el delimitador definido en `DELIMITER`. El encoding utilizado es "cp1252" para 
       manejar caracteres especiales comunes en documentos en español (como tildes y ñ).
    
    2. Si la columna 'Fecha de Registro' existe:
        - Se convierte al tipo `datetime` utilizando `pd.to_datetime()`.
        - Se usa `errors='coerce'` para manejar valores inválidos como `NaT`.
        - Se define `dayfirst=True` porque se espera el formato de fecha en estilo latino.
        - Se eliminan las filas donde la conversión falló y la fecha quedó como `NaT`.

    3. Si el archivo no se encuentra, se muestra un mensaje por consola y se devuelve un
       DataFrame vacío para evitar que el código falle aguas abajo.

    4. Si ocurre otra excepción, también se captura, imprime un mensaje descriptivo y se
       retorna un DataFrame vacío.

    Retorno:
        pd.DataFrame: Un DataFrame con los datos leídos y validados, o vacío en caso de error.
    """

    try:
        df = pd.read_csv(CSV_PATH, delimiter=DELIMITER, encoding="cp1252")

        if "Fecha de Registro" in df.columns:
            df["Fecha de Registro"] = pd.to_datetime(
                df["Fecha de Registro"],
                errors='coerce',
                dayfirst=True
            )
            df = df.dropna(subset=["Fecha de Registro"])

        return df

    except FileNotFoundError:
        print(f"Archivo no encontrado en la ruta: {CSV_PATH}")

    except Exception as e:
        print(f"Error cargando el archivo CSV: {e}")

    return pd.DataFrame()
