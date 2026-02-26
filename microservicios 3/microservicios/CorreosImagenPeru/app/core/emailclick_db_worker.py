import time
import traceback
from app.bll.email_click_bll import EmailClickBLL

def start_emailclick_db_worker(images_folder: str, poll_seconds: int = 3, batch: int = 25):
    bll = EmailClickBLL()
    dal = bll.db_dal

    print("🧵 [EMAILCLICK-DB] Worker BD iniciado")

    while True:
        try:
            items = dal.claim_detalles_pendientes(limit=batch, retry_minutes=5)
            if not items:
                time.sleep(poll_seconds)
                continue

            for it in items:
                idDetalle = it["idDetalle"]
                idEncabezado = it["idEncabezado"]
                to_email = it["email_destinatario"]
                subject = it["asunto"]
                body = it["cuerpo"]
                senderEmail = (it["remitente"] or "").strip()

                print(f"📨 [EMAILCLICK] Enviando → idDetalle={idDetalle} | {to_email}")

                try:
                    html = bll._construir_html(body, images_folder, idDetalle, senderEmail)

                    bll.correo_dal.enviar_uno(
                        correo_destino=to_email,
                        subject=subject,
                        html_body=html,
                        senderEmail=senderEmail,
                        images_folder=images_folder,
                    )

                    dal.actualizar_detalle_resultado(idDetalle, "ENVIADO", None)
                    print(f"✅ [EMAILCLICK] ENVIADO → {to_email}")

                except Exception as e:
                    err = str(e)
                    err_l = err.lower()

                    if (
                        "mailbox unavailable" in err_l
                        or "try again later" in err_l
                        or "s2017062302" in err_l
                    ):
                        estado = "ERROR_TEMPORAL"
                    elif (
                        "5.1.1" in err_l
                        or "user unknown" in err_l
                        or "recipient address rejected" in err_l
                    ):
                        estado = "REBOTADO"
                    else:
                        estado = "ERROR"

                    dal.actualizar_detalle_resultado(idDetalle, estado, err)
                    print(f"❌ [EMAILCLICK] {estado} → {to_email} | {err}")

                # Intentar cerrar encabezado si ya no quedan pendientes
                resumen = dal.get_resumen_encabezado(idEncabezado)
                if resumen["pendientes"] == 0:
                    if resumen["errores"] == 0 and resumen["enviados"] > 0:
                        dal.finalizar_encabezado(idEncabezado, "FINALIZADO", True)
                        print(f"🏁 [EMAILCLICK] Encabezado {idEncabezado} FINALIZADO")
                    else:
                        dal.finalizar_encabezado(idEncabezado, "FINALIZADO_CON_ERROR", False)
                        print(f"⚠️ [EMAILCLICK] Encabezado {idEncabezado} FINALIZADO_CON_ERROR")

        except Exception as e:
            print("❌ [EMAILCLICK-DB] Error loop:", e)
            print(traceback.format_exc())
            time.sleep(5)
