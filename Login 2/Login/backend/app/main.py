from fastapi import FastAPI
from routers import auth_router, usuarios_router, reportes_router, dashboard_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://172.18.73.76:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Incluir el router de autenticación
app.include_router(auth_router.router)
app.include_router(usuarios_router.router)
app.include_router(reportes_router.router)
app.include_router(dashboard_router.router)

@app.get("/")
async def root():
    return {"message": "NEXUM API Backend running!"}
