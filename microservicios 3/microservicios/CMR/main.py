# main.py
from fastapi import FastAPI
from app.api.conversaciones_api import router as conversaciones_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Microservicio CRM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(conversaciones_router)

@app.get("/")
async def read_root():
    return {"message": "Microservicio CRM activo"}
