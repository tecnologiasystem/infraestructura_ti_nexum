from app.config.database import get_connection


"""
Obtiene todas las áreas existentes en la base de datos.

Ejecuta:
    EXEC sp_area_crud @Operacion=2

Retorna:
    Lista de diccionarios, cada uno representando una fila del resultado.
"""
def obtener_areas():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_area_crud @Operacion=2")
        columns = [column[0] for column in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    finally:
        conn.close()


"""
Crea una nueva área en la base de datos.

Parámetros:
    area: Objeto con atributo 'nombreArea'.

Ejecuta:
    EXEC sp_area_crud @Operacion=1, @nombreArea=?

Retorna:
    Mensaje de éxito.
"""
def crear_area_bd(area):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_area_crud @Operacion=1, @nombreArea=?", (area.nombreArea,))
        conn.commit()
        return {"message": "Área creada exitosamente"}
    finally:
        conn.close()


"""
Edita el nombre de un área existente.

Parámetros:
    area: Objeto con atributos 'idArea' y 'nombreArea'.

Ejecuta:
    EXEC sp_area_crud @Operacion=3, @idArea=?, @nombreArea=?

Retorna:
    Mensaje de éxito.
"""
def editar_area_bd(area):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_area_crud @Operacion=3, @idArea=?, @nombreArea=?", (area.idArea, area.nombreArea))
        conn.commit()
        return {"message": "Área actualizada exitosamente"}
    finally:
        conn.close()


"""
Desactiva (elimina lógicamente) un área por su ID.

Parámetros:
    idArea: ID del área a desactivar.

Ejecuta:
    EXEC sp_area_crud @Operacion=4, @idArea=?

Retorna:
    Mensaje de éxito.
"""
def eliminar_area_bd(idArea):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_area_crud @Operacion=4, @idArea=?", (idArea,))
        conn.commit()
        return {"message": "Área desactivada exitosamente"}
    finally:
        conn.close()


"""
Activa un área previamente desactivada por su ID.

Parámetros:
    idArea: ID del área a reactivar.

Ejecuta:
    EXEC sp_area_crud @Operacion=5, @idArea=?

Retorna:
    Mensaje de éxito.
"""
def activar_area_bd(idArea):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("EXEC sp_area_crud @Operacion=5, @idArea=?", (idArea,))
        conn.commit()
        return {"message": "Área activada exitosamente"}
    finally:
        conn.close()
