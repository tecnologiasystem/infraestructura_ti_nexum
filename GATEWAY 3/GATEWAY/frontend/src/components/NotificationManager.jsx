import { useEffect, useRef } from "react";
import { notification } from "antd";
import { API_URL_GATEWAY } from "../config";
import io from "socket.io-client";

let socket;
const notificationSound = new Audio("/sounds/iphone-note-sms.mp3");

const NotificationManager = () => {
  const socketInitialized = useRef(false);

  useEffect(() => {
    if (socketInitialized.current) return;

    socket = io("http://172.18.72.111:8004", {
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
      timeout: 10000,
      autoConnect: true,
    });

    socket.on("connect", () => {
      const id = localStorage.getItem("idUsuario");
      if (id) socket.emit("register", { user_id: id });
    });

    const mostrarNotificacion = async (mensaje, remitente, remitenteId, fileName) => {
      const descripcion = fileName ? `📎 ${fileName}` : mensaje;

      notification.open({
        message: `💬 Mensaje de ${remitente}`,
        description: descripcion.length > 80 ? descripcion.slice(0, 80) + "..." : descripcion,
        placement: "bottomRight",
        duration: 5,
        onClick: () => {
          window.location.href = "/chat";
          localStorage.setItem("userChat", remitenteId);
        },
      });

      try {
        notificationSound.play();
      } catch {}
    };

    socket.on("private_message", async (data) => {
      const myId = localStorage.getItem("idUsuario");
      const isOwn = String(data.sender_id) === String(myId);
      if (isOwn) return;

      let nombre = data.sender_id;

      try {
        const res = await fetch(`${API_URL_GATEWAY}/gateway/buscarPersonas?query=${data.sender_id}&user_id=${myId}`);
        const result = await res.json();
        const persona = result.find((p) => p.idUsuarioApp.toString() === data.sender_id);
        if (persona) nombre = persona.nombre;
      } catch {}

      mostrarNotificacion(data.message, nombre, data.sender_id, data.fileName);
    });

    socketInitialized.current = true;
  }, []);

  return null;
};

export default NotificationManager;
