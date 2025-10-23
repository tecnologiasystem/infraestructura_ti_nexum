from typing import List, Tuple, Optional, Dict, Any
from app.config.database import get_connection

def insertar_detalle_bulk(
    numeros: List[str],
    mensaje: str,
    campana: str,
    adjunto_json: Optional[str],  # JSON de rutas
    file_name: Optional[str],
    id_usuario_app: Optional[int]
) -> Tuple[int, Optional[str]]:
    conn = get_connection()
    if conn is None:
        return 0, "Error al conectar con la BD"
    try:
        cursor = conn.cursor()
        cursor.fast_executemany = True
        sql = """
            EXEC dbo.SP_CRUD_ClientesEnvioWhatsApp
                @accion=1,
                @Numero=?,
                @Mensaje=?,
                @fileName=?,
                @Adjunto=?,
                @Estado=?,
                @IdUsuarioApp=?,
                @Campana=?
        """
        params = []
        for n in numeros:
            n2 = (n or '').strip()
            if not n2:
                continue
            params.append((n2, mensaje, file_name, adjunto_json, 'PENDIENTE', id_usuario_app, campana))


        if not params:
            return 0, None
        cursor.executemany(sql, params)
        conn.commit()
        return len(params), None
    except Exception as e:
        return 0, str(e)
    finally:
        try: cursor.close()
        except: pass
        conn.close()

def obtener_y_marcar_pendientes(
    limit: int = 1,
    nuevo_estado: str = "ENVIADO"
) -> Tuple[list[dict], Optional[str]]:
    conn = get_connection()
    if conn is None:
        return [], "Error al conectar con la BD"
    try:
        conn.autocommit = False
        cur = conn.cursor()

        sql_sel = """
            SELECT TOP (?) id, Numero, Mensaje, Adjunto
            FROM dbo.ClientesEnvioWhatsApp WITH (ROWLOCK, READPAST, UPDLOCK)
            WHERE Estado = 'PENDIENTE'
            ORDER BY NEWID()
        """
        cur.execute(sql_sel, (limit,))
        rows = cur.fetchall()

        if not rows:
            conn.commit()
            return [], None

        ids = [r[0] for r in rows]
        placeholders = ",".join("?" for _ in ids)
        sql_upd = f"""
            UPDATE dbo.ClientesEnvioWhatsApp
               SET Estado = ?
             WHERE id IN ({placeholders});
        """
        cur.execute(sql_upd, (nuevo_estado, *ids))
        conn.commit()

        out = [{"id": r[0], "numero": r[1], "mensaje": r[2], "adjunto": r[3]} for r in rows]
        return out, None
    except Exception as e:
        try: conn.rollback()
        except: pass
        return [], str(e)
    finally:
        try: cur.close()
        except: pass
        try: conn.close()
        except: pass

def obtener_y_marcar_pendientes_por_campana(
    campana: str,
    limit: int = 1,
    nuevo_estado: str = "ENVIADO"
) -> Tuple[list[dict], Optional[str]]:
    conn = get_connection()
    if conn is None:
        return [], "Error al conectar con la BD"
    try:
        conn.autocommit = False
        cur = conn.cursor()

        sql_sel = """
            SELECT TOP (?) id, Numero, Mensaje, Adjunto
            FROM dbo.ClientesEnvioWhatsApp WITH (ROWLOCK, READPAST, UPDLOCK)
            WHERE Estado = 'PENDIENTE' AND Campana = ?
            ORDER BY NEWID()
        """
        cur.execute(sql_sel, (limit, campana))
        rows = cur.fetchall()

        if not rows:
            conn.commit()
            return [], None

        ids = [r[0] for r in rows]
        placeholders = ",".join("?" for _ in ids)
        sql_upd = f"""
            UPDATE dbo.ClientesEnvioWhatsApp
               SET Estado = ?
             WHERE id IN ({placeholders});
        """
        cur.execute(sql_upd, (nuevo_estado, *ids))
        conn.commit()

        out = [{"id": r[0], "numero": r[1], "mensaje": r[2], "adjunto": r[3]} for r in rows]
        return out, None
    except Exception as e:
        try: conn.rollback()
        except: pass
        return [], str(e)
    finally:
        try: cur.close()
        except: pass
        try: conn.close()
        except: pass

def actualizar_tiene_whatsapp_por_numero(
    numero: str,
    tiene_whatsapp: str     
) -> Tuple[int, Optional[str]]:

    conn = get_connection()
    if conn is None:
        return 0, "Error al conectar con la BD"

    try:
        cur = conn.cursor()
        sql = """
            EXEC dbo.SP_CRUD_ClientesEnvioWhatsApp
                @accion=6,
                @Numero=?,
                @Tiene_Whatsapp=?
        """
        cur.execute(sql, (numero, tiene_whatsapp))

        filas = cur.rowcount or 0
        conn.commit()
        return filas, None
    except Exception as e:
        try: conn.rollback()
        except: pass
        return 0, str(e)
    finally:
        try: cur.close()
        except: pass
        try: conn.close()
        except: pass

def clientes_envio() -> List[Dict[str, Any]]:
    sql = """
    SELECT TOP (1000000) [Numero],[Mensaje],[fileName],[Adjunto],
           [FechaHoraEnvio],[Estado],[Tiene_Whatsapp], [Campana]
    FROM [NEXUM].[dbo].[ClientesEnvioWhatsApp]
    ORDER BY id DESC
    """
    with get_connection() as con:
        cur = con.cursor()
        cur.execute(sql)
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]