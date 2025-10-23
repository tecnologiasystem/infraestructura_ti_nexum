import React, { useEffect, useState } from "react";
import {
  Card,
  Typography,
  Spin,
  Tabs,
  Table,
  Button,
  Modal,
  Pagination,
  Input,
  Select,
  Progress,
} from "antd";
import axios from "axios";
import dayjs from "dayjs";
import { API_URL_GATEWAY } from "../../config";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  CartesianGrid,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

const { Title } = Typography;
const { TabPane } = Tabs;
const { Search } = Input;

export default function ControlRpa() {
  const [loading, setLoading] = useState(false);
  const [encabezados, setEncabezados] = useState({});
  const [currentOrigen, setCurrentOrigen] = useState("SUPER NOTARIADO");
  const [vista, setVista] = useState("encabezados");
  const [dashboard, setDashboard] = useState([]);
  const [loadingDashboard, setLoadingDashboard] = useState(false);
  const [loadingExcel, setLoadingExcel] = useState(false);
  const [dataView, setDataView] = useState("tabla");
  const [tokensRunt, setTokensRunt] = useState({});
  const [vigenciaResumen, setVigenciaResumen] = useState({});
  const [vigenciaLoading, setVigenciaLoading] = useState(false);

  const fmtDuracion = (min) => {
    if (!isFinite(min)) return "-";
    const tot = Math.max(min, 0);
    if (tot < 60) return `${tot.toFixed(1)} min`;
    const h = Math.floor(tot / 60);
    const m = Math.round(tot % 60);
    if (h < 24) return `${h} h ${m} min`;
    const d = Math.floor(h / 24);
    const hr = h % 24;
    return `${d} d ${hr} h ${m} min`;
  };

  const [modal, setModal] = useState({
    visible: false,
    origen: null,
    idEnc: null,
    rows: [],
    total: 0,
    page: 1,
    pageSize: 8,
    loading: false,
    filterCC: "",
  });

  const [modalGrafica, setModalGrafica] = useState({
    visible: false,
    item: null,
  });

const openGrafica = (item) => {
  if (!dashboard || dashboard.length === 0) {
    fetchDashboard();
  }
  setModalGrafica({ visible: true, item });

  if (currentOrigen === "VIGENCIA" && !vigenciaResumen[item.idEncabezado]) {
    fetchVigenciaResumen(item.idEncabezado);
  }
};


  const closeGrafica = () => {
    setModalGrafica({ visible: false, item: null });
  };

  const COLORS = ["#0088FE", "#FF8042"];

  const fetchVigenciaResumen = async (idEncabezado) => {
  try {
    setVigenciaLoading(true);
    const { data } = await axios.get(
      `${API_URL_GATEWAY}/rpa/encabezados/${currentOrigen}/${idEncabezado}/resumen`
    );
    setVigenciaResumen(prev => ({
      ...prev,
      [idEncabezado]: {
        vigenteVivo: Number(data?.vigenteVivo) || 0,
        canceladaMuerte: Number(data?.canceladaMuerte) || 0,
      }
    }));
  } catch (e) {
    console.error("Error obteniendo resumen de VIGENCIA:", e);
    setVigenciaResumen(prev => ({
      ...prev,
      [idEncabezado]: { vigenteVivo: 0, canceladaMuerte: 0 }
    }));
  } finally {
    setVigenciaLoading(false);
  }
};

const getPieChartData = (item) => {
  if (currentOrigen === "VIGENCIA") {
    const res = vigenciaResumen[item.idEncabezado];
    const vigenteVivo = res?.vigenteVivo ?? 0;
    const canceladaMuerte = res?.canceladaMuerte ?? 0;
    const total = vigenteVivo + canceladaMuerte;

    return [
      { name: "Vigente (Vivo)", value: total > 0 ? vigenteVivo : 0 },
      { name: "Cancelada por Muerte", value: total > 0 ? canceladaMuerte : 0 },
    ];
  }

  const irrelevantes = item.totalRegistros - item.totalRelevantes;
  return [
    { name: "Datos", value: item.totalRelevantes },
    { name: "Sin Datos", value: irrelevantes },
  ];
};

  const [modalTokens, setModalTokens] = useState({
    visible: false,
    item: null,
  });

  const openModalTokens = (item) => {
    setModalTokens({ visible: true, item });
  };

  const closeModalTokens = () => {
    setModalTokens({ visible: false, item: null });
  };

  const rpAs = [
    "SUPER NOTARIADO",
    "RUNT",
    "RUES",
    "SIMIT",
    "FAMISANAR",
    "NUEVA EPS",
    "VIGILANCIA",
    "WHATSAPP",
    "CAMARACOMERCIO",
    "VIGENCIA",
  ];

  const columnasEnc = [
    { title: "ID Encabezado", dataIndex: "idEncabezado", key: "idEncabezado" },
    {
      title: "Automatización",
      dataIndex: "automatizacion",
      key: "automatizacion",
    },
    { title: "Usuario", dataIndex: "nombreUsuario", key: "nombreUsuario" },

    {
      title: "Fecha Cargue",
      dataIndex: "fechaCargue",
      key: "fechaCargue",
      render: (ts) => dayjs(ts).format("DD/MM/YYYY HH:mm:ss"),
    },
    {
      title: "Total Registros",
      dataIndex: "totalRegistros",
      key: "totalRegistros",
    },
    { title: "Estado", dataIndex: "estado", key: "estado" },
    {
      title: "Fecha Pausa",
      dataIndex: "fechaPausa",
      key: "fechaPausa",
      render: (ts) => (ts ? dayjs(ts).format("DD/MM/YYYY HH:mm:ss") : "-"),
    },
    {
      title: "Fecha Finalización",
      dataIndex: "fechaFinalizacion",
      key: "fechaFinalizacion",
      render: (ts) => (ts ? dayjs(ts).format("DD/MM/YYYY HH:mm:ss") : "-"),
    },
    {
      title: "",
      key: "acciones",
      render: (_, rec) => (
        <div style={{ display: "flex", gap: 8 }}>
          <Button onClick={() => openModal(rec.idEncabezado)}>
            Ver Detalles
          </Button>
          <Button onClick={() => openGrafica(rec)}>Ver Gráfica</Button>
          {currentOrigen === "RUNT" && (
            <Button onClick={() => openModalTokens(rec)}>Tokens</Button>
          )}
        </div>
      ),
    },
  ];

  const columnasCaidas = [
    { title: "ID Encabezado", dataIndex: "idEncabezado", key: "idEncabezado" },
    {
      title: "Automatización",
      dataIndex: "automatizacion",
      key: "automatizacion",
    },
    { title: "Usuario", dataIndex: "nombreUsuario", key: "nombreUsuario" },
    {
      title: "Fecha Cargue",
      dataIndex: "fechaCargue",
      key: "fechaCargue",
      render: (ts) => dayjs(ts).format("DD/MM/YYYY HH:mm:ss"),
    },
    {
      title: "Total Registros",
      dataIndex: "totalRegistros",
      key: "totalRegistros",
    },
    {
      title: "Fecha Caída",
      dataIndex: "fechaCaida",
      key: "fechaCaida",
      render: (ts) => dayjs(ts).format("DD/MM/YYYY HH:mm:ss"),
    },
    {
      title: "Fecha Reactivación",
      dataIndex: "fechaReactivacion",
      key: "fechaReactivacion",
      render: (ts) => (ts ? dayjs(ts).format("DD/MM/YYYY HH:mm:ss") : "-"),
    },
    {
      title: "Tiempo Inactivo",
      dataIndex: "tiempoInactivo",
      key: "tiempoInactivo",
      render: (s) => (s ? `${Math.round(s / 60)} min` : "-"),
    },
    { title: "Mensaje", dataIndex: "mensaje", key: "mensaje" },
  ];

  const descargarExcelTodoOrigen = async (origen) => {
    setLoadingExcel(true);
    try {
      const url = `${API_URL_GATEWAY}/gateway/rpa/${origen}/detalles/descargar_todos`;
      const response = await axios.get(url, { responseType: "blob" });

      const blob = new Blob([response.data], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = downloadUrl;
      link.download = `${origen}_detalles_completos.xlsx`;
      link.click();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (e) {
      console.error("Error al descargar el Excel de todos los detalles:", e);
    } finally {
      setLoadingExcel(false);
    }
  };

  const fetchEncabezados = async (origen) => {
    setLoading(true);
    try {
      const { data } = await axios.get(
        `${API_URL_GATEWAY}/gateway/rpa/encabezados`,
        { params: { origen } }
      );
      setEncabezados((prev) => ({ ...prev, [origen]: data }));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const fetchDashboard = async () => {
    setLoadingDashboard(true);
    try {
      const { data } = await axios.get(
        `${API_URL_GATEWAY}/gateway/rpa/dashboard`
      );
      setDashboard(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingDashboard(false);
    }
  };

  const openModal = (idEncabezado) => {
    setModal((m) => ({
      ...m,
      visible: true,
      origen: currentOrigen,
      idEnc: idEncabezado,
      page: 1,
      filterCC: "",
    }));
    fetchDetalles(currentOrigen, idEncabezado, 1, "");
  };

  const closeModal = () => {
    setModal({
      visible: false,
      origen: null,
      idEnc: null,
      rows: [],
      total: 0,
      page: 1,
      pageSize: 8,
      loading: false,
      filterCC: "",
    });
  };

  const fetchTokensRunt = async () => {
    try {
      const { data } = await axios.get(
        `${API_URL_GATEWAY}/parametro/tokens-usados`
      );
      console.log("Respuesta tokens:", data);

      const tokensMap = {};
      data.forEach((row) => {
        tokensMap[row.idEncabezado] = row.tokensGastados;
      });
      setTokensRunt(tokensMap);
    } catch (e) {
      console.error("Error al obtener tokens:", e);
    }
  };

  const getGraficaTokensRunt = () => {
    const rows = encabezados["RUNT"] || [];
    return rows
      .filter((r) => tokensRunt[r.idEncabezado])
      .map((r) => ({
        idEncabezado: r.idEncabezado,
        tokensGastados: tokensRunt[r.idEncabezado],
      }));
  };
  const getTotalTokensGastadosRunt = () => {
    return Object.values(tokensRunt).reduce((total, val) => total + val, 0);
  };

  const getGraficaTiempos = () => {
    const caidasMap = dashboard.reduce((acc, c) => {
      const id = c.idEncabezado;
      acc[id] = (acc[id] || 0) + (c.tiempoInactivo || 0);
      return acc;
    }, {});

    return (encabezados[currentOrigen] || [])
      .map((e) => {
        if (!e.fechaFinalizacion) return null;
        const inicio = dayjs(e.fechaCargue);
        const fin = dayjs(e.fechaFinalizacion);
        const totalSegundos = fin.diff(inicio, "second");
        const inactivo = caidasMap[e.idEncabezado] || 0;
        const activo = totalSegundos - inactivo;
        return {
          idEncabezado: e.idEncabezado,
          tiempoActivoMin: Math.max(activo / 60, 0),
          tiempoInactivoMin: inactivo / 60,
        };
      })
      .filter(Boolean);
  };
  const getTiemposItem = (item) => {
    if (!item || !item.fechaCargue || !item.fechaFinalizacion) return [];

    const inicioProc = dayjs(item.fechaCargue);
    const finProc = dayjs(item.fechaFinalizacion);

    const totalMin = Math.max(finProc.diff(inicioProc, "minute", true), 0);

    const inactivoMin = dashboard
      .filter((d) => d.idEncabezado === item.idEncabezado)
      .reduce((acc, d) => {
        if (!d.fechaCaida) return acc;
        const caida = dayjs(d.fechaCaida);
        const reactiv = d.fechaReactivacion
          ? dayjs(d.fechaReactivacion)
          : finProc;

        const ini = caida.isAfter(inicioProc) ? caida : inicioProc;
        const fin = reactiv.isBefore(finProc) ? reactiv : finProc;

        if (fin.isAfter(ini)) {
          return acc + Math.max(fin.diff(ini, "minute", true), 0);
        }
        return acc;
      }, 0);

    const inactivoMinValid = Math.min(inactivoMin, totalMin);

    return [
      {
        idEncabezado: item.idEncabezado,
        tiempoTotalMin: totalMin,
        tiempoInactivoMin: inactivoMinValid,
      },
    ];
  };

  const fetchDetalles = async (origen, idEnc, page, cc) => {
    setModal((m) => ({ ...m, loading: true }));

    try {
      let data;
      if (cc && cc.length >= 4) {
        const { data: result } = await axios.get(
          `${API_URL_GATEWAY}/gateway/rpa/encabezados/${origen}/${idEnc}/detalles/buscar_por_cedula`,
          { params: { cedula: cc } }
        );
        data = result;
      } else {
        const offset = (page - 1) * modal.pageSize;
        const response = await axios.get(
          `${API_URL_GATEWAY}/gateway/rpa/encabezados/${origen}/${idEnc}/detalles`,
          { params: { offset, limit: modal.pageSize, cc } }
        );
        data = response.data;
      }

      setModal((m) => ({
        ...m,
        rows: Array.isArray(data.rows) ? data.rows : [],
        total: typeof data.total === "number" ? data.total : 0,
        page,
        filterCC: cc,
      }));
    } catch (e) {
      console.error(e);
    } finally {
      setModal((m) => ({ ...m, loading: false }));
    }
  };

  useEffect(() => {
    if (vista === "encabezados") {
      fetchEncabezados(currentOrigen);
      if (currentOrigen === "RUNT") fetchTokensRunt();
    } else {
      fetchDashboard();
    }
  }, [vista, currentOrigen]);

  const contarCaidasPorEncabezado = (data) => {
    const agrupado = {};

    data.forEach((reg) => {
      const key = `${reg.automatizacion}__${reg.idEncabezado}`;
      if (!agrupado[key]) {
        agrupado[key] = {
          idEncabezado: reg.idEncabezado,
          automatizacion: reg.automatizacion,
          nombreUsuario: reg.nombreUsuario,
          estado: reg.estado || "-",
          totalCaidas: 0,
          historial: [],
        };
      }
      agrupado[key].totalCaidas += 1;
      agrupado[key].historial.push(reg);
    });

    return Object.values(agrupado);
  };

  const rawRows = encabezados[currentOrigen] || [];

  const chartData = rawRows.map((item) => ({
    ...item,
    name: item.automatizacion,
    registros: item.totalRegistros,
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload || !payload.length) return null;

    const data = payload[0].payload;

    return (
      <div
        style={{
          background: "#fff",
          border: "1px solid #ccc",
          padding: 10,
          maxWidth: 250,
        }}
      >
        <p style={{ margin: 0, fontWeight: "bold" }}>{data.name}</p>
        <hr style={{ margin: "4px 0" }} />

        {Object.entries(data).map(([key, val]) => (
          <p key={key} style={{ margin: "2px 0" }}>
            <strong>
              {key
                .replace(/([A-Z])/g, " $1")
                .replace(/^./, (s) => s.toUpperCase())}
              :
            </strong>{" "}
            {String(val)}
          </p>
        ))}
      </div>
    );
  };

  return (
    <Card style={{ margin: 3 }}>
      <h1 className="excel-tittle">Control RPAs</h1>

      <Tabs activeKey={vista} onChange={(v) => setVista(v)}>
        <TabPane tab="Datos por Automatización" key="encabezados" />
        <TabPane tab="Registro de Caídas" key="caidas" />
      </Tabs>

      {vista === "encabezados" ? (
        <>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 16,
            }}
          >
            <Select
              value={currentOrigen}
              onChange={(origen) => {
                setCurrentOrigen(origen);
                if (!encabezados[origen]) fetchEncabezados(origen);
              }}
              options={rpAs.map((origen) => ({ label: origen, value: origen }))}
              style={{ width: 200 }}
            />

            <Button
              type="primary"
              onClick={() => descargarExcelTodoOrigen(currentOrigen)}
            >
              Descargar Todo {currentOrigen}
            </Button>
          </div>

          {loading ? (
            <Spin />
          ) : dataView === "tabla" ? (
            <Table
              dataSource={encabezados[currentOrigen] || []}
              columns={columnasEnc}
              rowKey="idEncabezado"
              pagination={{ pageSize: 8 }}
              scroll={{ x: 800 }}
            />
          ) : currentOrigen === "RUNT" ? (
            <>
            
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  data={getGraficaTokensRunt()}
                  layout="vertical"
                  margin={{ top: 20, right: 30, left: 80, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="idEncabezado" type="category" />
                  <RechartsTooltip />
                  <Bar
                    dataKey="tokensGastados"
                    name="Tokens Usados"
                    fill="#8884d8"
                  />
                </BarChart>
              </ResponsiveContainer>

              <div style={{ textAlign: "center", marginTop: 20, fontSize: 16 }}>
                <strong>Total Tokens Usados:</strong>{" "}
                {getTotalTokensGastadosRunt().toLocaleString(undefined, {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </div>
            </>
          ) : (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart
                data={chartData}
                margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <RechartsTooltip content={<CustomTooltip />} />
                <Bar dataKey="registros" name="Total Registros" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </>
      ) : (
        <Table
          dataSource={contarCaidasPorEncabezado(dashboard)}
          columns={[
            {
              title: "ID Encabezado",
              dataIndex: "idEncabezado",
              key: "idEncabezado",
            },
            {
              title: "Automatización",
              dataIndex: "automatizacion",
              key: "automatizacion",
            },
            {
              title: "Usuario",
              dataIndex: "nombreUsuario",
              key: "nombreUsuario",
            },
            {
              title: "Total Caídas",
              dataIndex: "totalCaidas",
              key: "totalCaidas",
            },
          ]}
          expandable={{
            expandedRowRender: (record) => (
              <Table
                columns={columnasCaidas}
                dataSource={record.historial}
                rowKey={(r, i) => `${record.idEncabezado}-${i}`}
                pagination={false}
                size="small"
              />
            ),
            rowExpandable: (record) => record.historial.length > 0,
          }}
          rowKey="idEncabezado"
          pagination={{ pageSize: 5 }}
          style={{ marginTop: 20 }}
          scroll={{ x: 1000 }}
        />
      )}

      <Modal
        title={`Detalles de ${modal.origen} #${modal.idEnc}`}
        visible={modal.visible}
        onCancel={closeModal}
        footer={null}
        width="80%"
        destroyOnClose
      >
        <Search
          placeholder="Buscar por cédula"
          allowClear
          enterButton="Buscar"
          style={{ marginBottom: 16, width: 300 }}
          value={modal.filterCC}
          onChange={(e) =>
            setModal((prev) => ({ ...prev, filterCC: e.target.value }))
          }
          onSearch={(q) =>
            fetchDetalles(modal.origen, modal.idEnc, 1, q || modal.filterCC)
          }
        />

        {modal.loading ? (
          <Spin />
        ) : (
          <>
            <Table
              dataSource={modal.rows}
              columns={
                modal.rows.length
                  ? Object.keys(modal.rows[0]).map((col) => ({
                      title: col,
                      dataIndex: col,
                      key: col,
                    }))
                  : []
              }
              rowKey={(r, i) => i}
              pagination={false}
              scroll={{ x: 1000 }}
            />
            <Pagination
              current={modal.page}
              pageSize={modal.pageSize}
              total={modal.total}
              onChange={(p) =>
                fetchDetalles(modal.origen, modal.idEnc, p, modal.filterCC)
              }
              style={{ marginTop: 16, textAlign: "right" }}
            />
          </>
        )}
      </Modal>

      <Modal
        title={`Distribución de registros - ${modalGrafica.item?.automatizacion}`}
        visible={modalGrafica.visible}
        onCancel={closeGrafica}
        footer={null}
        width={800}
      >
        {modalGrafica.item && (
          <div
            style={{ display: "grid", gridTemplateColumns: "1fr", rowGap: 24 }}
          >
            <div>
              <ResponsiveContainer width="100%" height={320}>
                <PieChart>
                  <Pie
                    data={getPieChartData(modalGrafica.item)}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={110}
                    label={({ name, percent, value }) =>
                      `${name}: ${value} (${(percent * 100).toFixed(1)}%)`
                    }
                  >
                    {getPieChartData(modalGrafica.item).map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>

              <div
                style={{
                  textAlign: "center",
                  marginTop: 10,
                  color: "rgb(105,105,105)",
                }}
              >
                <strong>Total registros:</strong>{" "}
                {modalGrafica.item?.totalRegistros?.toLocaleString()}
              </div>
            </div>
            <div>
              {(() => {
                const d = getTiemposItem(modalGrafica.item)[0];
                if (!d) return null;

                const pctInactivo = Math.min(
                  Math.max(
                    (d.tiempoInactivoMin / (d.tiempoTotalMin || 1)) * 100,
                    0
                  ),
                  100
                ).toFixed(1);

                return (
                  <div style={{ textAlign: "center" }}>
                    <div
                      style={{
                        marginBottom: 15,
                        maxWidth: 520,
                        width: "90%",
                        marginInline: "auto",
                      }}
                    >
                      <Progress
                        percent={pctInactivo}
                        status="active"
                        strokeColor={{ "0%": "#ff6666", "100%": "#cc0000" }}
                        trailColor="#82ca9d"
                        strokeWidth={20}
                        showInfo={false}
                      />
                    </div>
                    <div>
                      <strong>Activo:</strong>{" "}
                      {fmtDuracion(d.tiempoTotalMin - d.tiempoInactivoMin)}{" "}
                      &nbsp; | &nbsp;
                      <strong>Inactivo:</strong>{" "}
                      {fmtDuracion(d.tiempoInactivoMin)} &nbsp; | &nbsp;
                      <strong>Total:</strong> {fmtDuracion(d.tiempoTotalMin)}
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>
        )}
      </Modal>

      <Modal
        title={`Tokens usados - Encabezado #${modalTokens.item?.idEncabezado}`}
        visible={modalTokens.visible}
        onCancel={closeModalTokens}
        footer={null}
        width={500}
      >
        {modalTokens.item && (
          <div style={{ textAlign: "center", padding: "20px" }}>
            <div style={{ fontSize: 16, marginBottom: 10 }}>
              <div>
                <strong>Total de registros:</strong>{" "}
                {modalTokens.item.totalRegistros}
              </div>
              <div>
                <strong>Tokens por consulta:</strong> 2.01
              </div>
            </div>

            <div
              style={{
                fontSize: "60px",
                fontWeight: "bold",
                color: "#4a4a4a",
                marginTop: 30,
              }}
            >
              {tokensRunt[modalTokens.item.idEncabezado]?.toLocaleString(
                undefined,
                {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                }
              ) ?? "0.00"}
            </div>

            <div style={{ marginTop: 10, fontSize: 18, color: "#888" }}>
              tokens usados
            </div>
          </div>
        )}
      </Modal>

      {loadingExcel && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            backgroundColor: "rgba(255,255,255,0.7)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 9999,
          }}
        >
          <div style={{ textAlign: "center" }}>
            <Spin size="large" />
            <div style={{ marginTop: 20, fontSize: 16, fontWeight: "bold" }}>
              Generando y descargando Excel...
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
