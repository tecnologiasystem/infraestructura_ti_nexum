import os
import threading
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from app.api.email_click_api import router as email_click_router
from app.core.emailclick_db_worker import start_emailclick_db_worker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def create_app() -> FastAPI:
    load_dotenv()

    app = FastAPI(title="Email Click Service")

    upload_folder = os.getenv("UPLOAD_FOLDER", "uploads")
    images_folder = os.getenv("IMAGES_FOLDER", "static/imagenes")
    timezone = os.getenv("TIMEZONE", "America/Bogota")

    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(images_folder, exist_ok=True)

    if not os.path.exists("static"):
        os.makedirs("static", exist_ok=True)

    images_abs = os.path.join(BASE_DIR, images_folder)
    app.mount("/static", StaticFiles(directory=images_abs), name="static")

    # Guardamos config en app.state
    app.state.UPLOAD_FOLDER = upload_folder
    app.state.IMAGES_FOLDER = images_folder
    app.state.TIMEZONE = timezone

    # Scheduler (para envíos programados)
    scheduler = BackgroundScheduler(timezone=timezone)
    scheduler.start()
    app.state.scheduler = scheduler

    # ARRANQUE DEL WORKER
    @app.on_event("startup")
    def start_db_worker():
        t = threading.Thread(
            target=start_emailclick_db_worker,
            args=(images_folder,),
            daemon=True
        )
        t.start()
        print("🧵 [MAIN] Worker BD EmailClick iniciado")

    # Routes
    app.include_router(
        email_click_router,
        prefix="/email_click_api",
        tags=["EmailClick"]
    )

    @app.on_event("shutdown")
    def shutdown_event():
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass

    return app

app = create_app()
