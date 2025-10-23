from fastapi import FastAPI
from app.api.acuerdoPago_api import router as acuerdoPago_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Microservicio Teseo",
    description="Teseo",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(acuerdoPago_router, prefix="/acuerdoPago_api")

@app.get("/")
async def read_root():
    return {"message": "Microservicio Teseo activo"}
