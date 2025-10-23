import React, { useState, useEffect, useRef } from "react";
import io from "socket.io-client";
import {
  Layout,
  List,
  Avatar,
  Input,
  Card,
  Typography,
  Button,
  Tooltip,
  Modal,
  message,
} from "antd";
import {
  SendOutlined,
  SearchOutlined,
  PaperClipOutlined,
  SmileOutlined,
  TeamOutlined,
  MessageOutlined,
} from "@ant-design/icons";
import EmojiPicker from "emoji-picker-react";
import dayjs from "dayjs";
import "./Chat.css";
import { API_URL_GATEWAY } from "../../config";
import { v4 as uuidv4 } from "uuid";
import isSameOrAfter from "dayjs/plugin/isSameOrAfter";
import advancedFormat from "dayjs/plugin/advancedFormat";
import "dayjs/locale/es";
import { notification } from "antd";

dayjs.locale("es");
dayjs.extend(isSameOrAfter);
dayjs.extend(advancedFormat);

// Socket único global con mejor manejo de conexión
let socket;
let socketConnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 10;

const initSocket = () => {
  if (socket && socket.connected) return socket;

  // Si ya existe un socket pero está desconectado, limpiarlo
  if (socket) {
    socket.removeAllListeners();
    socket.close();
  }

  // Crear nueva instancia con opciones mejoradas
  socket = io("http://172.18.72.111:8004", {
    transports: ["websocket", "polling"], // Habilitamos fallback a polling
    reconnection: true,
    reconnectionAttempts: MAX_RECONNECT_ATTEMPTS,
    reconnectionDelay: 1000,
    timeout: 10000,
    autoConnect: true,
  });

  // Manejo de eventos de conexión mejorado
  socket.on("connect", () => {
    console.log("🟢 Socket conectado:", socket.id);
    socketConnectAttempts = 0; // Reiniciamos contador de intentos

    const storedUserId = localStorage.getItem("idUsuario");
    if (storedUserId) {
      console.log("🧠 [Socket] Registrando usuario:", storedUserId);
      socket.emit("register", { user_id: storedUserId }, (ack) => {
        if (ack && ack.success) {
          console.log("✅ Usuario registrado exitosamente en el socket");
        } else {
          console.warn("⚠️ No se recibió confirmación del registro en socket");
        }
      });
    }
  });

  socket.on("connect_error", (err) => {
    socketConnectAttempts++;
    if (socketConnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
      message.error(
        "Error persistente al conectar con el servidor de chat. Por favor, recarga la página."
      );
    } else {
      message.warning("Problemas de conexión con el chat. Reconectando...");
    }
  });

  socket.on("disconnect", (reason) => {
    if (reason === "io server disconnect") {
      // El servidor cerró la conexión, reconectamos manualmente
      setTimeout(() => {
        socket.connect();
      }, 1000);
    }
    // Los otros casos son manejados automáticamente por socket.io
  });

  socket.on("reconnect", (attemptNumber) => {
    // Re-registrar usuario tras reconexión
    const storedUserId = localStorage.getItem("idUsuario");
    if (storedUserId) {
      socket.emit("register", { user_id: storedUserId });
    }
  });

  socket.io.on("reconnect_attempt", () => {});

  socket.io.on("reconnect_error", (err) => {
    console.error("❌ Error en reconexión:", err);
  });

  socket.io.on("reconnect_failed", () => {
    message.error(
      "No se pudo reconectar al servidor de chat. Por favor, recarga la página."
    );
  });

  return socket;
};

const notificationSound = new Audio("/sounds/iphone-note-sms.mp3");

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

// Componente de estado de conexión
const ConnectionStatus = ({ isConnected }) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: "6px",
      fontSize: "12px",
      color: isConnected ? "#52c41a" : "#ff4d4f",
      fontWeight: "500",
    }}
  >
    <div
      style={{
        width: "8px",
        height: "8px",
        borderRadius: "50%",
        backgroundColor: isConnected ? "#52c41a" : "#ff4d4f",
        animation: isConnected ? "none" : "pulse 2s infinite",
      }}
    />
    {isConnected ? "Conectado" : "Reconectando..."}
  </div>
);

const ChatApp = () => {
  const [userId, setUserId] = useState("");
  const [nombre, setUserNombre] = useState("");
  const [userRole, setUserRole] = useState(null);
  const [chatPartners, setChatPartners] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [recipientId, setRecipientId] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [messageText, setMessageText] = useState("");
  const [attachedFile, setAttachedFile] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [searchModalVisible, setSearchModalVisible] = useState(false);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [allMessages, setAllMessages] = useState({});
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const emojiPickerRef = useRef(null);
  const [unreadMessages, setUnreadMessages] = useState({});
  const [modoGrupal, setModoGrupal] = useState(false);
  const socketListenersRef = useRef(false);
  const [highlightedMessageIndex, setHighlightedMessageIndex] = useState(null);
  const messageRefs = useRef([]);
  const [chatSearchTerm, setChatSearchTerm] = useState("");
  const usuariosMapRef = useRef({});
  const [isSocketReady, setIsSocketReady] = useState(false);
  const campanasFullRef = useRef([]);
  const [imagenEnModal, setImagenEnModal] = useState(null);
  const [nombreImagenModal, setNombreImagenModal] = useState("");
  const [notificacionGeneral, setNotificacionGeneral] = useState(0);
  const [messageStatus, setMessageStatus] = useState({}); // Para rastrear estado de mensajes
  const pendingMessagesRef = useRef([]); // Cola de mensajes pendientes

  const [miembrosGrupo, setMiembrosGrupo] = useState([]);
  const [modalMiembrosVisible, setModalMiembrosVisible] = useState(false);
  const [puedeEnviarMensajeGeneral, setPuedeEnviarMensajeGeneral] =
    useState(false);

  useEffect(() => {
    const preventDefault = (e) => {
      e.preventDefault();
      e.stopPropagation();
    };

    window.addEventListener("dragover", preventDefault);
    window.addEventListener("drop", preventDefault);

    return () => {
      window.removeEventListener("dragover", preventDefault);
      window.removeEventListener("drop", preventDefault);
    };
  }, []);

  useEffect(() => {
    if (document.hasFocus()) {
      document.title = "Toki";
    } else {
      document.title =
        notificacionGeneral > 0 ? `(${notificacionGeneral}) Toki` : "Toki";
    }
  }, [notificacionGeneral]);

  useEffect(() => {
    const handleFocus = () => {
      document.title = "Toki";
      setNotificacionGeneral(0);
    };

    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, []);

  useEffect(() => {
    if ("Notification" in window && Notification.permission !== "granted") {
      Notification.requestPermission();
    }
  }, []);

  // Función para procesar los mensajes pendientes cuando el socket se reconecta
  const processPendingMessages = () => {
    if (!socket || !socket.connected || pendingMessagesRef.current.length === 0)
      return;

    // Creamos una copia para no modificar mientras iteramos
    const pendingMessages = [...pendingMessagesRef.current];
    pendingMessagesRef.current = [];

    pendingMessages.forEach((msg) => {
      if (msg.isGroupMessage) {
        socket.emit("group_message", msg, (ack) => {
          if (ack && ack.received) {
            setMessageStatus((prev) => ({
              ...prev,
              [msg.tempId]: "delivered",
            }));
          }
        });
      } else {
        socket.emit("private_message", msg, (ack) => {
          if (ack && ack.received) {
            setMessageStatus((prev) => ({
              ...prev,
              [msg.tempId]: "delivered",
            }));
          }
        });
      }
    });
  };

  const obtenerNombreCampaña = (idCampana) => {
    const campanaInfo = campanasFullRef.current.find(
      (c) => c.idCampana === parseInt(idCampana)
    );
    return campanaInfo
      ? campanaInfo.descripcionCampana
      : `Grupo Campaña ${idCampana}`;
  };

  // Función mejorada para guardar mensajes en el servidor
  const guardarMensaje = async (mensaje) => {
    try {
      const endpoint = modoGrupal
        ? `${API_URL_GATEWAY}/gateway/guardarMensajeGrupo`
        : `${API_URL_GATEWAY}/gateway/guardarMensaje`;

      const payload = {
        sender_id: mensaje.sender_id,
        message: mensaje.message || "",
        timestamp: mensaje.timestamp || Date.now(),
        file: mensaje.file || null,
        fileName: mensaje.fileName || null,
      };

      if (modoGrupal) {
        const campId = mensaje.room || currentUser.campanas[0].toString();
        payload.idCampana = campId;
      } else {
        payload.recipient_id = mensaje.recipient_id;
      }

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 segundos de timeout

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(
          `Error al guardar mensaje: ${response.status} ${errorText}`
        );
      }

      return true; // Éxito
    } catch (error) {
      // Si es un error de timeout o red, podríamos reintentar
      if (error.name === "AbortError" || error.message.includes("network")) {
        setTimeout(() => guardarMensaje(mensaje), 5000); // Reintentar en 5 segundos
      }
      return false;
    }
  };

  const addOrUpdateChatPartner = (partner) => {
    setChatPartners((prev) => {
      const index = prev.findIndex((p) => p.id === partner.id);
      if (index >= 0) {
        const updated = [...prev];
        updated[index] = { ...updated[index], ...partner };
        return updated.sort((a, b) => b.lastMessageAt - a.lastMessageAt);
      } else {
        return [partner, ...prev].sort(
          (a, b) => b.lastMessageAt - a.lastMessageAt
        );
      }
    });
  };

  const setupSocketListeners = () => {
    if (socketListenersRef.current || !socket) return;
    socketListenersRef.current = true;

    socket.on("private_message", async (data) => {
      const myId = localStorage.getItem("idUsuario");
      const isOwn = String(data.sender_id) === String(myId);
      const otherId = isOwn ? data.recipient_id : data.sender_id;

      if (String(otherId).startsWith("grupo_")) return;

      const userKey = String(otherId);
      const newMsg = {
        ...data,
        isOwnMessage: isOwn,
        timestamp: data.timestamp || Date.now(),
        file: data.file || null,
        fileName: data.fileName || null,
      };

      if (isOwn && data.tempId) {
        setMessageStatus((prev) => ({ ...prev, [data.tempId]: "delivered" }));
      }

      // Evitar duplicados
      setAllMessages((prev) => {
        if (
          isOwn &&
          data.tempId &&
          prev[userKey]?.some((m) => m.tempId === data.tempId)
        ) {
          return {
            ...prev,
            [userKey]: prev[userKey].map((m) =>
              m.tempId === data.tempId ? { ...m, status: "delivered" } : m
            ),
          };
        }
        return {
          ...prev,
          [userKey]: [...(prev[userKey] || []), newMsg],
        };
      });

      if (!isOwn) {
        socket.emit("message_received", {
          message_id: data.tempId,
          recipient_id: myId,
          sender_id: data.sender_id,
        });

        guardarMensaje(data);
      }

      // Buscar nombre si no está
      let userInPartners = chatPartners.find((p) => p.id === userKey);

      if (!isOwn) {
        // Mostrar notificación visual
        let nombreRemitente =
          usuariosMapRef.current[data.sender_id] || userInPartners?.name;

        if (!nombreRemitente) {
          try {
            const res = await fetch(
              `${API_URL_GATEWAY}/gateway/buscarPersonas?query=${encodeURIComponent(
                data.sender_id
              )}&user_id=${localStorage.getItem("idUsuario")}`
            );
            const result = await res.json();
            const userData = result.find(
              (u) => u.idUsuarioApp.toString() === data.sender_id
            );
            if (userData) {
              nombreRemitente = userData.nombre;
              usuariosMapRef.current[data.sender_id] = nombreRemitente;

              // Actualiza la lista lateral también
              addOrUpdateChatPartner({
                id: data.sender_id.toString(),
                name: nombreRemitente,
                role: userData.rol || "",
                lastMessageAt: Date.now(),
              });
            }
          } catch (err) {
            nombreRemitente = "Usuario";
          }
        }

        // ✅ Mostrar notificación con nombre correcto
        mostrarPopupNotificacion(
          newMsg.message,
          nombreRemitente || "Usuario",
          data.sender_id,
          newMsg.fileName
        );

        try {
          notificationSound.play().catch((e) => {
            console.warn("🔇 Error al reproducir sonido:", e);
          });
        } catch (e) {
          console.warn("🔇 Error al reproducir sonido:", e);
        }
      }

      // Marcar como no leído si no está en la vista
      if (!document.hasFocus() || currentUser?.id !== userKey) {
        setUnreadMessages((prev) => ({
          ...prev,
          [userKey]: (prev[userKey] || 0) + 1,
        }));
      }

      if (!document.hasFocus()) {
        setNotificacionGeneral((prev) => prev + 1);
      }

      // Si no tenemos el nombre, lo buscamos y lo guardamos
      if (
        !userInPartners ||
        !userInPartners.name ||
        userInPartners.name === userKey
      ) {
        try {
          if (!userKey || isNaN(Number(userKey))) {
            return;
          }

          const res = await fetch(
            `${API_URL_GATEWAY}/gateway/buscarPersonas?query=${encodeURIComponent(
              userKey
            )}&user_id=${localStorage.getItem("idUsuario")}`
          );
          const result = await res.json();
          const userData = result.find(
            (u) => u.idUsuarioApp.toString() === userKey
          );
          if (userData) {
            usuariosMapRef.current[userKey] = userData.nombre; // ✅ actualiza el nombre inmediatamente

            addOrUpdateChatPartner({
              id: userKey,
              name: userData.nombre || userKey,
              role: userData.rol || "",
              lastMessageAt: Date.now(),
            });
          }
        } catch (err) {}
      } else {
        addOrUpdateChatPartner({
          id: userKey,
          name: userInPartners.name,
          role: userInPartners.role || "",
          lastMessageAt: Date.now(),
        });
      }
    });

    // Evento de confirmación de entrega
    socket.on("message_received", (data) => {
      if (data.message_id) {
        setMessageStatus((prev) => ({
          ...prev,
          [data.message_id]: "delivered",
        }));

        // Actualizar el estado del mensaje en allMessages
        setAllMessages((prev) => {
          const userId = data.recipient_id;
          if (prev[userId]) {
            return {
              ...prev,
              [userId]: prev[userId].map((msg) =>
                msg.tempId === data.message_id
                  ? { ...msg, status: "delivered" }
                  : msg
              ),
            };
          }
          return prev;
        });
      }
    });

    socket.on("group_message", (data) => {
      const campanaId = data.room;
      const myId = localStorage.getItem("idUsuario");

      // 🛑 Filtro 1: ignorar si no hay room o no es numérico
      if (!String(campanaId).match(/^\d+$/)) {
        console.warn("🚫 ID de grupo no válido (room):", campanaId);
        return;
      }

      // 🛑 Filtro 2: mensaje que parece privado (porque tiene recipient_id)
      if (data.recipient_id && !data.room) {
        console.warn("🚫 Mensaje parece privado pero llegó como grupal:", data);
        return;
      }

      const groupKey = `grupo_${campanaId}`;
      const isOwn = String(data.sender_id) === String(myId);

      const newMsg = {
        ...data,
        isOwnMessage: isOwn,
        timestamp: data.timestamp || Date.now(),
        file: data.file || null,
        fileName: data.fileName || null,
      };

      // ✅ Evita duplicados por tempId
      if (isOwn && data.tempId) {
        setMessageStatus((prev) => ({ ...prev, [data.tempId]: "delivered" }));
      }

      setAllMessages((prev) => {
        if (
          isOwn &&
          data.tempId &&
          prev[groupKey]?.some((m) => m.tempId === data.tempId)
        ) {
          return {
            ...prev,
            [groupKey]: prev[groupKey].map((m) =>
              m.tempId === data.tempId ? { ...m, status: "delivered" } : m
            ),
          };
        }
        return {
          ...prev,
          [groupKey]: [...(prev[groupKey] || []), newMsg],
        };
      });

      if (!isOwn) {
        socket.emit("group_message_received", {
          message_id: data.tempId,
          room: campanaId,
          recipient_id: myId,
          sender_id: data.sender_id,
        });

        //guardarMensaje(data);

        try {
          notificationSound.play().catch((e) => {
            console.warn("🔇 Error al reproducir sonido:", e);
          });
        } catch (e) {
          console.warn("🔇 Error al reproducir sonido:", e);
        }

        const nombreRemitente =
          usuariosMapRef.current[data.sender_id] || "Grupo";
        mostrarPopupNotificacion(
          newMsg.message,
          nombreRemitente,
          data.sender_id,
          newMsg.fileName
        );
      }

      if (!document.hasFocus() || currentUser?.id !== groupKey) {
        setUnreadMessages((prev) => ({
          ...prev,
          [groupKey]: (prev[groupKey] || 0) + 1,
        }));
      }

      if (!document.hasFocus()) {
        setNotificacionGeneral((prev) => prev + 1);
      }

      addOrUpdateChatPartner({
        id: groupKey,
        name: obtenerNombreCampaña(campanaId),
        role: "Grupo",
        campanas: [campanaId],
        lastMessageAt: Date.now(),
      });
    });

    socket.on("general_message", (data) => {
      const newMsg = {
        sender_id: data.sender_id,
        message: data.message,
        file: data.file || null,
        fileName: data.fileName || null,
        isOwnMessage:
          String(data.sender_id) === String(localStorage.getItem("idUsuario")),
        timestamp: data.timestamp || Date.now(),
      };

      // Agregar al estado del grupo general
      setAllMessages((prev) => ({
        ...prev,
        grupo_general: [...(prev["grupo_general"] || []), newMsg],
      }));

      // Mostrar notificación
      mostrarPopupNotificacion(
        newMsg.message,
        "¡Al Día Con System!",
        "grupo_general",
        newMsg.fileName
      );

      try {
        notificationSound.play().catch((e) => {
          console.warn("🔇 Error al reproducir sonido:", e);
        });
      } catch (e) {
        console.warn("🔇 Error al reproducir sonido:", e);
      }

      // Incrementar contadores
      if (!document.hasFocus() || currentUser?.id !== "grupo_general") {
        setUnreadMessages((prev) => ({
          ...prev,
          grupo_general: (prev["grupo_general"] || 0) + 1,
        }));
      }

      if (!document.hasFocus()) {
        setNotificacionGeneral((prev) => prev + 1);
      }
    });

    // Confirmación para mensajes grupales
    socket.on("group_message_received", (data) => {
      if (data.message_id) {
        setMessageStatus((prev) => ({
          ...prev,
          [data.message_id]: "delivered",
        }));
      }
    });

    socket.on("user_list", (usuarios) => {
      // Implementación para manejar la lista de usuarios
    });

    // Estado de disponibilidad del socket
    setIsSocketReady(true);

    // Procesar mensajes pendientes que pudieran existir
    processPendingMessages();
  };

  const currentMessages = allMessages[recipientId] || [];

  const cargarTodasLasPersonas = async () => {
    try {
      // Obtener campañas del usuario
      const resCampanas = await fetch(
        `${API_URL_GATEWAY}/gateway/usuariosCampanas/dar`
      );
      const campanasData = await resCampanas.json();

      const resCampanasFull = await fetch(
        `${API_URL_GATEWAY}/gateway/campanas/dar`
      );
      const campanasFull = await resCampanasFull.json();
      campanasFullRef.current = campanasFull;

      const usuarioId = Number(localStorage.getItem("idUsuario"));
      const usuarioCampanas = campanasData.filter(
        (camp) => camp.idUsuarioApp === usuarioId
      );
      const idsCampanas = usuarioCampanas.map((camp) => camp.idCampana);

      // Validación del parámetro query
      const urlBuscarPersonas = `${API_URL_GATEWAY}/gateway/buscarPersonas?query=&user_id=${usuarioId}`;
      const resPersonas = await fetch(urlBuscarPersonas);

      // Validación clave
      if (!resPersonas.ok) {
        console.error(
          "❌ Error al llamar buscarPersonas con query vacío",
          resPersonas.statusText
        );
        message.error(
          "Error al obtener las personas. Intentando nuevamente..."
        );

        // Reintentar después de un breve delay
        setTimeout(() => cargarTodasLasPersonas(), 3000);
        return;
      }

      const data = await resPersonas.json();

      // Asegurar que data es un array antes de hacer map
      if (!Array.isArray(data)) {
        console.error("⚠️ La respuesta NO es un array:", data);
        message.error(
          "La respuesta recibida no es válida. Intentando nuevamente..."
        );
        setTimeout(() => cargarTodasLasPersonas(), 3000);
        return;
      }

      const personasConCampanas = data.map((p) => {
        const campanasDePersona = campanasData.filter(
          (camp) => camp.idUsuarioApp === p.idUsuarioApp
        );
        const campanasPersonaIds = campanasDePersona.map(
          (camp) => camp.idCampana
        );
        return {
          ...p,
          campanas: campanasPersonaIds,
        };
      });

      const rolActual = parseInt(localStorage.getItem("idRol"));

      const personas = personasConCampanas
        .filter((persona) => {
          const comparteCampana =
            Array.isArray(persona.campanas) &&
            persona.campanas.some((camp) => idsCampanas.includes(camp));
          const esOtroAsesor =
            rolActual === 14 && persona.rol?.toLowerCase() === "asesor";
          return comparteCampana && !esOtroAsesor;
        })
        .map((p) => ({
          id: p.idUsuarioApp.toString(),
          name: p.nombre,
          role: p.rol,
          campanas: p.campanas || [],
        }));

      const mapaUsuarios = {};
      personas.forEach((p) => {
        mapaUsuarios[p.id] = p.name;
      });
      usuariosMapRef.current = mapaUsuarios;

      const gruposVirtuales = idsCampanas.map((idCampana) => {
        const campanaInfo = campanasFull.find((c) => c.idCampana === idCampana);
        return {
          id: `grupo_${idCampana}`,
          name: campanaInfo
            ? `${campanaInfo.descripcionCampana}`
            : `Grupo ${idCampana}`,
          role: "Grupo",
          campanas: [idCampana],
        };
      });

      const grupoGeneral = {
        id: "grupo_general",
        name: "¡Al Día Con System! 🎉",
        role: "General",
      };

      setChatPartners([grupoGeneral, ...gruposVirtuales, ...personas]);
      localStorage.setItem("chatPartners", JSON.stringify(personas));
    } catch (err) {
      console.error("❌ Error al cargar personas:", err);
      message.error("Error al cargar la lista de contactos. Reintentando...");
      setTimeout(() => cargarTodasLasPersonas(), 5000);
    }
  };

  const effectiveUserId =
    userId || localStorage.getItem("id") || localStorage.getItem("idUsuario");

  useEffect(() => {
    const rol = parseInt(localStorage.getItem("idRol")) || 0;
    setUserRole(rol);

    const storedUserId = localStorage.getItem("idUsuario");
    const storedUserNombre = localStorage.getItem("userName");

    if (storedUserId && storedUserNombre) {
      setUserId(storedUserId);
      setUserNombre(storedUserNombre);

      // Restaurar chats
      const savedPartners = localStorage.getItem("chatPartners");
      if (savedPartners) {
        try {
          const parsed = JSON.parse(savedPartners);
          const ordered = parsed.sort(
            (a, b) => (b.lastMessageAt || 0) - (a.lastMessageAt || 0)
          );
          setChatPartners(ordered);
        } catch (err) {
          console.error("❌ Error al parsear chatPartners:", err);
        }
      }

      // Inicializar socket de manera más robusta
      socket = initSocket();

      // Asegurarse que el usuario está registrado con confirmación
      if (socket && socket.connected) {
        socket.emit("register", { user_id: storedUserId }, (ack) => {
          if (ack && ack.success) {
          }
          setupSocketListeners();
        });
      } else {
        socket.once("connect", () => {
          socket.emit("register", { user_id: storedUserId });
          setupSocketListeners();
        });
      }

      // Cargar historial de chats
      fetchUserChats(storedUserId, 0);
    }

    return () => {
      // Limpieza
      if (socket) {
        socket.off("private_message");
        socket.off("group_message");
        socket.off("message_received");
        socket.off("group_message_received");
      }
    };
  }, [userId]);

  // Efecto para configurar los listeners del socket cuando esté disponible
  useEffect(() => {
    if (socket && !socketListenersRef.current) {
      setupSocketListeners();
    }
  }, [socket]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [currentMessages]);

  useEffect(() => {
    cargarTodasLasPersonas();
  }, []); // Solo una vez al montar

  useEffect(() => {
    const handlePaste = (event) => {
      const items = event.clipboardData?.items;
      if (!items || !currentUser) return;

      for (const item of items) {
        if (item.type.indexOf("image") !== -1) {
          const file = item.getAsFile();
          if (file) {
            handleAttachDroppedFile(file); // ya se encarga de enviar solo el archivo como mensaje
          }
        }
      }
    };

    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  }, [currentUser]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        emojiPickerRef.current &&
        !emojiPickerRef.current.contains(event.target)
      ) {
        setShowEmojiPicker(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Comprobar y procesar mensajes pendientes cada vez que el socket cambia de estado
  useEffect(() => {
    if (isSocketReady && socket && socket.connected) {
      processPendingMessages();
    }
  }, [isSocketReady]);

  const fetchUserChats = async (userId, REC) => {
    // Validar claramente que REC sea numérico antes de hacer fetch
    if (isNaN(Number(REC))) {
      console.warn("REC no es numérico:", REC);
      return;
    }

    try {
      const response = await fetch(
        `${API_URL_GATEWAY}/gateway/getChats?user_id=${localStorage.getItem(
          "idUsuario"
        )}&recipient_id=${REC}`,
        { signal: AbortSignal.timeout(15000) } // Timeout de 15 segundos
      );

      if (!response.ok) {
        throw new Error(
          `Error en la respuesta: ${response.status} ${response.statusText}`
        );
      }

      const data = await response.json();

      if (Array.isArray(data)) {
        const messagesPorUsuario = {};
        const uniqueUserIds = new Set();

        data.forEach((chat) => {
          const sender = String(chat.sender_id || chat.idRemitente);
          const recipient = String(chat.recipient_id || chat.idDestinatario);
          const otherUserId = sender === userId ? recipient : sender;

          const newMsg = {
            sender_id: sender,
            recipient_id: recipient,
            message: chat.message || chat.mensaje || "",
            file: chat.file || null,
            fileName: chat.fileName || null,
            isOwnMessage: String(sender) === String(effectiveUserId),
            timestamp: chat.timestamp || Date.now(),
            status: "delivered", // mensajes históricos ya están entregados
          };

          uniqueUserIds.add(otherUserId);

          if (!messagesPorUsuario[otherUserId]) {
            messagesPorUsuario[otherUserId] = [];
          }
          messagesPorUsuario[otherUserId].push(newMsg);
        });

        setAllMessages((prev) => {
          const nuevo = { ...prev };
          for (const [otherUserId, mensajes] of Object.entries(
            messagesPorUsuario
          )) {
            nuevo[otherUserId] = [...(prev[otherUserId] || []), ...mensajes];
          }
          return nuevo;
        });

        const partnersDetails = await Promise.all(
          Array.from(uniqueUserIds).map(async (pid) => {
            try {
              const res = await fetch(
                `${API_URL_GATEWAY}/gateway/buscarPersonas?query=${encodeURIComponent(
                  pid
                )}&user_id=${localStorage.getItem("idUsuario")}`
              );
              const result = await res.json();
              const userData = result.find(
                (u) => u.idUsuarioApp.toString() === pid
              );
              return {
                id: pid,
                name: userData?.nombre || pid,
                role: userData?.rol || "",
              };
            } catch {
              return { id: pid, name: pid, role: "" };
            }
          })
        );

        const previous = localStorage.getItem("chatPartners");
        let previousPartners = [];
        if (previous) {
          try {
            previousPartners = JSON.parse(previous);
          } catch (e) {
            console.error("❌ Error parsing stored chatPartners:", e);
          }
        }

        const merged = [...partnersDetails];
        previousPartners.forEach((old) => {
          const exists = merged.find((p) => p.id === old.id);
          if (!exists) {
            merged.push(old);
          }
        });

        const ordered = merged
          .map((p) => {
            const msgs = allMessages[p.id] || [];
            const lastMsg = msgs[msgs.length - 1];
            return {
              ...p,
              lastMessageAt: lastMsg?.timestamp || p.lastMessageAt || 0,
            };
          })
          .sort((a, b) => b.lastMessageAt - a.lastMessageAt);

        localStorage.setItem("chatPartners", JSON.stringify(ordered));
        setChatPartners(ordered);
      }
    } catch (error) {
      console.error("❌ Error al obtener chats:", error);
      message.error("Error al cargar el historial de mensajes");
    }
  };

  const cargarMensajesGenerales = async () => {
    try {
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway/traerMensajesGenerales`
      );
      if (!res.ok) throw new Error("Error al traer mensajes generales");
      const data = await res.json();

      if (Array.isArray(data)) {
        setAllMessages((prev) => ({
          ...prev,
          grupo_general: data.map((msg) => ({
            sender_id: String(msg.sender_id || msg.idRemitente),
            sender_name: msg.nombreRemitente || "Desconocido",
            recipient_id: String(msg.recipient_id || msg.idDestinatario),
            message: msg.message || msg.mensaje || "",
            file: msg.fileAdjunto || msg.file || null,
            fileName: msg.fileName || null,
            isOwnMessage:
              String(msg.sender_id || msg.idRemitente) ===
              String(localStorage.getItem("idUsuario")),
            timestamp: new Date(msg.fechaEnvio).getTime() || Date.now(),
          })),
        }));
      } else {
        console.warn("⚠️ Mensajes generales no son array:", data);
      }
    } catch (err) {
      console.error("❌ Error al cargar mensajes generales:", err);
      message.error("No se pudieron cargar los mensajes generales");
    }
  };

  const handleSelectUser = async (user) => {
    if (!user || !user.id) {
      message.error("Usuario no válido.");
      return;
    }

    const isGrupo = user.id.startsWith("grupo_");
    const numericId = isGrupo ? user.id.replace("grupo_", "") : user.id;

    if (!isGrupo && isNaN(Number(numericId))) {
      console.warn("⚠️ Usuario seleccionado con id inválido:", numericId);
      message.error("Selección inválida. Por favor, elige otro usuario.");
      return;
    }

    setCurrentUser(user);
    setUnreadMessages((prev) => {
      const updated = { ...prev };
      delete updated[user.id];
      return updated;
    });

    setRecipientId(user.id.toString());
    localStorage.setItem("userChat", user.id);

    if (user.id === "grupo_general") {
      setModoGrupal(false);
      const userId = localStorage.getItem("idUsuario");

      try {
        // ✅ Verificar permiso para mensajes generales
        const resPermiso = await fetch(
          `${API_URL_GATEWAY}/gateway/puedeEnviarMensajeGeneral/${userId}`
        );
        const permisoData = await resPermiso.json();
        setPuedeEnviarMensajeGeneral(permisoData.puedeEnviar);
      } catch (err) {
        console.error(
          "❌ Error al verificar permiso de mensajes generales:",
          err
        );
        setPuedeEnviarMensajeGeneral(false);
      }

      try {
        await cargarMensajesGenerales(); // tu función que carga mensajes generales
      } catch (err) {
        console.error("❌ Error al cargar mensajes generales:", err);
        message.error("Error al cargar mensajes generales");
      }

      return;
    }
    if (isGrupo) {
      setModoGrupal(true);
      try {
        const res = await fetch(
          `${API_URL_GATEWAY}/gateway/traerChatsGrupo?room=${numericId}`
        );
        const data = await res.json();

        if (Array.isArray(data)) {
          const mensajes = data.map((msg) => ({
            sender_id: String(msg.sender_id || msg.idRemitente),
            recipient_id: String(msg.recipient_id || msg.idDestinatario),
            message: msg.message || msg.mensaje || "",
            file: msg.fileAdjunto || msg.file || null,
            fileName: msg.fileName || null,
            isOwnMessage:
              String(msg.sender_id || msg.idRemitente) ===
              String(localStorage.getItem("idUsuario")),
            timestamp: new Date(msg.fechaEnvio).getTime() || Date.now(),
          }));

          setAllMessages((prev) => ({
            ...prev,
            [user.id]: mensajes,
          }));
        }
      } catch (err) {
        console.error("❌ Error al traer mensajes del grupo:", err);
        message.error("Error al cargar mensajes del grupo");
      }
      return;
    }

    setModoGrupal(false);
    try {
      const tuId = localStorage.getItem("idUsuario");
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway/getChats?user_id=${tuId}&recipient_id=${numericId}`
      );
      const data = await res.json();

      if (Array.isArray(data)) {
        setAllMessages((prev) => ({
          ...prev,
          [user.id]: data.map((msg) => ({
            sender_id: String(msg.sender_id || msg.idRemitente),
            recipient_id: String(msg.recipient_id || msg.idDestinatario),
            message: msg.message || msg.mensaje || "",
            file: msg.fileAdjunto || msg.file || null,
            fileName: msg.fileName || null,
            isOwnMessage:
              String(msg.sender_id || msg.idRemitente) ===
              String(effectiveUserId),
            timestamp: msg.timestamp || Date.now(),
          })),
        }));
      }
    } catch (err) {
      console.error("Error al traer mensajes:", err);
      message.error("Error al cargar mensajes");
    }
  };

  useEffect(() => {
    setChatSearchTerm(""); // limpia el input al cambiar de usuario
    setHighlightedMessageIndex(null); // opcional: elimina cualquier resaltado anterior
  }, [currentUser]);

  const handleSendMessage = async () => {
    if (!currentUser || (!messageText.trim() && !attachedFile)) return;

    const tempId = uuidv4();
    const userId = localStorage.getItem("idUsuario");

    const newMsg = {
      tempId,
      sender_id: userId,
      message: messageText.trim() || "{adjunto}",
      file: attachedFile?.base64 || null,
      fileName: attachedFile?.name || null,
      isOwnMessage: true,
      timestamp: Date.now(),
    };

    if (currentUser.id === "grupo_general") {
      // ➡️ Mensaje general
      const payload = {
        sender_id: userId,
        message: newMsg.message,
        fileName: newMsg.fileName,
        fileAdjunto: newMsg.file,
      };

      try {
        const res = await fetch(
          `${API_URL_GATEWAY}/gateway/guardarMensajeGeneral`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          }
        );

        if (!res.ok) {
          message.error("No se pudo enviar el mensaje general");
        } else {
          // Agregar el mensaje localmente para mostrarlo sin recargar
          setAllMessages((prev) => ({
            ...prev,
            grupo_general: [...(prev["grupo_general"] || []), newMsg],
          }));
        }
      } catch (error) {
        console.error("❌ Error al enviar mensaje general:", error);
        message.error("Error al enviar mensaje general");
      }
    } else if (modoGrupal && currentUser.campanas?.length > 0) {
      // ➡️ Mensaje grupal
      const campanaId = currentUser.campanas[0].toString();
      const messageToSend = {
        ...newMsg,
        room: campanaId,
      };

      if (socket && socket.connected) {
        socket.emit("group_message", messageToSend, (ack) => {
          if (ack && ack.received) {
            setMessageStatus((prev) => ({
              ...prev,
              [messageToSend.tempId]: "delivered",
            }));
          }
        });
      } else {
        message.warning("Reconectando al servidor de chat...");
        socket = initSocket();
        socket.once("connect", () => {
          socket.emit("group_message", messageToSend);
        });
      }

      const groupKey = `grupo_${campanaId}`;
      setAllMessages((prev) => ({
        ...prev,
        [groupKey]: [...(prev[groupKey] || []), messageToSend],
      }));
      setRecipientId(groupKey);
    } else {
      // ➡️ Mensaje privado
      const privateMsg = {
        ...newMsg,
        recipient_id: currentUser.id.toString(),
        room: undefined,
      };

      if (socket && socket.connected) {
        socket.emit("private_message", privateMsg, (ack) => {
          if (ack && ack.received) {
            setMessageStatus((prev) => ({
              ...prev,
              [privateMsg.tempId]: "delivered",
            }));
          } else {
            console.warn("❌ El servidor NO confirmó el mensaje");
          }
        });
      } else {
        message.warning("Reconectando al servidor de chat...");
        socket = initSocket();
        socket.once("connect", () => {
          socket.emit("private_message", privateMsg, (ack) => {
            if (ack && ack.received) {
              setMessageStatus((prev) => ({
                ...prev,
                [privateMsg.tempId]: "delivered",
              }));
            } else {
              console.warn("❌ No confirmado tras reconexión");
            }
          });
        });
      }

      await guardarMensaje({
        ...privateMsg,
        sender_id: userId,
        recipient_id: currentUser.id.toString(),
      });

      setAllMessages((prev) => ({
        ...prev,
        [currentUser.id]: [...(prev[currentUser.id] || []), privateMsg],
      }));
    }

    setMessageText("");
    setAttachedFile(null);
  };

  const handleAttachFile = (event) => {
    const file = event.target.files[0];
    if (file && file.size > 100 * 1024 * 1024) {
      message.error("El archivo es demasiado grande. Máximo 100MB");
      return;
    }

    if (file && currentUser) {
      const reader = new FileReader();
      reader.onload = async () => {
        const fileData = reader.result;
        const userId = localStorage.getItem("idUsuario");

        const fileMessage = {
          sender_id: userId,
          message: "{adjunto}",
          file: fileData,
          fileName: file.name,
          isOwnMessage: true,
          timestamp: Date.now(),
        };

        if (currentUser.id === "grupo_general") {
          // ➡️ Mensaje general con adjunto
          const payload = {
            sender_id: userId,
            message: fileMessage.message,
            fileName: fileMessage.fileName,
            fileAdjunto: fileMessage.file,
          };

          try {
            const res = await fetch(
              `${API_URL_GATEWAY}/gateway/guardarMensajeGeneral`,
              {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
              }
            );

            if (!res.ok) {
              message.error("No se pudo enviar el archivo al grupo general");
            } else {
              setAllMessages((prev) => ({
                ...prev,
                grupo_general: [...(prev["grupo_general"] || []), fileMessage],
              }));
            }
          } catch (error) {
            console.error("❌ Error al enviar archivo general:", error);
            message.error("Error al enviar archivo al grupo general");
          }
        } else if (modoGrupal && currentUser.campanas?.length > 0) {
          const campanaId = currentUser.campanas[0].toString();
          const groupFileMessage = { ...fileMessage, room: campanaId };

          if (socket && socket.connected) {
            socket.emit("group_message", groupFileMessage);
          } else {
            message.warning("Reconectando al servidor de chat...");
            socket = initSocket();
            socket.once("connect", () => {
              socket.emit("group_message", groupFileMessage);
            });
          }

          const groupKey = `grupo_${campanaId}`;
          setAllMessages((prev) => ({
            ...prev,
            [groupKey]: [...(prev[groupKey] || []), groupFileMessage],
          }));
        } else {
          const privateFileMessage = {
            ...fileMessage,
            recipient_id: currentUser.id.toString(),
          };

          if (socket && socket.connected) {
            socket.emit("private_message", privateFileMessage);
          } else {
            message.warning("Reconectando al servidor de chat...");
            socket = initSocket();
            socket.once("connect", () => {
              socket.emit("private_message", privateFileMessage);
            });
          }

          await guardarMensaje(privateFileMessage);

          setAllMessages((prev) => ({
            ...prev,
            [currentUser.id]: [
              ...(prev[currentUser.id] || []),
              privateFileMessage,
            ],
          }));
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handleAttachDroppedFile = (file) => {
    if (file.size > 100 * 1024 * 1024) {
      message.error("El archivo es demasiado grande. Máximo 100MB");
      return;
    }

    if (currentUser) {
      const reader = new FileReader();
      reader.onload = async () => {
        const fileData = reader.result;
        const tempId = uuidv4();
        const userId = localStorage.getItem("idUsuario");

        const baseMsg = {
          tempId,
          sender_id: userId,
          message: "{adjunto}",
          file: fileData,
          fileName: file.name,
          isOwnMessage: true,
          timestamp: Date.now(),
        };

        if (currentUser.id === "grupo_general") {
          // ➡️ Mensaje general con archivo arrastrado
          const payload = {
            sender_id: userId,
            message: baseMsg.message,
            fileName: baseMsg.fileName,
            fileAdjunto: baseMsg.file,
          };

          try {
            const res = await fetch(
              `${API_URL_GATEWAY}/gateway/guardarMensajeGeneral`,
              {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
              }
            );

            if (!res.ok) {
              message.error("No se pudo enviar el archivo al grupo general");
            } else {
              setAllMessages((prev) => ({
                ...prev,
                grupo_general: [...(prev["grupo_general"] || []), baseMsg],
              }));
            }
          } catch (error) {
            console.error("❌ Error al enviar archivo general:", error);
            message.error("Error al enviar archivo al grupo general");
          }
        } else if (modoGrupal && currentUser.campanas?.length > 0) {
          const campanaId = currentUser.campanas[0].toString();
          const fileMessage = { ...baseMsg, room: campanaId };

          if (socket && socket.connected) {
            socket.emit("group_message", fileMessage);
          } else {
            message.warning("Reconectando al servidor de chat...");
            socket = initSocket();
            socket.once("connect", () =>
              socket.emit("group_message", fileMessage)
            );
          }

          const groupKey = `grupo_${campanaId}`;
          setAllMessages((prev) => ({
            ...prev,
            [groupKey]: [...(prev[groupKey] || []), fileMessage],
          }));
        } else {
          const privateMessage = {
            ...baseMsg,
            recipient_id: currentUser.id.toString(),
          };

          if (socket && socket.connected) {
            socket.emit("private_message", privateMessage);
          } else {
            message.warning("Reconectando al servidor de chat...");
            socket = initSocket();
            socket.once("connect", () =>
              socket.emit("private_message", privateMessage)
            );
          }

          await guardarMensaje(privateMessage);

          setAllMessages((prev) => ({
            ...prev,
            [currentUser.id]: [...(prev[currentUser.id] || []), privateMessage],
          }));
        }
      };

      reader.readAsDataURL(file);
    }
  };

  const buscarPersonas = async (texto = "") => {
    try {
      const query = texto?.trim() ?? "";

      const response = await fetch(
        `${API_URL_GATEWAY}/gateway/buscarPersonas?query=${encodeURIComponent(
          query
        )}&user_id=${localStorage.getItem("idUsuario")}`
      );

      if (!response.ok) {
        const errorText = await response.text();
        console.error("❌ Error al buscar personas:", errorText);
        message.error("Error al buscar personas");
        return;
      }

      const result = await response.json();

      if (Array.isArray(result)) {
        const rolActual = parseInt(localStorage.getItem("idRol"));

        const nuevos = result
          .filter((u) => {
            const esValido = !isNaN(Number(u.idUsuarioApp));
            const esOtroAsesor =
              rolActual === 14 && u.rol?.toLowerCase() === "asesor";
            return esValido && !esOtroAsesor;
          })
          .map((u) => ({
            id: u.idUsuarioApp.toString(),
            name: u.nombre,
            role: u.rol,
          }));

        setChatPartners((prev) => {
          const idsPrevios = new Set(prev.map((p) => p.id));
          const nuevosSinRepetidos = nuevos.filter(
            (n) => !idsPrevios.has(n.id)
          );
          return [...prev, ...nuevosSinRepetidos].sort(
            (a, b) => (b.lastMessageAt || 0) - (a.lastMessageAt || 0)
          );
        });
      } else {
        console.warn("⚠️ Resultado inesperado:", result);
        message.warning("No se pudo interpretar la respuesta del servidor");
      }
    } catch (error) {
      console.error("❌ Error buscando personas:", error);
      message.error("Error inesperado al buscar usuarios");
    }
  };

  const handleSearchMessages = (term) => {
    if (!currentUser || !term.trim()) return;

    const mensajes = allMessages[currentUser.id] || [];
    const index = mensajes.findIndex((m) =>
      m.message?.toLowerCase().includes(term.toLowerCase())
    );

    if (index >= 0) {
      setHighlightedMessageIndex(index);
      messageRefs.current[index]?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
      setTimeout(() => setHighlightedMessageIndex(null), 2000);
    } else {
      message.info("No se encontraron resultados");
    }
  };

  const handleEmojiClick = (emojiData) => {
    setMessageText((prev) => prev + emojiData.emoji);
  };

  useEffect(() => {
    const withTimestamps = chatPartners.map((p) => {
      const msgs = allMessages[p.id] || [];
      const last = msgs[msgs.length - 1];
      return {
        ...p,
        lastMessageAt: last?.timestamp || p.lastMessageAt || 0,
      };
    });

    const sorted = [...withTimestamps].sort(
      (a, b) => b.lastMessageAt - a.lastMessageAt
    );
    localStorage.setItem("chatPartners", JSON.stringify(sorted));
    setChatPartners(sorted);
  }, [allMessages]);

  // Comprobar periódicamente la conexión del socket
  useEffect(() => {
    const checkSocket = setInterval(() => {
      if (!socket || !socket.connected) {
        socket = initSocket();
        setupSocketListeners();
      }
    }, 10000); // Comprobar cada 10 segundos

    return () => clearInterval(checkSocket);
  }, []);

  const clasificarMensaje = (mensaje, fileName) => {
    if (mensaje !== "{adjunto}") return mensaje;

    if (!fileName) return "Archivo adjunto";

    const ext = fileName.toLowerCase().split(".").pop();
    if (["jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff"].includes(ext)) {
      return "📷 Imagen";
    }
    return "📎 Documento";
  };

  const mostrarPopupNotificacion = (
    mensaje,
    remitente,
    remitenteId,
    fileName = null
  ) => {
    const descripcion = clasificarMensaje(mensaje, fileName);

    notification.open({
      message: (
        <span>
          <span style={{ fontWeight: "bold" }}>💬 {remitente}</span> te envió un
          mensaje
        </span>
      ),
      description:
        descripcion.length > 80
          ? descripcion.slice(0, 80) + "..."
          : descripcion,
      placement: "bottomRight",
      duration: 8,
      style: {
        backgroundColor: "#e6f7ff",
        borderRadius: "8px",
        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
        cursor: "pointer",
      },
      onClick: () => {
        const user = chatPartners.find((p) => p.id === remitenteId);
        if (user) {
          handleSelectUser(user);
        } else {
          console.warn(
            "Usuario no encontrado en la lista de chatPartners:",
            remitenteId
          );
        }
      },
    });
  };
  const obtenerMiembrosGrupo = async (idCampana) => {
    try {
      const userId = localStorage.getItem("idUsuario");
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway/usuariosGrupo?user_id=${userId}&idCampana=${idCampana}`
      );
      if (!res.ok) throw new Error("Error al obtener miembros");
      const data = await res.json();
      return data;
    } catch (err) {
      console.error("❌ Error al cargar miembros del grupo:", err);
      return [];
    }
  };

  return (
    <Layout className="chat-container">
      <Sider
        width={320} // antes: 280
        className="sidebarChat"
        style={{
          background: "#fff",
          overflow: "auto",
          display: "flex",
          flexDirection: "column",
          height: "100%", // antes: "86vh"
        }}
      >
        <div style={{ padding: "8px" }}>
          <Input.Search
            placeholder="Buscar usuario..."
            onChange={(e) => {
              const val = e.target.value;
              setSearchTerm(val);
              buscarPersonas(val);
            }}
            className="chat-search"
          />
        </div>

        <div className="chat-list">
          <List
            itemLayout="horizontal"
            dataSource={
              searchTerm.trim()
                ? chatPartners.filter((u) =>
                    u.name.toLowerCase().includes(searchTerm.toLowerCase())
                  )
                : chatPartners
            }
            renderItem={(user) => (
              <List.Item
                onClick={() => handleSelectUser(user)}
                className={currentUser?.id === user.id ? "active" : ""}
                style={{
                  cursor: "pointer",
                  position: "relative",
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  marginBottom: "4px",
                }}
              >
                <Avatar
                  size={44}
                  style={{
                    backgroundColor: user.id.startsWith("grupo_")
                      ? "#667eea"
                      : user.id === "grupo_general"
                      ? "#4fd1c7"
                      : "#764ba2",
                    fontWeight: "600",
                    fontSize: "16px",
                  }}
                >
                  {user.id === "grupo_general"
                    ? "🎉"
                    : user.id.startsWith("grupo_")
                    ? "👥"
                    : user.name[0]?.toUpperCase()}
                </Avatar>

                <div className="chat-user-block" style={{ flex: 1 }}>
                  <div className="nombre">{user.name}</div>
                  <div className="rol">{user.role}</div>
                </div>

                {unreadMessages[user.id] > 0 && (
                  <div className="unread-badge">
                    {unreadMessages[user.id] > 99
                      ? "99+"
                      : unreadMessages[user.id]}
                  </div>
                )}
              </List.Item>
            )}
          />
        </div>
      </Sider>

      <Layout className="chat-content">
        {currentUser ? (
          <Header
            className="chat-header"
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "16px",
                maxWidth: "60%",
                overflow: "hidden",
              }}
            >
              <Title
                level={4}
                className="username"
                style={{
                  margin: 0,
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {currentUser.name}
              </Title>

              <ConnectionStatus isConnected={socket?.connected || false} />

              {userRole === 13 && currentUser.id.startsWith("grupo_") && (
                <Tooltip title="Ver miembros del grupo">
                  <Button
                    type="text"
                    icon={<TeamOutlined />}
                    onClick={async () => {
                      const idCampana = currentUser.campanas?.[0];
                      if (!idCampana) return;
                      const miembros = await obtenerMiembrosGrupo(idCampana);
                      setMiembrosGrupo(miembros);
                      setModalMiembrosVisible(true);
                    }}
                  />
                </Tooltip>
              )}
            </div>

            <Input.Search
              placeholder="Buscar en el chat"
              value={chatSearchTerm}
              onChange={(e) => setChatSearchTerm(e.target.value)}
              onSearch={(value) => {
                handleSearchMessages(value);
                setChatSearchTerm(""); // limpia después de buscar
              }}
              style={{ width: 200 }}
              enterButton={<SearchOutlined />}
            />
          </Header>
        ) : (
          <Header
            style={{ background: "#fff", padding: "24px", textAlign: "center" }}
          >
            <Title level={3}>Selecciona un usuario para chatear</Title>
          </Header>
        )}

        <Content className="messages">
          {currentUser && (
            <Card
              bodyStyle={{
                padding: 0,
                display: "flex",
                flexDirection: "column",
                height: "100%", // antes: "70vh"
                overflow: "hidden",
                borderRadius: "16px",
                background: "transparent",
              }}
              style={{
                border: "none",
                borderRadius: "16px",
                background: "transparent",
                boxShadow: "none",
              }}
            >
              <div
                className="messages-container"
                onDragOver={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                }}
                onDrop={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  const file = e.dataTransfer.files[0];
                  if (file) handleAttachDroppedFile(file);
                }}
              >
                {(() => {
                  const mensajes = allMessages[currentUser.id] || [];
                  let lastDate = null;

                  return mensajes.map((msg, idx) => {
                    const msgDate = dayjs(msg.timestamp).format("YYYY-MM-DD");
                    const isNewDate = msgDate !== lastDate;
                    lastDate = msgDate;

                    return (
                      <React.Fragment key={idx}>
                        {isNewDate && (
                          <div className="date-separator">
                            <span>
                              {dayjs(msg.timestamp).format(
                                "dddd, D [de] MMMM [de] YYYY"
                              )}
                            </span>
                          </div>
                        )}

                        <div
                          ref={(el) => (messageRefs.current[idx] = el)}
                          className={`message-bubble ${
                            msg.isOwnMessage ? "sent" : "received"
                          } ${
                            highlightedMessageIndex === idx ? "highlighted" : ""
                          }`}
                        >
                          {currentUser.id.startsWith("grupo_") &&
                            !msg.isOwnMessage && (
                              <div className="group-sender">
                                {msg.sender_name ||
                                  usuariosMapRef.current[msg.sender_id] ||
                                  "Desconocido"}
                              </div>
                            )}

                          {msg.message !== "{adjunto}" ? (
                            // Si el mensaje no es un adjunto
                            msg.fileName?.toLowerCase().endsWith(".mp4") ? (
                              // Si el mensaje es un mp4 (video), muestra video embebido
                              <video
                                controls
                                width="250"
                                style={{ borderRadius: "12px" }}
                              >
                                <source src={msg.message} type="video/mp4" />
                                Tu navegador no soporta videos.
                              </video>
                            ) : (
                              // Sino, muestra el texto normal
                              <span>{msg.message}</span>
                            )
                          ) : msg.file ? (
                            <div className="file-attachment">
                              {msg.fileName
                                ?.toLowerCase()
                                .match(/\.(jpeg|jpg|gif|png)$/i) ? (
                                // Si es imagen, muestra la imagen
                                <img
                                  src={
                                    msg.file?.startsWith("data:")
                                      ? msg.file
                                      : `data:image/png;base64,${msg.file}`
                                  }
                                  alt={msg.fileName}
                                  style={{
                                    maxWidth: "200px",
                                    maxHeight: "200px",
                                    borderRadius: "12px",
                                    marginBottom: "5px",
                                    cursor: "pointer",
                                  }}
                                  onClick={() => {
                                    setImagenEnModal(
                                      msg.file?.startsWith("data:")
                                        ? msg.file
                                        : `data:image/*;base64,${msg.file}`
                                    );
                                    setNombreImagenModal(
                                      msg.fileName || "imagen"
                                    );
                                  }}
                                />
                              ) : msg.fileName
                                  ?.toLowerCase()
                                  .endsWith(".mp4") ? (
                                // Si es video como adjunto, muestra el reproductor
                                <video
                                  controls
                                  width="250"
                                  style={{ borderRadius: "12px" }}
                                >
                                  <source
                                    src={
                                      msg.file?.startsWith("data:")
                                        ? msg.file
                                        : `data:video/mp4;base64,${msg.file}`
                                    }
                                    type="video/mp4"
                                  />
                                  Tu navegador no soporta videos.
                                </video>
                              ) : (
                                // Sino, muestra como adjunto descargable
                                <a
                                  href={
                                    msg.file?.startsWith("data:")
                                      ? msg.file
                                      : `data:application/octet-stream;base64,${msg.file}`
                                  }
                                  download={msg.fileName}
                                  className="file-download-link"
                                >
                                  <div className="file-icon">📎</div>
                                  <div className="file-name">
                                    {msg.fileName}
                                  </div>
                                </a>
                              )}
                            </div>
                          ) : (
                            <span>Archivo no disponible</span>
                          )}

                          <div className="message-time">
                            {dayjs(msg.timestamp).format("h:mm A")}
                          </div>
                        </div>
                      </React.Fragment>
                    );
                  });
                })()}

                <div ref={messagesEndRef} />
              </div>
              {(currentUser.id !== "grupo_general" ||
                puedeEnviarMensajeGeneral) && (
                <div className="chat-input-container">
                  {attachedFile && (
                    <div className="attached-file-preview">
                      📎 {attachedFile.name}
                      <Button
                        type="link"
                        size="small"
                        onClick={() => setAttachedFile(null)}
                      >
                        ✕
                      </Button>
                    </div>
                  )}

                  <div className="chat-input-row">
                    <Input.TextArea
                      value={messageText}
                      onChange={(e) => setMessageText(e.target.value)}
                      placeholder="Escribe un mensaje..."
                      autoSize={{ minRows: 1, maxRows: 6 }}
                      className="chat-input-textarea"
                      onPressEnter={(e) => {
                        if (!e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                        }
                      }}
                    />

                    <div className="chat-input-actions">
                      <Tooltip title="Adjuntar archivo">
                        <Button
                          type="text"
                          icon={<PaperClipOutlined />}
                          onClick={() => fileInputRef.current.click()}
                        />
                      </Tooltip>

                      <input
                        type="file"
                        ref={fileInputRef}
                        style={{ display: "none" }}
                        onChange={handleAttachFile}
                      />

                      <Tooltip title="Emojis">
                        <Button
                          type="text"
                          icon={<SmileOutlined />}
                          onClick={() => setShowEmojiPicker((prev) => !prev)}
                        />
                      </Tooltip>

                      <Tooltip title="Enviar mensaje">
                        <Button
                          type="primary"
                          shape="circle"
                          icon={<SendOutlined />}
                          onClick={handleSendMessage}
                          disabled={!messageText.trim() && !attachedFile}
                        />
                      </Tooltip>
                    </div>
                  </div>

                  {showEmojiPicker && (
                    <div
                      className="emoji-picker-container"
                      ref={emojiPickerRef}
                    >
                      <EmojiPicker onEmojiClick={handleEmojiClick} />
                    </div>
                  )}
                </div>
              )}
            </Card>
          )}
        </Content>
      </Layout>

      <Modal
        open={!!imagenEnModal}
        footer={null}
        onCancel={() => setImagenEnModal(null)}
        centered
        width="90%"
        style={{ maxWidth: "800px" }}
        bodyStyle={{
          textAlign: "center",
          padding: 0,
          borderRadius: "16px",
          overflow: "hidden",
        }}
      >
        <div style={{ position: "relative" }}>
          <img
            src={imagenEnModal}
            alt={nombreImagenModal}
            style={{
              width: "100%",
              maxHeight: "80vh",
              objectFit: "contain",
              borderRadius: "16px 16px 0 0",
            }}
          />
          <div
            style={{
              padding: "16px",
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              color: "white",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span style={{ fontWeight: "500" }}>{nombreImagenModal}</span>
            <Button
              type="primary"
              ghost
              href={imagenEnModal}
              download={nombreImagenModal}
              style={{
                borderColor: "white",
                color: "white",
              }}
            >
              📥 Descargar
            </Button>
          </div>
        </div>
      </Modal>

      <Modal
        open={searchModalVisible}
        onCancel={() => setSearchModalVisible(false)}
        footer={null}
        title="Resultados de búsqueda"
      >
        <List
          dataSource={searchResults}
          renderItem={(item) => (
            <List.Item>
              <Text>
                {item.message} ({dayjs().format("HH:mm")})
              </Text>
            </List.Item>
          )}
        />
      </Modal>
      <Modal
        title={
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
              fontSize: "18px",
              fontWeight: "600",
            }}
          >
            <TeamOutlined style={{ color: "#667eea" }} />
            Miembros del grupo
          </div>
        }
        open={modalMiembrosVisible}
        footer={null}
        onCancel={() => setModalMiembrosVisible(false)}
        width={500}
        bodyStyle={{ padding: "16px 24px" }}
      >
        <List
          itemLayout="horizontal"
          dataSource={miembrosGrupo}
          renderItem={(item) => (
            <List.Item
              style={{
                padding: "12px 0",
                borderBottom: "1px solid #f0f0f0",
              }}
            >
              <List.Item.Meta
                avatar={
                  <Avatar
                    style={{
                      background:
                        "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                      fontWeight: "600",
                    }}
                  >
                    {item.nombre?.[0]?.toUpperCase()}
                  </Avatar>
                }
                title={<span style={{ fontWeight: "500" }}>{item.nombre}</span>}
                description={<span style={{ color: "#666" }}>{item.rol}</span>}
              />
            </List.Item>
          )}
        />
      </Modal>
    </Layout>
  );
};

export default ChatApp;
