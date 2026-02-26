import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from xmlrpc import server

class CorreoDAL:
    @staticmethod
    def _resolve_email_password(sender_email: str):
        """
        Busca credenciales en variables tipo:
        EMAIL_1 / PASSWORD_1
        EMAIL_2 / PASSWORD_2
        ...
        Retorna (smtp_user, smtp_pass) si encuentra match por email.
        """
        if not sender_email:
            return None, None

        for i in range(1, 51):
            email_i = os.getenv(f"EMAIL_{i}")
            pass_i  = os.getenv(f"PASSWORD_{i}")
            if email_i and pass_i and email_i.strip().lower() == sender_email.strip().lower():
                return email_i, pass_i

        return None, None
    
    def enviar_uno(
        self,
        correo_destino: str,
        subject: str,
        html_body: str,
        senderEmail: str,
        images_folder: str
    ) -> None:
        
        senderEmail = senderEmail.replace(" ", "").strip()

        smtp_host = os.getenv("SMTP_HOST", "smtp.office365.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))

        # Resolver credenciales según remitente
        smtp_user, smtp_pass = self._resolve_email_password(senderEmail)

        if not smtp_user or not smtp_pass:
            raise RuntimeError(f"No hay credenciales para el remitente {senderEmail}")

        # Ruta imagen la que guardó el endpoint /guardar_imagen
        image_path = os.path.join(images_folder, "clickable_mi_image.png")

        if not os.path.exists(image_path):
            raise RuntimeError(f"No se encontró la imagen: {image_path}")

        # SMTP
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)

        try:
            msg = MIMEMultipart("related")
            msg["From"] = senderEmail
            msg["To"] = correo_destino
            msg["Subject"] = subject

            # HTML
            msg.attach(MIMEText(html_body, "html"))

            # Imagen embebida DEBE coincidir con el HTML: cid:clickimg
            with open(image_path, "rb") as f:
                img = MIMEImage(f.read(), name="clickable_mi_image.png")
                img.add_header("Content-ID", "<clickimg>")
                img.add_header("Content-Disposition", "inline", filename="clickable_mi_image.png")
                msg.attach(img)

            # Envío
            server.sendmail(senderEmail, [correo_destino], msg.as_string())

        finally:
            server.quit()

    def _mk_smtp(self, smtp_host: str, smtp_port: int, smtp_user: str, smtp_pass: str, timeout: int = 120):
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=timeout)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        return server

    def _smtp_safe_quit(self, server):
        try:
            if server:
                server.quit()
        except Exception:
            pass

    def _smtp_noop(self, server):
        try:
            # mantiene viva la conexión
            server.noop()
        except Exception:
            pass

    def enviar_uno_con_server(
        self,
        server,
        correo_destino: str,
        subject: str,
        html_body: str,
        senderEmail: str,
        images_folder: str
    ) -> None:
        senderEmail = senderEmail.replace(" ", "").strip()

        image_path = os.path.join(images_folder, "clickable_mi_image.png")
        if not os.path.exists(image_path):
            raise RuntimeError(f"No se encontró la imagen: {image_path}")

        msg = MIMEMultipart("related")
        msg["From"] = senderEmail
        msg["To"] = correo_destino
        msg["Subject"] = subject

        msg.attach(MIMEText(html_body, "html"))

        with open(image_path, "rb") as f:
            img = MIMEImage(f.read(), name="clickable_mi_image.png")
            img.add_header("Content-ID", "<clickimg>")
            img.add_header("Content-Disposition", "inline", filename="clickable_mi_image.png")
            msg.attach(img)

        server.sendmail(senderEmail, [correo_destino], msg.as_string())

    def enviar_masivo(self, clientes, subject, html_body, senderEmail: str, images_folder: str) -> int:
        smtp_host = os.getenv("SMTP_HOST", "smtp.office365.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))

        # credenciales según el remitente seleccionado
        smtp_user, smtp_pass = self._resolve_email_password(senderEmail)

        if not smtp_user or not smtp_pass:
            smtp_user = os.getenv("REMITENTE", "")
            smtp_pass = os.getenv("PASSWORD", "")

        if not smtp_user or not smtp_pass:
            raise RuntimeError(f"No hay credenciales configuradas para senderEmail={senderEmail}")

        # Usar la carpeta que te pasan
        image_path = os.path.join(images_folder, "clickable_mi_image.png")

        if not os.path.exists(image_path):
            raise RuntimeError(f"No se encontró la imagen: {image_path}")

        enviados = 0
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)

        try:
            for cliente in clientes:
                correo = cliente.get("Correo")
                if not correo:
                    continue

                msg = MIMEMultipart("related")
                msg["From"] = senderEmail
                msg["To"] = correo
                msg["Subject"] = subject

                msg.attach(MIMEText(html_body, "html"))

                with open(image_path, "rb") as f:
                    img = MIMEImage(f.read(), name="clickable_mi_image.png")
                    img.add_header("Content-ID", "<clickimg>")
                    img.add_header("Content-Disposition", "inline", filename="clickable_mi_image.png")
                    msg.attach(img)

                result = server.sendmail(senderEmail, [correo], msg.as_string())
                print("📨 sendmail result ->", correo, result)

                enviados += 1
        finally:
            server.quit()

        return enviados
