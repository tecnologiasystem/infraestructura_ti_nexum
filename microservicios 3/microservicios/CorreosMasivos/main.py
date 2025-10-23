from fastapi import FastAPI
from app.api.Email_api import router as email_api
from fastapi.middleware.cors import CORSMiddleware

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


app.include_router(email_api)

@app.get("/")
async def read_root():
    return {"message": "Microservicio Email activo"}
