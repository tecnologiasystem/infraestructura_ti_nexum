import os
import pandas as pd

def verificar_archivo(ruta_archivo):
    """
    Verifica si un archivo existe en la ruta especificada.

    Parámetro:
        ruta_archivo (str): Ruta completa del archivo a verificar.

    Retorna:
        bool: True si el archivo existe, False en caso contrario.

    Uso:
        Se usa para asegurarse de que el archivo que se quiere procesar esté disponible
        antes de intentar abrirlo o leerlo, evitando errores por archivos no encontrados.
    """
    return os.path.exists(ruta_archivo)

def leer_excel(file_path):
    """
    Lee un archivo Excel y devuelve su contenido como un DataFrame de pandas.

    Parámetro:
        file_path (str): Ruta completa del archivo Excel a leer.

    Retorna:
        pandas.DataFrame: Contenido del Excel con valores NaN reemplazados por cadena vacía.

    Detalles de implementación:
        - Usa el motor 'openpyxl' para asegurar compatibilidad con archivos .xlsx.
        - Imprime las columnas detectadas y las primeras 10 filas para facilitar el
          debugging y verificar que la lectura fue correcta.
        - Reemplaza valores NaN (celdas vacías) con strings vacíos para evitar problemas
          al procesar los datos posteriormente.
        - En caso de error al leer el archivo, lanza una excepción con mensaje claro
          para identificar la causa del fallo.
    """
    try:
        df = pd.read_excel(file_path, engine="openpyxl", header=0)
        print("Columnas detectadas:", df.columns)
        print("Primeras filas del DataFrame:", df.head(10))
        
        # Rellenar valores nulos con cadena vacía para evitar errores en procesamiento posterior
        df = df.fillna("")

        return df
    except Exception as e:
        raise Exception(f"Error al leer el Excel: {str(e)}")
