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
import "./rpaSuperNotariado.css";
import InfoPopup from "../../components/InfoPopup";


const RpaSuperNotariado = () => {
  // ===== Estados generales =====
  const [excelData, setExcelData] = useState([]);
  const [automatizaciones, setAutomatizaciones] = useState([]);
  const [subiendo, setSubiendo] = useState(false);
  const [pausedEncabezado, setPausedEncabezado] = useState(null);

  // ===== Estados: encabezados paginados (server-side) =====
  const [autoPage, setAutoPage] = useState(1);
  const [autoPageSize, setAutoPageSize] = useState(5); // ← de a 5
  const [autoTotal, setAutoTotal] = useState(0);
  const [autoLoading, setAutoLoading] = useState(false);

  // ===== Estados: modal de detalles paginados =====
  const [modalDetalleVisible, setModalDetalleVisible] = useState(false);
  const [detalleAutomatizacion, setDetalleAutomatizacion] = useState(null);
  const [detailsRows, setDetailsRows] = useState([]);
  const [detailsTotal, setDetailsTotal] = useState(0);
  const [detailsPage, setDetailsPage] = useState(1);
  const [detailsPageSize, setDetailsPageSize] = useState(10);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsFilterCC, setDetailsFilterCC] = useState("");

const [showInfoPopup, setShowInfoPopup] = useState(false);
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

  // ===== Carga agrupado (si lo sigues mostrando en otra sección) =====
  const cargarDatosDesdeBD = async () => {
    try {
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway/superNotariado_api/detalle/listar_agrupado`
      );
      const { data } = await res.json();
      setExcelData(data);
    } catch (error) {
      console.error("Error exacto:", error.message);
      message.error("Error al cargar datos desde la base de datos");
    }
  };

  // ===== Resumen real (procesados / total) con fallback =====
  const fetchResumen = async (idEncabezado) => {
    // 1) Intento endpoint de resumen “nuevo”
    try {
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway/Juridica/automatizaciones/${idEncabezado}/resumen`
      );
      if (res.ok) return await res.json(); // { procesados, totalRegistros }
    } catch (_) {}
    // 2) Fallback: resumido actual (detallesIngresados/totalRegistros)
    const r = await fetch(
      `${API_URL_GATEWAY}/gateway/Juridica/listarAutomatizacionesDetalleResumido?id_encabezado=${idEncabezado}`
    );
    const data = await r.json(); // { detallesIngresados, totalRegistros }
    return {
      procesados: Number(data?.detallesIngresados || 0),
      totalRegistros: Number(data?.totalRegistros || 0),
    };
  };

  // ===== Listado: pedir SOLO 5 encabezados por página (server-side) =====
  const cargarAutomatizaciones = async (
    page = autoPage,
    pageSize = autoPageSize
  ) => {
    setAutoLoading(true);
    try {
      const offset = (page - 1) * pageSize;

      // 1) Intento endpoint paginado (retrocompat si aún devuelve array)
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway/Jurica/listarAutomatizaciones?offset=${offset}&limit=${pageSize}`
      );
      const data = await res.json();

      const rows = Array.isArray(data) ? data : data.rows || [];
      const total = Array.isArray(data)
        ? data.total ?? rows.length
        : data.total ?? 0;

      // 2) Para esos 5, traigo su resumen real
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
      message.error("Error al cargar el progreso de automatizaciones");
    } finally {
      setAutoLoading(false);
    }
  };

  // ===== Refrescar una fila (usa resumen real) =====
  const refrescarProgreso = async (idEncabezado) => {
    try {
      const { procesados, totalRegistros } = await fetchResumen(idEncabezado);
      const porcentaje = totalRegistros
        ? Math.round((procesados / totalRegistros) * 100)
        : 0;

      // Notificar solo si terminó estrictamente (evita falsos 100 por redondeo)
      if (procesados === totalRegistros && totalRegistros > 0) {
        try {
          const resp = await fetch(
            `${API_URL_GATEWAY}/gateway/notificarFinalizacionSuperNotariado`,
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

  // ===== Detalles paginados (modal) con fallback =====
  const traerDetalles = async (idEncabezado, page, cc, pageSize) => {
    const offset = (page - 1) * pageSize;
    setDetailsLoading(true);
    try {
      // 1) Intento endpoint paginado “nuevo”
      const url = new URL(
        `${API_URL_GATEWAY}/gateway/Jurica/automatizaciones/${idEncabezado}/detalles`
      );
      url.searchParams.set("offset", offset);
      url.searchParams.set("limit", pageSize);
      if (cc && cc.trim()) url.searchParams.set("cc", cc.trim());

      let res = await fetch(url.toString());
      if (res.ok) {
        const data = await res.json(); // { rows, total } esperado
        if (
          data &&
          (Array.isArray(data.rows) || Array.isArray(data?.detalles))
        ) {
          // aceptar {rows,total} o {detalles,total}
          const rows = Array.isArray(data.rows)
            ? data.rows
            : data.detalles || [];
          setDetailsRows(rows);
          setDetailsTotal(Number(data.total || rows.length || 0));
          return;
        }
      }

      // 2) Fallback: endpoint actual que trae TODO y agrupa en front (pesado)
      res = await fetch(
        `${API_URL_GATEWAY}/gateway/Jurica/listarAutomatizacionesDetalle?id_encabezado=${idEncabezado}`
      );
      const full = await res.json(); // { detalles: [...] }
      const detallesValidos = (full?.detalles || []).filter(
        (item) => String(item?.matricula || "").toLowerCase() !== "pausado"
      );

      // Aplicar filtro CC si viene
      const filtrados =
        cc && cc.trim()
          ? detallesValidos.filter((d) =>
              String(d.CC || d.cedula || "").includes(cc.trim())
            )
          : detallesValidos;

      // Emular paginado en front como fallback
      const total = filtrados.length;
      const start = offset;
      const end = offset + pageSize;
      const pageRows = filtrados.slice(start, end);

      setDetailsRows(pageRows);
      setDetailsTotal(total);
    } catch (e) {
      console.error(e);
      message.error("Error al cargar detalles");
    } finally {
      setDetailsLoading(false);
    }
  };

  const verDetalleAutomatizacion = (idEncabezado) => {
    const rec = automatizaciones.find((a) => a.idEncabezado === idEncabezado);
    const titulo = rec?.automatizacion || `ID ${idEncabezado}`;

    setDetalleAutomatizacion({ idEncabezado, automatizacion: titulo });
    setModalDetalleVisible(true);
    setDetailsPage(1);
    setDetailsFilterCC("");

    traerDetalles(idEncabezado, 1, "", detailsPageSize || 10);
  };

  // ===== Pausar / Reanudar =====
  const handlePause = async (id) => {
    await fetch(`${API_URL_GATEWAY}/gateway/superNotariado_api/pausar/${id}`, {
      method: "POST",
    });
    setPausedEncabezado(id);
    cargarAutomatizaciones(autoPage, autoPageSize);
    message.success("Encabezado pausado");
  };

  const handleResume = async (id) => {
    await fetch(
      `${API_URL_GATEWAY}/gateway/superNotariado_api/reanudar/${id}`,
      { method: "POST" }
    );
    setPausedEncabezado(null);
    cargarAutomatizaciones(autoPage, autoPageSize);
    message.success("Encabezado reanudado");
  };

  // ===== Primer load =====
  useEffect(() => {
    cargarDatosDesdeBD();
    cargarAutomatizaciones(1, 5); // ← arranca trayendo 5
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

  // ===== Render =====
  return (
    <div className="rpa-vigilancia-container">
            {showInfoPopup && (
        <InfoPopup
          title={popupData.title}
          message={popupData.message}
          onClose={() => setShowInfoPopup(false)}
        />
      )}
      <Card className="rpa-main-card">
        {/* Header Section */}
        <div className="rpa-header">
          <h1 className="excel-tittle">RPA Super Notariado</h1>
          <p className="excel-description">
            Automatización de consulta de información registral en la Superintendencia de Notariado y Registro.
          </p>
        </div>

        {/* Action Buttons Section */}
        <div className="rpa-actions">
          <div className="rpa-button-group">
            <Button
              className="rpa-btn-primary"
              onClick={() => {
                window.open(
                  `${API_URL_GATEWAY}/gateway/excel/plantillaNotariado`
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
                    `${API_URL_GATEWAY}/gateway/excel/guardarNotariado`,
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
                    const result = data;
                    message.success("Archivo subido correctamente");
                    cargarDatosDesdeBD();
                    if (result?.idEncabezado) {
                      refrescarProgreso(result.idEncabezado);
                    }
                    onSuccess(result);
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

        {/* Progress Section */}
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
                // mostramos el % real que ya calculamos en cargarAutomatizaciones
              }))}
              pagination={{
                current: autoPage,
                pageSize: autoPageSize, // ← siempre 5
                total: autoTotal,
                showSizeChanger: false, // ← fijo en 5
                onChange: (page, pageSize) => {
                  cargarAutomatizaciones(page, pageSize);
                },
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
                      percent={record.porcentaje || 0}
                      status={
                        (record.porcentaje || 0) === 100 ? "success" : "active"
                      }
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
                  title: "Control",
                  key: "control",
                  render: (_, record) =>
                    record.estado !== "Pausado" ? (
                      <Button
                        className="rpa-action-btn pause"
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

      {/* Detail Modal */}
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
                  `${API_URL_GATEWAY}/gateway/excel/exportar_resultadosNotariado?id_encabezado=${detalleAutomatizacion.idEncabezado}`
                );
              }}
            >
              Descargar Excel
            </Button>
          )}
        </div>

        <Table
          className="rpa-table"
          rowKey={(r, i) => `${r.idDetalle || i}-${r.CC || r.cedula || ""}`}
          dataSource={detailsRows}
          loading={detailsLoading}
          columns={[
            {
              title: "Cédula",
              dataIndex: "CC",
              key: "CC",
              render: (text, row) => row.CC ?? row.cedula ?? "",
            },
            { title: "Ciudad", dataIndex: "ciudad", key: "ciudad" },
            { title: "Matrícula", dataIndex: "matricula", key: "matricula" },
            { title: "Dirección", dataIndex: "direccion", key: "direccion" },
            {
              title: "Vinculado A",
              dataIndex: "vinculadoA",
              key: "vinculadoA",
            },
            {
              title: "Documento",
              key: "doc",
              render: (_, row) => {
                const cc = row.CC ?? row.cedula;
                return cc ? (
                  <Button
                    className="rpa-action-btn detail"
                    type="link"
                    onClick={() =>
                      window.open(
                        `${API_URL_GATEWAY}/gateway/excel/descargar_pdf_notariado?cedula=${cc}`,
                        "_blank"
                      )
                    }
                  >
                    Ver Documento
                  </Button>
                ) : null;
              },
            },
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

export default RpaSuperNotariado;
