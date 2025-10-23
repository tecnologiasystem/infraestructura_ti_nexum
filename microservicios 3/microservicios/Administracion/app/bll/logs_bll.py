"""
Capa de lógica de negocio (BLL) para el manejo de logs del sistema.

Incluye funciones para consultar logs de inicio de sesión y exportarlos
con detalles adicionales como campañas asociadas.
"""

from app.dal.logs_dal import obtener_logs
from app.dal.logs_dal import obtener_logs_con_campanas


"""
Función que obtiene todos los registros de inicio de sesión del sistema.

Invoca:
    obtener_logs() desde la capa DAL.

Retorna:
    Lista de logs con detalles como usuario, fecha, IP, etc.
"""
def get_logs_login():
    return obtener_logs()


"""
Función que exporta logs filtrados por usuario y rango de fechas, 
incluyendo campañas asociadas a los registros.

Parámetros:
    usuario: Nombre del usuario a filtrar (puede estar vacío).
    desde: Fecha de inicio del rango (en formato string).
    hasta: Fecha de fin del rango (en formato string).

Invoca:
    obtener_logs_con_campanas() desde la capa DAL.

Retorna:
    Lista de logs filtrados y enriquecidos para exportación.
"""
def exportar_logs_excel(usuario: str, desde: str, hasta: str):
    return obtener_logs_con_campanas(usuario, desde, hasta)

