import React, { useEffect, useState } from "react";
import {
  Table,
  Tag,
  Typography,
  Space,
  Button,
  message,
  Badge,
  Spin,
  Tabs,
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  DatePicker,
  Select,
  Divider,
} from "antd";
import {
  ReloadOutlined,
  ArrowLeftOutlined,
  DownloadOutlined,
} from "@ant-design/icons";
import axios from "axios";
import { API_URL_GATEWAY_RPA } from "../../config";
import { useNavigate } from "react-router-dom";
import "./EmailReporte.css";

const { Title } = Typography;
const { RangePicker } = DatePicker;

export default function EmailCargues() {
  // ============= ESTADOS =============
  const [encabezados, setEncabezados] = useState([]);
  const [encLoading, setEncLoading] = useState(false);
  const [detallesByEnc, setDetallesByEnc] = useState({});
  const [loadingDetalle, setLoadingDetalle] = useState({});

  // Estados del dashboard
  const [rangeFechas, setRangeFechas] = useState(null);
  const [remitenteFiltro, setRemitenteFiltro] = useState(null);
  const [dashLoading, setDashLoading] = useState(false);
  const [dashResumen, setDashResumen] = useState(null);
  const [dashPorRemitente, setDashPorRemitente] = useState([]);
  const [dashPorDia, setDashPorDia] = useState([]);
  const [dashTopErrores, setDashTopErrores] = useState([]);

  const navigate = useNavigate();

  // ============= UTILIDADES =============
  const toYmd = (d) => {
    if (!d) return null;
    if (typeof d.format === "function") return d.format("YYYY-MM-DD");
    const dt = new Date(d);
    const y = dt.getFullYear();
    const m = String(dt.getMonth() + 1).padStart(2, "0");
    const day = String(dt.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  };

  const buildDashParams = () => {
    const params = {};
    if (rangeFechas?.length === 2) {
      params.fecha_inicio = toYmd(rangeFechas[0]);
      params.fecha_fin = toYmd(rangeFechas[1]);
    }
    if (remitenteFiltro) params.remitente = remitenteFiltro;
    return params;
  };

  // ============= API CALLS =============
  const fetchEncabezados = async () => {
    try {
      setEncLoading(true);
      const { data } = await axios.get(
        `${API_URL_GATEWAY_RPA}/gateway/correos/encabezados`
      );
      setEncabezados(data?.data || []);
    } catch (e) {
      console.error(e);
      message.error("No se pudieron cargar los encabezados");
    } finally {
      setEncLoading(false);
    }
  };

  const fetchDashboard = async () => {
    try {
      setDashLoading(true);
      const paramsBase = buildDashParams();
      
      const [r1, r2, r3, r4] = await Promise.all([
        axios.get(`${API_URL_GATEWAY_RPA}/gateway/correos/dashboard/resumen`, { 
          params: paramsBase 
        }),
        axios.get(`${API_URL_GATEWAY_RPA}/gateway/correos/dashboard/porRemitente`, {
          params: { ...paramsBase, remitente: undefined },
        }),
        axios.get(`${API_URL_GATEWAY_RPA}/gateway/correos/dashboard/porDia`, { 
          params: paramsBase 
        }),
        axios.get(`${API_URL_GATEWAY_RPA}/gateway/correos/dashboard/topErrores`, {
          params: { ...paramsBase, top: 20 },
        }),
      ]);

      setDashResumen(r1?.data?.data || null);
      setDashPorRemitente(r2?.data?.data || []);
      setDashPorDia(r3?.data?.data || []);
      setDashTopErrores(r4?.data?.data || []);
    } catch (e) {
      console.error(e);
      message.error("No se pudo cargar el tablero");
    } finally {
      setDashLoading(false);
    }
  };

  const fetchDetalle = async (idEncabezado) => {
    setLoadingDetalle((prev) => ({ ...prev, [idEncabezado]: true }));
    try {
      const { data } = await axios.get(
        `${API_URL_GATEWAY_RPA}/gateway/correos/detalle`,
        { params: { idEncabezado } }
      );
      setDetallesByEnc((prev) => ({
        ...prev,
        [idEncabezado]: data?.data || [],
      }));
    } catch (e) {
      console.error(e);
      message.error(`No se pudo cargar el detalle del cargue #${idEncabezado}`);
    } finally {
      setLoadingDetalle((prev) => ({ ...prev, [idEncabezado]: false }));
    }
  };

  const exportarExcelPorEncabezado = async (idEncabezado) => {
    try {
      const url = `${API_URL_GATEWAY_RPA}/gateway/correos/exportarExcelPorEncabezado?idEncabezado=${idEncabezado}`;
      const response = await fetch(url);
      if (!response.ok) throw new Error("Error al generar el Excel");
      
      const blob = await response.blob();
      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = `detalle_${idEncabezado}.xlsx`;
      link.click();
    } catch (e) {
      console.error(e);
      message.error("No se pudo descargar el Excel");
    }
  };

  // ====== PAUSAR / REANUDAR CARGUE ======
const pausarCargue = async (idEncabezado) => {
  try {
    await axios.post(
      `${API_URL_GATEWAY_RPA}/gateway/correos/encabezados/${idEncabezado}/pausar`
    );
    message.success("Cargue pausado");
    fetchEncabezados();
  } catch (e) {
    console.error(e);
    message.error("No se pudo pausar el cargue");
  }
};

const reanudarCargue = async (idEncabezado) => {
  try {
    await axios.post(
      `${API_URL_GATEWAY_RPA}/gateway/correos/encabezados/${idEncabezado}/reanudar`
    );
    message.success("Cargue reanudado");
    fetchEncabezados();
  } catch (e) {
    console.error(e);
    message.error("No se pudo reanudar el cargue");
  }
};


  // ============= EFFECTS =============
  useEffect(() => {
    fetchEncabezados();
    fetchDashboard();
  }, []);

  useEffect(() => {
    fetchDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rangeFechas, remitenteFiltro]);

  // ============= CONFIGURACIÓN DE COLUMNAS =============
  const encabezadosCols = [
    { 
      title: "Remitente", 
      dataIndex: "descripcion" 
    },
    { 
      title: "Usuario", 
      dataIndex: "idUsuario", 
      width: 120 
    },
    {
      title: "Total",
      dataIndex: "totalRegistros",
      width: 90,
      render: (v) => <Badge count={v} />,
    },
    {
      title: "Estado",
      dataIndex: "estado",
      width: 140,
      render: (estado) => {
        const colorMap = {
          FINALIZADO: "green",
          PAUSADO: "orange",
          default: "blue"
        };
        const color = colorMap[estado] || colorMap.default;
        return <Tag color={color}>{estado}</Tag>
      },
    },
    {
  title: "Acción",
  key: "accion",
  width: 140,
  render: (_, record) => {
    const { estado, idEncabezado } = record;

    if (estado === "FINALIZADO") {
      return <Tag color="green">Finalizado</Tag>;
    }

    if (estado === "PAUSADO") {
      return (
        <Button
          type="primary"
          size="small"
          onClick={() => reanudarCargue(idEncabezado)}
        >
          ▶ Reanudar
        </Button>
      );
    }

    return (
      <Button
        danger
        size="small"
        onClick={() => pausarCargue(idEncabezado)}
      >
        ⏸ Pausar
      </Button>
    );
  },
},

  ];

  const detalleCols = [
    { 
      title: "Destinatario", 
      dataIndex: "email_destinatario" 
    },
    { 
      title: "Asunto", 
      dataIndex: "asunto" 
    },
    {
      title: "Estado Envío",
      dataIndex: "estado_envio",
      width: 150,
      render: (estado) => {
        const colorMap = {
          ENVIADO: "green",
          ERROR: "red",
          default: "orange"
        };
        const color = colorMap[estado] || colorMap.default;
        return <Tag color={color}>{estado}</Tag>;
      },
    },
    { 
      title: "Registro", 
      dataIndex: "fecha_registro", 
      width: 180 
    },
    { 
      title: "Envío", 
      dataIndex: "fecha_envio", 
      width: 180 
    },
    { 
      title: "Error", 
      dataIndex: "error_detalle" 
    },
  ];

  // ============= COMPONENTES DE RENDERIZADO =============
  const renderHeader = () => (
    <div className="email-reporte-header">
      <Space>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>
          Volver
        </Button>
        <Title level={3} style={{ margin: 0 }}>
          Reporte de Correos
        </Title>
        <Button 
          icon={<ReloadOutlined />} 
          onClick={() => {
            fetchEncabezados();
            fetchDashboard();
          }}
        >
          Actualizar
        </Button>
      </Space>
    </div>
  );

  const renderFiltros = () => (
    <Card className="filters-card">
      <Space wrap>
        <span style={{ fontWeight: 600 }}>Filtros:</span>
        <RangePicker
          value={rangeFechas}
          onChange={setRangeFechas}
          allowClear
        />
             <Select
          allowClear
          style={{ width: 320 }}
          placeholder="Filtrar por remitente"
          value={remitenteFiltro}
          onChange={setRemitenteFiltro}
          options={(dashPorRemitente || [])
            .map(x => x.remitente)
            .filter(Boolean)
            .map(x => ({ label: x, value: x }))}
         />
        
      </Space>
    </Card>
  );

  const renderEstadisticasGenerales = () => (
    <Row gutter={[12, 12]}>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic title="Total" value={dashResumen?.total ?? 0} />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic title="Enviados" value={dashResumen?.enviados ?? 0} />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic title="Errores" value={dashResumen?.errores ?? 0} />
        </Card>
      </Col>
      <Col xs={24} sm={12} md={6}>
        <Card>
          <Statistic title="Pendientes" value={dashResumen?.pendientes ?? 0} />
        </Card>
      </Col>
    </Row>
  );

  const renderTasasYTiempos = () => (
    <Row gutter={[12, 12]} style={{ marginTop: 12 }}>
      <Col xs={24} md={12}>
        <Card title="Margen de error">
          <Space direction="vertical" style={{ width: "100%" }}>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>Tasa de error</span>
                <strong>{dashResumen?.pct_error ?? 0}%</strong>
              </div>
              <Progress percent={Number(dashResumen?.pct_error ?? 0)} />
            </div>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>Tasa de enviado</span>
                <strong>{dashResumen?.pct_enviado ?? 0}%</strong>
              </div>
              <Progress percent={Number(dashResumen?.pct_enviado ?? 0)} />
            </div>
          </Space>
        </Card>
      </Col>
      <Col xs={24} md={12}>
        <Card title="Tiempo de envío">
          <Row gutter={[12, 12]}>
            <Col xs={12}>
              <Statistic
                title="Promedio (seg)"
                value={dashResumen?.avg_segundos_envio ?? 0}
                precision={2}
              />
            </Col>
            <Col xs={12}>
              <Statistic
                title="P95 (seg)"
                value={dashResumen?.p95_segundos_envio ?? 0}
                precision={2}
              />
            </Col>
          </Row>
        </Card>
      </Col>
    </Row>
  );

  const renderTablasPorRemitenteyDia = () => (
    <Row gutter={[12, 12]}>
      <Col xs={24} lg={12}>
        <Card title="Por remitente (cuántos con cada correo)">
          <Table
            size="small"
            rowKey={(r) => r.remitente}
            dataSource={dashPorRemitente}
            pagination={{ pageSize: 8 }}
            columns={[
              { title: "Remitente", dataIndex: "remitente" },
              { title: "Total", dataIndex: "total", width: 90 },
              { title: "Enviados", dataIndex: "enviados", width: 90 },
              { title: "Errores", dataIndex: "errores", width: 90 },
              {
                title: "% error",
                dataIndex: "pct_error",
                width: 100,
                render: (v) => (
                  <Tag color={Number(v) > 5 ? "red" : "green"}>{v}%</Tag>
                ),
              },
            ]}
          />
        </Card>
      </Col>
      <Col xs={24} lg={12}>
        <Card title="Por día">
          <Table
            size="small"
            rowKey={(r) => r.dia}
            dataSource={dashPorDia}
            pagination={{ pageSize: 8 }}
            columns={[
              { title: "Día", dataIndex: "dia", width: 120 },
              { title: "Total", dataIndex: "total", width: 90 },
              { title: "Enviados", dataIndex: "enviados", width: 90 },
              { title: "Errores", dataIndex: "errores", width: 90 },
              { title: "Pendientes", dataIndex: "pendientes", width: 100 },
            ]}
          />
        </Card>
      </Col>
    </Row>
  );

  const renderTopErrores = () => (
    <Card title="Top errores (qué está fallando)">
      <Table
        size="small"
        rowKey={(r, idx) => `${idx}-${r.error}`}
        dataSource={dashTopErrores}
        pagination={{ pageSize: 10 }}
        columns={[
          { title: "Error", dataIndex: "error" },
          { title: "Cantidad", dataIndex: "cantidad", width: 120 },
        ]}
      />
    </Card>
  );

  const renderTablero = () => (
    <div>
      {renderFiltros()}
      <Spin spinning={dashLoading}>
        {renderEstadisticasGenerales()}
        {renderTasasYTiempos()}
        <Divider />
        {renderTablasPorRemitenteyDia()}
        <Divider />
        {renderTopErrores()}
      </Spin>
    </div>
  );

  const renderDetalleExpandido = (record) => {
    const id = record.idEncabezado;
    const isLoading = !!loadingDetalle[id];
    const data = detallesByEnc[id];

    if (isLoading) {
      return (
        <div style={{ padding: 16, textAlign: "center" }}>
          <Spin /> Cargando detalle...
        </div>
      );
    }

    if (!data) {
      return <div style={{ padding: 16 }}>Sin datos</div>;
    }

    return (
      <div>
        <div style={{ marginBottom: 8, textAlign: "right" }}>
          <Button
            className="download-btn"
            icon={<DownloadOutlined />}
            onClick={() => exportarExcelPorEncabezado(id)}
          >
            Descargar Excel
          </Button>
        </div>
        <Table
          columns={detalleCols}
          dataSource={data}
          rowKey="idDetalle"
          bordered
          size="small"
          pagination={false}
        />
      </div>
    );
  };

  const renderDetallePorCargue = () => (
    <Table
      columns={encabezadosCols}
      dataSource={encabezados}
      rowKey="idEncabezado"
      loading={encLoading}
      bordered
      size="middle"
      pagination={{ pageSize: 10 }}
      expandable={{
        expandedRowRender: renderDetalleExpandido,
        onExpand: (expanded, record) => {
          if (expanded) {
            const id = record.idEncabezado;
            if (!detallesByEnc[id]) {
              fetchDetalle(id);
            }
          }
        },
        rowExpandable: () => true,
      }}
    />
  );

  // ============= RENDER PRINCIPAL =============
  return (
    <div className="email-reporte-container">
      {renderHeader()}

      <Tabs
        defaultActiveKey="tablero"
        items={[
          {
            key: "tablero",
            label: "Tablero",
            children: renderTablero(),
          },
          {
            key: "detalle",
            label: "Detalle por cargue",
            children: renderDetallePorCargue(),
          },
        ]}
      />
    </div>
  );
}