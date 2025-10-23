"""
Módulo de lógica de negocio (BLL) para análisis de productividad.

Este archivo actúa como intermediario entre el controlador (API) y la capa de acceso a datos (DAL).
"""

from app.dal.productividad_dal import procesar_excel

def calcular_productividad(file_bytes: bytes):
    """
    Función principal del BLL para calcular productividad.

    Parámetros:
    - file_bytes: Contenido binario del archivo Excel cargado por el usuario.

    Retorna:
    - imagen: Gráfico generado por la función DAL en formato binario.
    - resultado: Diccionario con métricas o análisis derivado del archivo Excel.
    """
    imagen, resultado = procesar_excel(file_bytes)
    return imagen, resultado
