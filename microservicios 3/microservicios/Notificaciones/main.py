from fastapi import FastAPI
from app.api.mensajeWhatsapp_api import router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Microservicio Mensaje Whatsapp",
    description="WhatsApp",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/mensajeWhatsapp_api")

@app.get("/")
async def read_root():
    return {"message": "Microservicio WhatsApp activo"}
