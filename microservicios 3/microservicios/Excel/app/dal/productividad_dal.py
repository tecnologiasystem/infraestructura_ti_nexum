from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt

def procesar_excel(file_bytes: bytes):
    """
    Procesa un archivo Excel cargado en memoria y calcula estadísticas de productividad
    basado en el avance de tareas, su duración, fechas de inicio/fin y atrasos.

    También genera un gráfico en formato PNG del porcentaje completado por tarea.
    """

    """
    1. Leer el archivo Excel a un DataFrame de pandas.
    """
    df = pd.read_excel(BytesIO(file_bytes))

    """
    2. Verificar que todas las columnas necesarias estén presentes.
    """
    columnas_requeridas = ["Nombre de tarea", "Porcentaje completado", "Duración (días)", "Comienzo", "Fin"]
    for col in columnas_requeridas:
        if col not in df.columns:
            raise ValueError(f"Falta columna: '{col}'.")

    """
    3. Limpiar columnas clave: reemplazar nulos, convertir fechas.
    """
    df["Porcentaje completado"] = df["Porcentaje completado"].fillna(0)
    df["Comienzo"] = pd.to_datetime(df["Comienzo"], errors="coerce")
    df["Fin"] = pd.to_datetime(df["Fin"], errors="coerce")

    """
    4. Calcular días de atraso solo para tareas no completadas.
    """
    hoy = pd.Timestamp.now()
    df["Dias_atraso"] = (hoy - df["Fin"]).dt.days
    df["Dias_atraso"] = df.apply(
        lambda row: row["Dias_atraso"] if (row["Fin"] < hoy and row["Porcentaje completado"] < 100) else 0,
        axis=1
    )

    """
    5. Cálculo de métricas generales de productividad.
    """
    tareas_totales = len(df)
    tareas_finalizadas = len(df[df["Porcentaje completado"] >= 100])
    productividad = round((tareas_finalizadas / tareas_totales) * 100, 2) if tareas_totales > 0 else 0
    promedio_avance = round(df["Porcentaje completado"].mean(), 2)
    duracion_total = df["Duración (días)"].sum()
    promedio_avance_diario = round(df["Porcentaje completado"].sum() / duracion_total, 2) if duracion_total > 0 else 0

    """
    6. Extraer tareas con atraso.
    """
    tareas_retrasadas = df[df["Dias_atraso"] > 0][["Nombre de tarea", "Porcentaje completado", "Dias_atraso"]]

    """
    7. Detectar tareas críticas por baja productividad, atraso y duración alta.
    """
    tareas_criticas = df[
        (df["Porcentaje completado"] < 50) &
        (df["Dias_atraso"] > 5) &
        (df["Duración (días)"] > 5)
    ][["Nombre de tarea", "Porcentaje completado", "Dias_atraso", "Duración (días)"]]

    """
    8. Asignar recomendaciones a cada tarea crítica.
    """
    tareas_criticas["Recomendacion"] = tareas_criticas.apply(
        lambda row: "Dividir tareas grandes y dar seguimiento diario." 
        if row["Duración (días)"] > 15 
        else "Asignar recursos adicionales o replantear dependencias.", axis=1
    )

    """
    9. Generar recomendaciones generales con base en métricas.
    """
    recomendaciones = []
    if promedio_avance < 70:
        recomendaciones.append("Revisar asignación de recursos y dependencias para evitar cuellos de botella.")
    if len(tareas_retrasadas) > 3:
        recomendaciones.append("Programar reuniones de seguimiento semanales con responsables de tareas críticas.")
    if promedio_avance_diario < 2:
        recomendaciones.append("Definir entregables parciales y fechas intermedias para impulsar avance diario.")

    """
    10. Generar gráfico de barras horizontal del avance por tarea.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    df_sorted = df.sort_values(by="Porcentaje completado", ascending=True)
    ax.barh(df_sorted["Nombre de tarea"], df_sorted["Porcentaje completado"])
    ax.set_xlabel("% Completado")
    ax.set_title("Avance de cada tarea")
    plt.tight_layout()

    """
    11. Guardar la figura en un objeto BytesIO como imagen PNG.
    """
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)

    """
    12. Preparar resumen final con todos los datos estructurados.
    """
    df["Comienzo"] = df["Comienzo"].dt.strftime("%Y-%m-%d")
    df["Fin"] = df["Fin"].dt.strftime("%Y-%m-%d")

    resultado = {
        "total_tareas": tareas_totales,
        "tareas_finalizadas": tareas_finalizadas,
        "productividad_global": productividad,
        "promedio_avance": promedio_avance,
        "promedio_avance_diario": promedio_avance_diario,
        "tareas_retrasadas": tareas_retrasadas.to_dict(orient="records"),
        "tareas_mas_criticas": tareas_criticas.to_dict(orient="records"),
        "recomendaciones_generales": recomendaciones,
        "detalle_tareas": df[[
            "Nombre de tarea", "Porcentaje completado", "Dias_atraso", "Duración (días)", "Comienzo", "Fin"
        ]].to_dict(orient="records")
    }

    """
    13. Retorna el gráfico y el análisis como resultado.
    """
    return buffer, resultado
