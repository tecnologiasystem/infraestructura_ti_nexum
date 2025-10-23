from app.bll.chat_bll import registrar_actividad, obtener_campanas_usuario_bll, guardar_mensaje_general_bll

"""
Este módulo define y registra todos los eventos que maneja el servidor de WebSockets
usando la librería `socketio`. Se encarga de registrar usuarios conectados, manejar
mensajes privados, grupales y generales, y sincronizar la lista de usuarios.

Cualquier error que se presente durante el flujo debería imprimir trazas en consola
para facilitar la depuración.
"""



"""
Diccionario global que almacena la relación entre IDs de usuario y sus respectivos
Socket IDs activos. Esto permite identificar qué usuario está conectado y a quién enviar mensajes.
"""
users = {}  # user_id: socket_id



def register_socket_events(sio):
    """
    Registra todos los eventos personalizados que puede recibir el servidor Socket.IO.

    Este es el punto de entrada de los canales WebSocket. Define comportamientos para:
    - Conexión inicial
    - Registro de usuarios
    - Mensajería privada
    - Mensajería grupal y general
    - Manejo de desconexión
    - Sincronización de listas de usuarios
    """

    @sio.event
    async def connect(sid, environ):
        """
        Se ejecuta automáticamente cuando un cliente establece conexión con el servidor.

        - sid: Identificador de sesión asignado por Socket.IO
        - environ: Información del entorno HTTP

        En caso de fallo: Este evento rara vez lanza errores, pero si los hay, pueden
        estar relacionados con problemas de red o configuración CORS en frontend/backend.
        """
        print(f"✅ Cliente conectado: {sid}")



    @sio.event
    async def register(sid, data):
        """
        Asocia un usuario autenticado con su sesión activa en el WebSocket.

        - data["user_id"]: ID del usuario conectado
        - Se actualiza el diccionario global `users` con esta relación
        - Se emiten eventos para informar al resto de usuarios conectados
        - Se une al usuario a las salas (rooms) de sus campañas activas

        En caso de fallo: Si `obtener_campanas_usuario_bll` falla, el usuario no podrá
        recibir mensajes grupales. Se loguea el error, pero no se detiene el flujo.
        """
        user_id = str(data["user_id"])
        users[user_id] = sid
        print(f"📌 Usuario {user_id} registrado con sid {sid}")

        await sio.emit("user_list", list(users.keys()))
        await sio.emit("register_ack", {"success": True}, to=sid)

        try:
            ids_campanas = obtener_campanas_usuario_bll(user_id)
            for campana_id in ids_campanas:
                await sio.enter_room(sid, str(campana_id))
                print(f"👥 Usuario {user_id} unido a campaña {campana_id}")
        except Exception as e:
            print(f"❌ Error al unir a campañas: {e}")

        return {"success": True}



    @sio.event
    async def private_message(sid, data):
        """
        Maneja el envío de un mensaje privado entre dos usuarios.

        - Se construye un mensaje con todos los campos relevantes (texto, archivo, timestamp)
        - Si el receptor está conectado, se le emite el mensaje
        - Independientemente de eso, el mensaje se guarda en la base de datos

        En caso de fallo:
        - Si `registrar_actividad` lanza error, se imprime traza pero no se detiene el flujo.
        - Si el receptor no está conectado, el mensaje no se pierde porque queda registrado.
        """
        print("📨 Mensaje recibido:", data)
        try:
            file_data = data.get("file")
            file_name = data.get("fileName")
            message_to_send = {
                "sender_id": data["sender_id"],
                "recipient_id": data["recipient_id"],
                "message": data.get("message", "{adjunto}"),
                "file": file_data,
                "fileName": file_name,
                "timestamp": data.get("timestamp"),
                "tempId": data.get("tempId")
            }

            recipient_sid = users.get(str(data["recipient_id"]))
            if recipient_sid:
                await sio.emit("private_message", message_to_send, to=recipient_sid)
                print(f"📤 Enviado a {recipient_sid} con archivo: {file_name if file_name else 'No'}")
            else:
                print(f"⚠️ Usuario {data['recipient_id']} no conectado")

            try:
                registrar_actividad(
                    usuario=data["sender_id"],
                    destinatario=str(data["recipient_id"]),
                    mensaje=data.get("message", "{adjunto}"),
                    file=file_data,
                    fileName=file_name
                )
            except Exception as e:
                print("❌ Error al registrar mensaje en BD:", e)

            return {"received": True}

        except Exception as e:
            import traceback
            traceback.print_exc()
            print("❌ Error al manejar mensaje:", e)
            return {"received": False}



    @sio.event
    async def disconnect(sid):
        """
        Evento que se dispara al desconectarse un cliente.

        - Busca qué usuario estaba conectado con ese `sid`
        - Lo elimina del diccionario `users`
        - Notifica a todos que este usuario se desconectó

        En caso de fallo: Si el `sid` no está registrado, simplemente no se hace nada.
        """
        user_id = None
        for uid, stored_sid in list(users.items()):
            if stored_sid == sid:
                user_id = uid
                del users[uid]
                break
        if user_id:
            await sio.emit("user_disconnected", {"user_id": user_id})
            await sio.emit("user_list", list(users.keys()))
            print(f"🔌 Usuario desconectado: {user_id}")

    @sio.event
    async def group_message(sid, data):
        """
        Maneja un mensaje enviado a un grupo/campaña.
        El cliente debe incluir: sender_id, room (idCampana), message|file|fileName, tempId.
        """
        try:
            room_id = str(data["room"])
            full_msg = {
                **data,
                "timestamp": data.get("timestamp") or int(time.time()*1000)
            }

            await sio.emit("group_message", full_msg, room=room_id, skip_sid=sid)

            registrar_actividad(
                usuario=data["sender_id"],
                destinatario=f"grupo_{room_id}",
                mensaje=data.get("message", "{adjunto}"),
                file=data.get("file"),
                fileName=data.get("fileName"),
            )

            return {"received": True}
        except Exception as e:
            print("❌ Error en group_message:", e)
            return {"received": False}


