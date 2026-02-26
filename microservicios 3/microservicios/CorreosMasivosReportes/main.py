from fastapi import FastAPI
from app.api.Reporte_api import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Microservicio Email Reportes",
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


app.include_router(router)

@app.get("/")
async def read_root():
    return {"message": "Microservicio Email Reportes activo"}
