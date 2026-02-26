import os
import json
from datetime import datetime
from typing import Tuple, Optional
from app.dal.excel_dal import ExcelDAL
from app.dal.imagen_dal import ImagenDAL
from app.dal.correo_dal import CorreoDAL
import time
from app.dal.email_imagenes_dal import EmailImagenesDAL
import re
from urllib.parse import quote

class EmailClickBLL:
    excel_file_path: str | None = None
    def __init__(self):
        self.excel_dal = ExcelDAL()
        self.imagen_dal = ImagenDAL()
        self.correo_dal = CorreoDAL()
        self.db_dal = EmailImagenesDAL()

    def _pick(self, row: dict, keys: list[str]) -> str | None:
        for k in keys:
            if k in row and row[k] is not None:
                v = str(row[k]).strip()
                if v and v.lower() != "nan":
                    return v
        return None

    def _personalize(self, template: str, row: dict) -> str:
        if not template:
            return ""

        def repl(match):
            key = match.group(1).strip()
            for k in (key, key.upper(), key.lower()):
                if k in row and row[k] is not None:
                    return str(row[k])
            return ""  

        return re.sub(r"\{([^}]+)\}", repl, template)

    async def subir_excel(self, upload_file, upload_folder: str):
        try:
            path = await self.excel_dal.guardar_excel(upload_file, upload_folder)
            EmailClickBLL.excel_file_path = path

            # leer filas y columnas
            rows = self.excel_dal.obtener_clientes(path)
            variables = list(rows[0].keys()) if rows else []

            return True, "Archivo Excel cargado correctamente", variables, upload_file.filename
        except Exception as e:
            return False, str(e), [], upload_file.filename if upload_file else ""

    async def guardar_imagen(self, upload_file, areas_raw: str, images_folder: str) -> Tuple[bool, str]:
        try:
            areas = json.loads(areas_raw)
            await self.imagen_dal.guardar_imagen_y_areas(upload_file, areas, images_folder)
            return True, "Imagen guardada correctamente"
        except Exception as e:
            return False, str(e)

    def _obtener_clientes(self, excel_path: str | None = None):
        path = excel_path or EmailClickBLL.excel_file_path
        if not path:
            return []
        return self.excel_dal.obtener_clientes(path)

    def _construir_html(self, body: str, images_folder: str, idDetalle: int, senderEmail: str) -> str:
        public_base = os.getenv("PUBLIC_BASE_URL", "https://optime.systemgroupglobal.com")
        sender_encoded = quote(senderEmail, safe='')

        areas = self.imagen_dal.leer_areas(images_folder)
        destino = areas[0].get("url") if areas else None

        if destino:
            track_url = f"{public_base}/gateway/emailclick/track/{idDetalle}?a=1&senderEmail={sender_encoded}"
            image_html = f"""
                <a href="{track_url}" target="_blank">
                    <img src="cid:clickimg" style="max-width:600px;width:100%;">
                </a>
            """
        else:
            image_html = """
                <img src="cid:clickimg" style="max-width:600px;width:100%;">
            """

        return f"""
        <html>
        <body>
            <p>{body}</p>
            {image_html}
        </body>
        </html>
        """


    def _get_email(self, row: dict) -> str:
        for k in ("Correo", "correo", "Email", "email", "E-mail", "MAIL", "mail", "CORREO"):
            v = row.get(k)
            if v is None:
                continue
            v = str(v).strip()
            if v and v.lower() != "nan":
                return v
        return ""
    
    def crear_encabezado(
        self,
        idUsuario: Optional[int],
        totalRegistros: int,
        descripcion: Optional[str],
        remitente: Optional[str],
    ) -> int:
        return self.db_dal.crear_encabezado(
            idUsuario=idUsuario,
            totalRegistros=totalRegistros,
            descripcion=descripcion,
            remitente=remitente,
        )
    
    def enviar_correos_batch(
    self,
    idEncabezado: int,
    subject: str,
    body: str,
    senderEmail: str,
    images_folder: str,
    idUsuario: int | None = None,
    excel_path: str | None = None,) -> Tuple[bool, str, Optional[int]]:

        areas = self.imagen_dal.leer_areas(images_folder)
        destino = areas[0]["url"] if areas else None

        try:
            senderEmail = senderEmail.replace(" ", "").strip()

            clientes = self._obtener_clientes(excel_path)

            destinatarios = []
            for c in clientes:
                correo = self._get_email(c)
                if correo:
                    c["Correo"] = correo
                    destinatarios.append(c)

            if len(destinatarios) == 0:
                return False, "No hay destinatarios válidos (revisa columna Correo/Email).", None

            # Crear detalles PENDIENTE + mapa
            mapa = {}
            for c in destinatarios:
                correo = c["Correo"]
                subject_row = self._personalize(subject, c)
                body_row = self._personalize(body, c)

                idDetalle = self.db_dal.crear_detalle(
                    idEncabezado=idEncabezado,
                    email_destinatario=correo,
                    asunto=subject_row,
                    cuerpo=body_row,
                    click_url=destino,
                    adjuntos=None,
                )
                mapa[correo] = {"idDetalle": idDetalle, "subject": subject_row, "body": body_row}

            # BATCH SMTP
            BATCH_SIZE = int(os.getenv("EMAIL_SMTP_BATCH_SIZE", "75"))
            NOOP_EVERY = int(os.getenv("EMAIL_SMTP_NOOP_EVERY", "15"))
            SLEEP_BETWEEN_BATCH = float(os.getenv("EMAIL_SMTP_SLEEP", "1"))

            smtp_host = os.getenv("SMTP_HOST", "smtp.office365.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))

            smtp_user, smtp_pass = self.correo_dal._resolve_email_password(senderEmail)
            if not smtp_user or not smtp_pass:
                return False, f"No hay credenciales SMTP para {senderEmail}", idEncabezado

            enviados = 0
            errores = 0
            server = None

            def connect():
                return self.correo_dal._mk_smtp(smtp_host, smtp_port, smtp_user, smtp_pass, timeout=120)

            try:
                server = connect()

                for i, c in enumerate(destinatarios, start=1):
                    correo = c["Correo"]
                    info = mapa[correo]

                    idDetalle = info["idDetalle"]
                    subject_row = info["subject"]
                    body_row = info["body"]

                    html_row = self._construir_html(body_row, images_folder, idDetalle, senderEmail)

                    try:
                        self.correo_dal.enviar_uno_con_server(
                            server=server,
                            correo_destino=correo,
                            subject=subject_row,
                            html_body=html_row,
                            senderEmail=senderEmail,
                            images_folder=images_folder,
                        )
                        self.db_dal.actualizar_detalle_resultado(idDetalle, "ENVIADO", None)
                        enviados += 1
                    except Exception as e:
                        err = str(e)
                        err_l = err.lower()

                        # Outlook / Hotmail temporal
                        if (
                            "mailbox unavailable" in err_l
                            or "try again later" in err_l
                            or "s2017062302" in err_l
                        ):
                            estado = "ERROR_TEMPORAL"

                        # Rebote definitivo (correo no existe)
                        elif (
                            "5.1.1" in err_l
                            or "user unknown" in err_l
                            or "recipient address rejected" in err_l
                        ):
                            estado = "REBOTADO"

                        else:
                            estado = "ERROR"

                        self.db_dal.actualizar_detalle_resultado(idDetalle, estado, err)
                        errores += 1

                        print(f"❌ {estado} → {correo} | {err}")


                    if NOOP_EVERY > 0 and (i % NOOP_EVERY == 0):
                        self.correo_dal._smtp_noop(server)

                    if BATCH_SIZE > 0 and (i % BATCH_SIZE == 0):
                        self.correo_dal._smtp_safe_quit(server)
                        time.sleep(SLEEP_BETWEEN_BATCH)
                        server = connect()

            finally:
                self.correo_dal._smtp_safe_quit(server)

            # Finalizar encabezado
            if errores == 0 and enviados > 0:
                self.db_dal.finalizar_encabezado(idEncabezado, "FINALIZADO", True)
            else:
                self.db_dal.finalizar_encabezado(idEncabezado, "FINALIZADO_CON_ERROR", False)

            return True, f"Enviados: {enviados}, Errores: {errores}", idEncabezado

        except Exception as e:
            return False, f"Error al enviar correos: {e}", None



    def enviar_correos_ahora(
        self,
        subject: str,
        body: str,
        senderEmail: str,
        images_folder: str,
        idUsuario: Optional[int] = None,
        descripcion: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[int]]:
        try:
            senderEmail = senderEmail.replace(" ", "").strip()

            clientes = self._obtener_clientes()

            destinatarios = []
            for c in clientes:
                correo = self._get_email(c)
                if correo:
                    c["Correo"] = correo  # normaliza la clave
                    destinatarios.append(c)

            print("📧 total clientes:", len(clientes))
            print("📧 total destinatarios:", len(destinatarios))
            if destinatarios:
                print("📧 ejemplo correo:", destinatarios[0]["Correo"])


            # 1) Crear encabezado
            idEncabezado = self.db_dal.crear_encabezado(
                idUsuario=idUsuario,
                totalRegistros=len(destinatarios),
                descripcion=descripcion,
                remitente=senderEmail,
            )

            # 2) Crear detalles PENDIENTE
            mapa_detalle_por_correo = {}
            for c in destinatarios:
                correo = c["Correo"]
                subject_row = self._personalize(subject, c)
                body_row = self._personalize(body, c)

                idDetalle = self.db_dal.crear_detalle(
                    idEncabezado=idEncabezado,
                    email_destinatario=correo,
                    asunto=subject_row,
                    cuerpo=body_row,
                    adjuntos=None,
                )

                # guarda también qué subject/body le toca a ese correo para enviarlo igual
                mapa_detalle_por_correo[correo] = {"idDetalle": idDetalle, "subject": subject_row, "body": body_row}


            enviados = 0
            errores = 0

            for c in destinatarios:
                correo = c["Correo"]
                info = mapa_detalle_por_correo[correo]

                idDetalle = info["idDetalle"]
                subject_row = info["subject"]
                body_row = info["body"]

                html_row = self._construir_html(body_row, images_folder, idDetalle, senderEmail)

                try:
                    self.correo_dal.enviar_uno(
                        correo_destino=correo,
                        subject=subject_row,
                        html_body=html_row,
                        senderEmail=senderEmail,
                        images_folder=images_folder,
                    )
                    self.db_dal.actualizar_detalle_resultado(idDetalle, "ENVIADO", None)
                    enviados += 1
                except Exception as e:
                    self.db_dal.actualizar_detalle_resultado(idDetalle, "ERROR", str(e))
                    errores += 1

            # 4) Finalizar encabezado
            if errores == 0 and enviados > 0:
                self.db_dal.finalizar_encabezado(idEncabezado, "FINALIZADO", True)
            else:
                self.db_dal.finalizar_encabezado(idEncabezado, "FINALIZADO_CON_ERROR", False)

            return True, f"Enviados: {enviados}, Errores: {errores}", idEncabezado

        except Exception as e:
            return False, f"Error al enviar correos: {e}", None

    def programar_envio(self, scheduler, subject, body, fecha_envio_str, senderEmail, images_folder) -> Tuple[bool, str]:
        senderEmail = senderEmail.replace(" ", "").strip()
        try:
            fecha_envio = datetime.strptime(fecha_envio_str, "%Y-%m-%dT%H:%M")
            if fecha_envio <= datetime.now():
                return False, "La fecha debe ser futura"

            job_id = f"job_{fecha_envio.timestamp()}"

            #nle pasamos images_folder para que el job no dependa de Request/app.state
            scheduler.add_job(
                func=self.enviar_correos_ahora,
                trigger="date",
                run_date=fecha_envio,
                args=[subject, body, senderEmail, images_folder],
                id=job_id,
                replace_existing=True
            )

            return True, f"Correo programado para {fecha_envio}"
        except ValueError as e:
            return False, f"Formato de fecha inválido: {str(e)}"
        except Exception as e:
            return False, str(e)

    def preparar_detalles_pendientes(
            self,
            idEncabezado: int,
            subject: str,
            body: str,
            senderEmail: str,
            images_folder: str,
            excel_path: str | None = None,
        ) -> tuple[bool, str]:
            try:
                areas = self.imagen_dal.leer_areas(images_folder)
                destino = areas[0].get("url") if areas else None

                clientes = self._obtener_clientes(excel_path)

                destinatarios = []
                for c in clientes:
                    correo = self._get_email(c)
                    if correo:
                        c["Correo"] = correo
                        destinatarios.append(c)

                if not destinatarios:
                    return False, "No hay destinatarios válidos (revisa columna Correo/Email)."

                for c in destinatarios:
                    correo = c["Correo"]
                    subject_row = self._personalize(subject, c)
                    body_row = self._personalize(body, c)

                    cedula_row = self._pick(c, ["Cedula", "CEDULA"])
                    nombre_row = self._pick(c, ["Nombre", "NOMBRE"])
                    campana_row = self._pick(c, ["Campaña", "CAMPAÑA"])

                    self.db_dal.crear_detalle(
                        idEncabezado=idEncabezado,
                        email_destinatario=correo,
                        asunto=subject_row,
                        cuerpo=body_row,
                        click_url=destino,
                        adjuntos=None,
                        cedula=cedula_row,
                        nombre_cliente=nombre_row,
                        campana=campana_row,
                    )

                return True, f"Detalles creados: {len(destinatarios)}"
            except Exception as e:
                return False, f"Error preparando detalles: {e}"