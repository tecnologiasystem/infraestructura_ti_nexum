import React, { useEffect, useState } from "react";
import { Card, Typography, Spin, Select, Row, Col, DatePicker, Button, Input, Table } from "antd";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LabelList,
} from "recharts";
import axios from "axios";
import { API_URL_GATEWAY } from "./../../config";
import { DownloadOutlined, SearchOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import isSameOrBefore from "dayjs/plugin/isSameOrBefore";
import isSameOrAfter from "dayjs/plugin/isSameOrAfter";

dayjs.extend(isSameOrBefore);
dayjs.extend(isSameOrAfter);

const { RangePicker } = DatePicker;
const { Title } = Typography;
const { Option } = Select;
const COLORS = ["#F39200", "#36A9E1", "#90BC1F"];

const TableroControl = () => {
  const [graficoCampanas, setGraficoCampanas] = useState([]);
  const [graficoRoles, setGraficoRoles] = useState([]);
  const [graficoLogins, setGraficoLogins] = useState([]);
  const [logs, setLogs] = useState([]);
  const [filtroUsuario, setFiltroUsuario] = useState("");
  const [loading, setLoading] = useState(false);
  const [graficoSeleccionado, setGraficoSeleccionado] = useState("campana");
  const [fechaSeleccionada, setFechaSeleccionada] = useState(null);
  const [rangoFechas, setRangoFechas] = useState([]);

  useEffect(() => {
    const fetchGraficos = async () => {
      try {
        setLoading(true);
        const [campanasRes, rolesRes, loginsRes] = await Promise.all([
          axios.get(`${API_URL_GATEWAY}/gateway/graficos/usuarios_por_campana`),
          axios.get(`${API_URL_GATEWAY}/gateway/graficos/usuarios_por_rol`),
          axios.get(`${API_URL_GATEWAY}/gateway/graficos/logs_por_dia`),
        ]);

        const campanaData = campanasRes.data?.labels.map((label, i) => ({
          name: label,
          total: campanasRes.data.valores[i],
        })) || [];

        const rolData = rolesRes.data?.labels.map((label, i) => ({
          name: label,
          total: rolesRes.data.valores[i],
        })) || [];

        const loginsData = loginsRes.data?.map((item) => ({
          name: item.fecha,
          total: item.total,
          usuarios: item.usuarios,
        })) || [];

        setGraficoCampanas(campanaData);
        setGraficoRoles(rolData);
        setGraficoLogins(loginsData);
      } catch (error) {
        console.error("Error al cargar los gráficos", error);
      } finally {
        setLoading(false);
      }
    };

    const fetchLogs = async () => {
      try {
        const res = await axios.get(`${API_URL_GATEWAY}/gateway/logs/iniciosesion`);
        setLogs(res.data);
      } catch (error) {
        console.error("Error al obtener logs:", error);
      }
    };

    fetchGraficos();
    fetchLogs();
  }, []);

  const descargarExcelPorRango = () => {
    if (rangoFechas.length !== 2) return;

    const desde = dayjs(rangoFechas[0]).startOf("day").format("YYYY-MM-DD HH:mm:ss");
    const hasta = dayjs(rangoFechas[1]).endOf("day").format("YYYY-MM-DD HH:mm:ss");

    const url = `${API_URL_GATEWAY}/gateway/logs/iniciosesion/exportar?usuario=${encodeURIComponent(filtroUsuario)}&desde=${desde}&hasta=${hasta}`;
    window.open(url, "_blank");
  };

  const obtenerDatosGrafico = () => {
    switch (graficoSeleccionado) {
      case "rol":
        return { titulo: "Distribución de Usuarios por Rol", data: graficoRoles, color: COLORS[1] };
      case "logins":
        return { titulo: "Inicios de Sesión por Día", data: graficoLogins, color: COLORS[2] };
      case "verlogs":
        return { titulo: "Detalle de Inicios de Sesión", data: [], color: COLORS[2] };
      default:
        return { titulo: "Distribución de Usuarios por Campaña", data: graficoCampanas, color: COLORS[0] };
    }
  };

  const filtrar = (registro) => {
    const usuarioMatch = registro.usuario.toLowerCase().includes(filtroUsuario.toLowerCase());
    let entrada;
    try {
      entrada = dayjs(registro.entrada);
    } catch {
      return false;
    }
    const fechaMatch =
      entrada.isValid() &&
      (!rangoFechas.length ||
        (entrada.isSameOrAfter(rangoFechas[0], "minute") && entrada.isSameOrBefore(rangoFechas[1], "minute")));
    return usuarioMatch && fechaMatch;
  };

  const columnas = [
    {
      title: "Usuario",
      dataIndex: "usuario",
      key: "usuario",
    },
    {
      title: "Entrada",
      dataIndex: "entrada",
      key: "entrada",
      render: (text) => dayjs(text).format("DD/MM/YYYY HH:mm:ss"),
    },
    {
      title: "Vencimiento",
      dataIndex: "vencimiento",
      key: "vencimiento",
      render: (text) => dayjs(text).format("DD/MM/YYYY HH:mm:ss"),
    },
    {
      title: "IP",
      dataIndex: "IP",
      key: "IP",
    },
  ];

  const { titulo, data, color } = obtenerDatosGrafico();

  return (
    <div style={{ padding: 20 }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
        <h1 className="areas-title">Tablero de Control</h1>
        </Col>
        <Col style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
          <Select
            value={graficoSeleccionado}
            onChange={setGraficoSeleccionado}
            style={{ width: 280 }}
          >
            <Option value="campana">Usuarios por Campaña</Option>
            <Option value="rol">Usuarios por Rol</Option>
            <Option value="logins">Inicios de Sesión por Día</Option>
            <Option value="verlogs">Ver Detalle de Logs</Option>
          </Select>

          {(graficoSeleccionado === "verlogs") && (
            <>
              <Input
                placeholder="Filtrar por usuario"
                prefix={<SearchOutlined />}
                value={filtroUsuario}
                onChange={(e) => setFiltroUsuario(e.target.value)}
              />
              <RangePicker
                value={rangoFechas}
                onChange={(dates) =>
                  setRangoFechas(dates ? [dates[0].startOf("day"), dates[1].endOf("day")] : [])
                }
                format="YYYY-MM-DD"
              />
              <Button
                icon={<DownloadOutlined />}
                onClick={descargarExcelPorRango}
                disabled={rangoFechas.length !== 2}
                type="primary"
              >
                Descargar Excel
              </Button>
            </>
          )}
        </Col>
      </Row>

      <Card>
        <Title level={4}>{titulo}</Title>

        {loading ? (
          <Spin size="large" />
        ) : graficoSeleccionado === "verlogs" ? (
          <Table
            dataSource={logs.filter(filtrar)}
            columns={columnas}
            rowKey={(record) => `${record.token}-${record.entrada}`}
            pagination={{ pageSize: 8 }}
          />
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart
              data={
                graficoSeleccionado === "logins" && rangoFechas.length === 2
                  ? data.filter((d) => {
                      const fecha = dayjs(d.name);
                      const desde = dayjs(rangoFechas[0]).startOf("day");
                      const hasta = dayjs(rangoFechas[1]).endOf("day");
                      return fecha.isSameOrAfter(desde) && fecha.isSameOrBefore(hasta);
                    })
                  : data
              }
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} domain={[0, 'dataMax + 20']} />
              <Tooltip
                content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                    const total = payload[0].value;
                    const color = payload[0].color;

                    switch (graficoSeleccionado) {
                        case "campana":
                        case "rol":
                        return (
                            <div style={{ backgroundColor: "#fff", padding: 10, border: "1px solid #ccc" }}>
                            <strong>{label}</strong>
                            <br />
                            <span style={{ color }}>{`Total usuarios: ${total}`}</span>
                            </div>
                        );

                        case "logins":
                        const usuarios = payload[0].payload.usuarios || [];
                        return (
                            <div style={{ backgroundColor: "#fff", padding: 10, border: "1px solid #ccc" }}>
                            <strong>{label}</strong>
                            <br />
                            <span style={{ color }}>{`Inicios: ${total}`}</span>
                            <br />
                            <span style={{ color }}>{`Total usuarios: ${usuarios.length}`}</span>
                            </div>
                        );

                        default:
                        return null;
                    }
                    }
                    return null;
                }}
                />
              <Bar dataKey="total" fill={color}>
                <LabelList dataKey="total" position="top" />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </Card>
    </div>
  );
};

export default TableroControl;
