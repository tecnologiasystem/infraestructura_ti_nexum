import React, { useState, useEffect } from "react";
import {
  Upload,
  Button,
  Table,
  message,
  Card,
  Modal,
  Input,
  Progress,
  Typography,
} from "antd";
import { UploadOutlined, ReloadOutlined } from "@ant-design/icons";
import { API_URL_GATEWAY } from "../../config";
import "./rpaVigencia.css";

const RpaVigencia = () => {
  const [excelData, setExcelData] = useState([]);
  const [cedulaSearch, setCedulaSearch] = useState("");
  const [automatizaciones, setAutomatizaciones] = useState([]);
  const [modalDetalleVisible, setModalDetalleVisible] = useState(false);
  const [detalleAutomatizacion, setDetalleAutomatizacion] = useState(null);
  const [detalleFiltrado, setDetalleFiltrado] = useState([]);
  const [subiendo, setSubiendo] = useState(false);
  const [pausedEncabezado, setPausedEncabezado] = useState(null);

  const cargarDatosDesdeBD = async () => {
    try {
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway-rpa/vigenciaJuridico_api/detalle/listar_agrupadoVigencia`
      );
      const { data } = await res.json();
      setExcelData(data);
    } catch (error) {
      console.error("Error exacto:", error.message);
      message.error("Error al cargar datos desde la base de datos");
    }
  };

  // Función para cargar automatizaciones con cálculo de progreso
  const cargarAutomatizaciones = async () => {
    try {
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway-rpa/Jurica/listarAutomatizacionesVigencia`
      );
      const data = await res.json();

      // Calcular el progreso para cada automatización
      const automationsWithProgress = await Promise.all(
        data.map(async (auto) => {
          const detalleRes = await fetch(
            `${API_URL_GATEWAY}/gateway-rpa/Jurica/listarAutomatizacionesDetalleVigencia?id_encabezado=${auto.idEncabezado}`
          );
          const detalleData = await detalleRes.json();

          // Calcular registros con datos completos (procesados)
          const procesados = detalleData.detalles.filter(
            (d) => d.vigencia || d.fechaConsulta
          ).length;

          const porcentaje = auto.totalRegistros
            ? Math.round((procesados / auto.totalRegistros) * 100)
            : 0;

          return {
            ...auto,
            procesados,
            porcentaje,
          };
        })
      );

      setAutomatizaciones(automationsWithProgress);
    } catch (err) {
      console.error("Error al cargar automatizaciones:", err);
      message.error("Error al cargar el progreso de automatizaciones");
    }
  };

  // Función para refrescar el progreso de una automatización específica
  const refrescarProgreso = async (idEncabezado) => {
    try {
      const detalleRes = await fetch(
        `${API_URL_GATEWAY}/gateway-rpa/Jurica/listarAutomatizacionesDetalleVigencia?id_encabezado=${idEncabezado}`
      );
      const detalleData = await detalleRes.json();

      // Calcular registros con datos completos (procesados)
      const procesados = detalleData.detalles.filter(
        (d) => d.vigencia || d.fechaConsulta
      ).length;

      const totalRegistros = detalleData.totalRegistros || 0;
      const porcentaje = totalRegistros
        ? Math.round((procesados / totalRegistros) * 100)
        : 0;

      if (porcentaje === 100) {
        const myId = localStorage.getItem("idUsuario");

        await fetch(
          `${API_URL_GATEWAY}/gateway-rpa/notificarFinalizacionVigencia`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              idEncabezado: idEncabezado,
            }),
          }
        )
          .then((res) => res.json())
          .then((data) => {
            if (data.success) {
              message.success("✅ Correo de finalización enviado");
            } else {
              message.warning("⚠️ No se pudo enviar el correo");
            }
          })
          .catch((err) => {
            console.error("Error al enviar notificación:", err);
            message.error("Error al notificar finalización");
          });
      }

      setAutomatizaciones((prev) =>
        prev.map((auto) =>
          auto.idEncabezado === idEncabezado
            ? {
                ...auto,
                procesados,
                totalRegistros,
                porcentaje,
              }
            : auto
        )
      );
      message.success("Progreso actualizado");
    } catch (err) {
      console.error("Error al refrescar progreso:", err);
      message.error("Error al actualizar progreso");
    }
  };

  const verDetalleAutomatizacion = async (idEncabezado) => {
    try {
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway-rpa/Jurica/listarAutomatizacionesDetalleVigencia?id_encabezado=${idEncabezado}`
      );
      const data = await res.json();

      const detallesProcesados = data.detalles
        .filter((d) => d.vigencia || d.fechaConsulta)
        .filter((d) => d.vigencia?.toLowerCase() !== "pausado");
      console.log("Detalles recibidos del backend:", data.detalles);

      // Agrupar por cédula y numerar cada item dentro del grupo
      const agrupado = Object.entries(
        detallesProcesados.reduce((acc, item) => {
          const cedula = item.cedula || item.CC || item.cc || "SIN_CEDULA";
          console.log("Agrupando cedula:", cedula, "item:", item);
          if (!acc[cedula]) acc[cedula] = [];
          acc[cedula].push(item);
          return acc;
        }, {})
      ).map(([cedula, detalles]) => ({
        cedula,
        detalles: detalles.map((item, index) => ({
          ...item,
          numItem: index + 1,
        })),
      }));

      setDetalleAutomatizacion(data);
      setDetalleFiltrado(agrupado);
      setModalDetalleVisible(true);
    } catch (err) {
      console.error("Error al cargar detalle de automatización:", err);
      message.error("Error al obtener detalle");
    }
  };

  useEffect(() => {
    cargarDatosDesdeBD();
    cargarAutomatizaciones();
  }, []);

  const obtenerPorcentaje = (estado) => {
    const match = estado.match(/\((\d+)%\)/);
    return match ? parseInt(match[1]) : estado === "Finalizada" ? 100 : 0;
  };

  const detalleFiltradoPorCedula = (detalleFiltrado || []).filter(
    (registro) => {
      return (
        typeof registro?.cedula === "string" &&
        registro.cedula.includes(cedulaSearch.trim())
      );
    }
  );

  const handlePause = async (id) => {
    await fetch(
      `${API_URL_GATEWAY}/gateway-rpa/vigenciaJuridico_api/pausar/${id}`,
      { method: "POST" }
    );
    setPausedEncabezado(id);
    cargarAutomatizaciones();
    message.success("Encabezado pausado");
  };

  const handleResume = async (id) => {
    await fetch(
      `${API_URL_GATEWAY}/gateway-rpa/vigenciaJuridico_api/reanudar/${id}`,
      { method: "POST" }
    );
    setPausedEncabezado(null);
    cargarAutomatizaciones();
    message.success("Encabezado reanudado");
  };

  return (
    <div className="rpa-vigilancia-container">
      <Card className="rpa-main-card">
        {/* Header */}
        <div className="rpa-header">
          <h1 className="excel-tittle">
            RPA Verificación de Vigencia de Cédulas
          </h1>
          <p className="excel-description">
            Automatización del proceso de consulta de vigencia de cédulas.
          </p>
        </div>

        {/* Acciones */}
        <div className="rpa-actions">
          <div className="rpa-button-group">
            <Button
              className="rpa-btn-primary"
              onClick={() =>
                window.open(
                  `${API_URL_GATEWAY}/gateway-rpa/excel/plantillaVigencia`
                )
              }
            >
              Descargar plantilla
            </Button>

            <Upload
              customRequest={async ({ file, onSuccess, onError }) => {
                try {
                  setSubiendo(true);
                  const myId = localStorage.getItem("idUsuario");

                  const formData = new FormData();
                  formData.append("file", file);
                  formData.append("idUsuario", myId);

                  const res = await fetch(
                    `${API_URL_GATEWAY}/gateway-rpa/excel/guardarVigencia`,
                    {
                      method: "POST",
                      body: formData,
                    }
                  );

                  let data;
                  try {
                    data = await res.json();
                  } catch {
                    data = null;
                  }

                  if (res.ok) {
                    message.success("Archivo subido correctamente");
                    cargarDatosDesdeBD();
                    onSuccess(data);
                  } else {
                    console.error("Respuesta del servidor:", data);
                    message.error("Error al subir el archivo");
                    onError(data || new Error("Error desconocido"));
                  }
                } catch (error) {
                  console.error("Error al subir:", error);
                  message.error("Error al subir el archivo");
                  onError(error);
                } finally {
                  setSubiendo(false);
                }
              }}
              accept=".xlsx,.xls"
              showUploadList={false}
              multiple={false}
            >
              <Button
                className="rpa-btn-secondary"
                icon={<UploadOutlined />}
                loading={subiendo}
              >
                Subir archivo Excel
              </Button>
            </Upload>
          </div>
        </div>

        {/* Progreso */}
        {automatizaciones.length > 0 && (
          <div className="rpa-progress-section">
            <div className="progress-section-header">
              <Typography.Title level={3} className="progress-title">
                Progreso de Automatizaciones
              </Typography.Title>
            </div>

            <Table
              className="rpa-table"
              dataSource={automatizaciones.map((a, i) => ({
                key: i,
                ...a,
                procesados: a.procesados || 0,
                porcentaje: a.porcentaje || 0,
              }))}
              pagination={{ pageSize: 5 }}
              columns={[
                {
                  title: "Automatización",
                  dataIndex: "automatizacion",
                  key: "automatizacion",
                },
                {
                  title: "Cargado Por",
                  dataIndex: "nombreUsuario",
                  key: "nombreUsuario",
                },
                {
                  title: "Fecha de cargue",
                  dataIndex: "fechaCargue",
                  key: "fechaCargue",
                  render: (text) => {
                    const fecha = new Date(text);
                    return fecha.toLocaleString("es-CO", {
                      year: "numeric",
                      month: "2-digit",
                      day: "2-digit",
                      hour: "2-digit",
                      minute: "2-digit",
                      second: "2-digit",
                    });
                  },
                },
                {
                  title: "Progreso",
                  key: "progreso",
                  width: 200,
                  render: (_, record) => (
                    <Progress
                      className="rpa-progress-bar"
                      percent={record.porcentaje}
                      status={record.porcentaje === 100 ? "success" : "active"}
                    />
                  ),
                },
                {
                  title: "Completados",
                  key: "registros",
                  width: 260,
                  render: (_, record) => (
                    <div className="rpa-refresh-row">
                      <span className="rpa-metric">
                        {record.procesados} / {record.totalRegistros}
                      </span>
                      <Button
                        className="rpa-action-btn refresh"
                        icon={<ReloadOutlined />}
                        size="small"
                        type="default"
                        onClick={() => refrescarProgreso(record.idEncabezado)}
                      >
                        Refrescar
                      </Button>
                    </div>
                  ),
                },
                {
                  title: "",
                  key: "control",
                  render: (_, record) =>
                    record.estado !== "Pausado" ? (
                      <Button
                        className="rpa-action-btn pause"
                        danger
                        onClick={() => handlePause(record.idEncabezado)}
                      >
                        Pausar
                      </Button>
                    ) : (
                      <Button
                        className="rpa-action-btn resume"
                        type="primary"
                        onClick={() => handleResume(record.idEncabezado)}
                      >
                        Reanudar
                      </Button>
                    ),
                },
                {
                  title: "Acción",
                  key: "accion",
                  render: (_, record) => (
                    <Button
                      className="rpa-action-btn detail"
                      type="link"
                      onClick={() =>
                        verDetalleAutomatizacion(record.idEncabezado)
                      }
                    >
                      Ver Detalle
                    </Button>
                  ),
                },
              ]}
              size="small"
            />
          </div>
        )}
      </Card>

      {/* Modal Detalle */}
      <Modal
        className="rpa-modal"
        title={`Detalle automatización ${
          detalleAutomatizacion?.automatizacion || ""
        }`}
        visible={modalDetalleVisible}
        onCancel={() => setModalDetalleVisible(false)}
        footer={null}
        width={1000}
      >
        <div className="rpa-search-container">
          <Input.Search
            className="rpa-search"
            placeholder="Buscar por cédula..."
            allowClear
            value={cedulaSearch}
            onChange={(e) => setCedulaSearch(e.target.value)}
            style={{ width: 300 }}
            enterButton="Buscar"
          />
          {detalleAutomatizacion?.idEncabezado && (
            <Button
              className="rpa-btn-primary"
              onClick={() => {
                window.open(
                  `${API_URL_GATEWAY}/gateway-rpa/excel/exportar_resultadosVigencia?id_encabezado=${detalleAutomatizacion.idEncabezado}`
                );
              }}
            >
              Descargar Excel
            </Button>
          )}
        </div>

        {detalleFiltradoPorCedula.length > 0 ? (
          <Table
            className="rpa-table"
            rowKey="cedula"
            dataSource={detalleFiltradoPorCedula}
            columns={[{ title: "Cédula", dataIndex: "cedula", key: "cedula" }]}
            expandable={{
              expandedRowRender: (record) => (
                <Table
                  className="rpa-table"
                  rowKey={(r, i) => `${r.idDetalle || i}-${record.cedula}`}
                  dataSource={record.detalles}
                  columns={[
                    {
                      title: "Vigencia",
                      dataIndex: "vigencia",
                      key: "vigencia",
                    },
                    {
                      title: "Fecha Consulta",
                      dataIndex: "fechaConsulta",
                      key: "fechaConsulta",
                    },
                  ]}
                  pagination={false}
                  size="small"
                />
              ),
              expandRowByClick: true,
            }}
            pagination={{ pageSize: 8 }}
            size="small"
            scroll={{ x: "max-content" }}
          />
        ) : (
          <p>No hay datos disponibles para esta automatización.</p>
        )}
      </Modal>
    </div>
  );
};

export default RpaVigencia;
