from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from app.api.APIChat import router as chat_router
from app.api.chat_api import register_socket_events

"""
Inicializa el servidor Socket.IO en modo asíncrono (`asgi`) y habilita CORS globalmente.
Este archivo representa el punto de entrada principal de la aplicación FastAPI
con soporte para WebSockets y HTTP.

Estructura:
- Inicializa FastAPI
- Configura CORS
- Registra rutas HTTP del chat
- Registra eventos WebSocket
- Expone `app_with_sockets` como la aplicación completa
"""



"""
Instancia del servidor Socket.IO asíncrono.

- cors_allowed_origins="*": Permite conexiones desde cualquier origen (útil para frontend externo).
- async_mode="asgi": Modo requerido para integrarse con FastAPI y ASGI.
"""
sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")



"""
Inicializa la aplicación FastAPI sin rutas por ahora.
"""
app = FastAPI()



"""
Middleware CORS para permitir acceso desde cualquier origen.

Configuración:
- allow_origins=["*"]: Acepta peticiones desde todos los dominios.
- allow_credentials=True: Permite incluir cookies o headers de autenticación.
- allow_methods=["*"]: Permite todos los métodos HTTP (GET, POST, etc.).
- allow_headers=["*"]: Permite todos los encabezados personalizados.
"""
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



"""
Se registran los endpoints HTTP del módulo de chat.

Estos endpoints están definidos en `APIChat.py` y se agrupan bajo el prefijo `/chat`.
"""
app.include_router(chat_router, prefix="/chat")



"""
Se registran todos los eventos personalizados de WebSocket para el chat.

Estos eventos son manejados dentro de `chat_api.py` y cubren:
- Conexión
- Mensajes privados
- Mensajes grupales
- Desconexión
- Validaciones de permisos
"""
register_socket_events(sio)



"""
Combina la app FastAPI y Socket.IO para crear la aplicación final con soporte para WebSocket + HTTP.

Esta variable (`app_with_sockets`) es la que se debe usar como entrada para el servidor ASGI (Uvicorn o Hypercorn).
"""
app_with_sockets = socketio.ASGIApp(sio, app)
