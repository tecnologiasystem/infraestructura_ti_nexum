from app.dal.excel_dal import leer_excel, guardar_excel
from app.utils.conversor import numero_a_texto
import pandas as pd
from functools import lru_cache
from app.dal.nombre_dal import procesar_nombre_completo_mejorado_v2
from tqdm import tqdm  

"""
Bandera para controlar el uso de 'swifter' (desactivado por estabilidad)
"""
USE_SWIFTER = False

"""
Decorador de cache para evitar reprocesar los mismos nombres completos múltiples veces.
Esto mejora el rendimiento cuando hay muchos valores repetidos.
"""
@lru_cache(maxsize=10000)
def procesar_nombre_cacheado(nombre_completo: str):
    return procesar_nombre_completo_mejorado_v2(nombre_completo)

def primer_nombre_apellido_fuzzy_mejorado(nombre_completo: str) -> str:
    """
    Extrae el primer nombre y el primer apellido desde un nombre completo.

    Aplica una capa de limpieza y usa la función cacheada para evitar recomputar
    resultados ya conocidos.

    Retorna:
    - Cadena en formato "Nombre Apellido"
    """
    if not isinstance(nombre_completo, str) or pd.isna(nombre_completo):
        return ""
    try:
        nombre, apellido = procesar_nombre_cacheado(nombre_completo.strip())
        return f"{nombre} {apellido}".strip()
    except Exception as e:
        print(f"❌ Error al procesar nombre '{nombre_completo}': {e}")
        return ""

def procesar_columnas_numericas_mejorado(input_path: str, output_path: str, columnas: list, modo="numerico"):
    """
    Función principal que recibe un archivo Excel de entrada, limpia y transforma ciertas columnas,
    y guarda el resultado en un nuevo archivo.

    Parámetros:
    - input_path: Ruta del archivo original
    - output_path: Ruta donde se guardará el archivo procesado
    - columnas: Lista de nombres de columnas numéricas a convertir a texto
    - modo: "numerico", "nombres" o "completo" (controla qué acciones se aplican)
    """
    df = leer_excel(input_path)

    """
    Limpieza general de columnas: elimina espacios y normaliza strings
    """
    df.columns = df.columns.str.strip()
    df = df.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x) if col.dtype == "object" else col)

    """
    Detecta si hay una columna llamada 'nombre' para aplicar formato mejorado
    """
    columna_nombre = next((col for col in df.columns if col.lower() == 'nombre'), None)

    if modo in ["completo", "nombres"] and columna_nombre:
        print("⚡ Procesando nombres únicos y aplicando mapeo rápido...")

        """
        Se crea un mapa con resultados ya procesados para nombres únicos (optimiza rendimiento)
        """
        nombres_unicos = df[columna_nombre].dropna().unique()
        mapa_resultados = {}
        for nombre in tqdm(nombres_unicos):
            try:
                resultado = primer_nombre_apellido_fuzzy_mejorado(nombre)
                mapa_resultados[nombre] = resultado
            except Exception as e:
                print(f"❌ Error en nombre '{nombre}': {e}")
                mapa_resultados[nombre] = ""

        """
        Se agrega nueva columna con nombre formateado
        """
        df['Nombre_Formateado'] = df[columna_nombre].map(mapa_resultados)
        print("✅ Nombre_Formateado agregado con éxito")

        """
        Si el modo es solo 'nombres', se guarda el resultado inmediatamente
        """
        if modo == "nombres":
            guardar_excel(df, output_path)
            return output_path

    elif modo in ["completo", "nombres"] and not columna_nombre:
        print("⚠️ No se encontró columna 'nombre'")

    """
    Corrección de nombres de bancos en columnas específicas para evitar errores de formato
    """
    for col in ['Entidad', 'CARTERA', 'banco', 'BANCO']:
        if col in df.columns:
            df[col] = df[col].str.replace(r'\bBBVA\b', 'BBUVA', case=False, regex=True)

    """
    Se validan las columnas indicadas por el usuario comparando nombres en minúscula
    """
    columnas_encontradas = []
    columnas_no_encontradas = []
    columnas_df_limpias = [c.strip().lower() for c in df.columns]

    for col_usuario in columnas:
        col_usuario_clean = col_usuario.strip().lower()
        if col_usuario_clean in columnas_df_limpias:
            idx = columnas_df_limpias.index(col_usuario_clean)
            columnas_encontradas.append(df.columns[idx])
        else:
            columnas_no_encontradas.append(col_usuario)

    if columnas_no_encontradas:
        print(f"⚠️ Columnas no encontradas: {columnas_no_encontradas}")

    """
    Función auxiliar para convertir un número a texto si es posible
    """
    def convertir_si_numero(valor):
        if pd.isna(valor):
            return valor
        try:
            num = float(valor)
            if pd.isna(num):
                return valor
            return numero_a_texto(int(num))
        except:
            return valor

    """
    Recorre y convierte las columnas numéricas indicadas
    """
    for col in columnas_encontradas:
        print(f"🔢 Procesando columna numérica: '{col}'")
        df[col] = df[col].apply(convertir_si_numero)

    print(f"✅ Procesadas {len(columnas_encontradas)}/{len(columnas)} columnas")

    """
    Guarda el DataFrame final con los cambios realizados
    """
    guardar_excel(df, output_path)
    return output_path
