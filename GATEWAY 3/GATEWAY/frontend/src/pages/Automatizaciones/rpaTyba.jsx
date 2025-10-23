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
import "./rpaTyba.css";

const RpaTyba = () => {
  // ===== agrupado (opcional si lo usas en otra parte) =====
  const [excelData, setExcelData] = useState([]);
  const [subiendo, setSubiendo] = useState(false);
  const [pausedEncabezado, setPausedEncabezado] = useState(null);

  // ===== encabezados (server-side) =====
  const [automatizaciones, setAutomatizaciones] = useState([]);
  const [autoPage, setAutoPage] = useState(1);
  const [autoPageSize, setAutoPageSize] = useState(5); // ← de a 5
  const [autoTotal, setAutoTotal] = useState(0);
  const [autoLoading, setAutoLoading] = useState(false);

  // ===== modal detalles (server-side) =====
  const [modalDetalleVisible, setModalDetalleVisible] = useState(false);
  const [detalleAutomatizacion, setDetalleAutomatizacion] = useState(null);
  const [detailsRows, setDetailsRows] = useState([]);
  const [detailsTotal, setDetailsTotal] = useState(0);
  const [detailsPage, setDetailsPage] = useState(1);
  const [detailsPageSize, setDetailsPageSize] = useState(10);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [detailsFilterCC, setDetailsFilterCC] = useState("");

  // ===== cargar agrupado (si lo necesitas) =====
  const cargarDatosDesdeBD = async () => {
    try {
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway-rpa/tyba_api/detalle/listar_agrupadoTyba`
      );
      const { data } = await res.json();
      setExcelData(data);
    } catch (error) {
      console.error("Error exacto:", error.message);
      message.error("Error al cargar datos desde la base de datos");
    }
  };

  // ===== resumen real (con fallback) =====
  const fetchResumen = async (idEncabezado) => {
    // 1) endpoint nativo (si existe)
    try {
      const r = await fetch(
        `${API_URL_GATEWAY}/gateway-rpa/Juridica/automatizacionesTyba/${idEncabezado}/resumen`
      );
      if (r.ok) return await r.json(); // { procesados, totalRegistros }
    } catch (_) {}
    // 2) fallback: contar desde el detalle actual
    const detalleRes = await fetch(
      `${API_URL_GATEWAY}/gateway-rpa/Jurica/listarAutomatizacionesDetalleTyba?id_encabezado=${idEncabezado}`
    );
    const detalleData = await detalleRes.json();
    const base = (detalleData?.detalles || [])
      .filter(
        (d) =>
          d.radicado ||
          d.proceso ||
          d.departamento ||
          d.coorporacion ||
          d.despacho
      )
      .filter((d) => String(d.radicado || "").toLowerCase() !== "pausado");

    const procesados = base.length;
    const totalRegistros = Number(detalleData?.totalRegistros || 0);
    return { procesados, totalRegistros };
  };

  // ===== encabezados: pedir 5 por página =====
  const cargarAutomatizaciones = async (
    page = autoPage,
    pageSize = autoPageSize
  ) => {
    setAutoLoading(true);
    try {
      const offset = (page - 1) * pageSize;

      // 1) intenta endpoint paginado del gateway-rpa (retrocompat si devuelve array)
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway-rpa/Jurica/listarAutomatizacionesTyba?offset=${offset}&limit=${pageSize}`
      );
      const data = await res.json();

      const rows = Array.isArray(data) ? data : data.rows || [];
      const total = Array.isArray(data)
        ? data.total ?? rows.length
        : data.total ?? 0;

      // 2) para esas 5 filas, trae el resumen real
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

  // ===== refrescar una fila (notifica solo si terminó estrictamente) =====
  const refrescarProgreso = async (idEncabezado) => {
    try {
      const { procesados, totalRegistros } = await fetchResumen(idEncabezado);
      const porcentaje = totalRegistros
        ? Math.round((procesados / totalRegistros) * 100)
        : 0;

      if (procesados === totalRegistros && totalRegistros > 0) {
        try {
          const resp = await fetch(
            `${API_URL_GATEWAY}/gateway-rpa/notificarFinalizacionTyba`,
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

  // ===== detalles paginados (filtro por cédula) con fallback =====
  const traerDetalles = async (idEncabezado, page, cc, pageSize) => {
    const offset = (page - 1) * pageSize;
    setDetailsLoading(true);
    try {
      // 1) endpoint paginado “nuevo”
      const url = new URL(
        `${API_URL_GATEWAY}/gateway-rpa/Jurica/automatizacionesTyba/${idEncabezado}/detalles`
      );
      url.searchParams.set("offset", offset);
      url.searchParams.set("limit", pageSize);
      if (cc && cc.trim()) url.searchParams.set("cc", cc.trim());

      let res = await fetch(url.toString());
      if (res.ok) {
        const data = await res.json(); // { rows,total } o {detalles,total}
        if (
          data &&
          (Array.isArray(data.rows) || Array.isArray(data.detalles))
        ) {
          const rows = Array.isArray(data.rows)
            ? data.rows
            : data.detalles || [];
          setDetailsRows(rows);
          setDetailsTotal(Number(data.total || rows.length || 0));
          return;
        }
      }

      // 2) fallback: endpoint actual (todo) + filtrar/paginar en front
      res = await fetch(
        `${API_URL_GATEWAY}/gateway-rpa/Jurica/listarAutomatizacionesDetalleTyba?id_encabezado=${idEncabezado}`
      );
      const full = await res.json(); // {detalles:[...]}
      const base = (full?.detalles || [])
        .filter(
          (d) =>
            d.radicado ||
            d.proceso ||
            d.departamento ||
            d.coorporacion ||
            d.despacho
        )
        .filter((d) => String(d.radicado || "").toLowerCase() !== "pausado");

      const filtrados =
        cc && cc.trim()
          ? base.filter((d) => {
              const k = String(d.cedula || d.CC || d.cc || "");
              return k.includes(cc.trim());
            })
          : base;

      const total = filtrados.length;
      const pageRows = filtrados.slice(offset, offset + pageSize);

      setDetailsRows(pageRows);
      setDetailsTotal(total);
    } catch (e) {
      console.error(e);
      message.error("Error al cargar detalles");
    } finally {
      setDetailsLoading(false);
    }
  };

  // ===== abrir modal y cargar primera página =====
  const verDetalleAutomatizacion = (idEncabezado) => {
    const rec = automatizaciones.find((a) => a.idEncabezado === idEncabezado);
    const titulo = rec?.automatizacion || `ID ${idEncabezado}`;

    setDetalleAutomatizacion({ idEncabezado, automatizacion: titulo });
    setModalDetalleVisible(true);
    setDetailsPage(1);
    setDetailsFilterCC("");

    traerDetalles(idEncabezado, 1, "", detailsPageSize || 10);
  };

  // ===== pausar / reanudar =====
  const handlePause = async (id) => {
    await fetch(`${API_URL_GATEWAY}/gateway-rpa/tyba_api/pausar/${id}`, {
      method: "POST",
    });
    setPausedEncabezado(id);
    cargarAutomatizaciones(autoPage, autoPageSize);
    message.success("Encabezado pausado");
  };

  const handleResume = async (id) => {
    await fetch(`${API_URL_GATEWAY}/gateway-rpa/tyba_api/reanudar/${id}`, {
      method: "POST",
    });
    setPausedEncabezado(null);
    cargarAutomatizaciones(autoPage, autoPageSize);
    message.success("Encabezado reanudado");
  };

  // ===== primer load =====
  useEffect(() => {
    cargarDatosDesdeBD();
    cargarAutomatizaciones(1, 5); // ← arranca trayendo 5
  }, []);

  // ===== UI =====
  return (
    <div className="rpa-vigilancia-container">
      <Card className="rpa-main-card">
        {/* Header */}
        <div className="rpa-header">
          <h1 className="excel-tittle">RPA Tyba</h1>
          <p className="excel-description">
            Automatización del proceso de consulta judicial (Tyba).
          </p>
        </div>

        {/* Acciones */}
        <div className="rpa-actions">
          <div className="rpa-button-group">
            <Button
              className="rpa-btn-primary"
              onClick={() =>
                window.open(
                  `${API_URL_GATEWAY}/gateway-rpa/excel/plantillaTyba`
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
                    `${API_URL_GATEWAY}/gateway-rpa/excel/guardarTyba`,
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
              loading={autoLoading}
              dataSource={automatizaciones.map((a, i) => ({
                key: `${a.idEncabezado}-${i}`,
                ...a,
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
                  `${API_URL_GATEWAY}/gateway-rpa/excel/exportar_resultadosTyba?id_encabezado=${detalleAutomatizacion.idEncabezado}`
                );
              }}
            >
              Descargar Excel
            </Button>
          )}
        </div>

        <Table
          className="rpa-table"
          rowKey={(r, i) =>
            `${r.idDetalle || i}-${r.cedula || r.CC || r.cc || ""}`
          }
          dataSource={detailsRows}
          loading={detailsLoading}
          columns={[
            {
              title: "Cédula",
              dataIndex: "cedula",
              key: "cedula",
              render: (t, r) => r.cedula ?? r.CC ?? r.cc ?? "",
            },
            { title: "Radicado", dataIndex: "radicado", key: "radicado" },
            { title: "Proceso", dataIndex: "proceso", key: "proceso" },
            {
              title: "Departamento",
              dataIndex: "departamento",
              key: "departamento",
            },
            {
              title: "Corporación",
              dataIndex: "coorporacion",
              key: "coorporacion",
            },
            { title: "Despacho", dataIndex: "despacho", key: "despacho" },
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

export default RpaTyba;
