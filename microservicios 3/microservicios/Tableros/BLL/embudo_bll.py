from DAL.embudo_dal import (
    get_funnel_data, 
    get_call_metrics_by_hour, 
    get_cumulative_commitments_comparison, 
    get_assignments_campaign_raw
)

def obtener_embudo_llamadas() -> list[dict]:
    """
    Llama al DAL para obtener las 6 etapas del embudo
    y simplemente regresa la lista tal cual.
    """
    return get_funnel_data()

def obtener_efectividad_por_hora() -> list[dict]:
    """
    Calcula métricas porcentuales por hora basadas en los datos del DAL.
    Añade a cada fila los porcentajes calculados para:
    - llamadas contestadas
    - llamadas abandonadas
    - contacto efectivo
    - promesas de pago

    Se asegura de no dividir por cero usando un total mínimo de 1.
    """
    datos = get_call_metrics_by_hour()
    for fila in datos:
        total = fila["total"] or 1  # evitar división por cero
        fila["contestadas_pct"] = round(fila["contestadas"] / total * 100, 2)
        fila["abandonadas_pct"] = round(fila["abandonadas"] / total * 100, 2)
        fila["contacto_efectivo_pct"] = round(fila["contacto_efectivo"] / total * 100, 2)
        fila["promesas_pago_pct"] = round(fila["promesas_pago"] / total * 100, 2)
    return datos

def obtener_commitments_acumulados():
    """
    Obtiene datos acumulados de commitments comparados a lo largo del tiempo.
    """
    return get_cumulative_commitments_comparison()

def obtener_assignments_campaign(idUsuario: int, rol: str, limit: int = 6) -> list[dict]:
    """
    Obtiene el raw data de assignments por campaña para un usuario y rol dados,
    ordena por valor descendente, limita a los primeros 'limit' y agrupa el resto en 'Other'.

    :param idUsuario: ID del usuario para filtrar asignaciones
    :param rol: rol del usuario para filtrar asignaciones
    :param limit: cantidad máxima de campañas individuales a retornar (default=6)
    :return: lista de diccionarios con nombre de campaña y valor, incluyendo 'Other' si aplica
    """
    raw = get_assignments_campaign_raw(idUsuario, rol)
    sorted_data = sorted(raw, key=lambda x: x['value'], reverse=True)
    top = sorted_data[:limit]
    resto = sorted_data[limit:]
    other_total = sum(item['value'] for item in resto)
    if other_total > 0:
        top.append({"name": "Other", "value": other_total})
    return top
