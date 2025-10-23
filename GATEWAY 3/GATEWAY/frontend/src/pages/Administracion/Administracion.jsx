import React, { useEffect, useState } from "react";
import {
  Card,
  Row,
  Col,
  Typography,
  Switch,
  message,
  Spin,
} from "antd";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LabelList,
} from "recharts";
import axios from "axios";
import { API_URL_GATEWAY } from "./../../config";
import menuItems from "../../config/menuItems";
import * as AntIcons from "@ant-design/icons";

const { Title } = Typography;

const COLORS = ["#F39200", "#36A9E1", "#90BC1F", "#662483", "#000F9F"];

const UsuariosGrafico = () => {
  const [usuarios, setUsuarios] = useState([]);
  const [areas, setAreas] = useState([]);
  const [roles, setRoles] = useState([]);
  const [campanas, setCampanas] = useState([]);
  const [usuariosCampanas, setUsuariosCampanas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [userRole, setUserRole] = useState(null);

  const [mostrarGrafico, setMostrarGrafico] = useState(false);
  const [mostrarRol, setMostrarRol] = useState(true);
  const [mostrarArea, setMostrarArea] = useState(false);
  const [mostrarCampana, setMostrarCampana] = useState(true);

  const [graficoCampanas, setGraficoCampanas] = useState([]);
  const [graficoRoles, setGraficoRoles] = useState([]);

  useEffect(() => {
    const rol = parseInt(localStorage.getItem("idRol")) || 0;
    setUserRole(rol);

    const fetchData = async () => {
      try {
        setLoading(true);
        const [
          usuariosRes,
          areasRes,
          rolesRes,
          campanasRes,
          usuariosCampanasRes,
          graficoCampanasRes,
          graficoRolesRes
        ] = await Promise.all([
          axios.get(`${API_URL_GATEWAY}/gateway/usuarios/dar`),
          axios.get(`${API_URL_GATEWAY}/gateway/areas/dar`),
          axios.get(`${API_URL_GATEWAY}/gateway/roles/dar`),
          axios.get(`${API_URL_GATEWAY}/gateway/campanas/dar`),
          axios.get(`${API_URL_GATEWAY}/gateway/usuariosCampanas/dar`),
          axios.get(`${API_URL_GATEWAY}/gateway/graficos/usuarios_por_campana`),
          axios.get(`${API_URL_GATEWAY}/gateway/graficos/usuarios_por_rol`)
        ]);

        setUsuarios(usuariosRes.data || []);
      setAreas(areasRes.data || []);
      setRoles(rolesRes.data?.roles || []);
      setCampanas(campanasRes.data || []);
      setUsuariosCampanas(usuariosCampanasRes.data || []);

      // Datos para gráficos
      const campanaData = graficoCampanasRes.data?.labels.map((label, i) => ({
        name: label,
        total: graficoCampanasRes.data.valores[i],
      })) || [];

      const rolData = graficoRolesRes.data?.labels.map((label, i) => ({
        name: label,
        total: graficoRolesRes.data.valores[i],
      })) || [];

      setGraficoCampanas(campanaData);
      setGraficoRoles(rolData);

    } catch (error) {
      message.error("Error al cargar datos");
    } finally {
      setLoading(false);
    }
  };

  fetchData();
}, []);

  const obtenerNombre = (id, lista, key = "id") => {
    if (!Array.isArray(lista)) return "—";
    const item = lista.find((x) => String(x[key]) === String(id));
    return item?.nombre || item?.rol || item?.nombreArea || item?.descripcionCampana || "Desconocido";
  };

  const generarDatos = () => {
    const conteoCampanas = {};

    usuariosCampanas.forEach((relacion) => {
      const campanaObj = campanas.find(c => c.idCampana === relacion.idCampana);
      const nombreCampana = campanaObj?.descripcionCampana || "Sin nombre";

      if (!conteoCampanas[nombreCampana]) {
        conteoCampanas[nombreCampana] = 0;
      }

      conteoCampanas[nombreCampana] += 1;
    });

    return Object.entries(conteoCampanas).map(([campana, total]) => ({
      name: campana,
      total,
    }));
  };



  const data = generarDatos();

  const adminSubItems = menuItems.find((item) => item.key === "administracion")?.children || [];
  const adminMenuOptions = adminSubItems.filter((child) => child.roles.includes(userRole));

  const renderIcon = (iconName) => {
    const IconComponent = AntIcons[iconName];
    return IconComponent ? <IconComponent style={{ fontSize: "36px" }} /> : null;
  };

  const handleSectionClick = (path) => {
    window.location.href = path;
  };

  return (
    <div style={{ padding: 20 }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: "16px" }}>
        <Col>
          <Title level={3}>Administración</Title>
        </Col>
        {userRole === 1 && (
          <Col style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontWeight: 500 }}>Mostrar gráficos</span>
            <Switch checked={mostrarGrafico} onChange={setMostrarGrafico} size="large" />
          </Col>
        )}
      </Row>
  
      <Row gutter={32}>
        <Col span={userRole === 1 && mostrarGrafico ? 6 : 24}>
          <Row gutter={[16, 16]}>
            {adminMenuOptions.map((item, index) => (
              <Col xs={24} sm={12} md={12} lg={userRole === 1 && mostrarGrafico ? 24 : 6} key={item.key}>
                <Card
                  hoverable
                  style={{
                    borderRadius: "20px",
                    background: COLORS[index % COLORS.length],
                    textAlign: "center",
                    color: "#fff",
                    minHeight: "100px",
                    height: "100px",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "center",
                    cursor: "pointer",
                  }}
                  bodyStyle={{ padding: "12px" }}
                  onClick={() => handleSectionClick(item.path)}
                >
                  {renderIcon(item.icon)}
                  <h3 style={{ marginTop: "8px", fontWeight: "bold" }}>{item.label}</h3>
                </Card>
              </Col>
            ))}
          </Row>
        </Col>
  
        {userRole === 1 && mostrarGrafico && (
          <Col span={18}>
            <Card>
              <Title level={4}>Distribución de Usuarios por Campaña</Title>
              {loading ? <Spin size="large" /> : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={graficoCampanas}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="total" fill={COLORS[0]}>
                      <LabelList dataKey="total" position="top" />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>
  
            <Card style={{ marginTop: 24 }}>
              <Title level={4}>Distribución de Usuarios por Rol</Title>
              {loading ? <Spin size="large" /> : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={graficoRoles}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="total" fill={COLORS[1]}>
                      <LabelList dataKey="total" position="top" />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </Card>
          </Col>
        )}
      </Row>
    </div>
  );
  
};

export default UsuariosGrafico;
