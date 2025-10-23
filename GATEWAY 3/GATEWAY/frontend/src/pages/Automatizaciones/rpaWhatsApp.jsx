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
import "./rpaWhatsApp.css";

const RpaWhatsApp = () => {
  const [excelData, setExcelData] = useState([]);
  const [numeroSearch, setNumeroSearch] = useState("");
  const [automatizaciones, setAutomatizaciones] = useState([]);
  const [modalDetalleVisible, setModalDetalleVisible] = useState(false);
  const [detalleAutomatizacion, setDetalleAutomatizacion] = useState(null);
  const [detalleFiltrado, setDetalleFiltrado] = useState([]);
  const [subiendo, setSubiendo] = useState(false);
  const [pausedEncabezado, setPausedEncabezado] = useState(null);

  // ========= Data base =========
  const cargarDatosDesdeBD = async () => {
    try {
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway/WhatsApp_api/detalle/listar_agrupadoWhatsApp`
      );
      const { data } = await res.json();
      setExcelData(data);
    } catch (error) {
      console.error("Error exacto:", error.message);
      message.error("Error al cargar datos desde la base de datos");
    }
  };

  // ========= Encabezados / progreso =========
  const cargarAutomatizaciones = async () => {
    try {
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway/WhatsApp/listarAutomatizacionesWhatsApp`
      );
      const data = await res.json();

      const automationsWithProgress = (data || []).map((auto) => {
        const procesados = auto.detallesIngresados || 0;
        const total = auto.totalRegistros || 0;
        const porcentaje = total ? Math.round((procesados / total) * 100) : 0;
        return { ...auto, procesados, totalRegistros: total, porcentaje };
      });

      setAutomatizaciones(automationsWithProgress);
    } catch (err) {
      console.error("Error al cargar automatizaciones:", err);
      message.error("Error al cargar el progreso de automatizaciones");
    }
  };

  const refrescarProgreso = async (idEncabezado) => {
    try {
      const detalleRes = await fetch(
        `${API_URL_GATEWAY}/gateway/WhatsApp/listarAutomatizacionesDetalleWhatsApp?id_encabezado=${idEncabezado}`
      );
      const detalleData = await detalleRes.json();

      const procesados = (detalleData?.detalles || []).filter(
        (d) => d.tiene_whatsApp && d.tiene_whatsApp.trim() !== ""
      ).length;

      const totalRegistros = detalleData.totalRegistros || 0;
      const porcentaje = totalRegistros
        ? Math.round((procesados / totalRegistros) * 100)
        : 0;

      if (porcentaje === 100) {
        try {
          const resp = await fetch(
            `${API_URL_GATEWAY}/gateway/notificarFinalizacionWhatsApp`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ idEncabezado }),
            }
          ).then((r) => r.json());

          resp?.success
            ? message.success("✅ Correo de finalización enviado")
            : message.warning("⚠️ No se pudo enviar el correo");
        } catch (e) {
          console.error("Error al notificar finalización:", e);
          message.error("Error al notificar finalización");
        }
      }

      setAutomatizaciones((prev) =>
        prev.map((auto) =>
          auto.idEncabezado === idEncabezado
            ? { ...auto, procesados, totalRegistros, porcentaje }
            : auto
        )
      );

      message.success("Progreso actualizado");
    } catch (err) {
      console.error("Error al refrescar progreso:", err);
      message.error("Error al actualizar progreso");
    }
  };

  // ========= Detalle =========
  const verDetalleAutomatizacion = async (idEncabezado) => {
    try {
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway/WhatsApp/listarAutomatizacionesDetalleWhatsApp?id_encabezado=${idEncabezado}`
      );
      const data = await res.json();

      const detallesProcesados = (data.detalles || [])
        .filter((d) => d.numero || d.tiene_whatsApp)
        .filter((d) => d.nombres?.toLowerCase() !== "pausado");

      const agrupado = Object.entries(
        detallesProcesados.reduce((acc, item) => {
          const numero = item.Numero || item.numero || "SIN_NUMERO";
          if (!acc[numero]) acc[numero] = [];
          acc[numero].push(item);
          return acc;
        }, {})
      ).map(([numero, detalles]) => ({
        numero,
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

  // ========= Efecto inicial =========
  useEffect(() => {
    cargarDatosDesdeBD();
    cargarAutomatizaciones();
  }, []);

  // ========= Filtros =========
  const detalleFiltradoPorNumero = (detalleFiltrado || []).filter(
    (registro) => {
      return (
        typeof registro?.numero === "string" &&
        registro.numero.includes(numeroSearch.trim())
      );
    }
  );

  // ========= Pausa / Reanudar =========
  const handlePause = async (id) => {
    await fetch(`${API_URL_GATEWAY}/gateway/WhatsApp_api/pausar/${id}`, {
      method: "POST",
    });
    setPausedEncabezado(id);
    cargarAutomatizaciones();
    message.success("Encabezado pausado");
  };

  const handleResume = async (id) => {
    await fetch(`${API_URL_GATEWAY}/gateway/WhatsApp_api/reanudar/${id}`, {
      method: "POST",
    });
    setPausedEncabezado(null);
    cargarAutomatizaciones();
    message.success("Encabezado reanudado");
  };

  // ========= Render =========
  return (
    <div className="rpa-vigilancia-container">
      <Card className="rpa-main-card">
        {/* Header */}
        <div className="rpa-header">
          <h1 className="excel-tittle">RPA WhatsApp</h1>
          <p className="excel-description">
            Automatización del proceso de consulta y registro de disponibilidad de números en WhatsApp.
          </p>
        </div>

        {/* Acciones */}
        <div className="rpa-actions">
          <div className="rpa-button-group">
            <Button
              className="rpa-btn-primary"
              onClick={() => {
                window.open(
                  `${API_URL_GATEWAY}/gateway/excel/plantillaWhatsApp`
                );
              }}
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
                    `${API_URL_GATEWAY}/gateway/excel/guardarWhatsApp`,
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
                key: `${a.idEncabezado}-${i}`,
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

      {/* Modal de Detalle */}
      <Modal
        className="rpa-modal"
        title={`Detalle automatización ${
          detalleAutomatizacion?.automatizacion || ""
        }`}
        visible={modalDetalleVisible} // usa "open" si antd v5
        onCancel={() => setModalDetalleVisible(false)}
        footer={null}
        width={1000}
      >
        <div className="rpa-search-container">
          <Input.Search
            className="rpa-search"
            placeholder="Buscar por número..."
            allowClear
            value={numeroSearch}
            onChange={(e) => setNumeroSearch(e.target.value)}
            style={{ width: 300 }}
            enterButton="Buscar"
          />
          {detalleAutomatizacion?.idEncabezado && (
            <Button
              className="rpa-btn-primary"
              onClick={() => {
                window.open(
                  `${API_URL_GATEWAY}/gateway/excel/exportar_resultadosWhatsApp?id_encabezado=${detalleAutomatizacion.idEncabezado}`
                );
              }}
            >
              Descargar Excel
            </Button>
          )}
        </div>

        {detalleFiltradoPorNumero.length > 0 ? (
          <Table
            className="rpa-table"
            rowKey="numero"
            dataSource={detalleFiltradoPorNumero}
            columns={[
              {
                title: "Numero",
                dataIndex: "numero",
                key: "numero",
              },
            ]}
            expandable={{
              expandedRowRender: (record) => (
                <Table
                  className="rpa-table"
                  rowKey={(r) => r.idDetalle}
                  dataSource={record.detalles}
                  columns={[
                    {
                      title: "Tiene WhatsApp",
                      dataIndex: "tiene_whatsApp",
                      key: "tiene_whatsApp",
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

export default RpaWhatsApp;
