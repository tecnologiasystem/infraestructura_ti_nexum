from fastapi import FastAPI
from app.api.prueba_api import router as param_router

app = FastAPI(title="API Parametros Generales")

app.include_router(param_router)
