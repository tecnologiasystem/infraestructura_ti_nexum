# email_imagenes_dal.py
from datetime import datetime
from typing import Optional, List, Dict, Any
from config.database import get_connection  

class EmailImagenesDAL:
    def crear_encabezado(
        self,
        idUsuario: Optional[int],
        totalRegistros: int,
        descripcion: Optional[str],
        remitente: Optional[str],
    ) -> int:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
    """
    INSERT INTO dbo.EmailImagenesEncabezado
        (idUsuario, fechaCargue, totalRegistros, estado, correoEnviado, descripcion, remitente)
    OUTPUT INSERTED.idEncabezado
    VALUES
        (?, GETDATE(), ?, 'CARGADO', 0, ?, ?);
    """,
    (idUsuario, totalRegistros, descripcion, remitente),
        )
        row = cursor.fetchone()
        conn.commit()
        return int(row[0])


    def crear_detalle(
        self,
        idEncabezado: int,
        email_destinatario: str,
        asunto: str,
        cuerpo: str,
        click_url: str | None = None,
        adjuntos: Optional[str] = None,
        cedula: str = None,
        nombre_cliente: str = None,
        campana: str = None,
    ) -> int:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.EmailImagenesDetalle
                (idEncabezado, email_destinatario, asunto, cuerpo, adjuntos, click_url,
                estado_envio, error_detalle, fecha_registro, fecha_envio, cedula, nombre_cliente, campana)
            OUTPUT INSERTED.idDetalle
            VALUES
                (?, ?, ?, ?, ?, ?, 'PENDIENTE', NULL, GETDATE(), NULL, ?, ?, ?);
            """,
            (idEncabezado, email_destinatario, asunto, cuerpo, adjuntos, click_url, cedula, nombre_cliente, campana),
        )
        row = cursor.fetchone()
        conn.commit()
        return int(row[0])


    def actualizar_detalle_resultado(
        self,
        idDetalle: int,
        estado_envio: str,
        error_detalle: Optional[str] = None,
    ) -> None:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE dbo.EmailImagenesDetalle
            SET estado_envio = ?,
                error_detalle = ?,
                fecha_envio = GETDATE()
            WHERE idDetalle = ?;
            """,
            (estado_envio, error_detalle, idDetalle),
        )
        conn.commit()

    def finalizar_encabezado(
        self,
        idEncabezado: int,
        estado: str,
        correoEnviado: bool,
    ) -> None:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE dbo.EmailImagenesEncabezado
            SET estado = ?,
                correoEnviado = ?,
                fechaFinalizacion = GETDATE()
            WHERE idEncabezado = ?;
            """,
            (estado, 1 if correoEnviado else 0, idEncabezado),
        )
        conn.commit()

    def registrar_click(self, idDetalle: int, area: int, ip: str, user_agent: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.EmailImagenesClicks
                (idDetalle, area, ip, user_agent, fecha_click)
            VALUES (?, ?, ?, ?, GETDATE());
            """,
            (idDetalle, area, ip, user_agent),
        )
        conn.commit()

    def obtener_click_url(self, idDetalle: int) -> str | None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT click_url FROM dbo.EmailImagenesDetalle WHERE idDetalle = ?", (idDetalle,))
        row = cursor.fetchone()
        return row[0] if row else None

    def claim_detalles_pendientes(self, limit: int = 25, retry_minutes: int = 5) -> List[Dict[str, Any]]:
            """
            Toma (claim) detalles pendientes de forma atómica:
            - PENDIENTE
            - ERROR_TEMPORAL pero con fecha_envio vieja (para reintento)
            Los marca EN_PROCESO y retorna la info necesaria + remitente del encabezado.
            """
            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                f"""
                ;WITH cte AS (
                    SELECT TOP ({limit})
                        d.idDetalle
                    FROM dbo.EmailImagenesDetalle d WITH (ROWLOCK, READPAST, UPDLOCK)
                    WHERE
                        d.estado_envio = 'PENDIENTE'
                        OR (
                            d.estado_envio = 'ERROR_TEMPORAL'
                            AND d.fecha_envio < DATEADD(MINUTE, -?, GETDATE())
                        )
                    ORDER BY d.idDetalle ASC
                )
                UPDATE d
                SET
                    d.estado_envio = 'EN_PROCESO',
                    d.error_detalle = NULL
                OUTPUT
                    inserted.idDetalle,
                    inserted.idEncabezado,
                    inserted.email_destinatario,
                    inserted.asunto,
                    inserted.cuerpo,
                    inserted.click_url,
                    e.remitente
                FROM dbo.EmailImagenesDetalle d
                INNER JOIN cte ON cte.idDetalle = d.idDetalle
                INNER JOIN dbo.EmailImagenesEncabezado e ON e.idEncabezado = d.idEncabezado;
                """,
                (retry_minutes,),
            )

            rows = cursor.fetchall()
            conn.commit()

            # OJO: ajusta índices si tu cursor retorna tuplas
            result = []
            for r in rows:
                result.append({
                    "idDetalle": r[0],
                    "idEncabezado": r[1],
                    "email_destinatario": r[2],
                    "asunto": r[3],
                    "cuerpo": r[4],
                    "click_url": r[5],
                    "remitente": r[6],
                })
            return result

    def get_resumen_encabezado(self, idEncabezado: int) -> Dict[str, int]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                SUM(CASE WHEN estado_envio IN ('PENDIENTE','EN_PROCESO','ERROR_TEMPORAL') THEN 1 ELSE 0 END) AS pendientes,
                SUM(CASE WHEN estado_envio = 'ENVIADO' THEN 1 ELSE 0 END) AS enviados,
                SUM(CASE WHEN estado_envio IN ('ERROR','REBOTADO') THEN 1 ELSE 0 END) AS errores
            FROM dbo.EmailImagenesDetalle
            WHERE idEncabezado = ?;
            """,
            (idEncabezado,)
        )
        row = cursor.fetchone()
        return {"pendientes": int(row[0] or 0), "enviados": int(row[1] or 0), "errores": int(row[2] or 0)}