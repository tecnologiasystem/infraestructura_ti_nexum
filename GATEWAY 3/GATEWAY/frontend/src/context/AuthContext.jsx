// context/AuthContext.js
import React, { createContext, useEffect, useRef } from 'react';
import { notification } from 'antd';
import { io } from 'socket.io-client';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const socketRef = useRef(null);
  const notificationSound = new Audio("/sounds/iphone-note-sms.mp3");

  useEffect(() => {
    const socket = io("http://172.18.72.111:8004", {
      transports: ["websocket"],
      autoConnect: true,
      reconnection: true,
    });
    socketRef.current = socket;

    const userId = localStorage.getItem("idUsuario");

    socket.on("connect", () => {
      if (userId) {
        socket.emit("register", { user_id: userId });
      }
    });

    const mostrarPopupNotificacion = (mensaje, remitente) => {
      notification.open({
        message: <strong>💬 {remitente}</strong>,
        description: mensaje.length > 80 ? mensaje.slice(0, 80) + "..." : mensaje,
        placement: "bottomRight",
        duration: 5,
        style: {
          backgroundColor: "#e6f7ff",
          borderRadius: "8px",
          boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
        },
      });

      try {
        notificationSound.play().catch(() => {});
      } catch (e) {
        console.warn("🔇 Error al reproducir sonido:", e);
      }
    };

    // 🔔 Escuchar mensajes privados
    socket.on("private_message", (data) => {
      if (String(data.sender_id) !== String(userId)) {
        const remitente = "Mensaje privado"; // opcional: luego puedes buscar el nombre real
        const mensaje = data.message || "📎 Archivo adjunto";
        mostrarPopupNotificacion(mensaje, remitente);
      }
    });

    // 🔔 Escuchar mensajes grupales
    socket.on("group_message", (data) => {
      if (String(data.sender_id) !== String(userId)) {
        const remitente = `Grupo ${data.room}`; // o usar el nombre real si lo tienes
        const mensaje = data.message || "📎 Archivo adjunto";
        mostrarPopupNotificacion(mensaje, remitente);
      }
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  const authState = {
    isAuthenticated: true,
    socket: socketRef.current,
  };

  return (
    <AuthContext.Provider value={authState}>
      {children}
    </AuthContext.Provider>
  );
};
