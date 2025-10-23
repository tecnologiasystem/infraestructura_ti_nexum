import pandas as pd
import os

"""
RUTA_EXCEL define la ubicación del archivo Excel que contiene los nombres y apellidos comunes.
Se construye dinámicamente usando la ubicación del archivo actual (__file__) y un subdirectorio llamado 'data'.
"""
RUTA_EXCEL = os.path.join(os.path.dirname(__file__), "data\\nombres_apellidos.xlsx")

def cargar_nombres_apellidos():
    """
    Carga los nombres y apellidos comunes desde un archivo Excel.

    Retorna:
    - Un conjunto de nombres comunes (en minúsculas y sin nulos)
    - Un conjunto de apellidos comunes (en minúsculas y sin nulos)

    En caso de error (archivo no encontrado o columnas faltantes), retorna conjuntos vacíos.
    """
    try:
        """
        Leemos el archivo Excel usando pandas y extraemos las columnas relevantes.
        Se eliminan los valores nulos y se normalizan a minúsculas.
        """
        df = pd.read_excel(RUTA_EXCEL)
        nombres = set(df['nombres_comunes'].dropna().str.lower())
        apellidos = set(df['apellidos_comunes'].dropna().str.lower())
        return nombres, apellidos

    except Exception as e:
        """
        En caso de cualquier error (como archivo corrupto, columna inexistente, etc.), se notifica por consola.
        Se retorna un par de conjuntos vacíos para evitar romper el flujo del programa.
        """
        print(f"⚠️ Error cargando nombres y apellidos comunes: {e}")
        return set(), set()

"""
Se invoca la función al momento de importar el módulo, para dejar los nombres y apellidos ya listos en variables globales.
"""
nombres_comunes, apellidos_comunes = cargar_nombres_apellidos()

"""
Se imprime por consola la cantidad de nombres y apellidos cargados correctamente.
"""
print(f"📚 Nombres cargados: {len(nombres_comunes)}, Apellidos cargados: {len(apellidos_comunes)}")
