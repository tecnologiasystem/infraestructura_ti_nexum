from fastapi import APIRouter
from app.bll.contactabilidad_bll import cargar_datos, entrenar_modelo, generar_predicciones, obtener_metricas

""" 
Se crea un enrutador para el módulo de contactabilidad,
donde se definirán los endpoints relacionados con predicciones y métricas.
"""
router = APIRouter()

@router.get("/predicciones")
def obtener_predicciones():
    """
    Endpoint GET /predicciones

    Carga un subconjunto de datos (limitado a 1000 registros),
    entrena un modelo de machine learning con esos datos y
    luego genera predicciones usando ese modelo.

    Retorna las predicciones como una lista de diccionarios.
    """
    df = cargar_datos(limit=1000)
    model, le_tel, le_dia = entrenar_modelo(df)
    resultados = generar_predicciones(model, le_tel, le_dia, df)
    return resultados.to_dict(orient="records")

@router.get("/metricas")
def obtener_metricas():
    """
    Endpoint GET /metricas

    Retorna las métricas de evaluación del modelo entrenado, tales como
    precisión, recall, f1-score, matriz de confusión, etc.
    Esto es útil para analizar el rendimiento del modelo de predicción.
    """
    return obtener_metricas()

