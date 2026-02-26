import React, { useEffect, useState, useMemo } from "react";
import {
  Table,
  Drawer,
  Tag,
  Descriptions,
  Layout,
  Typography,
  Space,
  Select,
  Input,
  Button,
  message,
  Spin,
  Divider,
  Badge,
  List,
  Card,
  Row,
  Col,
  Statistic,
  Modal,
  DatePicker,
} from "antd";

import {
  UserOutlined,
  MessageOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  PhoneOutlined,
  MailOutlined,
  WhatsAppOutlined,
  BarChartOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  DownloadOutlined,
} from "@ant-design/icons";

import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import axios from "axios";
import dayjs from "dayjs";
import { API_URL_GATEWAY_CONNECT } from "../../config";

const { Content } = Layout;
const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

const resultadoColor = (resultado) => {
  if (!resultado) return "default";
  const r = resultado.toUpperCase();
  if (r === "ACUERDO_PAGO") return "green";
  if (r === "RECHAZO") return "red";
  if (r === "EN_CONVERSACION") return "blue";
  if (r === "SIN_MENSAJES") return "default";
  return "processing";
};

const CrmConversaciones = () => {
  const [conversaciones, setConversaciones] = useState([]);
  const [loading, setLoading] = useState(false);

  // filtros
  const [fUserId, setFUserId] = useState("");
  const [fCanal, setFCanal] = useState("");
  const [fIsActive, setFIsActive] = useState("");
  const [fCampaignId, setFCampaignId] = useState("");

  // detalle
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [detalle, setDetalle] = useState(null);
  const [loadingDetalle, setLoadingDetalle] = useState(false);

  // Control de visualización del tablero
  const [mostrarTablero, setMostrarTablero] = useState(false);

  // Modal para ver detalle de datos del gráfico
  const [modalVisible, setModalVisible] = useState(false);
  const [modalData, setModalData] = useState({ title: "", conversaciones: [] });

  // Modal de exportación
  const [modalExportVisible, setModalExportVisible] = useState(false);

  // exportar
  const [fDateRange, setFDateRange] = useState(null);
  const [fIntencion, setFIntencion] = useState("");
  const [fTipificacion, setFTipificacion] = useState("");

  //pais
  const [fPais, setFPais] = useState("");

  const ORIGEN_POR_CAMPANA = {
  NPL: "57 3203624083",
  PERU: "51 928039591",
  COLTE_DENTIX: "57 3202478979",
};

const exportarExcel = async () => {
  try {
    const params = new URLSearchParams();

    if (fCanal) params.append("canal", fCanal);

    const camp = fCampaignId.trim();
    if (camp !== "") params.append("campaign_id", camp);

    const tip = fTipificacion.trim();
    if (tip !== "") params.append("intencion", tip);

    if (fDateRange && fDateRange.length === 2) {
      params.append("fecha_inicio", fDateRange[0].format("YYYY-MM-DD"));
      params.append("fecha_fin", fDateRange[1].format("YYYY-MM-DD"));
    }

    if (fPais) params.append("pais", fPais);

    const url = `${API_URL_GATEWAY_CONNECT}/gateway/crm/conversaciones/export?${params.toString()}`;

    const resp = await axios.get(url, { responseType: "blob" });

    // nombre desde header (si viene)
    const cd = resp.headers["content-disposition"] || "";
    const match = cd.match(/filename="?([^"]+)"?/);
    const filename = match?.[1] || "crm_export.xlsx";

    const blobUrl = window.URL.createObjectURL(new Blob([resp.data]));
    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(blobUrl);

    setModalExportVisible(false);
    message.success("Excel descargado");
  } catch (err) {
    console.error(err);
    message.error("No se pudo exportar. Revisa el backend (posible 401/500) y consola.");
  }
};


  const abrirModalExportar = () => {
    setModalExportVisible(true);
  };

  const limpiarFiltrosExportar = () => {
    setFDateRange(null);
    setFIntencion("");
    setFTipificacion("");
    setFCanal("");
    setFIsActive("");
    setFCampaignId("");
  };

  const cargarConversaciones = async () => {
    try {
      setLoading(true);
      const params = {};
      if (fUserId.trim()) params.user_id = fUserId.trim();
      if (fCanal) params.canal = fCanal;
      if (fIsActive !== "") params.is_active = fIsActive === "true";

      const camp = fCampaignId.trim();
      if (camp !== "") {
        params.campaign_id = camp; // string, sin Number()
      }

      const resp = await axios.get(
        `${API_URL_GATEWAY_CONNECT}/gateway/crm/conversaciones`,
        { params }
      );
      setConversaciones(resp.data || []);
    } catch (err) {
      console.error(err);
      message.error("Error al cargar conversaciones");
    } finally {
      setLoading(false);
    }
  };

  const cargarDetalle = async (conversacion_id) => {
    try {
      setLoadingDetalle(true);
      const resp = await axios.get(
        `${API_URL_GATEWAY_CONNECT}/gateway/crm/conversaciones/detalle/${conversacion_id}`
      );
      setDetalle(resp.data);
      setDrawerOpen(true);
    } catch (err) {
      console.error(err);
      message.error("Error al cargar detalle de la conversación");
    } finally {
      setLoadingDetalle(false);
    }
  };

  useEffect(() => {
    cargarConversaciones();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  //pais
const conversacionesConPais = useMemo(() => {
  return conversaciones.map((c) => {
    if (!c.user_id)
      return { ...c, pais: "Desconocido", origen: "N/D" };

    const camp = String(c.campaign_id)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toUpperCase();

    let pais = "Desconocido";
    if (camp.includes("PERU")) pais = "Perú";
    else if (camp.includes("NPL")) pais = "Colombia";
    else if (camp.includes("COLTE DENTIX")) pais = "colte - dentix";


    let origen = "N/D";
    if (camp.includes("NPL")) origen = ORIGEN_POR_CAMPANA.NPL;
    else if (camp.includes("PERU")) origen = ORIGEN_POR_CAMPANA.PERU;
    else if (camp.includes("COLTE-DENTIX")) origen = ORIGEN_POR_CAMPANA.COLTE_DENTIX;


    return { ...c, pais, origen };
  });
}, [conversaciones]);


  const conversacionesPorPais = useMemo(() => {
    return conversacionesConPais.reduce((acc, c) => {
      acc[c.pais] = (acc[c.pais] || 0) + 1;
      return acc;
    }, {});
  }, [conversacionesConPais]);

  const conversacionesFiltradas = useMemo(() => {
    return conversacionesConPais.filter((c) => {
      if (fPais && c.pais !== fPais) return false;
      return true;
    });
  }, [conversacionesConPais, fPais]);

  // ============================================
  // Cálculo de KPIs para el tablero
  // ============================================
  const kpis = useMemo(() => {
    const total = conversacionesFiltradas.length;
    const activas = conversacionesFiltradas.filter((c) => c.is_active).length;
    const cerradas = total - activas;

    // Por canal
    const porCanal = conversacionesFiltradas.reduce((acc, c) => {
      acc[c.canal] = (acc[c.canal] || 0) + 1;
      return acc;
    }, {});

    // Por estado
    const porEstado = conversacionesFiltradas.reduce((acc, c) => {
      const estado = c.current_state || "inicio";
      acc[estado] = (acc[estado] || 0) + 1;
      return acc;
    }, {});

    // Por campaña
    const porCampana = conversacionesFiltradas.reduce((acc, c) => {
      if (c.campaign_id) {
        acc[c.campaign_id] = (acc[c.campaign_id] || 0) + 1;
      }
      return acc;
    }, {});

    // Conversaciones por usuario único
    const usuariosUnicos = new Set(
      conversacionesFiltradas.map((c) => c.user_id)
    ).size;

    return {
      total,
      activas,
      cerradas,
      porCanal,
      porEstado,
      porCampana,
      usuariosUnicos,
    };
  }, [conversacionesFiltradas]);

  // Obtener valores únicos para filtros
  const uniqueCampaigns = [
    ...new Set(
      conversacionesFiltradas.map((c) => c.campaign_id).filter(Boolean)
    ),
  ].sort((a, b) => a - b);
  const uniqueStates = [
    ...new Set(
      conversacionesFiltradas.map((c) => c.current_state).filter(Boolean)
    ),
  ];
  const uniqueCanales = [
    ...new Set(conversacionesFiltradas.map((c) => c.canal).filter(Boolean)),
  ];
  const uniqueUsers = [
    ...new Set(conversacionesFiltradas.map((c) => c.user_id).filter(Boolean)),
  ].sort();

  const columns = [
    {
      title: "Origen",
      dataIndex: "origen",
      width: 140,
      render: (v) => <Tag color="purple">{v}</Tag>,
    },

    {
      title: "Destinatario",
      dataIndex: "user_id",
      filters: uniqueUsers.map((u) => ({ text: u, value: u })),
      onFilter: (value, record) => record.user_id === value,
      filterSearch: true,
    },
    {
      title: "Campaña",
      dataIndex: "campaign_id",
      width: 120,
      filters: uniqueCampaigns.map((c) => ({ text: c, value: c })),
      onFilter: (value, record) => record.campaign_id === value,
    },
    {
      title: "Tipificación Actual",
      dataIndex: "current_state",
      width: 130,
      render: (state) => <Tag>{state || "inicio"}</Tag>,
      filters: uniqueStates.map((s) => ({
        text: s || "inicio",
        value: s || "inicio",
      })),
      onFilter: (value, record) => (record.current_state || "inicio") === value,
    },
    {
      title: "Canal",
      dataIndex: "canal",
      width: 110,
      render: (canal) => <Tag color="geekblue">{canal}</Tag>,
      filters: uniqueCanales.map((c) => ({ text: c, value: c })),
      onFilter: (value, record) => record.canal === value,
    },
    {
      title: "Activa",
      dataIndex: "is_active",
      width: 90,
      render: (v) =>
        v ? (
          <Badge status="processing" text="Activa" />
        ) : (
          <Badge status="default" text="Cerrada" />
        ),
      filters: [
        { text: "Activa", value: true },
        { text: "Cerrada", value: false },
      ],
      onFilter: (value, record) => record.is_active === value,
    },
    {
      title: "Creada",
      dataIndex: "created_at",
      width: 180,
      render: (d) => (d ? dayjs(d).format("YYYY-MM-DD HH:mm") : ""),
      sorter: (a, b) => {
        const dateA = a.created_at ? new Date(a.created_at).getTime() : 0;
        const dateB = b.created_at ? new Date(b.created_at).getTime() : 0;
        return dateA - dateB;
      },
    },
    {
      title: "Actualizada",
      dataIndex: "updated_at",
      width: 180,
      render: (d) => (d ? dayjs(d).format("YYYY-MM-DD HH:mm") : ""),
      sorter: (a, b) => {
        const dateA = a.updated_at ? new Date(a.updated_at).getTime() : 0;
        const dateB = b.updated_at ? new Date(b.updated_at).getTime() : 0;
        return dateA - dateB;
      },
    },
    {
      title: "País",
      dataIndex: "pais",
      width: 100,
      render: (pais) => <Tag>{pais}</Tag>,
      filters: [
        { text: "Colombia", value: "Colombia" },
        { text: "Perú", value: "Perú" },
        { text: "Desconocido", value: "Desconocido" },
      ],
      onFilter: (value, record) => record.pais === value,
    },
  ];

  const onRowClick = (record) => {
    cargarDetalle(record.id);
  };

  // --------------------------------------------
  // Render mensajes dentro del drawer
  // --------------------------------------------
  const renderMensajes = () => {
    if (!detalle?.mensajes?.length) {
      return (
        <Text type="secondary">No hay mensajes en esta conversación.</Text>
      );
    }

    return (
      <List
        size="small"
        itemLayout="vertical"
        dataSource={detalle.mensajes}
        renderItem={(m) => {
          const esCliente =
            (m.agente || "").toLowerCase() === "cliente" ||
            (m.agente || "").toLowerCase() === "user" ||
            (m.agente || "").toLowerCase() === "usuario";

          return (
            <List.Item
              style={{
                borderRadius: 8,
                marginBottom: 8,
                background: esCliente ? "#fff" : "#fafafa",
                border: "1px solid #f0f0f0",
              }}
            >
              <Space direction="vertical" style={{ width: "100%" }}>
                <Space
                  style={{ justifyContent: "space-between", width: "100%" }}
                >
                  <Text strong>
                    {esCliente ? "Cliente" : m.agente || "Cliente"}
                  </Text>
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {m.created_at
                      ? dayjs(m.created_at).format("YYYY-MM-DD HH:mm")
                      : ""}
                  </Text>
                </Space>

                {m.texto && (
                  <Text style={{ whiteSpace: "pre-wrap" }}>{m.texto}</Text>
                )}

                <Space wrap>
                  {m.intencion && (
                    <Tag color="blue">Intención: {m.intencion}</Tag>
                  )}
                  {m.emocion && <Tag color="purple">Emoción: {m.emocion}</Tag>}
                  {m.necesita_humano && <Tag color="red">Necesita humano</Tag>}
                  {m.confianza != null && (
                    <Tag>Confianza: {Number(m.confianza).toFixed(2)}</Tag>
                  )}
                </Space>
              </Space>
            </List.Item>
          );
        }}
      />
    );
  };

  const resumen = detalle?.resumen;
  const conv = detalle?.conversacion;

  // ============================================
  // Funciones para renderizar el tablero
  // ============================================
  const COLORS = {
    whatsapp: "#25D366",
    sms: "#1890ff",
    email: "#f5222d",
    default: "#722ed1",
    activa: "#52c41a",
    cerrada: "#8c8c8c",
  };

  const CHART_COLORS = [
    "#667eea",
    "#f093fb",
    "#4facfe",
    "#fa709a",
    "#feca57",
    "#48dbfb",
    "#ff6b6b",
    "#ee5a6f",
  ];

  const getIconByCanal = (canal) => {
    switch (canal?.toLowerCase()) {
      case "whatsapp":
        return <WhatsAppOutlined style={{ fontSize: 20, color: "#25D366" }} />;
      case "sms":
        return <MessageOutlined style={{ fontSize: 20, color: "#1890ff" }} />;
      case "email":
        return <MailOutlined style={{ fontSize: 20, color: "#f5222d" }} />;
      default:
        return <PhoneOutlined style={{ fontSize: 20, color: "#722ed1" }} />;
    }
  };

  // Preparar datos para gráficos
  const dataPieCanal = useMemo(
    () =>
      Object.entries(kpis.porCanal).map(([canal, value]) => ({
        name: canal.toUpperCase(),
        value,
        color: COLORS[canal.toLowerCase()] || COLORS.default,
      })),
    [kpis.porCanal]
  );

  const dataPieEstado = useMemo(
    () =>
      Object.entries(kpis.porEstado)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 6)
        .map(([estado, value], index) => ({
          name: estado,
          value,
          color: CHART_COLORS[index % CHART_COLORS.length],
        })),
    [kpis.porEstado]
  );

  const dataBarCampanas = useMemo(
    () =>
      Object.entries(kpis.porCampana)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([campana, conversaciones]) => ({
          campana: `Camp ${campana}`,
          conversaciones,
        })),
    [kpis.porCampana]
  );

  const dataActivasVsCerradas = useMemo(
    () => [
      { name: "Activas", value: kpis.activas, color: COLORS.activa },
      { name: "Cerradas", value: kpis.cerradas, color: COLORS.cerrada },
    ],
    [kpis.activas, kpis.cerradas]
  );

  // Funciones para manejar clics en gráficos
  const handlePieClick = (data, filterType) => {
    let filteredConversaciones = [];
    let title = "";

    if (filterType === "estado") {
      filteredConversaciones = conversaciones.filter(
        (c) =>
          (data.name === "Activas" && c.is_active) ||
          (data.name === "Cerradas" && !c.is_active)
      );
      title = `Conversaciones ${data.name} (${data.value})`;
    } else if (filterType === "canal") {
      const canalName = data.name.toLowerCase();
      filteredConversaciones = conversaciones.filter(
        (c) => c.canal?.toLowerCase() === canalName
      );
      title = `Conversaciones por ${data.name} (${data.value})`;
    }

    setModalData({ title, conversaciones: filteredConversaciones });
    setModalVisible(true);
  };

  const handleBarClick = (data, filterType) => {
    let filteredConversaciones = [];
    let title = "";

    if (filterType === "estadoConv") {
      filteredConversaciones = conversaciones.filter(
        (c) => (c.current_state || "inicio") === data.name
      );
      title = `Conversaciones en estado "${data.name}" (${data.value})`;
    } else if (filterType === "campana") {
      const campanaId = parseInt(data.campana.replace("Camp ", ""));
      filteredConversaciones = conversaciones.filter(
        (c) => c.campaign_id === campanaId
      );
      title = `Conversaciones de ${data.campana} (${data.conversaciones})`;
    }

    setModalData({ title, conversaciones: filteredConversaciones });
    setModalVisible(true);
  };

  const renderTablero = () => (
    <>
      {/* Filtros en el Dashboard */}
      <Space
        style={{
          width: "100%",
          padding: 12,
          background: "white",
          borderRadius: 12,
          boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
          marginBottom: 16,
        }}
        wrap
      >
        <Space direction="vertical" size={4}>
          <Text type="secondary">Canal</Text>
          <Select value={fCanal} onChange={setFCanal} style={{ width: 140 }}>
            <Option value="">(Todos)</Option>
            <Option value="whatsapp">WhatsApp</Option>
            <Option value="sms">SMS</Option>
            <Option value="email">Email</Option>
          </Select>
        </Space>

        <Space direction="vertical" size={4}>
          <Text type="secondary">Estado</Text>
          <Select
            value={fIsActive}
            onChange={setFIsActive}
            style={{ width: 140 }}
          >
            <Option value="">(Todos)</Option>
            <Option value="true">Activas</Option>
            <Option value="false">Cerradas</Option>
          </Select>
        </Space>
        <Space direction="vertical" size={4}>
          <Text type="secondary">País</Text>
          <Select value={fPais} onChange={setFPais} style={{ width: 140 }}>
            <Option value="">(Todos)</Option>
            <Option value="Colombia">Colombia</Option>
            <Option value="Perú">Perú</Option>
            <Option value="Desconocido">Desconocido</Option>
          </Select>
        </Space>

        <Button type="primary" onClick={cargarConversaciones}>
          Buscar
        </Button>
        <Button icon={<DownloadOutlined />} onClick={abrirModalExportar}>
          Exportar Excel
        </Button>
      </Space>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {/* KPI Principal - Total */}
        <Col xs={24} sm={12} md={6}>
          <Card
            bordered={false}
            style={{
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              borderRadius: 12,
              boxShadow: "0 4px 12px rgba(102, 126, 234, 0.3)",
            }}
          >
            <Statistic
              title={
                <span style={{ color: "rgba(255,255,255,0.85)" }}>
                  Total Conversaciones
                </span>
              }
              value={kpis.total}
              prefix={<MessageOutlined />}
              valueStyle={{ color: "#fff", fontSize: 32 }}
            />
          </Card>
        </Col>

        {/* KPI - Activas */}
        <Col xs={24} sm={12} md={6}>
          <Card
            bordered={false}
            style={{
              background: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
              borderRadius: 12,
              boxShadow: "0 4px 12px rgba(245, 87, 108, 0.3)",
            }}
          >
            <Statistic
              title={
                <span style={{ color: "rgba(255,255,255,0.85)" }}>
                  Conversaciones Activas
                </span>
              }
              value={kpis.activas}
              prefix={<SyncOutlined spin />}
              valueStyle={{ color: "#fff", fontSize: 32 }}
            />
          </Card>
        </Col>

        {/* KPI - Cerradas */}
        <Col xs={24} sm={12} md={6}>
          <Card
            bordered={false}
            style={{
              background: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
              borderRadius: 12,
              boxShadow: "0 4px 12px rgba(79, 172, 254, 0.3)",
            }}
          >
            <Statistic
              title={
                <span style={{ color: "rgba(255,255,255,0.85)" }}>
                  Conversaciones Cerradas
                </span>
              }
              value={kpis.cerradas}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: "#fff", fontSize: 32 }}
            />
          </Card>
        </Col>

        {/* KPI - Usuarios Únicos */}
        <Col xs={24} sm={12} md={6}>
          <Card
            bordered={false}
            style={{
              background: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
              borderRadius: 12,
              boxShadow: "0 4px 12px rgba(250, 112, 154, 0.3)",
            }}
          >
            <Statistic
              title={
                <span style={{ color: "rgba(255,255,255,0.85)" }}>
                  Usuarios Únicos
                </span>
              }
              value={kpis.usuariosUnicos}
              prefix={<UserOutlined />}
              valueStyle={{ color: "#fff", fontSize: 32 }}
            />
          </Card>
        </Col>

        {/* Distribución Activas vs Cerradas */}
        <Col xs={24} md={12}>
          <Card
            title={
              <span style={{ fontSize: 16, fontWeight: 600 }}>
                Estado de Conversaciones
              </span>
            }
            bordered={false}
            style={{
              borderRadius: 12,
              boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
              height: "100%",
            }}
          >
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={dataActivasVsCerradas}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(1)}%`
                  }
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                  onClick={(data) => handlePieClick(data, "estado")}
                  cursor="pointer"
                >
                  {dataActivasVsCerradas.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* Distribución por Estado */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <span style={{ fontSize: 16, fontWeight: 600 }}>
                Top Estados de Conversación
              </span>
            }
            bordered={false}
            style={{
              borderRadius: 12,
              boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
            }}
          >
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={dataPieEstado}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="name"
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis />
                <Tooltip />
                <Legend wrapperStyle={{ paddingTop: "35px" }} />
                <Bar
                  dataKey="value"
                  name="Conversaciones"
                  fill="#667eea"
                  onClick={(data) => handleBarClick(data, "estadoConv")}
                  cursor="pointer"
                >
                  {dataPieEstado.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* Resumen visual de podio */}
        {/* {Object.keys(kpis.porCampana).length > 0 && (
        <Col xs={24}>
          <Card
            title={<span style={{ fontSize: 16, fontWeight: 600 }}>🏆 Top 5 Campañas con más Conversaciones</span>}
            bordered={false}
            style={{ borderRadius: 12, boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}
          >
            <Row gutter={[16, 16]}>
              {Object.entries(kpis.porCampana)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5)
                .map(([campana, count], index) => (
                  <Col xs={24} sm={12} md={8} lg={4} key={campana}>
                    <Card
                      bordered={false}
                      style={{
                        background: index === 0 ? 'linear-gradient(135deg, #ffd700 0%, #ffed4e 100%)' :
                                   index === 1 ? 'linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%)' :
                                   index === 2 ? 'linear-gradient(135deg, #cd7f32 0%, #d4a574 100%)' :
                                   '#f5f5f5',
                        borderRadius: 8,
                        textAlign: 'center',
                      }}
                    >
                      <div style={{ fontSize: 24, fontWeight: 'bold', marginBottom: 8 }}>
                        {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '🎖️'}
                      </div>
                      <Text strong style={{ fontSize: 16 }}>Campaña {campana}</Text>
                      <div style={{ marginTop: 8 }}>
                        <Text type="secondary" style={{ fontSize: 24, fontWeight: 600 }}>{count}</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>conversaciones</Text>
                      </div>
                    </Card>
                  </Col>
                ))}
            </Row>
          </Card>
        </Col>
      )} */}
      </Row>
    </>
  );

  return (
    <Layout style={{ height: "100%", background: "#f5f5f5", marginTop: 60 }}>
      <Content style={{ padding: 16 }}>
        <Space direction="vertical" style={{ width: "100%" }} size="large">
          {/* Header con título y botón de tablero */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: 16,
            }}
          >
            <Title level={3} style={{ margin: 0 }}>
              CRM – Auditoría de Conversaciones
            </Title>

            <Button
              type={mostrarTablero ? "primary" : "default"}
              icon={
                mostrarTablero ? <EyeInvisibleOutlined /> : <BarChartOutlined />
              }
              onClick={() => setMostrarTablero(!mostrarTablero)}
              size="large"
              style={{
                borderRadius: 8,
                boxShadow: mostrarTablero
                  ? "0 4px 12px rgba(24, 144, 255, 0.3)"
                  : "none",
              }}
            >
              {mostrarTablero ? "Ocultar Dashboard" : "Ver Dashboard"}
            </Button>
          </div>

          {/* Tablero de Control / KPIs - Con animación */}
          {mostrarTablero && (
            <div
              style={{
                animation: "fadeIn 0.3s ease-in",
              }}
            >
              {renderTablero()}
            </div>
          )}

          {/* Mini Resumen siempre visible */}
          {!mostrarTablero && (
            <Card
              bordered={false}
              style={{
                borderRadius: 12,
                boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
                background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              }}
            >
              <Row gutter={16}>
                <Col xs={12} sm={6}>
                  <Statistic
                    title={
                      <span style={{ color: "rgba(255,255,255,0.85)" }}>
                        Total
                      </span>
                    }
                    value={kpis.total}
                    prefix={<MessageOutlined />}
                    valueStyle={{ color: "#fff", fontSize: 24 }}
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title={
                      <span style={{ color: "rgba(255,255,255,0.85)" }}>
                        Activas
                      </span>
                    }
                    value={kpis.activas}
                    prefix={<SyncOutlined spin />}
                    valueStyle={{ color: "#fff", fontSize: 24 }}
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title={
                      <span style={{ color: "rgba(255,255,255,0.85)" }}>
                        Cerradas
                      </span>
                    }
                    value={kpis.cerradas}
                    prefix={<CheckCircleOutlined />}
                    valueStyle={{ color: "#fff", fontSize: 24 }}
                  />
                </Col>
                <Col xs={12} sm={6}>
                  <Statistic
                    title={
                      <span style={{ color: "rgba(255,255,255,0.85)" }}>
                        Usuarios
                      </span>
                    }
                    value={kpis.usuariosUnicos}
                    prefix={<UserOutlined />}
                    valueStyle={{ color: "#fff", fontSize: 24 }}
                  />
                </Col>
              </Row>
            </Card>
          )}

          {/* Filtros - Solo visibles cuando NO está el dashboard */}
          {!mostrarTablero && (
            <Space
              style={{
                width: "100%",
                padding: 12,
                background: "white",
                borderRadius: 12,
                boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
              }}
              wrap
            >
              <Space direction="vertical" size={4}>
                <Text type="secondary">Canal</Text>
                <Select
                  value={fCanal}
                  onChange={setFCanal}
                  style={{ width: 140 }}
                >
                  <Option value="">(Todos)</Option>
                  <Option value="whatsapp">WhatsApp</Option>
                  <Option value="sms">SMS</Option>
                  <Option value="email">Email</Option>
                </Select>
              </Space>

              <Space direction="vertical" size={4}>
                <Text type="secondary">Estado</Text>
                <Select
                  value={fIsActive}
                  onChange={setFIsActive}
                  style={{ width: 140 }}
                >
                  <Option value="">(Todos)</Option>
                  <Option value="true">Activas</Option>
                  <Option value="false">Cerradas</Option>
                </Select>
              </Space>

              <Button type="primary" onClick={cargarConversaciones}>
                Buscar
              </Button>
            </Space>
          )}

          {/* Tabla de conversaciones - Solo visible cuando NO está el dashboard */}
          {!mostrarTablero && (
            <div
              style={{
                background: "white",
                borderRadius: 12,
                padding: 12,
                boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
                animation: "fadeIn 0.3s ease-in",
              }}
            >
              <Table
                rowKey="id"
                loading={loading}
                dataSource={conversacionesFiltradas}
                columns={columns}
                size="small"
                onRow={(record) => ({
                  onClick: () => onRowClick(record),
                  style: { cursor: "pointer" },
                })}
                pagination={{ pageSize: 20, showSizeChanger: true }}
              />
            </div>
          )}
        </Space>

        {/* Modal para mostrar conversaciones filtradas del gráfico */}
        <Modal
          title={modalData.title}
          open={modalVisible}
          onCancel={() => setModalVisible(false)}
          width={900}
          footer={[
            <Button
              key="close"
              type="primary"
              onClick={() => setModalVisible(false)}
            >
              Cerrar
            </Button>,
          ]}
        >
          <Table
            rowKey="id"
            dataSource={modalData.conversaciones}
            columns={columns}
            size="small"
            onRow={(record) => ({
              onClick: () => {
                setModalVisible(false);
                onRowClick(record);
              },
              style: { cursor: "pointer" },
            })}
            pagination={{ pageSize: 10, showSizeChanger: true }}
            scroll={{ y: 400 }}
          />
        </Modal>

        {/* Modal para configurar exportación a Excel */}
        <Modal
          title="📊 Exportar Conversaciones a Excel"
          open={modalExportVisible}
          onCancel={() => setModalExportVisible(false)}
          width={700}
          footer={[
            <Button key="limpiar" onClick={limpiarFiltrosExportar}>
              Limpiar Filtros
            </Button>,
            <Button key="cancel" onClick={() => setModalExportVisible(false)}>
              Cancelar
            </Button>,
            <Button
              key="export"
              type="primary"
              icon={<DownloadOutlined />}
              onClick={exportarExcel}
            >
              Descargar Excel
            </Button>,
          ]}
        >
          <Space direction="vertical" style={{ width: "100%" }} size="large">
            <Text type="secondary">
              Configura los filtros para exportar las conversaciones y mensajes
              que necesites.
            </Text>

            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12}>
                <Space direction="vertical" size={4} style={{ width: "100%" }}>
                  <Text strong>Canal</Text>
                  <Select
                    value={fCanal}
                    onChange={setFCanal}
                    style={{ width: "100%" }}
                    placeholder="Selecciona un canal"
                  >
                    <Option value="">(Todos)</Option>
                    <Option value="whatsapp">WhatsApp</Option>
                    <Option value="sms">SMS</Option>
                    <Option value="email">Email</Option>
                  </Select>
                </Space>
              </Col>

              <Col xs={24} sm={12}>
                <Space direction="vertical" size={4} style={{ width: "100%" }}>
                  <Text strong>País</Text>
                  <Select
                    value={fPais}
                    onChange={setFPais}
                    style={{ width: "100%" }}
                    placeholder="Selecciona un país"
                  >
                    <Option value="">(Todos)</Option>
                    <Option value="Colombia">Colombia</Option>
                    <Option value="Perú">Perú</Option>
                    <Option value="Desconocido">Desconocido</Option>
                  </Select>
                </Space>
              </Col>

              <Col xs={24} sm={12}>
                <Space direction="vertical" size={4} style={{ width: "100%" }}>
                  <Text strong>Estado</Text>
                  <Select
                    value={fIsActive}
                    onChange={setFIsActive}
                    style={{ width: "100%" }}
                    placeholder="Activas o cerradas"
                  >
                    <Option value="">(Todos)</Option>
                    <Option value="true">Activas</Option>
                    <Option value="false">Cerradas</Option>
                  </Select>
                </Space>
              </Col>

              <Col xs={24} sm={12}>
                <Space direction="vertical" size={4} style={{ width: "100%" }}>
                  <Text strong>Campaña</Text>
                  <Select
                    value={fCampaignId}
                    onChange={setFCampaignId}
                    style={{ width: "100%" }}
                    placeholder="Selecciona una campaña"
                    showSearch
                    optionFilterProp="children"
                  >
                    <Option value="">(Todas)</Option>
                    {uniqueCampaigns.map((c) => (
                      <Option key={c} value={c.toString()}>
                        Campaña {c}
                      </Option>
                    ))}
                  </Select>
                </Space>
              </Col>

              <Col xs={24} sm={12}>
                <Space direction="vertical" size={4} style={{ width: "100%" }}>
                  <Text strong>Tipificación (Current State)</Text>
                  <Select
                    value={fTipificacion}
                    onChange={setFTipificacion}
                    style={{ width: "100%" }}
                    placeholder="Selecciona una tipificación"
                    showSearch
                    optionFilterProp="children"
                  >
                    <Option value="">(Todas)</Option>
                    {uniqueStates.map((s) => (
                      <Option key={s} value={s}>
                        {s}
                      </Option>
                    ))}
                  </Select>
                </Space>
              </Col>

              <Col xs={24}>
                <Space direction="vertical" size={4} style={{ width: "100%" }}>
                  <Text strong>Rango de Fechas (mensajes)</Text>
                  <RangePicker
                    value={fDateRange}
                    onChange={setFDateRange}
                    format="YYYY-MM-DD"
                    style={{ width: "100%" }}
                    placeholder={["Fecha inicio", "Fecha fin"]}
                  />
                </Space>
              </Col>
            </Row>

            <div
              style={{
                background: "#f0f5ff",
                padding: 12,
                borderRadius: 8,
                border: "1px solid #adc6ff",
              }}
            >
              <Text type="secondary" style={{ fontSize: 12 }}>
                💡 <strong>Tip:</strong> El archivo Excel incluirá todas las
                conversaciones y sus mensajes según los filtros seleccionados.
                Si no seleccionas ningún filtro, se exportarán todas las
                conversaciones.
              </Text>
            </div>
          </Space>
        </Modal>

        <Drawer
          title={
            conv
              ? `Conversación #${conv.id} – ${conv.user_id || ""}`
              : "Detalle de conversación"
          }
          width={700}
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
        >
          {loadingDetalle ? (
            <Spin />
          ) : detalle ? (
            <Space direction="vertical" style={{ width: "100%" }} size="large">
              {/* Resumen / KPI */}
              <Space direction="vertical" style={{ width: "100%" }}>
                <Text strong>Resumen de la conversación</Text>
                <Space wrap>
                  <Tag color={resultadoColor(resumen?.resultado)}>
                    {resumen?.resultado || "SIN_MENSAJES"}
                  </Tag>
                  {resumen?.ultima_intencion && (
                    <Tag color="blue">
                      Última intención: {resumen.ultima_intencion}
                    </Tag>
                  )}
                  {resumen?.necesita_humano && (
                    <Tag color="red">Requirió humano</Tag>
                  )}
                </Space>

                <Descriptions
                  bordered
                  size="small"
                  column={2}
                  style={{ marginTop: 8 }}
                >
                  <Descriptions.Item label="Total mensajes">
                    {resumen?.total_mensajes ?? 0}
                  </Descriptions.Item>
                  <Descriptions.Item label="Mensajes cliente">
                    {resumen?.mensajes_cliente ?? 0}
                  </Descriptions.Item>
                  <Descriptions.Item label="Mensajes agente/bot">
                    {resumen?.mensajes_agente ?? 0}
                  </Descriptions.Item>
                  <Descriptions.Item label="Canal">
                    {conv.canal}
                  </Descriptions.Item>
                  <Descriptions.Item label="Tipificación Actual">
                    {conv.current_state}
                  </Descriptions.Item>
                  <Descriptions.Item label="Activa">
                    {conv.is_active ? "Sí" : "No"}
                  </Descriptions.Item>
                  <Descriptions.Item label="Creada">
                    {conv.created_at
                      ? dayjs(conv.created_at).format("YYYY-MM-DD HH:mm")
                      : ""}
                  </Descriptions.Item>
                  <Descriptions.Item label="Última actualización">
                    {conv.updated_at
                      ? dayjs(conv.updated_at).format("YYYY-MM-DD HH:mm")
                      : ""}
                  </Descriptions.Item>
                </Descriptions>
              </Space>

              <Divider />

              {/* Mensajes */}
              <Space direction="vertical" style={{ width: "100%" }}>
                <Text strong>Mensajes</Text>
                {renderMensajes()}
              </Space>
            </Space>
          ) : (
            <Text type="secondary">
              Selecciona una conversación para ver su detalle.
            </Text>
          )}
        </Drawer>
      </Content>
    </Layout>
  );
};

export default CrmConversaciones;

// Agregar estilos de animación
const style = document.createElement("style");
style.textContent = `
  @keyframes fadeIn {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
`;
document.head.appendChild(style);
