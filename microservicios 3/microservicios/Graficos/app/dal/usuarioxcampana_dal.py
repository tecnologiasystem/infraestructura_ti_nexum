from app.config.database import get_connectionGraficos

def obtener_campanas():
    """
    Recupera información sobre las campañas y su asignación a usuarios desde la base de datos 'NEXUM'.

    Este procedimiento se conecta a la base de datos a través de `get_connectionGraficos()` y realiza dos consultas:

    1. `SELECT IdCampana, DescripcionCampana FROM campana`:
        - Extrae una lista de campañas existentes.
        - Devuelve una tupla con `IdCampana` (identificador único) y `DescripcionCampana` (nombre o descripción de la campaña).

    2. `SELECT IdCampana FROM UsuariosCampanas`:
        - Recupera la relación entre campañas y usuarios.
        - Devuelve solo los IDs de las campañas que están asignadas a usuarios, permitiendo posteriormente contar cuántos usuarios están asociados a cada campaña.

    Luego de ejecutar ambas consultas:
    - La conexión se cierra correctamente con `conn.close()` para liberar recursos.
    - Se retorna una tupla con:
        - `campanas_data`: lista de campañas disponibles.
        - `usuarios_data`: lista de asignaciones (uno por cada relación campaña-usuario).

    Retorna:
        Tuple (campanas_data, usuarios_data)
    """
    conn = get_connectionGraficos()
    cursor = conn.cursor()

    cursor.execute('SELECT IdCampana, DescripcionCampana FROM campana')
    campanas_data = cursor.fetchall()

    cursor.execute('SELECT IdCampana FROM UsuariosCampanas')
    usuarios_data = cursor.fetchall()

    conn.close()
    return campanas_data, usuarios_data
