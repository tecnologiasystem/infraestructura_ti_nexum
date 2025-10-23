import pandas as pd
from app.config.database import CSV_PATH, DELIMITER

def load_csv_data():
    """
    Carga un archivo CSV desde la ruta especificada en `CSV_PATH` usando el delimitador definido en `DELIMITER`,
    y retorna un DataFrame con los encabezados limpios.

    Pasos que realiza esta función:
    
    1. `pd.read_csv(...)`:
        - Carga el archivo CSV como un DataFrame utilizando la codificación `cp1252`, 
          la cual es común en documentos en español que contienen caracteres especiales.
        - Utiliza el delimitador especificado por la constante `DELIMITER` para separar columnas.
        - La ruta del archivo es determinada por la constante `CSV_PATH`, que debe estar 
          definida en la configuración del sistema (`app.config.database`).

    2. `df.columns.str.strip()`:
        - Elimina espacios en blanco al inicio o final de cada nombre de columna.
        - Esto es fundamental para evitar errores cuando se accede a columnas por nombre,
          ya que los espacios invisibles pueden causar fallos silenciosos en el código.

    3. `return df`:
        - Devuelve el DataFrame limpio y listo para ser usado por otros procesos del sistema.
    """

    df = pd.read_csv(CSV_PATH, delimiter=DELIMITER, encoding="cp1252")
    df.columns = df.columns.str.strip()
    return df
