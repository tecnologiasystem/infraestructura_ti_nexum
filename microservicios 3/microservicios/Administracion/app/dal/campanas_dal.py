from app.config.database import get_connection


"""
Obtiene todas las campañas activas desde la base de datos.

Ejecuta:
    EXEC sp_campana_crud @Operacion=2

Retorna:
    Lista de campañas en formato de diccionario.
"""
def obtener_campanas_db():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_campana_crud @Operacion=2")
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return data
    finally:
        conn.close()


"""
Crea una nueva campaña en la base de datos.

Parámetros:
    campana: Objeto con atributo 'descripcionCampana'.

Ejecuta:
    EXEC sp_campana_crud @Operacion=1, @descripcionCampana=?

Retorna:
    Mensaje de éxito.
"""
def crear_campana_db(campana):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "EXEC sp_campana_crud @Operacion=1, @descripcionCampana=?",
            (campana.descripcionCampana,)
        )
        conn.commit()
        return {"message": "Campaña creada correctamente"}
    finally:
        conn.close()


"""
Edita una campaña existente.

Parámetros:
    campana: Objeto con 'idCampana' y 'descripcionCampana'.

Ejecuta:
    EXEC sp_campana_crud @Operacion=3, @idCampana=?, @descripcionCampana=?

Retorna:
    Mensaje de éxito.
"""
def editar_campana_db(campana):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "EXEC sp_campana_crud @Operacion=3, @idCampana=?, @descripcionCampana=?",
            (campana.idCampana, campana.descripcionCampana)
        )
        conn.commit()
        return {"message": "Campaña actualizada correctamente"}
    finally:
        conn.close()


"""
Desactiva (pone en estado inactivo) una campaña.

Parámetros:
    id_campana: ID de la campaña a desactivar.

Ejecuta:
    UPDATE campana SET estado = 0 WHERE idCampana = ?

Retorna:
    Mensaje de éxito.
"""
def eliminar_campana_db(id_campana):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE campana SET estado = 0 WHERE idCampana = ?",
            (id_campana,)
        )
        conn.commit()
        return {"message": "Campaña inactivada correctamente"}
    finally:
        conn.close()


"""
Activa una campaña previamente desactivada.

Parámetros:
    id_campana: ID de la campaña a activar.

Ejecuta:
    UPDATE campana SET estado = 1 WHERE idCampana = ?

Retorna:
    Mensaje de éxito.
"""
def activar_campana_db(id_campana):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE campana SET estado = 1 WHERE idCampana = ?",
            (id_campana,)
        )
        conn.commit()
        return {"message": "Campaña activada correctamente"}
    finally:
        conn.close()

