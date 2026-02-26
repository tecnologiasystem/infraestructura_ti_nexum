# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as homologacion_router

# Instancia de FastAPI
app = FastAPI(title="API Homologación Segura")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],        # GET, POST, PUT...
    allow_headers=["*"],        # Headers permitidos
)

# Incluir routers
app.include_router(homologacion_router, prefix="/api", tags=["homologacion"])

@app.get("/")
async def read_root():
    return {"message": "Microservicio activo"}
