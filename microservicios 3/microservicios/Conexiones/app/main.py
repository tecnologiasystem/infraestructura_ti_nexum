# notifications_service/app/main.py

from fastapi import FastAPI
"""
Importa la clase principal `FastAPI`, que permite inicializar la aplicación web
y definir su configuración general (título, versión, descripción, etc.).
"""

from fastapi.middleware.cors import CORSMiddleware
"""
Se importa el middleware de CORS (Cross-Origin Resource Sharing), el cual es
necesario cuando el frontend (React, Angular, etc.) se encuentra en un dominio distinto
al backend. Permite que navegadores puedan hacer peticiones al API.
"""

from app.api.sms_api import router  # Solo tu router de SMS
"""
Se importa el router principal del módulo `sms_api.py`, que contiene los endpoints
relacionados con el envío de SMS individuales y masivos.
"""

# ------------------------ Inicialización de la aplicación FastAPI ------------------------

app = FastAPI(
    title="Notifications Service - SMS",              # Nombre visible en la documentación Swagger
    description="Microservicio para envío de SMS individuales y masivos",  # Descripción general
    version="1.0.0"                                    # Versión de la API
)

# ------------------------ Configuración de CORS ------------------------

origins = ["*"]  # Se permite acceso desde cualquier dominio (útil para pruebas)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # Qué orígenes pueden hacer peticiones (se recomienda restringir en producción)
    allow_credentials=True,           # Si se permite el uso de cookies/autenticación cruzada
    allow_methods=["*"],              # Qué métodos HTTP están permitidos (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],              # Qué cabeceras se permiten (ej: Authorization, Content-Type)
)

# ------------------------ Registro de rutas ------------------------

# Se incluye el router importado desde `sms_api.py`
# Todas las rutas comenzarán con `/sms` (por ejemplo: /sms/sms_send o /sms/send_excel)
# Además, se agrupan bajo la etiqueta "SMS" en la documentación Swagger
app.include_router(router, prefix="/sms", tags=["SMS"])
