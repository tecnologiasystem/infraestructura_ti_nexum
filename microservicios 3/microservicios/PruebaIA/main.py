# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.analysis_api import router as analysis_router

app = FastAPI(title="API Analisis IA Proyectos", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # ajusta en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router)  # monta las rutas de /analitica/* y /healthz

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8030, reload=True)
