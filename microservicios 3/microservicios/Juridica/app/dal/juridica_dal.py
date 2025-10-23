from app.config.database import get_connection
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import pyodbc

#------- SUPERNOTARIADO -----------------------------------------------------------------
def obtener_automatizaciones():
    """
    Esta función obtiene el listado de automatizaciones de la tabla SuperNotariadoEncabezado
    junto con un conteo de los detalles ingresados por automatización.

    Detalles:
    - Se conecta a la base de datos usando get_connection().
    - En caso de fallo de conexión devuelve None y mensaje de error.
    - Ejecuta un query SQL que hace LEFT JOIN entre encabezado y detalle,
      contando solo detalles con matrícula no nula ni vacía.
    - Agrupa por idEncabezado y ordena por fecha de carga descendente.
    - Devuelve lista de filas o None con error si ocurre excepción.
    - Siempre cierra cursor y conexión para liberar recursos.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                e.estado,
                u.nombre AS nombreUsuario,
                COUNT(CASE 
                    WHEN d.matricula IS NOT NULL AND LTRIM(RTRIM(d.matricula)) <> '' THEN 1 
                END) AS detallesIngresados
            FROM SuperNotariadoEncabezado e
            LEFT JOIN SuperNotariadoDetalle d ON e.idEncabezado = d.idEncabezado
            LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
            GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
            ORDER BY e.fechaCargue DESC
        """)
        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar SP: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_automatizacion_por_id(id_encabezado: int):
    """
    Obtiene una automatización específica junto con sus detalles por el id_encabezado.

    Detalles:
    - Se conecta y valida conexión.
    - Ejecuta consulta con LEFT JOIN entre encabezado y detalle filtrando por id_encabezado.
    - Devuelve todas las filas que incluyen detalles, puede incluir filas sin detalle.
    - Maneja excepciones mostrando traceback y mensaje.
    - Cierra cursor y conexión siempre para liberar recursos.
    - Retorna tupla (rows, error), con error None si éxito.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                d.idDetalle,
                d.CC,
                d.numItem,
                d.ciudad,
                d.matricula,
                d.direccion,
                d.vinculadoA
            FROM SuperNotariadoEncabezado e
            LEFT JOIN SuperNotariadoDetalle d ON e.idEncabezado = d.idEncabezado
            WHERE e.idEncabezado = ?
        """, id_encabezado)

        rows = cursor.fetchall()
        return rows, None  # 🔧 Devuelve SIEMPRE una tupla con dos valores
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_CC_aConsultar():
    """
    Obtiene la primera cédula (CC) que no tenga matrícula asociada para procesos pendientes.

    Detalles:
    - Conexión estándar y validación.
    - Ejecuta query que busca la primera automatización con detalle sin matrícula (vacia o nula).
    - Ordena y limita a la primer coincidencia.
    - Retorna filas o None con error.
    - Cierra recursos correctamente.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
    SELECT e.idEncabezado,
    CAST(d.CC AS VARCHAR(50)) AS cedula
    FROM SuperNotariadoEncabezado e
    JOIN SuperNotariadoDetalle d ON e.idEncabezado = d.idEncabezado
    WHERE (d.matricula = '' OR d.matricula IS NULL)
      AND e.idEncabezado = (
          SELECT TOP 1 e2.idEncabezado
          FROM SuperNotariadoEncabezado e2
          JOIN SuperNotariadoDetalle d2 ON e2.idEncabezado = d2.idEncabezado
          WHERE d2.matricula = '' OR d2.matricula IS NULL
          ORDER BY e2.idEncabezado ASC
      )
    ORDER BY NEWID()
""")

        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar SP: {e}"

    finally:
        cursor.close()
        conn.close()

def contar_detalles_por_encabezadoSuperNotariado(id_encabezado: int, CC: str = None):
    conn = get_connection()
    if conn is None:
        return 0
    try:
        cursor = conn.cursor()
        if CC and CC.strip():
            cursor.execute("""
                SELECT COUNT(1)
                FROM SuperNotariadoDetalle d
                WHERE d.idEncabezado = ?
                  AND d.CC IS NOT NULL
                  AND LTRIM(RTRIM(d.CC)) <> ''
                  AND LTRIM(RTRIM(d.CC)) = LTRIM(RTRIM(?))
            """, (id_encabezado, CC.strip()))
        else:
            cursor.execute("""
                SELECT COUNT(1)
                FROM SuperNotariadoDetalle d
                WHERE d.idEncabezado = ?
                  AND d.CC IS NOT NULL
                  AND LTRIM(RTRIM(d.CC)) <> ''
            """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0
    finally:
        cursor.close()
        conn.close()


def obtener_detalles_por_encabezado_paginadoSuperNotariado(id_encabezado: int, offset: int, limit: int, CC: str = None):
    """
    Devuelve filas paginadas de detalles para un encabezado (con filtro opcional por cédula).
    """
    conn = get_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        if CC and CC.strip():
            cursor.execute("""
                SELECT 
                    d.idDetalle,
                    d.CC,
                    d.ciudad,
                    d.matricula,
                    d.direccion,
                    d.vinculadoA
                FROM SuperNotariadoDetalle d
                WHERE d.idEncabezado = ?
                  AND d.CC IS NOT NULL
                  AND LTRIM(RTRIM(d.CC)) <> ''
                  AND LTRIM(RTRIM(d.CC)) = LTRIM(RTRIM(?))
                ORDER BY d.idDetalle ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (id_encabezado, CC.strip(), offset, limit))
        else:
            cursor.execute("""
                SELECT 
                    d.idDetalle,
                    d.ciudad,
                    d.matricula,
                    d.direccion,
                    d.vinculadoA
                FROM SuperNotariadoDetalle d
                WHERE d.idEncabezado = ?
                  AND d.CC IS NOT NULL
                  AND LTRIM(RTRIM(d.CC)) <> ''
                ORDER BY d.idDetalle ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (id_encabezado, offset, limit))
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, r)) for r in cursor.fetchall()]
    except Exception:
        return []
    finally:
        cursor.close()
        conn.close()

def contar_total_por_encabezadoSuperNotariado(id_encabezado: int) -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM SuperNotariadoDetalle
            WHERE idEncabezado = ?
        """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_procesados_por_encabezadoSuperNotariado(id_encabezado: int) -> int:
    """
    Cuenta como PROCESADO si tiene algún dato de salida y NO está marcado como 'Pausado'.
    Ajusta las columnas a tus nombres reales si difieren.
    """
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM SuperNotariadoDetalle d
            WHERE d.idEncabezado = ?
              AND (
                    (NULLIF(LTRIM(RTRIM(d.ciudad))   ,'') IS NOT NULL AND LTRIM(RTRIM(d.matricula)) <> 'Pausado')
                 OR (NULLIF(LTRIM(RTRIM(d.matricula)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.direccion))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.vinculadoA))       ,'') IS NOT NULL)
              )
        """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_encabezados_SuperNotariado() -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(1) FROM SuperNotariadoEncabezado WITH(NOLOCK)")
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def obtener_encabezados_paginado_SuperNotariado(offset: int, limit: int):
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                e.estado,
                u.nombre AS nombreUsuario,
                COUNT(DISTINCT d.CC) AS detallesIngresados
            FROM SuperNotariadoEncabezado e
            LEFT JOIN SuperNotariadoDetalle d ON e.idEncabezado = d.idEncabezado
            LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
            GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
            ORDER BY e.fechaCargue DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, (offset, limit))
        return cursor.fetchall()
    finally:
        cursor.close(); conn.close()

#-------------- RUNT --------------------------
def obtener_automatizacionesRunt():
    """
    Obtiene la lista de automatizaciones del módulo Runt con conteo de detalles ingresados.

    Detalles:
    - Conexión estándar.
    - Consulta que cuenta los detalles por cédula distinta (DISTINCT d.cedula).
    - Agrupa y ordena por fecha de carga.
    - Maneja excepciones y cierra recursos.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            e.idEncabezado,
            e.automatizacion,
            e.fechaCargue,
            e.totalRegistros,
            e.estado,
            u.nombre AS nombreUsuario,
            COUNT(DISTINCT d.cedula) AS detallesIngresados
        FROM RuntEncabezado e
        LEFT JOIN RuntDetalle d ON e.idEncabezado = d.idEncabezado
        LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
        GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
        ORDER BY e.fechaCargue DESC
    """)

        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_automatizacion_por_idRunt(id_encabezado: int):
    """
    Obtiene una automatización Runt con sus detalles, filtrando solo detalles con cédula no nula ni vacía.

    Detalles:
    - Usa LEFT JOIN para obtener encabezado y detalles.
    - Filtro para evitar detalles sin cédula válida.
    - Maneja excepciones y siempre cierra recursos.
    - Retorna lista de filas o None con error.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                d.idDetalle,
                d.cedula,
                d.placaVehiculo,
                d.tipoServicio,
                d.estadoVehiculo,
                d.claseVehiculo,
                d.marca,
                d.modelo,
                d.numeroSerie,
                d.numeroChasis,
                d.cilindraje,
                d.tipoCombustible,
                d.autoridadTransito,
                d.linea,
                d.color,
                d.numeroMotor,
                d.numeroVIN,
                d.tipoCarroceria,
                d.polizaSOAT,
                d.revisionTecnomecanica,
                d.limitacionesPropiedad,
                d.garantiasAFavorDe
            FROM RuntEncabezado e
            LEFT JOIN RuntDetalle d ON e.idEncabezado = d.idEncabezado
            WHERE e.idEncabezado = ?
              AND d.cedula IS NOT NULL
              AND LTRIM(RTRIM(d.cedula)) <> ''
        """, id_encabezado)
        return cursor.fetchall()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_CC_aConsultarRunt():
    """
    Obtiene la primera cédula para Runt con campo numeroMotor vacío o nulo, para procesamiento pendiente.

    Detalles:
    - Query anidado para identificar primer idEncabezado con registros sin numeroMotor.
    - Ordena por idDetalle para devolver primer detalle disponible.
    - Maneja errores y cierra recursos correctamente.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
    SELECT
    e.idEncabezado,
    CAST(d.cedula AS VARCHAR(50)) AS cedula
FROM RuntEncabezado e
JOIN RuntDetalle d ON e.idEncabezado = d.idEncabezado
WHERE (d.placaVehiculo = '' OR d.placaVehiculo IS NULL)
AND NOT EXISTS (
    SELECT 1
    FROM RuntDetalle d2
    WHERE d2.cedula = d.cedula
    AND d2.placaVehiculo IS NOT NULL
    AND d2.placaVehiculo <> ''
)
ORDER BY NEWID()

""")

        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar SP: {e}"

    finally:
        cursor.close()
        conn.close()

def contar_detalles_por_encabezadoRunt(id_encabezado: int, cedula: str = None):
    conn = get_connection()
    if conn is None:
        return 0
    try:
        cursor = conn.cursor()
        if cedula and cedula.strip():
            cursor.execute("""
                SELECT COUNT(1)
                FROM RuntDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                  AND LTRIM(RTRIM(d.cedula)) = LTRIM(RTRIM(?))
            """, (id_encabezado, cedula.strip()))
        else:
            cursor.execute("""
                SELECT COUNT(1)
                FROM RuntDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
            """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0
    finally:
        cursor.close()
        conn.close()


def obtener_detalles_por_encabezado_paginadoRunt(id_encabezado: int, offset: int, limit: int, cedula: str = None):
    """
    Devuelve filas paginadas de detalles para un encabezado (con filtro opcional por cédula).
    """
    conn = get_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        if cedula and cedula.strip():
            cursor.execute("""
                SELECT 
                    d.idDetalle,
                    d.cedula,
                    d.placaVehiculo,
                    d.tipoServicio,
                    d.estadoVehiculo,
                    d.claseVehiculo,
                    d.marca,
                    d.modelo,
                    d.numeroSerie,
                    d.numeroChasis,
                    d.cilindraje,
                    d.tipoCombustible,
                    d.autoridadTransito,
                    d.linea,
                    d.color,
                    d.numeroMotor,
                    d.numeroVIN,
                    d.tipoCarroceria,
                    d.polizaSOAT,
                    d.revisionTecnomecanica,
                    d.limitacionesPropiedad,
                    d.garantiasAFavorDe
                FROM RuntDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                  AND LTRIM(RTRIM(d.cedula)) = LTRIM(RTRIM(?))
                ORDER BY d.idDetalle ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (id_encabezado, cedula.strip(), offset, limit))
        else:
            cursor.execute("""
                SELECT 
                    d.idDetalle,
                    d.placaVehiculo,
                    d.tipoServicio,
                    d.estadoVehiculo,
                    d.claseVehiculo,
                    d.marca,
                    d.modelo,
                    d.numeroSerie,
                    d.numeroChasis,
                    d.cilindraje,
                    d.tipoCombustible,
                    d.autoridadTransito,
                    d.linea,
                    d.color,
                    d.numeroMotor,
                    d.numeroVIN,
                    d.tipoCarroceria,
                    d.polizaSOAT,
                    d.revisionTecnomecanica,
                    d.limitacionesPropiedad,
                    d.garantiasAFavorDe
                FROM RuntDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                ORDER BY d.idDetalle ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (id_encabezado, offset, limit))
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, r)) for r in cursor.fetchall()]
    except Exception:
        return []
    finally:
        cursor.close()
        conn.close()

def contar_total_por_encabezadoRunt(id_encabezado: int) -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM RuntDetalle
            WHERE idEncabezado = ?
        """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_procesados_por_encabezadoRunt(id_encabezado: int) -> int:
    """
    Cuenta como PROCESADO si tiene algún dato de salida y NO está marcado como 'Pausado'.
    Ajusta las columnas a tus nombres reales si difieren.
    """
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM RuntDetalle d
            WHERE d.idEncabezado = ?
              AND (
                    (NULLIF(LTRIM(RTRIM(d.placaVehiculo))   ,'') IS NOT NULL AND LTRIM(RTRIM(d.placaVehiculo)) <> 'Pausado')
                 OR (NULLIF(LTRIM(RTRIM(d.tipoServicio)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.estadoVehiculo))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.claseVehiculo))       ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.marca)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.modelo))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.numeroSerie))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.numeroChasis))       ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.cilindraje)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.tipoCombustible))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.autoridadTransito))       ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.linea))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.color))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.numeroMotor))       ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.numeroVIN)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.tipoCarroceria))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.polizaSOAT))       ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.revisionTecnomecanica))       ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.limitacionesPropiedad)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.garantiasAFavorDe))    ,'') IS NOT NULL)
              )
        """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_encabezados_Runt() -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(1) FROM RuntEncabezado WITH(NOLOCK)")
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def obtener_encabezados_paginado_Runt(offset: int, limit: int):
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                e.estado,
                u.nombre AS nombreUsuario,
                COUNT(DISTINCT d.CC) AS detallesIngresados
            FROM RuntEncabezado e
            LEFT JOIN RuntDetalle d ON e.idEncabezado = d.idEncabezado
            LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
            GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
            ORDER BY e.fechaCargue DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, (offset, limit))
        return cursor.fetchall()
    finally:
        cursor.close(); conn.close()

#-------------- RUES--------------------------
def obtener_automatizacionesRues():
    """
    Obtiene lista de automatizaciones Rues con conteo de detalles ingresados.

    Detalles:
    - Consulta con LEFT JOIN encabezado y detalle.
    - Conteo solo de filas con cédula válida.
    - Agrupamiento y ordenamiento por fecha.
    - Manejo de errores y cierre de conexiones.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                e.estado,
                u.nombre AS nombreUsuario,
                COUNT(CASE 
                    WHEN d.identificacion IS NOT NULL AND LTRIM(RTRIM(d.identificacion)) <> '' THEN 1 
                END) AS detallesIngresados
            FROM RuesEncabezado e
            LEFT JOIN RuesDetalle d ON e.idEncabezado = d.idEncabezado
            LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
            GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
            ORDER BY e.fechaCargue DESC
        """)
        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_automatizacion_por_idRues(id_encabezado: int):
    """
    Obtiene automatización Rues específica por ID con sus detalles válidos.

    Detalles:
    - Filtra detalles con cédula válida (no nula ni vacía).
    - Manejo de excepciones y cierre correcto de recursos.
    - Retorna lista de filas o None con error.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                d.idDetalle,
                d.cedula,
                d.nombre,
                d.identificacion,
                d.categoria,
                d.camaraComercio,
                d.numeroMatricula,
                d.actividadEconomica
            FROM RuesEncabezado e
            LEFT JOIN RuesDetalle d ON e.idEncabezado = d.idEncabezado
            WHERE e.idEncabezado = ?
              AND d.cedula IS NOT NULL
              AND LTRIM(RTRIM(d.cedula)) <> ''
        """, id_encabezado)
        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_CC_aConsultarRues():
    """
    Obtiene la primera cédula para Rues con numeroMatricula vacío o nulo para procesamiento pendiente.

    Detalles:
    - Query anidado para encontrar el primer encabezado con detalle sin número de matrícula.
    - Ordena resultados para devolver el detalle más antiguo.
    - Maneja errores y cierra recursos.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
    SELECT e.idEncabezado,
    CAST(d.cedula AS VARCHAR(50)) AS cedula
    FROM RuesEncabezado e
    JOIN RuesDetalle d ON e.idEncabezado = d.idEncabezado
    WHERE (d.numeroMatricula = '' OR d.numeroMatricula IS NULL)
      AND e.idEncabezado = (
          SELECT TOP 1 e2.idEncabezado
          FROM RuesEncabezado e2
          JOIN RuesDetalle d2 ON e2.idEncabezado = d2.idEncabezado
          WHERE d2.numeroMatricula = '' OR d2.numeroMatricula IS NULL
          ORDER BY e2.idEncabezado ASC
      )
    ORDER BY NEWID()
""")

        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar SP: {e}"

    finally:
        cursor.close()
        conn.close()

def contar_detalles_por_encabezadoRues(id_encabezado: int, cedula: str = None):
    conn = get_connection()
    if conn is None:
        return 0
    try:
        cursor = conn.cursor()
        if cedula and cedula.strip():
            cursor.execute("""
                SELECT COUNT(1)
                FROM RuesDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                  AND LTRIM(RTRIM(d.cedula)) = LTRIM(RTRIM(?))
            """, (id_encabezado, cedula.strip()))
        else:
            cursor.execute("""
                SELECT COUNT(1)
                FROM RuesDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
            """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0
    finally:
        cursor.close()
        conn.close()


def obtener_detalles_por_encabezado_paginadoRues(id_encabezado: int, offset: int, limit: int, cedula: str = None):
    """
    Devuelve filas paginadas de detalles para un encabezado (con filtro opcional por cédula).
    """
    conn = get_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        if cedula and cedula.strip():
            cursor.execute("""
                SELECT 
                    d.idDetalle,
                    d.cedula,
                    d.nombre,
                    d.identificacion,
                    d.categoria,
                    d.camaraComercio,
                    d.numeroMatricula,
                    d.actividadEconomica
                FROM RuesDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                  AND LTRIM(RTRIM(d.cedula)) = LTRIM(RTRIM(?))
                ORDER BY d.idDetalle ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (id_encabezado, cedula.strip(), offset, limit))
        else:
            cursor.execute("""
                SELECT 
                    d.idDetalle,
                    d.nombre,
                    d.identificacion,
                    d.categoria,
                    d.camaraComercio,
                    d.numeroMatricula,
                    d.actividadEconomica
                FROM RuesDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                ORDER BY d.idDetalle ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (id_encabezado, offset, limit))
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, r)) for r in cursor.fetchall()]
    except Exception:
        return []
    finally:
        cursor.close()
        conn.close()

def contar_total_por_encabezadoRues(id_encabezado: int) -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM RuesDetalle
            WHERE idEncabezado = ?
        """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_procesados_por_encabezadoRues(id_encabezado: int) -> int:
    """
    Cuenta como PROCESADO si tiene algún dato de salida y NO está marcado como 'Pausado'.
    Ajusta las columnas a tus nombres reales si difieren.
    """
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM RuesDetalle d
            WHERE d.idEncabezado = ?
              AND (
                    (NULLIF(LTRIM(RTRIM(d.nombre))   ,'') IS NOT NULL AND LTRIM(RTRIM(d.numeroMatricula)) <> 'Pausado')
                 OR (NULLIF(LTRIM(RTRIM(d.identificacion)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.categoria))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.camaraComercio))       ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.numeroMatricula)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.actividadEconomica))    ,'') IS NOT NULL)
              )
        """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_encabezados_Rues() -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(1) FROM RuesEncabezado WITH(NOLOCK)")
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def obtener_encabezados_paginado_Rues(offset: int, limit: int):
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                e.estado,
                u.nombre AS nombreUsuario,
                COUNT(DISTINCT d.CC) AS detallesIngresados
            FROM RuesEncabezado e
            LEFT JOIN RuesDetalle d ON e.idEncabezado = d.idEncabezado
            LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
            GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
            ORDER BY e.fechaCargue DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, (offset, limit))
        return cursor.fetchall()
    finally:
        cursor.close(); conn.close()

#-------------- SIMIT -------------------------------------------------------
def obtener_automatizacionesSimit():
    """
    Obtiene la lista de automatizaciones del módulo SIMIT junto con el conteo de detalles ingresados.

    Detalles:
    - Se conecta a la base de datos usando get_connection().
    - Si falla la conexión, retorna None con mensaje de error.
    - Ejecuta una consulta SQL que hace LEFT JOIN entre SimitEncabezado y SimitDetalle.
    - Cuenta los detalles distintos por cédula para cada encabezado.
    - Agrupa por idEncabezado y ordena por fecha de carga descendente.
    - Retorna lista de filas o None con error.
    - Cierra cursor y conexión siempre para evitar fugas de recursos.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            e.idEncabezado,
            e.automatizacion,
            e.fechaCargue,
            e.totalRegistros,
            e.estado,
            u.nombre AS nombreUsuario,
            COUNT(DISTINCT d.cedula) AS detallesIngresados
        FROM SimitEncabezado e
        LEFT JOIN SimitDetalle d ON e.idEncabezado = d.idEncabezado
        LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
        GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
        ORDER BY e.fechaCargue DESC
    """)

        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()


def obtener_automatizacion_por_idSimit(id_encabezado: int):
    """
    Obtiene una automatización SIMIT completa con sus detalles por id_encabezado.

    Detalles:
    - Se conecta y valida la conexión.
    - Ejecuta consulta con LEFT JOIN filtrando detalles con cédula no nula ni vacía.
    - Devuelve todos los detalles asociados a ese encabezado.
    - Maneja excepciones y cierra recursos correctamente.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                d.idDetalle,
                d.cedula,
                d.tipo,
                d.placa,
                d.secretaria
            FROM SimitEncabezado e
            LEFT JOIN SimitDetalle d ON e.idEncabezado = d.idEncabezado
            WHERE e.idEncabezado = ?
              AND d.cedula IS NOT NULL
              AND LTRIM(RTRIM(d.cedula)) <> ''
        """, id_encabezado)
        return cursor.fetchall()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_CC_aConsultarSimit():
    """
    Obtiene la primera cédula del módulo SIMIT con placa vacía o nula para procesamiento pendiente.

    Detalles:
    - Ejecuta query con subconsulta para obtener el primer encabezado que tenga detalles con placa vacía.
    - Ordena resultados para devolver el primer detalle válido.
    - Maneja errores y cierra recursos correctamente.
    """
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
    SELECT e.idEncabezado, CAST(d.cedula AS VARCHAR(50)) AS cedula
    FROM SimitEncabezado e
    JOIN SimitDetalle d ON e.idEncabezado = d.idEncabezado
    WHERE (d.secretaria = '' OR d.secretaria IS NULL)
      AND e.idEncabezado = (
          SELECT TOP 1 e2.idEncabezado
          FROM SimitEncabezado e2
          JOIN SimitDetalle d2 ON e2.idEncabezado = d2.idEncabezado
          WHERE d2.secretaria = '' OR d2.secretaria IS NULL
          ORDER BY e2.idEncabezado ASC
      )
    ORDER BY NEWID()
""")

        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar SP: {e}"

    finally:
        cursor.close()
        conn.close()

def contar_detalles_por_encabezadoSimit(id_encabezado: int, cedula: str = None):
    conn = get_connection()
    if conn is None:
        return 0
    try:
        cursor = conn.cursor()
        if cedula and cedula.strip():
            cursor.execute("""
                SELECT COUNT(1)
                FROM SimitDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                  AND LTRIM(RTRIM(d.cedula)) = LTRIM(RTRIM(?))
            """, (id_encabezado, cedula.strip()))
        else:
            cursor.execute("""
                SELECT COUNT(1)
                FROM SimitDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
            """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0
    finally:
        cursor.close()
        conn.close()


def obtener_detalles_por_encabezado_paginadoSimit(id_encabezado: int, offset: int, limit: int, cedula: str = None):
    """
    Devuelve filas paginadas de detalles para un encabezado (con filtro opcional por cédula).
    """
    conn = get_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        if cedula and cedula.strip():
            cursor.execute("""
                SELECT 
                    d.idDetalle,
                    d.cedula,
                    d.tipo,
                    d.placa,
                    d.secretaria
                FROM SimitDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                  AND LTRIM(RTRIM(d.cedula)) = LTRIM(RTRIM(?))
                ORDER BY d.idDetalle ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (id_encabezado, cedula.strip(), offset, limit))
        else:
            cursor.execute("""
                SELECT 
                    d.idDetalle,
                    d.tipo,
                    d.placa,
                    d.secretaria
                FROM SimitDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                ORDER BY d.idDetalle ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (id_encabezado, offset, limit))
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, r)) for r in cursor.fetchall()]
    except Exception:
        return []
    finally:
        cursor.close()
        conn.close()

def contar_total_por_encabezadoSimit(id_encabezado: int) -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM SimitDetalle
            WHERE idEncabezado = ?
        """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_procesados_por_encabezadoSimit(id_encabezado: int) -> int:
    """
    Cuenta como PROCESADO si tiene algún dato de salida y NO está marcado como 'Pausado'.
    Ajusta las columnas a tus nombres reales si difieren.
    """
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM SimitDetalle d
            WHERE d.idEncabezado = ?
              AND (
                    (NULLIF(LTRIM(RTRIM(d.tipo))   ,'') IS NOT NULL AND LTRIM(RTRIM(d.secretaria)) <> 'Pausado')
                 OR (NULLIF(LTRIM(RTRIM(d.placa)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.secretaria))    ,'') IS NOT NULL)
              )
        """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_encabezados_Simit() -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(1) FROM SimitEncabezado WITH(NOLOCK)")
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def obtener_encabezados_paginado_Simit(offset: int, limit: int):
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                e.estado,
                u.nombre AS nombreUsuario,
                COUNT(DISTINCT d.CC) AS detallesIngresados
            FROM SimitEncabezado e
            LEFT JOIN SimitDetalle d ON e.idEncabezado = d.idEncabezado
            LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
            GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
            ORDER BY e.fechaCargue DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, (offset, limit))
        return cursor.fetchall()
    finally:
        cursor.close(); conn.close()

#-------------- VIGILANCIA ---------------------------------------------------------------------
def obtener_automatizacionesVigilancia():
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            e.idEncabezado,
            e.automatizacion,
            e.fechaCargue,
            e.totalRegistros,
            e.estado,
            u.nombre AS nombreUsuario,
            COUNT(DISTINCT d.radicado) AS detallesIngresados
        FROM VigilanciaEncabezado e
        LEFT JOIN VigilanciaDetalle d ON e.idEncabezado = d.idEncabezado
        LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
        GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
        ORDER BY e.fechaCargue DESC
    """)

        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_automatizacion_por_idVigilancia(id_encabezado: int):
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                d.idDetalle,
                d.radicado,
                d.fechaInicial,
                d.fechaFinal,
                d.fechaActuacion,
                d.actuacion,
                d.anotacion,
                d.fechaIniciaTermino,
                d.fechaFinalizaTermino,
                d.fechaRegistro,
                d.radicadoNuevo
            FROM VigilanciaEncabezado e
            LEFT JOIN VigilanciaDetalle d ON e.idEncabezado = d.idEncabezado
            WHERE e.idEncabezado = ?
              AND d.radicado IS NOT NULL
              AND LTRIM(RTRIM(d.radicado)) <> ''
        """, id_encabezado)
        return cursor.fetchall()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_Radicado_aConsultarVigilancia():
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT TOP 1 
            e.idEncabezado,
            CONVERT(VARCHAR(10), d.fechaInicial, 120) AS fechaInicial,
            CONVERT(VARCHAR(10), d.fechaFinal, 120) AS fechaFinal,
            CAST(d.radicado AS VARCHAR(100)) AS radicado
        FROM VigilanciaEncabezado e
        JOIN VigilanciaDetalle d ON e.idEncabezado = d.idEncabezado
        WHERE (d.actuacion = '' OR d.actuacion IS NULL)
        ORDER BY NEWID()

            """)
        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar SP: {e}"

    finally:
        cursor.close()
        conn.close()

def contar_detalles_por_encabezadoVigilancia(id_encabezado: int, radicado: str = None):
    conn = get_connection()
    if conn is None:
        return 0
    try:
        cursor = conn.cursor()
        if radicado and radicado.strip():
            cursor.execute("""
                SELECT COUNT(1)
                FROM VigilanciaDetalle d
                WHERE d.idEncabezado = ?
                  AND d.radicado IS NOT NULL
                  AND LTRIM(RTRIM(d.radicado)) <> ''
                  AND LTRIM(RTRIM(d.radicado)) = LTRIM(RTRIM(?))
            """, (id_encabezado, radicado.strip()))
        else:
            cursor.execute("""
                SELECT COUNT(1)
                FROM VigilanciaDetalle d
                WHERE d.idEncabezado = ?
                  AND d.radicado IS NOT NULL
                  AND LTRIM(RTRIM(d.radicado)) <> ''
            """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0
    finally:
        cursor.close()
        conn.close()


def obtener_detalles_por_encabezado_paginadoVigilancia(id_encabezado: int, offset: int, limit: int, radicado: str = None):
    """
    Devuelve filas paginadas de detalles para un encabezado (con filtro opcional por cédula).
    """
    conn = get_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        if radicado and radicado.strip():
            cursor.execute("""
                SELECT 
                    d.idDetalle,
                    d.radicado,
                    d.fechaInicial,
                    d.fechaFinal,
                    d.fechaActuacion,
                    d.actuacion,
                    d.anotacion,
                    d.fechaIniciaTermino,
                    d.fechaFinalizaTermino,
                    d.fechaRegistro,
                    d.radicadoNuevo
                FROM VigilanciaDetalle d
                WHERE d.idEncabezado = ?
                  AND d.radicado IS NOT NULL
                  AND LTRIM(RTRIM(d.radicado)) <> ''
                  AND LTRIM(RTRIM(d.radicado)) = LTRIM(RTRIM(?))
                ORDER BY d.idDetalle ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (id_encabezado, radicado.strip(), offset, limit))
        else:
            cursor.execute("""
                SELECT 
                    d.idDetalle,
                   d.fechaActuacion,
                    d.actuacion,
                    d.anotacion,
                    d.fechaIniciaTermino,
                    d.fechaFinalizaTermino,
                    d.fechaRegistro,
                    d.radicadoNuevo
                FROM VigilanciaDetalle d
                WHERE d.idEncabezado = ?
                  AND d.radicado IS NOT NULL
                  AND LTRIM(RTRIM(d.radicado)) <> ''
                ORDER BY d.idDetalle ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (id_encabezado, offset, limit))
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, r)) for r in cursor.fetchall()]
    except Exception:
        return []
    finally:
        cursor.close()
        conn.close()

def contar_total_por_encabezadoVigilancia(id_encabezado: int) -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM VigilanciaDetalle
            WHERE idEncabezado = ?
        """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_procesados_por_encabezadoVigilancia(id_encabezado: int) -> int:
    """
    Cuenta como PROCESADO si tiene algún dato de salida y NO está marcado como 'Pausado'.
    Ajusta las columnas a tus nombres reales si difieren.
    """
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM VigilanciaDetalle d
            WHERE d.idEncabezado = ?
              AND (
                    (NULLIF(LTRIM(RTRIM(d.fechaActuacion))   ,'') IS NOT NULL AND LTRIM(RTRIM(d.actuacion)) <> 'Pausado')
                 OR (NULLIF(LTRIM(RTRIM(d.actuacion)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.anotacion))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.fechaIniciaTermino)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.fechaFinalizaTermino))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.fechaRegistro)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.radicadoNuevo))    ,'') IS NOT NULL)
              )
        """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_encabezados_Vigilancia() -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(1) FROM VigilanciaEncabezado WITH(NOLOCK)")
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def obtener_encabezados_paginado_Vigilancia(offset: int, limit: int):
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                e.estado,
                u.nombre AS nombreUsuario,
                COUNT(DISTINCT d.CC) AS detallesIngresados
            FROM VigilanciaEncabezado e
            LEFT JOIN VigilanciaDetalle d ON e.idEncabezado = d.idEncabezado
            LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
            GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
            ORDER BY e.fechaCargue DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, (offset, limit))
        return cursor.fetchall()
    finally:
        cursor.close(); conn.close()

#-------------- CAMARA COMERCIO --------------------------
def obtener_automatizacionesCamaraComercio():
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            e.idEncabezado,
            e.automatizacion,
            e.fechaCargue,
            e.totalRegistros,
            e.estado,
            u.nombre AS nombreUsuario,
            COUNT(DISTINCT d.cedula) AS detallesIngresados
        FROM CamaraComercioEncabezado e
        LEFT JOIN CamaraComercioDetalle d ON e.idEncabezado = d.idEncabezado
        LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
        GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
        ORDER BY e.fechaCargue DESC
    """)

        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_automatizacion_por_idCamaraComercio(id_encabezado: int):

    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                d.idDetalle,
                d.cedula,
                d.identificacion,
                d.primerNombre,
                d.segundoNombre,
                d.primerApellido,
                d.segundoApellido,
                d.direccion,
                d.pais,
                d.departamento,
                d.municipio,
                d.telefono,
                d.correo
            FROM CamaraComercioEncabezado e
            LEFT JOIN CamaraComercioDetalle d ON e.idEncabezado = d.idEncabezado
            WHERE e.idEncabezado = ?
              AND d.cedula IS NOT NULL
              AND LTRIM(RTRIM(d.cedula)) <> ''
        """, id_encabezado)
        return cursor.fetchall()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_CC_aConsultarCamaraComercio():

    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
    SELECT
    e.idEncabezado,
    CAST(d.cedula AS VARCHAR(50)) AS cedula
FROM CamaraComercioEncabezado e
JOIN CamaraComercioDetalle d ON e.idEncabezado = d.idEncabezado
WHERE (d.identificacion = '' OR d.identificacion IS NULL)
ORDER BY NEWID()
""")

        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar SP: {e}"

    finally:
        cursor.close()
        conn.close()

def contar_detalles_por_encabezadoCamaraComercio(id_encabezado: int, cedula: str = None):
    conn = get_connection()
    if conn is None:
        return 0
    try:
        cursor = conn.cursor()
        if cedula and cedula.strip():
            cursor.execute("""
                SELECT COUNT(1)
                FROM CamaraComercioDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                  AND LTRIM(RTRIM(d.cedula)) = LTRIM(RTRIM(?))
            """, (id_encabezado, cedula.strip()))
        else:
            cursor.execute("""
                SELECT COUNT(1)
                FROM CamaraComercioDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
            """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0
    finally:
        cursor.close()
        conn.close()


def obtener_detalles_por_encabezado_paginadoCamaraComercio(id_encabezado: int, offset: int, limit: int, cedula: str = None):
    """
    Devuelve filas paginadas de detalles para un encabezado (con filtro opcional por cédula).
    """
    conn = get_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        if cedula and cedula.strip():
            cursor.execute("""
                SELECT 
                    d.idDetalle,
                    d.cedula,
                    d.identificacion,
                    d.primerNombre,
                    d.segundoNombre,
                    d.primerApellido,
                    d.segundoApellido,
                    d.direccion,
                    d.pais,
                    d.departamento,
                    d.municipio,
                    d.telefono,
                    d.correo
                FROM CamaraComercioDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                  AND LTRIM(RTRIM(d.cedula)) = LTRIM(RTRIM(?))
                ORDER BY d.idDetalle ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (id_encabezado, cedula.strip(), offset, limit))
        else:
            cursor.execute("""
                SELECT 
                    d.idDetalle,
                    d.identificacion,
                    d.primerNombre,
                    d.segundoNombre,
                    d.primerApellido,
                    d.segundoApellido,
                    d.direccion,
                    d.pais,
                    d.departamento,
                    d.municipio,
                    d.telefono,
                    d.correo
                FROM CamaraComercioDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                ORDER BY d.idDetalle ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (id_encabezado, offset, limit))
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, r)) for r in cursor.fetchall()]
    except Exception:
        return []
    finally:
        cursor.close()
        conn.close()

def contar_total_por_encabezadoCamaraComercio(id_encabezado: int) -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM CamaraComercioDetalle
            WHERE idEncabezado = ?
        """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_procesados_por_encabezadoCamaraComercio(id_encabezado: int) -> int:
    """
    Cuenta como PROCESADO si tiene algún dato de salida y NO está marcado como 'Pausado'.
    Ajusta las columnas a tus nombres reales si difieren.
    """
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM CamaraComercioDetalle d
            WHERE d.idEncabezado = ?
              AND (
                    (NULLIF(LTRIM(RTRIM(d.identificacion))   ,'') IS NOT NULL AND LTRIM(RTRIM(d.identificacion)) <> 'Pausado')
                 OR (NULLIF(LTRIM(RTRIM(d.primerNombre)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.segundoNombre))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.primerApellido)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.segundoApellido))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.direccion)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.pais))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.departamento)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.municipio))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.telefono)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.correo))    ,'') IS NOT NULL)
              )
        """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_encabezados_CamaraComercio() -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(1) FROM CamaraComercioEncabezado WITH(NOLOCK)")
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def obtener_encabezados_paginado_CamaraComercio(offset: int, limit: int):
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                e.estado,
                u.nombre AS nombreUsuario,
                COUNT(DISTINCT d.CC) AS detallesIngresados
            FROM CamaraComercioEncabezado e
            LEFT JOIN CamaraComercioDetalle d ON e.idEncabezado = d.idEncabezado
            LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
            GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
            ORDER BY e.fechaCargue DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, (offset, limit))
        return cursor.fetchall()
    finally:
        cursor.close(); conn.close()

#-------------- JURIDICO --------------------------
def obtener_automatizacionesJuridico():
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            e.idEncabezado,
            e.automatizacion,
            e.fechaCargue,
            e.totalRegistros,
            e.estado,
            u.nombre AS nombreUsuario,
            COUNT(DISTINCT d.nombreCompleto) AS detallesIngresados
        FROM JuridicoEncabezado e
        LEFT JOIN JuridicoDetalle d ON e.idEncabezado = d.idEncabezado
        LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
        GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
        ORDER BY e.fechaCargue DESC
    """)

        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_automatizacion_por_idJuridico(id_encabezado: int):
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                d.idDetalle,
                d.nombreCompleto,
                d.departamento,
                d.ciudad,
                d.especialidad
            FROM JuridicoEncabezado e
            LEFT JOIN JuridicoDetalle d ON e.idEncabezado = d.idEncabezado
            WHERE e.idEncabezado = ?
              AND d.nombreCompleto IS NOT NULL
              AND LTRIM(RTRIM(d.nombreCompleto)) <> ''
        """, id_encabezado)
        return cursor.fetchall()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

class DetalleModel(BaseModel):
    nombreCompleto: str
    departamento: Optional[str]
    ciudad: Optional[str]
    especialidad: Optional[str]
    idNombres: Optional[str]
    idDetalleJuridico: Optional[str]
    idActuaciones: Optional[str]
    
    
class EncabezadoModel(BaseModel):
    automatizacion: str
    idUsuario: int
    fechaCargue: datetime
    totalRegistros: int
    estado: Optional[str] = "En proceso"
    detalles: List[DetalleModel]

def insertar_encabezado(encabezado: EncabezadoModel) -> int:
    conn = get_connection()
    if conn is None:
        return -1
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO JuridicoEncabezado (automatizacion, idUsuario, fechaCargue, totalRegistros, estado)
            OUTPUT INSERTED.idEncabezado
            VALUES (?, ?, ?, ?, ?)
        """, encabezado.automatizacion, encabezado.idUsuario,
             encabezado.fechaCargue, encabezado.totalRegistros, encabezado.estado)

        row = cursor.fetchone()
        conn.commit()

        if row:
            id_encabezado = int(row[0])
            print("✅ Insert encabezado:", id_encabezado)
            return id_encabezado
        else:
            return -1
    except Exception as e:
        import traceback
        traceback.print_exc()
        return -1
    finally:
        cursor.close()
        conn.close()

def insertar_detalle(idEncabezado: int, detalle: DetalleModel):
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()

        # Declaración de @idDetalle como variable de salida
        cursor.execute("""
            DECLARE @idDetalle INT;
            EXEC SP_CRUD_JuridicoDetalle
                @Accion=1,
                @idDetalle=@idDetalle OUTPUT,
                @idEncabezado=?, 
                @nombreCompleto=?, 
                @departamento=?, 
                @ciudad=?, 
                @especialidad=?,
                @idNombres=?,
                @idDetalleJuridico=?,
                @idActuaciones=?;
            SELECT @idDetalle;
        """, idEncabezado, detalle.nombreCompleto, detalle.departamento, detalle.ciudad,
           detalle.especialidad, detalle.idNombres, detalle.idDetalleJuridico, detalle.idActuaciones)

        row = cursor.fetchone()
        id_generado = row[0] if row else None

        conn.commit()
        return id_generado, None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def obtener_detalles_agrupados():
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.nombreCompleto, d.*
            FROM JuridicoDetalle d
            INNER JOIN JuridicoEncabezado e ON d.idEncabezado = e.idEncabezado
            ORDER BY e.nombreCompleto
        """)

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        agrupado = {}
        for item in data:
            nombreCompleto = item["nombreCompleto"]
            agrupado.setdefault(nombreCompleto, []).append(item)

        return [{"nombreCompleto": c, "detalles": dets} for c, dets in agrupado.items()]

    except Exception as e:
        import traceback
        traceback.print_exc()
        return []

    finally:
        cursor.close()
        conn.close()

def obtener_detalles_agrupados_Juridico():
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nombreCompleto, departamento, ciudad, especialidad, idNombres, idDetalleJuridico, idActuaciones
            FROM JuridicoDetalle WITH (NOLOCK)
            WHERE 
                ISNULL(idNombres, '') <> '' OR 
                ISNULL(idDetalleJuridico, '') <> '' OR 
                ISNULL(idActuaciones, '') <> '' 
            ORDER BY nombreCompleto
        """)

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]

        agrupado = {}
        for item in data:
            nombreCompleto = item["nombreCompleto"]
            agrupado.setdefault(nombreCompleto, []).append(item)

        return [{"nombreCompleto": nombreCompleto, "detalles": detalles} for nombreCompleto, detalles in agrupado.items()]

    except Exception as e:
        import traceback
        traceback.print_exc()
        return []

    finally:
        cursor.close()
        conn.close()

def obtener_correo_usuarioJuridico(id_usuario: int) -> str:
    conn = get_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT correo FROM UsuariosApp WHERE idUsuarioApp = ?", id_usuario)
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    finally:
        cursor.close()
        conn.close()

def obtener_detalles_por_encabezado(id_encabezado: int, accion: int):
    conn = get_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        tsql = """
        DECLARE @out INT;
        EXEC dbo.SP_CRUD_JuridicoDetalle
            @Accion = ?,
            @idDetalle = @out OUTPUT,
            @idEncabezado = ?,
            @nombreCompleto = NULL,
            @departamento = NULL,
            @ciudad = NULL,
            @especialidad = NULL,
            @numItem = NULL,
            @idNombres = NULL,
            @idDetalleJuridico = NULL,
            @idActuaciones = NULL;
        """
        cursor.execute(tsql, (accion, id_encabezado))
        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    except Exception:
        import traceback
        traceback.print_exc()
        return []
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass

def obtener_accion4_por_encabezado(id_encabezado: int):
    return obtener_detalles_por_encabezado(id_encabezado, 4)

def obtener_accion5_por_encabezado(id_encabezado: int):
    return obtener_detalles_por_encabezado(id_encabezado, 5)


def obtener_idUsuario_por_encabezado(idEncabezado: int) -> Optional[int]:
    conn = get_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT idUsuario
            FROM JuridicoEncabezado
            WHERE idEncabezado = ?
        """, idEncabezado)
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    finally:
        cursor.close()
        conn.close()

def correo_ya_enviado(idEncabezado: int) -> bool:
    conn = get_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT correoEnviado
            FROM JuridicoEncabezado
            WHERE idEncabezado = ?
        """, idEncabezado)
        row = cursor.fetchone()
        return bool(row[0]) if row else False
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        conn.close()

def marcar_correo_enviado(idEncabezado: int) -> bool:
    conn = get_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE JuridicoEncabezado
            SET correoEnviado = 1
            WHERE idEncabezado = ?
        """, idEncabezado)
        conn.commit()
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        conn.close()

#--------- PAUSAR---------------------------------------------
def marcar_pausa_encabezado(id_encabezado: int, fecha_pausa: datetime) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE JuridicoEncabezado
            SET estado = ?, fechaPausa = ?
            WHERE idEncabezado = ?
        """, 'Pausado', fecha_pausa, id_encabezado)
        conn.commit()
        return True
    except:
        return False
    finally:
        cursor.close()
        conn.close()

def quitar_pausa_encabezado(id_encabezado: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE JuridicoEncabezado
            SET estado = ?, fechaPausa = NULL
            WHERE idEncabezado = ?
        """, 'En proceso', id_encabezado)
        conn.commit()
        return True
    except:
        return False
    finally:
        cursor.close()
        conn.close()
        
def pausar_detalle_encabezado(id_encabezado: int) -> bool:
    sql = """
    UPDATE dbo.JuridicoDetalle
    SET
      idNombres      = CASE WHEN idNombres      IS NULL OR idNombres      = '' THEN 'Pausado' ELSE idNombres      END
    WHERE idEncabezado = ?
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, id_encabezado)
        conn.commit()
        return True
    except:
        return False
    finally:
        cur.close()
        conn.close()

def reanudar_detalle_encabezado(id_encabezado: int) -> bool:
    sql = """
    UPDATE dbo.JuridicoDetalle
    SET
      idNombres      = CASE WHEN idNombres      = 'Pausado' THEN NULL ELSE idNombres     END
    WHERE idEncabezado = ?
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, id_encabezado)
        conn.commit()
        return True
    except:
        return False
    finally:
        cur.close()
        conn.close()
    
#-------------- TYBA   --------------------------
def obtener_automatizacionesTyba():
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            e.idEncabezado,
            e.automatizacion,
            e.fechaCargue,
            e.totalRegistros,
            e.estado,
            u.nombre AS nombreUsuario,
            COUNT(DISTINCT d.cedula) AS detallesIngresados
        FROM TybaEncabezado e
        LEFT JOIN TybaDetalle d ON e.idEncabezado = d.idEncabezado
        LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
        GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
        ORDER BY e.fechaCargue DESC
    """)

        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_automatizacion_por_idTyba(id_encabezado: int):
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                d.idDetalle,
                d.cedula,
                d.radicado,
                d.proceso,
                d.departamento,
                d.coorporacion,
                d.distrito,
                d.despacho,
                d.telefono,
                d.correo,
                d.fechaProvidencia,
                d.tipoProceso,
                d.subclaseProceso,
                d.ciudad,
                d.especialidad,
                d.numeroDespacho,
                d.direccion,
                d.celular,
                d.fechaPublicacion,
                d.sujetos,
                d.actuaciones
            FROM TybaEncabezado e
            LEFT JOIN TybaDetalle d ON e.idEncabezado = d.idEncabezado
            WHERE e.idEncabezado = ?
              AND d.cedula IS NOT NULL
              AND LTRIM(RTRIM(d.cedula)) <> ''
        """, id_encabezado)
        return cursor.fetchall()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_CC_aConsultarTyba():
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
    SELECT
    e.idEncabezado,
    CAST(d.cedula AS VARCHAR(50)) AS cedula
FROM TybaEncabezado e
JOIN TybaDetalle d ON e.idEncabezado = d.idEncabezado
WHERE (d.radicado = '' OR d.radicado IS NULL)
AND NOT EXISTS (
    SELECT 1
    FROM TybaDetalle d2
    WHERE d2.cedula = d.cedula
    AND d2.radicado IS NOT NULL
    AND d2.radicado <> ''
)
ORDER BY NEWID()

""")

        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar SP: {e}"

    finally:
        cursor.close()
        conn.close()

def contar_detalles_por_encabezadoTyba(id_encabezado: int, cedula: str = None):
    conn = get_connection()
    if conn is None:
        return 0
    try:
        cursor = conn.cursor()
        if cedula and cedula.strip():
            cursor.execute("""
                SELECT COUNT(1)
                FROM TybaDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                  AND LTRIM(RTRIM(d.cedula)) = LTRIM(RTRIM(?))
            """, (id_encabezado, cedula.strip()))
        else:
            cursor.execute("""
                SELECT COUNT(1)
                FROM TybaDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
            """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0]) if row else 0
    except Exception:
        return 0
    finally:
        cursor.close()
        conn.close()


def obtener_detalles_por_encabezado_paginadoTyba(id_encabezado: int, offset: int, limit: int, cedula: str = None):
    """
    Devuelve filas paginadas de detalles para un encabezado (con filtro opcional por cédula).
    """
    conn = get_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        if cedula and cedula.strip():
            cursor.execute("""
                SELECT 
                    d.idDetalle,
                    d.cedula,
                    d.radicado,
                    d.proceso,
                    d.departamento,
                    d.coorporacion,
                    d.distrito,
                    d.despacho,
                    d.telefono,
                    d.correo,
                    d.fechaProvidencia,
                    d.tipoProceso,
                    d.subclaseProceso,
                    d.ciudad,
                    d.especialidad,
                    d.numeroDespacho,
                    d.direccion,
                    d.celular,
                    d.fechaPublicacion,
                    d.sujetos,
                    d.actuaciones
                FROM TybaDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                  AND LTRIM(RTRIM(d.cedula)) = LTRIM(RTRIM(?))
                ORDER BY d.idDetalle ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (id_encabezado, cedula.strip(), offset, limit))
        else:
            cursor.execute("""
                SELECT 
                    d.idDetalle,
                    d.radicado,
                    d.proceso,
                    d.departamento,
                    d.coorporacion,
                    d.distrito,
                    d.despacho,
                    d.telefono,
                    d.correo,
                    d.fechaProvidencia,
                    d.tipoProceso,
                    d.subclaseProceso,
                    d.ciudad,
                    d.especialidad,
                    d.numeroDespacho,
                    d.direccion,
                    d.celular,
                    d.fechaPublicacion,
                    d.sujetos,
                    d.actuaciones
                FROM TybaDetalle d
                WHERE d.idEncabezado = ?
                  AND d.cedula IS NOT NULL
                  AND LTRIM(RTRIM(d.cedula)) <> ''
                ORDER BY d.idDetalle ASC
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """, (id_encabezado, offset, limit))
        cols = [c[0] for c in cursor.description]
        return [dict(zip(cols, r)) for r in cursor.fetchall()]
    except Exception:
        return []
    finally:
        cursor.close()
        conn.close()

def contar_total_por_encabezadoTyba(id_encabezado: int) -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM TybaDetalle
            WHERE idEncabezado = ?
        """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_procesados_por_encabezadoTyba(id_encabezado: int) -> int:
    """
    Cuenta como PROCESADO si tiene algún dato de salida y NO está marcado como 'Pausado'.
    Ajusta las columnas a tus nombres reales si difieren.
    """
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(1)
            FROM TybaDetalle d
            WHERE d.idEncabezado = ?
              AND (
                    (NULLIF(LTRIM(RTRIM(d.radicado))   ,'') IS NOT NULL AND LTRIM(RTRIM(d.radicado)) <> 'Pausado')
                 OR (NULLIF(LTRIM(RTRIM(d.proceso)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.departamento))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.coorporacion)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.distrito))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.despacho)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.telefono))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.correo)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.fechaProvidencia))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.tipoProceso)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.subclaseProceso))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.ciudad)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.especialidad))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.numeroDespacho)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.celular))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.fechaPublicacion)) ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.sujetos))    ,'') IS NOT NULL)
                 OR (NULLIF(LTRIM(RTRIM(d.actuaciones)) ,'') IS NOT NULL)                
              )
        """, (id_encabezado,))
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def contar_encabezados_Tyba() -> int:
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(1) FROM TybaEncabezado WITH(NOLOCK)")
        row = cursor.fetchone()
        return int(row[0] or 0)
    finally:
        cursor.close(); conn.close()

def obtener_encabezados_paginado_Tyba(offset: int, limit: int):
    conn = get_connection(); cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                e.estado,
                u.nombre AS nombreUsuario,
                COUNT(DISTINCT d.CC) AS detallesIngresados
            FROM TybaEncabezado e
            LEFT JOIN TybaDetalle d ON e.idEncabezado = d.idEncabezado
            LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
            GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
            ORDER BY e.fechaCargue DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """, (offset, limit))
        return cursor.fetchall()
    finally:
        cursor.close(); conn.close()


#-------------- VIGENCIA --------------------------
def obtener_automatizacionesVigencia():
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT 
            e.idEncabezado,
            e.automatizacion,
            e.fechaCargue,
            e.totalRegistros,
            e.estado,
            u.nombre AS nombreUsuario,
            COUNT(DISTINCT d.cedula) AS detallesIngresados
        FROM VigenciaEncabezado e
        LEFT JOIN VigenciaDetalle d ON e.idEncabezado = d.idEncabezado
        LEFT JOIN UsuariosApp u ON e.idUsuario = u.idUsuarioApp
        GROUP BY e.idEncabezado, e.automatizacion, e.fechaCargue, e.totalRegistros, e.estado, u.nombre
        ORDER BY e.fechaCargue DESC
    """)

        return cursor.fetchall(), None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

def obtener_automatizacion_por_idVigencia(id_encabezado: int):
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                e.idEncabezado,
                e.automatizacion,
                e.fechaCargue,
                e.totalRegistros,
                d.idDetalle,
                d.nombre,
                d.cedula,
                d.vigencia,
                d.fechaConsulta
            FROM VigenciaEncabezado e
            LEFT JOIN VigenciaDetalle d ON e.idEncabezado = d.idEncabezado
            WHERE e.idEncabezado = ?
              AND d.cedula IS NOT NULL
              AND LTRIM(RTRIM(d.cedula)) <> ''
        """, id_encabezado)
        return cursor.fetchall()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, f"Error al ejecutar la consulta: {e}"
    finally:
        cursor.close()
        conn.close()

class DetalleModelVigencia(BaseModel):
    nombre: str
    cedula: str

class EncabezadoModelVigencia(BaseModel):
    automatizacion: str
    idUsuario: int
    fechaCargue: datetime
    totalRegistros: int
    estado: Optional[str] = "En proceso"
    detalles: List[DetalleModelVigencia]

def insertar_encabezadoVigencia(encabezado: EncabezadoModelVigencia) -> int:
    conn = get_connection()
    if conn is None:
        return -1
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO VigenciaEncabezado (automatizacion, idUsuario, fechaCargue, totalRegistros, estado)
            OUTPUT INSERTED.idEncabezado
            VALUES (?, ?, ?, ?, ?)
        """, encabezado.automatizacion, encabezado.idUsuario,
             encabezado.fechaCargue, encabezado.totalRegistros, encabezado.estado)

        row = cursor.fetchone()
        conn.commit()

        if row:
            id_encabezado = int(row[0])
            print("✅ Insert encabezado:", id_encabezado)
            return id_encabezado
        else:
            return -1
    except Exception as e:
        import traceback
        traceback.print_exc()
        return -1
    finally:
        cursor.close()
        conn.close()

def insertar_detalleVigencia(idEncabezado: int, detalle: DetalleModelVigencia):
    conn = get_connection()
    if conn is None:
        return None, "Error al conectar con la base de datos"
    try:
        cursor = conn.cursor()

        # Declaración de @idDetalle como variable de salida
        cursor.execute("""
            DECLARE @idDetalle INT;
            EXEC SP_CRUD_VIGENCIA_DETALLE
                @Accion=1,
                @idDetalle=@idDetalle OUTPUT,
                @idEncabezado=?, 
                @nombre=?, 
                @cedula=? 
            SELECT @idDetalle;
        """, idEncabezado, detalle.nombre, detalle.cedula)

        row = cursor.fetchone()
        id_generado = row[0] if row else None

        conn.commit()
        return id_generado, None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None, str(e)
    finally:
        cursor.close()
        conn.close()

def obtener_correo_usuarioVigencia(id_usuario: int) -> str:
    conn = get_connection()
    if conn is None:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT correo FROM UsuariosApp WHERE idUsuarioApp = ?", id_usuario)
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    finally:
        cursor.close()
        conn.close()

def obtener_detalles_por_encabezadoVigencia(id_encabezado: int):
    conn = get_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nombre, cedula, vigencia, fechaConsulta
            FROM VigenciaDetalle WITH (NOLOCK)
            WHERE idEncabezado = ?
            ORDER BY cedula
        """, id_encabezado)

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        import traceback
        traceback.print_exc()
        return []

    finally:
        cursor.close()
        conn.close()


def obtener_idUsuario_por_encabezadoVigencia(idEncabezado: int) -> Optional[int]:
    conn = get_connection()
    if conn is None:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT idUsuario
            FROM VigenciaEncabezado
            WHERE idEncabezado = ?
        """, idEncabezado)
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    finally:
        cursor.close()
        conn.close()

def correo_ya_enviadoVigencia(idEncabezado: int) -> bool:
    conn = get_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT correoEnviado
            FROM VigenciaEncabezado
            WHERE idEncabezado = ?
        """, idEncabezado)
        row = cursor.fetchone()
        return bool(row[0]) if row else False
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        conn.close()

def marcar_correo_enviadoVigencia(idEncabezado: int) -> bool:
    conn = get_connection()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE VigenciaEncabezado
            SET correoEnviado = 1
            WHERE idEncabezado = ?
        """, idEncabezado)
        conn.commit()
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False
    finally:
        cursor.close()
        conn.close()

#--------- PAUSAR---------------------------------------------
def marcar_pausa_encabezadoVigencia(id_encabezado: int, fecha_pausa: datetime) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE VigenciaEncabezado
            SET estado = ?, fechaPausa = ?
            WHERE idEncabezado = ?
        """, 'Pausado', fecha_pausa, id_encabezado)
        conn.commit()
        return True
    except:
        return False
    finally:
        cursor.close()
        conn.close()

def quitar_pausa_encabezadoVigencia(id_encabezado: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE VigenciaEncabezado
            SET estado = ?, fechaPausa = NULL
            WHERE idEncabezado = ?
        """, 'En proceso', id_encabezado)
        conn.commit()
        return True
    except:
        return False
    finally:
        cursor.close()
        conn.close()
        
def pausar_detalle_encabezadoVigencia(id_encabezado: int) -> bool:
    sql = """
    UPDATE dbo.VigenciaDetalle
    SET
      vigencia      = CASE WHEN vigencia      IS NULL OR vigencia      = '' THEN 'Pausado' ELSE vigencia      END
    WHERE idEncabezado = ?
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, id_encabezado)
        conn.commit()
        return True
    except:
        return False
    finally:
        cur.close()
        conn.close()

def reanudar_detalle_encabezadoVigencia(id_encabezado: int) -> bool:
    sql = """
    UPDATE dbo.VigenciaDetalle
    SET
      vigencia      = CASE WHEN vigencia      = 'Pausado' THEN NULL ELSE vigencia     END
    WHERE idEncabezado = ?
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, id_encabezado)
        conn.commit()
        return True
    except:
        return False
    finally:
        cur.close()
        conn.close()