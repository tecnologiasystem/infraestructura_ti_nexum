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
import "./rpaFamisanar.css";
//import InfoPopup from "../../components/InfoPopup";

const RpaFamiSanar = () => {
  const [excelData, setExcelData] = useState([]);
  const [cedulaSearch, setCedulaSearch] = useState("");
  const [automatizaciones, setAutomatizaciones] = useState([]);
  const [modalDetalleVisible, setModalDetalleVisible] = useState(false);
  const [detalleAutomatizacion, setDetalleAutomatizacion] = useState(null);
  const [detalleFiltrado, setDetalleFiltrado] = useState([]);
  const [subiendo, setSubiendo] = useState(false);
  const [pausedEncabezado, setPausedEncabezado] = useState(null);
  const [detailsRows, setDetailsRows] = useState([]);
  const [detailsTotal, setDetailsTotal] = useState(0);
  const [detailsPage, setDetailsPage] = useState(1);
  const [detailsPageSize, setDetailsPageSize] = useState(10);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsFilterCC, setDetailsFilterCC] = useState("");
  const [autoPage, setAutoPage] = useState(1);
  const [autoPageSize, setAutoPageSize] = useState(5); // ← DE A 5
  const [autoTotal, setAutoTotal] = useState(0);
  const [autoLoading, setAutoLoading] = useState(false);

  /*const [showInfoPopup, setShowInfoPopup] = useState(false);
  const [popupData, setPopupData] = useState({ title: "", message: "" });

  const openInfo = (title, message) => {
    setPopupData({ title, message });
    setShowInfoPopup(true);
  };

  useEffect(() => {
    openInfo(
      "Recordatorio 📢",
      "Actualmente la página a la que corresponde la automatización presenta fallas, pronto estará disponible."
    );

    setTimeout(() => {
      setShowInfoPopup(false);
    }, 60000); // Se cierra solo después de 1 minuto
  }, []);
*/
  const cargarDatosDesdeBD = async () => {
    try {
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway/famisanar_api/detalle/listar_agrupadoFamiSanar`
      );
      const { data } = await res.json();
      setExcelData(data);
    } catch (error) {
      console.error("Error exacto:", error.message);
      message.error("Error al cargar datos desde la base de datos");
    }
  };

  const fetchResumen = async (idEncabezado) => {
    try {
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway/Salud/automatizacionesFamiSanar/${idEncabezado}/resumen`
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      try {
        const r = await fetch(
          `${API_URL_GATEWAY}/gateway/Salud/listarAutomatizacionesDetalleFamiSanar?id_encabezado=${idEncabezado}`
        );
        const data = await r.json();
        const procesados = (data?.detalles || []).filter(
          (d) =>
            (d.nombres || d.apellidos || d.estado || d.IPS || d.convenio) &&
            (d.nombres || "").toLowerCase() !== "pausado"
        ).length;
        const totalRegistros = Number(
          data?.totalRegistros || data?.detalles?.length || 0
        );
        return { idEncabezado, totalRegistros, procesados };
      } catch {
        return { idEncabezado, totalRegistros: 0, procesados: 0 };
      }
    }
  };

  // Función para cargar automatizaciones con cálculo de progreso
  const cargarAutomatizaciones = async (
    page = autoPage,
    pageSize = autoPageSize
  ) => {
    setAutoLoading(true);
    try {
      const offset = (page - 1) * pageSize;
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway/Salud/listarAutomatizacionesFamiSanar?offset=${offset}&limit=${pageSize}`
      );
      const data = await res.json();

      // Retrocompat: si aún vuelve array, adaptamos
      const rows = Array.isArray(data) ? data : data.rows || [];
      const total = Array.isArray(data)
        ? data.total ?? rows.length
        : data.total ?? 0;

      // Calcula % real por fila usando /resumen (o tu fallback existente)
      const withProgress = await Promise.all(
        rows.map(async (auto) => {
          const { procesados, totalRegistros } = await fetchResumen(
            auto.idEncabezado
          );
          const porcentaje = totalRegistros
            ? Math.round((procesados / totalRegistros) * 100)
            : 0;
          return { ...auto, procesados, totalRegistros, porcentaje };
        })
      );

      setAutomatizaciones(withProgress);
      setAutoPage(page);
      setAutoPageSize(pageSize);
      setAutoTotal(total);
    } catch (err) {
      console.error("Error al cargar automatizaciones:", err);
      message.error("Error al cargar automatizaciones");
    } finally {
      setAutoLoading(false);
    }
  };

  // Función para refrescar el progreso de una automatización específica
  const refrescarProgreso = async (idEncabezado) => {
    try {
      const { procesados, totalRegistros } = await fetchResumen(idEncabezado);
      const porcentaje = totalRegistros
        ? Math.round((procesados / totalRegistros) * 100)
        : 0;

      if (porcentaje === 100) {
        try {
          const resp = await fetch(
            `${API_URL_GATEWAY}/gateway/notificarFinalizacionFamiSanar`,
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
          console.error(e);
          message.error("Error al notificar finalización");
        }
      }

      setAutomatizaciones((prev) =>
        prev.map((a) =>
          a.idEncabezado === idEncabezado
            ? { ...a, procesados, totalRegistros, porcentaje }
            : a
        )
      );
      message.success("Progreso actualizado");
    } catch (err) {
      console.error("Error al refrescar progreso:", err);
      message.error("Error al actualizar progreso");
    }
  };

  const traerDetalles = async (idEncabezado, page, cc, pageSize) => {
    const offset = (page - 1) * pageSize;
    setDetailsLoading(true);
    try {
      const url = new URL(
        `${API_URL_GATEWAY}/gateway/Salud/automatizacionesFamiSanar/${idEncabezado}/detalles`
      );
      url.searchParams.set("offset", offset);
      url.searchParams.set("limit", pageSize);
      if (cc && cc.trim()) url.searchParams.set("cc", cc.trim());

      const res = await fetch(url.toString());
      const data = await res.json();
      setDetailsRows(Array.isArray(data?.rows) ? data.rows : []);
      setDetailsTotal(Number(data?.total || 0));
    } catch (e) {
      console.error(e);
      message.error("Error al cargar detalles");
    } finally {
      setDetailsLoading(false);
    }
  };

  // Abre el modal y carga la primera página de detalles paginados (sin agrupar en el front)
  const verDetalleAutomatizacion = (idEncabezado) => {
    const rec = automatizaciones.find((a) => a.idEncabezado === idEncabezado);
    const titulo = rec?.automatizacion || `ID ${idEncabezado}`;
    setDetalleAutomatizacion({ idEncabezado, automatizacion: titulo });
    setModalDetalleVisible(true);
    setDetailsPage(1);
    setDetailsFilterCC("");
    const pageSize = detailsPageSize || 10;
    traerDetalles(idEncabezado, 1, "", pageSize);
  };

  useEffect(() => {
    cargarDatosDesdeBD();
    cargarAutomatizaciones(1, 5);
  }, []);

  // useEffect(() => {
  //  Modal.destroyAll();
  //   Modal.info({
  //    title: "⚠️ Actualización en progreso",
  //    content: (
  //    <div>
  //    <p>Estamos realizando actualizaciones para este rpa.</p>
  //  <p>Por favor, vuelva a intentarlo más tarde.</p>
  //    </div>
  //  ),
  //  okText: "Entendido",
  //  centered: true,
  //  });
  //}, []);

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
    await fetch(`${API_URL_GATEWAY}/gateway/famisanar_api/pausar/${id}`, {
      method: "POST",
    });
    setPausedEncabezado(id);
    cargarAutomatizaciones();
    message.success("Encabezado pausado");
  };

  const handleResume = async (id) => {
    await fetch(`${API_URL_GATEWAY}/gateway/famisanar_api/reanudar/${id}`, {
      method: "POST",
    });
    setPausedEncabezado(null);
    cargarAutomatizaciones();
    message.success("Encabezado reanudado");
  };

  return (
    <div className="rpa-vigilancia-container">
     {/* {showInfoPopup && (
        <InfoPopup
          title={popupData.title}
          message={popupData.message}
          onClose={() => setShowInfoPopup(false)}
        />
      )}*/}
      <Card className="rpa-main-card">
        {/* Header */}
        <div className="rpa-header">
          <h1 className="excel-tittle">RPA FamiSanar</h1>
          <p className="excel-description">
            Automatización del proceso de consulta de la EPS Famisanar
          </p>
        </div>

        {/* Acciones */}
        <div className="rpa-actions">
          <div className="rpa-button-group">
            <Button
              className="rpa-btn-primary"
              onClick={() => {
                window.open(
                  `${API_URL_GATEWAY}/gateway/excel/plantillaFamiSanar`
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
                    `${API_URL_GATEWAY}/gateway/excel/guardarFamiSanar`,
                    { method: "POST", body: formData }
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
              loading={autoLoading}
              dataSource={automatizaciones.map((a, i) => ({
                key: `${a.idEncabezado}-${i}`,
                ...a,
                procesados: a.procesados || 0,
                porcentaje: a.porcentaje || 0,
              }))}
              pagination={{
                current: autoPage,
                pageSize: autoPageSize, // ← siempre 5
                total: autoTotal,
                showSizeChanger: false, // ← fijo en 5
                onChange: (page, pageSize) =>
                  cargarAutomatizaciones(page, pageSize),
              }}
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
        open={modalDetalleVisible}
        onCancel={() => setModalDetalleVisible(false)}
        footer={null}
        width={1000}
      >
        <div className="rpa-search-container">
          <Input.Search
            className="rpa-search"
            allowClear
            placeholder="Buscar por cédula..."
            value={detailsFilterCC}
            onChange={(e) => setDetailsFilterCC(e.target.value)}
            onSearch={(val) => {
              setDetailsPage(1);
              traerDetalles(
                detalleAutomatizacion.idEncabezado,
                1,
                val,
                detailsPageSize
              );
            }}
            style={{ width: 300 }}
            enterButton="Buscar"
            loading={detailsLoading}
          />
          {detalleAutomatizacion?.idEncabezado && (
            <Button
              className="rpa-btn-primary"
              onClick={() => {
                window.open(
                  `${API_URL_GATEWAY}/gateway/excel/exportar_resultadosFamiSanar?id_encabezado=${detalleAutomatizacion.idEncabezado}`
                );
              }}
            >
              Descargar Excel
            </Button>
          )}
        </div>

        <Table
          className="rpa-table"
          rowKey={(r, i) => `${r.idDetalle || i}-${r.cedula || ""}`}
          dataSource={detailsRows}
          loading={detailsLoading}
          columns={[
            { title: "Cédula", dataIndex: "cedula", key: "cedula" },
            { title: "Nombres", dataIndex: "nombres", key: "nombres" },
            { title: "Apellidos", dataIndex: "apellidos", key: "apellidos" },
            { title: "Estado", dataIndex: "estado", key: "estado" },
            { title: "IPS", dataIndex: "IPS", key: "IPS" },
            { title: "Convenio", dataIndex: "convenio", key: "convenio" },
            { title: "Tipo", dataIndex: "tipo", key: "tipo" },
            { title: "Categoría", dataIndex: "categoria", key: "categoria" },
            { title: "Semanas", dataIndex: "semanas", key: "semanas" },
            { title: "Edad", dataIndex: "edad", key: "edad" },
            { title: "Sexo", dataIndex: "sexo", key: "sexo" },
            { title: "Teléfono", dataIndex: "telefono", key: "telefono" },
            {
              title: "Departamento",
              dataIndex: "departamento",
              key: "departamento",
            },
            { title: "Municipio", dataIndex: "municipio", key: "municipio" },
            { title: "Causal", dataIndex: "causal", key: "causal" },
          ]}
          size="small"
          scroll={{ x: "max-content" }}
          pagination={{
            current: detailsPage,
            pageSize: detailsPageSize,
            total: detailsTotal,
            showSizeChanger: true,
            onChange: (page, pageSize) => {
              setDetailsPage(page);
              setDetailsPageSize(pageSize);
              traerDetalles(
                detalleAutomatizacion.idEncabezado,
                page,
                detailsFilterCC,
                pageSize
              );
            },
          }}
        />
      </Modal>
    </div>
  );
};

export default RpaFamiSanar;
