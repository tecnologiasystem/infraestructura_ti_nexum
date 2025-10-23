import pandas as pd
import pyodbc
from app.config.database import get_connection

def insertar_datos_llamadas(df: pd.DataFrame) -> int:
    """
    Inserta registros de llamadas en la base de datos a partir de un DataFrame.

    Parámetros:
    - df: DataFrame de pandas con columnas que coinciden con la estructura de la tabla ReporteLlamada.

    Flujo general:
    1. Establece conexión con la base de datos usando la cadena retornada por `get_connection()`.
    2. Limpia y convierte el campo 'tipo' si existe.
    3. Itera fila por fila del DataFrame:
        - Convierte los valores nulos de pandas (NaN) en None para que SQL los acepte.
        - Ejecuta un INSERT por cada fila.
        - Cuenta cuántas inserciones fueron exitosas.
    4. Hace commit de los cambios y cierra la conexión.
    5. Retorna la cantidad total de filas insertadas.
    """
    conn = pyodbc.connect(get_connection())  # Conexión a SQL Server
    cursor = conn.cursor()
    insertados = 0  # Contador de registros insertados exitosamente

    """
    Validación y limpieza previa de datos:
    Si la columna 'tipo' existe, se reemplaza el texto 'MANUAL' por None
    y luego se intenta convertir a tipo numérico (cualquier error se convierte en NaN).
    """
    if 'tipo' in df.columns:
        df['tipo'] = df['tipo'].replace('MANUAL', None)
        df['tipo'] = pd.to_numeric(df['tipo'], errors='coerce')

    """
    Se recorre cada fila del DataFrame para insertarla en la base de datos.
    """
    for _, row in df.iterrows():
        try:
            """
            Se extraen todos los valores de la fila actual en orden de columnas.
            Si algún valor es NaN (pandas), se convierte a None para que SQL lo acepte.
            """
            valores = [row.get(col) for col in df.columns]
            valores = [None if pd.isna(v) else v for v in valores]

            """
            Ejecutamos el INSERT hacia la tabla ReporteLlamada.
            El orden de los campos debe coincidir exactamente con el orden de columnas en la tabla.
            """
            cursor.execute("""
                INSERT INTO ReporteLlamada (
                    id_agent, agent_name, date_call, phone_code, telephone,
                    customer_id, customer_id2, time_sec, time_min, call_cod_id,
                    status_name, tipo, hang_up, campaign_id, campaign_name,
                    list_id, lead_id, uniqueid, tipo_llamada, comments
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, *valores)

            insertados += 1  # Si no falló, incrementamos el contador

        except Exception as e:
            """
            Si ocurre algún error en la fila, se imprime el error y la fila problemática
            para facilitar la depuración y se continúa con la siguiente.
            """
            print(f"❌ Error en fila {_}: {e}")
            print(f"🧾 Fila con error: {row.to_dict()}")
            continue

    """
    Confirmamos todos los cambios en la base de datos y cerramos la conexión.
    """
    conn.commit()
    conn.close()

    """
    Retornamos cuántas filas fueron insertadas exitosamente.
    """
    return insertados
