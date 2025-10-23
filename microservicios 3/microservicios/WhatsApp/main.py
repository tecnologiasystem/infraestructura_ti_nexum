from fastapi import FastAPI
from app.api.numero_api import router as whatsApp_router
from app.api.envioWhatsapp_api import router as envioWhatapp_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Microservicio WhatsApp",
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

app.include_router(whatsApp_router, prefix="/numero_api")
app.include_router(envioWhatapp_router, prefix="/enviowhatsapp_api")

@app.get("/")
async def read_root():
    return {"message": "Microservicio WhatsApp activo"}
