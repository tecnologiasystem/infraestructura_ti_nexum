from app.config.database import get_connection
import json
import logging

"""
DAL (Data Access Layer) para la gestión de candidatos en SQL Server.
Usa get_connection() centralizado desde database.py
"""

def es_registro_duplicado(conn, nombre_completo, correo_electronico):
    """
    Verifica si ya existe un candidato con el mismo nombre completo o correo.
    """
    query = """
    SELECT COUNT(*)
    FROM info_candidatos
    WHERE nombre_completo = ? OR correo_electronico = ?
    """
    try:
        cursor = conn.cursor()
        cursor.execute(query, (nombre_completo, correo_electronico))
        resultado = cursor.fetchone()[0] > 0
        cursor.close()
        return resultado
    except Exception as e:
        logging.error(f"Error verificando duplicados: {e}")
        return False

def insertar_candidato(candidato):
    """
    Inserta un nuevo candidato en la tabla info_candidatos.
    """
    conn = get_connection()
    if not conn:
        return False

    # Verificar duplicados
    if es_registro_duplicado(conn, candidato['nombre_completo'], candidato['correo_electronico']):
        logging.warning(f"Registro duplicado: {candidato['nombre_completo']} - {candidato['correo_electronico']}")
        conn.close()
        return False

    insert_query = """
    INSERT INTO info_candidatos 
    (nombre_completo, cedula, telefono, correo_electronico, habilidades, experiencia_laboral, formacion_academica, ciudad, direccion, profesion)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        cursor = conn.cursor()
        cursor.execute(insert_query, (
            candidato['nombre_completo'],
            candidato['cedula'],
            candidato['telefono'],
            candidato['correo_electronico'],
            candidato['habilidades'],
            json.dumps(candidato['experiencia_laboral'], ensure_ascii=False),
            json.dumps(candidato['formacion_academica'], ensure_ascii=False),
            candidato['ciudad'],
            candidato['direccion'],
            candidato['profesion']
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error al insertar candidato: {e}")
        conn.close()
        return False
