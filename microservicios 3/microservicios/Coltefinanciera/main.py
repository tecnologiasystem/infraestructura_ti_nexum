from fastapi import FastAPI
from app.api.contelfinanciera_api import router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Microservicio Coltefinanciera",
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

app.include_router(router, prefix="/coltefinanciera_api")

@app.get("/")
async def read_root():
    return {"message": "Microservicio Coltelfinanciera activo"}
