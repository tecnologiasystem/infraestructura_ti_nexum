from fastapi import FastAPI
from app.api.Email_api import router as email_api
from app.api.Email_api import email_queue, _handler_email
from fastapi.middleware.cors import CORSMiddleware
from app.dal.Email_dal import listar_encabezados_en_proceso_con_pendientes

app = FastAPI(
    title="Microservicio Email",
    description="Email",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    email_queue.start_worker(_handler_email)

    # ✅ Recovery: reanudar envíos en progreso que tengan pendientes
    try:
        encabezados = listar_encabezados_en_proceso_con_pendientes()
        for e in encabezados:
            email_queue.enqueue({
                "action": "resume",
                "idEncabezado": e["idEncabezado"],
                "senderEmail": e.get("remitente"),
                "idUsuario": e.get("idUsuario"),
            })
        print(f"♻️ Recovery: encolados {len(encabezados)} encabezados EN_PROCESO con pendientes")
    except Exception as ex:
        print(f"❌ Recovery falló: {ex}")

app.include_router(email_api)

@app.get("/")
async def read_root():
    return {"message": "Microservicio Email activo"}
