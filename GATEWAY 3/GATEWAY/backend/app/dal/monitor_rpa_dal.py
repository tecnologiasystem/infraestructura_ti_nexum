from config.db_config import get_connection
from datetime import datetime

def obtener_datos_encabezado(origen: str, id_encabezado: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            'SUPER NOTARIADO' AS origen, automatizacion, idUsuario, fechaCargue, totalRegistros, estado, fechaPausa, fechaFinalizacion
        FROM SuperNotariadoEncabezado
        WHERE idEncabezado = ?
        UNION ALL
        SELECT 
            'RUNT', automatizacion, idUsuario, fechaCargue, totalRegistros, estado, fechaPausa, fechaFinalizacion
        FROM RuntEncabezado
        WHERE idEncabezado = ?
        UNION ALL
        SELECT 
            'RUES', automatizacion, idUsuario, fechaCargue, totalRegistros, estado, fechaPausa, fechaFinalizacion
        FROM RuesEncabezado
        WHERE idEncabezado = ?
        UNION ALL
        SELECT 
            'FAMISANAR', automatizacion, idUsuario, fechaCargue, totalRegistros, estado, fechaPausa, fechaFinalizacion
        FROM FamiSanarEncabezado 
        WHERE idEncabezado = ?
        UNION ALL
        SELECT 
            'SIMIT', automatizacion, idUsuario, fechaCargue, totalRegistros, estado, fechaPausa, fechaFinalizacion
        FROM SimitEncabezado 
        WHERE idEncabezado = ?
        UNION ALL
        SELECT 
            'NUEVA EPS', automatizacion, idUsuario, fechaCargue, totalRegistros, estado, fechaPausa, fechaFinalizacion
        FROM NuevaEpsEncabezado
        WHERE idEncabezado = ?
        UNION ALL
        SELECT 
            'VIGILANCIA', automatizacion, idUsuario, fechaCargue, totalRegistros, estado, fechaPausa, fechaFinalizacion
        FROM VigilanciaEncabezado
        WHERE idEncabezado = ?
        UNION ALL
        SELECT 
            'WHATSAPP', automatizacion, idUsuario, fechaCargue, totalRegistros, estado, fechaPausa, fechaFinalizacion
        FROM WhatsAppEncabezado
        WHERE idEncabezado = ?
        UNION ALL
        SELECT 
            'CAMARACOMERCIO', automatizacion, idUsuario, fechaCargue, totalRegistros, estado, fechaPausa, fechaFinalizacion
        FROM CamaraComercioEncabezado
        WHERE idEncabezado = ?
        UNION ALL
        SELECT 
            'VIGENCIA', automatizacion, idUsuario, fechaCargue, totalRegistros, estado, fechaPausa, fechaFinalizacion
        FROM VigenciaEncabezado
        WHERE idEncabezado = ?
    """
    cursor.execute(query, (id_encabezado,)*10)
    row = cursor.fetchone()
    conn.close()

    return {
    "origen": row[0],
    "automatizacion": row[1],
    "idUsuario": row[2],
    "fechaCargue": row[3],
    "totalRegistros": row[4],
    "estado": row[5],
    "fechaPausa": row[6],
    "fechaFinalizacion": row[7],
} if row else None


def registrar_caida_rpa(id_encabezado, fechaCaida, mensaje, automatizacion, idUsuario, fechaCargue, totalRegistros):
    conn = get_connection()
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO ControlRPA (idEncabezado, automatizacion, idUsuario, fechaCargue,
        totalRegistros, fechaCaida, mensaje, estadoActual)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'INACTIVO')
    """

    cursor.execute(insert_query, (
        id_encabezado,
        automatizacion,
        idUsuario,
        fechaCargue,
        totalRegistros,
        fechaCaida,
        mensaje
    ))

    conn.commit()
    conn.close()

def obtener_dashboard() -> list[dict]:
    """
    Devuelve todas las caídas registradas con sus datos completos:
      - idEncabezado, automatizacion, idUsuario, fechaCargue, totalRegistros
      - fechaCaida, mensaje
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
       SELECT
    C.idEncabezado,
    C.automatizacion,
    U.nombre AS nombreUsuario,
    C.fechaCargue,
    C.totalRegistros,
    C.fechaCaida,
    C.mensaje,
    C.fechaReactivacion,
    C.tiempoInactivo
FROM ControlRPA C
LEFT JOIN [NEXUM].[dbo].[UsuariosApp] U
    ON C.idUsuario = U.idUsuarioApp
ORDER BY C.fechaCaida DESC

    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
    {
        "idEncabezado":   row[0],
        "automatizacion": row[1],
        "nombreUsuario":  row[2],  
        "fechaCargue":    row[3],
        "totalRegistros": row[4],
        "fechaCaida":     row[5],
        "mensaje":        row[6],
        "fechaReactivacion": row[7],
        "tiempoInactivo":    row[8],
    }
    for row in rows
]

def obtener_encabezados(origen: str) -> list[dict]:
    """
    Devuelve la lista de encabezados para el RPA indicado.
    origen puede ser 'FAMISANAR', 'RUNT', 'SUPER NOTARIADO', etc.
    """
    sql_map = {
        "FAMISANAR": """
            SELECT 
            E.idEncabezado,
            E.automatizacion,
            U.nombre          AS nombreUsuario,
            E.fechaCargue,
            E.totalRegistros,
            (
                SELECT COUNT(*) 
                FROM FamiSanarDetalle D
                WHERE D.idEncabezado = E.idEncabezado
                AND (
                    LTRIM(RTRIM(ISNULL(D.nombres,   ''))) <> 'vacio'
                    OR LTRIM(RTRIM(ISNULL(D.apellidos,     ''))) <> 'vacio'

                )
            )                  AS totalRelevantes,
            E.estado,
            E.fechaPausa,
            E.fechaFinalizacion
            FROM FamiSanarEncabezado E
            LEFT JOIN [NEXUM].[dbo].[UsuariosApp] U
            ON E.idUsuario = U.idUsuarioApp
            ORDER BY E.idEncabezado DESC;

        """,
        "RUNT": """
              SELECT 
    E.idEncabezado,
    E.automatizacion,
    U.nombre AS nombreUsuario,
    E.fechaCargue,
    E.totalRegistros,
    (
        SELECT COUNT(*) 
        FROM RuntDetalle D
        WHERE D.idEncabezado = E.idEncabezado
        AND (
            LTRIM(RTRIM(ISNULL(D.estadoVehiculo, ''))) <> 'vacío'
            OR LTRIM(RTRIM(ISNULL(D.marca, ''))) <> 'vacío'
        )
    ) AS totalRelevantes,
    E.estado,
    E.fechaPausa,
    E.fechaFinalizacion
FROM RuntEncabezado E
LEFT JOIN [NEXUM].[dbo].[UsuariosApp] U
    ON E.idUsuario = U.idUsuarioApp
ORDER BY E.idEncabezado DESC;
        """,
        "SUPER NOTARIADO": """
           SELECT 
            E.idEncabezado,
            E.automatizacion,
            U.nombre          AS nombreUsuario,
            E.fechaCargue,
            E.totalRegistros,
            (
                SELECT COUNT(*) 
                FROM SuperNotariadoDetalle D
                WHERE D.idEncabezado = E.idEncabezado
                AND (
                    LTRIM(RTRIM(ISNULL(D.matricula,   ''))) <> 'vacio'
                    OR LTRIM(RTRIM(ISNULL(D.ciudad,     ''))) <> 'vacio'
                    OR LTRIM(RTRIM(ISNULL(D.direccion,  ''))) <> 'vacio'
                    OR LTRIM(RTRIM(ISNULL(D.vinculadoA, ''))) <> 'vacio'
                )
            )                  AS totalRelevantes,
            E.estado,
            E.fechaPausa,
            E.fechaFinalizacion
            FROM SuperNotariadoEncabezado E
            LEFT JOIN [NEXUM].[dbo].[UsuariosApp] U
            ON E.idUsuario = U.idUsuarioApp
            ORDER BY E.idEncabezado DESC;

        """,
        "RUES": """
            SELECT 
                E.idEncabezado,
                E.automatizacion,
                U.nombre          AS nombreUsuario,
                E.fechaCargue,
                E.totalRegistros,
                (
                    SELECT COUNT(*) 
                    FROM RuesDetalle D
                    WHERE D.idEncabezado = E.idEncabezado
                    AND (
                        LTRIM(RTRIM(ISNULL(D.nombre,   ''))) <> 'vacio'
                        OR LTRIM(RTRIM(ISNULL(D.categoria,     ''))) <> 'vacio'

                    )
                )                  AS totalRelevantes,
                E.estado,
                E.fechaPausa,
                E.fechaFinalizacion
                FROM RuesEncabezado E
                LEFT JOIN [NEXUM].[dbo].[UsuariosApp] U
                ON E.idUsuario = U.idUsuarioApp
                ORDER BY E.idEncabezado DESC;
        """,
        "NUEVA EPS": """
            SELECT 
                E.idEncabezado,
                E.automatizacion,
                U.nombre          AS nombreUsuario,
                E.fechaCargue,
                E.totalRegistros,
                (
                    SELECT COUNT(*) 
                    FROM NuevaEpsDetalle D
                    WHERE D.idEncabezado = E.idEncabezado
                    AND (
                        LTRIM(RTRIM(ISNULL(D.nombre,   ''))) <> 'vacio'
                        OR LTRIM(RTRIM(ISNULL(D.edad,     ''))) <> 'vacio'

                    )
                )                  AS totalRelevantes,
                E.estado,
                E.fechaPausa,
                E.fechaFinalizacion
                FROM NuevaEpsEncabezado E
                LEFT JOIN [NEXUM].[dbo].[UsuariosApp] U
                ON E.idUsuario = U.idUsuarioApp
                ORDER BY E.idEncabezado DESC;

        """,
        "SIMIT": """
            SELECT 
                E.idEncabezado,
                E.automatizacion,
                U.nombre          AS nombreUsuario,
                E.fechaCargue,
                E.totalRegistros,
                (
                    SELECT COUNT(*) 
                    FROM SimitDetalle D
                    WHERE D.idEncabezado = E.idEncabezado
                    AND (
                        LTRIM(RTRIM(ISNULL(D.placa,   ''))) <> 'vacio'
                        OR LTRIM(RTRIM(ISNULL(D.secretaria,     ''))) <> 'vacio'

                    )
                )                  AS totalRelevantes,
                E.estado,
                E.fechaPausa,
                E.fechaFinalizacion
                FROM SimitEncabezado E
                LEFT JOIN [NEXUM].[dbo].[UsuariosApp] U
                ON E.idUsuario = U.idUsuarioApp
                ORDER BY E.idEncabezado DESC;

        """,
        "VIGILANCIA": """
            SELECT 
                E.idEncabezado,
                E.automatizacion,
                U.nombre          AS nombreUsuario,
                E.fechaCargue,
                E.totalRegistros,
                (
                    SELECT COUNT(*) 
                    FROM VigilanciaDetalle D
                    WHERE D.idEncabezado = E.idEncabezado
                    AND (
                        LTRIM(RTRIM(ISNULL(D.actuacion,   ''))) <> 'vacio'
                        OR LTRIM(RTRIM(ISNULL(D.anotacion,     ''))) <> 'vacio'
                    )
                )                  AS totalRelevantes,
                E.estado,
                E.fechaPausa,
                E.fechaFinalizacion
                FROM VigilanciaEncabezado E
                LEFT JOIN [NEXUM].[dbo].[UsuariosApp] U
                ON E.idUsuario = U.idUsuarioApp
                ORDER BY E.idEncabezado DESC;

        """,
        "WHATSAPP": """
            SELECT 
                E.idEncabezado,
                E.automatizacion,
                U.nombre          AS nombreUsuario,
                E.fechaCargue,
                E.totalRegistros,
                (
                    SELECT COUNT(*) 
                    FROM WhatsAppDetalle D
                    WHERE D.idEncabezado = E.idEncabezado
                    AND (
                        LTRIM(RTRIM(ISNULL(D.tiene_whatsApp,   ''))) <> 'no'
                    )
                )                  AS totalRelevantes,
                E.estado,
                E.fechaPausa,
                E.fechaFinalizacion
                FROM WhatsAppEncabezado E
                LEFT JOIN [NEXUM].[dbo].[UsuariosApp] U
                ON E.idUsuario = U.idUsuarioApp
                ORDER BY E.idEncabezado DESC;
        """,
        "CAMARACOMERCIO": """
            SELECT 
                E.idEncabezado,
                E.automatizacion,
                U.nombre          AS nombreUsuario,
                E.fechaCargue,
                E.totalRegistros,
                (
                    SELECT COUNT(*) 
                    FROM CamaraComercioDetalle D
                    WHERE D.idEncabezado = E.idEncabezado
                    AND (
                        LTRIM(RTRIM(ISNULL(D.identificacion,   ''))) <> 'no'
                    )
                )                  AS totalRelevantes,
                E.estado,
                E.fechaPausa,
                E.fechaFinalizacion
                FROM CamaraComercioEncabezado E
                LEFT JOIN [NEXUM].[dbo].[UsuariosApp] U
                ON E.idUsuario = U.idUsuarioApp
                ORDER BY E.idEncabezado DESC;
        """,
        "VIGENCIA": """
            SELECT 
                E.idEncabezado,
                E.automatizacion,
                U.nombre          AS nombreUsuario,
                E.fechaCargue,
                E.totalRegistros,
                (
                    SELECT COUNT(*) 
                    FROM VigenciaDetalle D
                    WHERE D.idEncabezado = E.idEncabezado
                    AND (
                        LTRIM(RTRIM(ISNULL(D.vigencia,   ''))) <> 'no'
                    )
                )                  AS totalRelevantes,
                E.estado,
                E.fechaPausa,
                E.fechaFinalizacion
                FROM VigenciaEncabezado E
                LEFT JOIN [NEXUM].[dbo].[UsuariosApp] U
                ON E.idUsuario = U.idUsuarioApp
                ORDER BY E.idEncabezado DESC;
        """,
    }

    query = sql_map.get(origen.upper())
    if not query:
        raise ValueError(f"Origen desconocido: {origen}")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close(); conn.close()

    return [
        {
            "idEncabezado":     r[0],
            "automatizacion":   r[1],
            "nombreUsuario":    r[2],
            "fechaCargue":      r[3],
            "totalRegistros":   r[4],
            "totalRelevantes":  r[5],
            "estado":           r[6],
            "fechaPausa":       r[7],
            "fechaFinalizacion": r[8],
        }
        for r in rows
    ]



def obtener_detalles(origen: str, id_encabezado: int) -> list[dict]:
    """
    Devuelve los detalles de un encabezado dado para el RPA indicado.
    """
    sql_map = {
        "FAMISANAR": """
            SELECT * 
            FROM FamiSanarDetalle 
            WHERE idEncabezado = ?
        """,
        "RUNT": """
            SELECT * 
            FROM RuntDetalle 
            WHERE idEncabezado = ?
        """,
        "SUPER NOTARIADO": """
            SELECT * 
            FROM SuperNotariadoDetalle 
            WHERE idEncabezado = ?
        """,
        "RUES": """
            SELECT * 
            FROM RuesDetalle 
            WHERE idEncabezado = ?
        """,
        "NUEVA EPS": """
            SELECT * 
            FROM NuevaEpsDetalle 
            WHERE idEncabezado = ?
        """,
        "SIMIT": """
            SELECT * 
            FROM SimitDetalle 
            WHERE idEncabezado = ?
        """,
        "VIGILANCIA": """
            SELECT * 
            FROM VigilanciaDetalle 
            WHERE idEncabezado = ?
        """,
        "WHATSAPP": """
            SELECT * 
            FROM WhatsAppDetalle 
            WHERE idEncabezado = ?
        """,
        "CAMARACOMERCIO": """
            SELECT * 
            FROM CamaraComercioDetalle
            WHERE idEncabezado = ?
        """,
        "VIGENCIA": """
            SELECT * 
            FROM VigenciaDetalle
            WHERE idEncabezado = ?
        """,
    }
    query = sql_map.get(origen.upper())
    if not query:
        raise ValueError(f"Origen desconocido: {origen}")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, id_encabezado)
    cols = [c[0] for c in cur.description]
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [ dict(zip(cols, row)) for row in rows ]


def obtener_detalles_paginados(
    origen: str,
    id_enc: int,
    offset: int,
    limit:  int,
    cc: str | None = None) -> dict:

    tabla_map = {
        "FAMISANAR":        "FamiSanarDetalle",
        "RUNT":             "RuntDetalle",
        "SUPER NOTARIADO":  "SuperNotariadoDetalle",
        "RUES":             "RuesDetalle",
        "NUEVA EPS":        "NuevaEpsDetalle",
        "SIMIT":            "SimitDetalle",
        "VIGILANCIA":       "VigilanciaDetalle",
        "WHATSAPP":         "WhatsAppDetalle",
        "CAMARACOMERCIO":   "CamaraComercioDetalle",
        "VIGENCIA":         "VigenciaDetalle",
    }

    cc_column_map = {
        "FAMISANAR":        "cedula",
        "RUNT":             "cedula",
        "SUPER NOTARIADO":  "CC",
        "RUES":             "cedula",
        "NUEVA EPS":        "cedula",
        "SIMIT":            "cedula",
        "VIGILANCIA":       "cc",
        "WHATSAPP":         "numero",
        "CAMARACOMERCIO":   "cedula",
        "VIGENCIA":   "cedula",
    }

    tabla = tabla_map.get(origen.upper())
    cc_column = cc_column_map.get(origen.upper())

    if not tabla:
        raise ValueError(f"Origen desconocido: {origen}")

    where = "idEncabezado = ?"
    params = [id_enc]

    if cc:
        where += f" AND {cc_column} LIKE ?"
        params.append(f"%{cc}%")

    sql_count = f"SELECT COUNT(*) FROM {tabla} WHERE {where}"

    sql_page = (
        f"SELECT * FROM {tabla} "
        f"WHERE {where} "
        f"ORDER BY idDetalle "
        f"OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
    )

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(sql_count, params)
    total = cur.fetchone()[0]

    page_params = params + [offset, limit]
    cur.execute(sql_page, page_params)

    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]

    cur.close()
    conn.close()

    return {"rows": rows, "total": total}


def obtener_todos_detalles_por_origen(origen: str) -> list[dict]:
    tabla_map = {
        "FAMISANAR":        "FamiSanarDetalle",
        "RUNT":             "RuntDetalle",
        "SUPER NOTARIADO":  "SuperNotariadoDetalle",
        "RUES":             "RuesDetalle",
        "NUEVA EPS":        "NuevaEpsDetalle",
        "SIMIT":            "SimitDetalle",
        "VIGILANCIA":       "VigilanciaDetalle",
        "WHATSAPP":         "WhatsAppDetalle",
        "CAMARACOMERCIO":   "CamaraComercioDetalle",
        "VIGENCIA":         "VigenciaDetalle",
    }
    tabla = tabla_map.get(origen.upper())
    if not tabla:
        raise ValueError(f"Origen desconocido: {origen}")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {tabla}")
    cols = [c[0] for c in cur.description]
    rows = cur.fetchall()
    cur.close(); conn.close()

    return [ dict(zip(cols, row)) for row in rows ]

def registrar_reactivacion_rpa(id_encabezado, fechaReactivacion, tiempoInactivo):
    conn = get_connection()
    cursor = conn.cursor()

    update_query = """
    UPDATE ControlRPA
    SET fechaReactivacion = ?, 
        tiempoInactivo = ?,
        estadoActual = 'ACTIVO'
    WHERE idEncabezado = ? 
      AND fechaReactivacion IS NULL
    """

    cursor.execute(update_query, (
        fechaReactivacion,
        tiempoInactivo,
        id_encabezado
    ))

    conn.commit()
    conn.close()

def existe_caida_sin_reactivacion(id_encabezado: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM ControlRPA
        WHERE idEncabezado = ? AND fechaReactivacion IS NULL
    """, id_encabezado)
    result = cursor.fetchone()[0]
    conn.close()
    return result > 0


def buscar_detalle_por_cedula(origen: str, id_encabezado: int, cedula: str) -> list[dict]:
    sql_map = {
        "FAMISANAR": """
            SELECT * 
            FROM FamiSanarDetalle 
            WHERE idEncabezado = ? AND cedula = ?
        """,
        "RUNT": """
            SELECT * 
            FROM RuntDetalle 
            WHERE idEncabezado = ? AND cedula = ?
        """,
        "SUPER NOTARIADO": """
            SELECT * 
            FROM SuperNotariadoDetalle 
            WHERE idEncabezado = ? AND CC = ?
        """,
        "RUES": """
            SELECT * 
            FROM RuesDetalle 
            WHERE idEncabezado = ? AND cedula = ?
        """,
        "NUEVA EPS": """
            SELECT * 
            FROM NuevaEpsDetalle 
            WHERE idEncabezado = ? AND cedula = ?
        """,
        "SIMIT": """
            SELECT * 
            FROM SimitDetalle 
            WHERE idEncabezado = ? AND cedula = ?
        """,
        "VIGILANCIA": """
            SELECT * 
            FROM VigilanciaDetalle 
            WHERE idEncabezado = ? AND cc = ?
        """,
        "WHATSAPP": """
            SELECT * 
            FROM WhatsAppDetalle 
            WHERE idEncabezado = ? AND numero = ?
        """,
        "CAMARACOMERCIO": """
            SELECT * 
            FROM CamaraComercioDetalle 
            WHERE idEncabezado = ? AND cedula = ?
        """,
        "VIGENCIA": """
            SELECT * 
            FROM VigenciaDetalle 
            WHERE idEncabezado = ? AND cedula = ?
        """,
    }

    query = sql_map.get(origen.upper())
    if not query:
        raise ValueError(f"Origen desconocido: {origen}")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, (id_encabezado, cedula))
    rows = cur.fetchall()
    columns = [col[0] for col in cur.description]
    cur.close()
    conn.close()

    return [dict(zip(columns, row)) for row in rows]

def obtener_ultima_fecha_caida(id_encabezado: int) -> datetime | None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT fechaCaida
        FROM ControlRPA
        WHERE idEncabezado = ? AND fechaReactivacion IS NULL
        ORDER BY fechaCaida DESC
    """, id_encabezado)
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]
    else:
        return None

def resumen_vigencia(id_encabezado: int) -> dict:
    """
    Devuelve totales para el pastel de VIGENCIA:
    - vigenteVivo
    - canceladaMuerte
    Soporta columna 'estado' o 'vigencia' según exista en VigenciaDetalle.
    """
    conn = get_connection()
    cur = conn.cursor()

    # 1) Detectar la columna disponible
    cur.execute("""
        SELECT name
        FROM sys.columns
        WHERE object_id = OBJECT_ID('dbo.VigenciaDetalle')
          AND name IN ('estado','vigencia')
    """)
    cols = {row[0].lower() for row in cur.fetchall()}
    col = 'estado' if 'estado' in cols else ('vigencia' if 'vigencia' in cols else None)
    if not col:
        cur.close(); conn.close()
        raise Exception("No se encontró columna 'estado' ni 'vigencia' en VigenciaDetalle")

    # 2) Contar con matches flexibles (por si hay variantes de texto)
    sql = f"""
        SELECT
            SUM(CASE WHEN {col} IN ('Vigente (Vivo)','Vigente','Vivo')
                      OR {col} LIKE '%Vigent%' OR {col} LIKE '%Vivo%' THEN 1 ELSE 0 END) AS vigenteVivo,
            SUM(CASE WHEN {col} IN ('Cancelada por Muerte','Cancelada','Muerte')
                      OR {col} LIKE '%Cancelad%' OR {col} LIKE '%Muerte%' THEN 1 ELSE 0 END) AS canceladaMuerte
        FROM dbo.VigenciaDetalle
        WHERE idEncabezado = ?
    """
    cur.execute(sql, (id_encabezado,))
    row = cur.fetchone()
    cur.close(); conn.close()

    return {
        "vigenteVivo": int(row[0] or 0),
        "canceladaMuerte": int(row[1] or 0),
    }