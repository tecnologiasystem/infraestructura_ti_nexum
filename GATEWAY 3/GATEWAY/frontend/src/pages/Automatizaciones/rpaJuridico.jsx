import React, { useState, useEffect } from "react";
import {
  Upload,
  Button,
  Table,
  message,
  Tabs,
  Card,
  Modal,
  Input,
  Progress,
  Typography,
} from "antd";
import { UploadOutlined, ReloadOutlined } from "@ant-design/icons";
import { API_URL_GATEWAY } from "../../config";
import "./rpaJuridico.css";

const RpaJuridico = () => {
  const [excelData, setExcelData] = useState([]);
  const [nombreCompletoSearch, setNombreCompletoSearch] = useState("");
  const [automatizaciones, setAutomatizaciones] = useState([]);
  const [modalDetalleVisible, setModalDetalleVisible] = useState(false);
  const [detalleAutomatizacion, setDetalleAutomatizacion] = useState(null);
  const [detalleFiltrado, setDetalleFiltrado] = useState([]);
  const [subiendo, setSubiendo] = useState(false);
  const [pausedEncabezado, setPausedEncabezado] = useState(null);
  const [accion5Rows, setAccion5Rows] = useState([]);
  const [accion4Rows, setAccion4Rows] = useState([]);

  const columnsAccion4 = [
    {
      title: "Numero Proceso",
      dataIndex: "IDPROCESO",
      key: "IDPROCESO",
      width: 160,
    },
    { title: "Radicado", dataIndex: "RADICADO", key: "RADICADO", width: 180 },

    // NombreJuridico
    {
      title: "Fecha Proceso",
      dataIndex: "fechaProceso",
      key: "NJ_fechaProceso",
      width: 160,
    },
    {
      title: "Fecha Ultima Actuacion",
      dataIndex: "fechaUltimaActuacion",
      key: "fechaUltimaActuacion",
      width: 190,
    },
    {
      title: "Despacho",
      dataIndex: "despacho",
      key: "NJ_despacho",
      width: 220,
    },
    {
      title: "Departamento",
      dataIndex: "departamento",
      key: "NJ_departamento",
      width: 160,
    },
    {
      title: "Sujetos Procesales",
      dataIndex: "sujetosProcesales",
      key: "sujetosProcesales",
      width: 320,
      ellipsis: true,
    },
    {
      title: "es Privado",
      dataIndex: "esPrivado",
      key: "esPrivado",
      width: 120,
    },

    // ActuacionesJuridico
    {
      title: "Fecha Actuacion",
      dataIndex: "fechaActuacion",
      key: "fechaActuacion",
      width: 160,
    },
    {
      title: "Actuacion",
      dataIndex: "actuacion",
      key: "actuacion",
      width: 220,
    },
    {
      title: "Anotacion",
      dataIndex: "anotacion",
      key: "anotacion",
      width: 320,
      ellipsis: true,
    },
    {
      title: "Fecha Inicial",
      dataIndex: "fechaInicial",
      key: "fechaInicial",
      width: 160,
    },
    {
      title: "Fecha Final",
      dataIndex: "fechaFinal",
      key: "fechaFinal",
      width: 160,
    },
    {
      title: "Fecha Registro",
      dataIndex: "fechaRegistro",
      key: "fechaRegistro",
      width: 160,
    },

    // DetalleJuridico
    {
      title: "Fecha Proceso",
      dataIndex: "fechaProceso",
      key: "DJ_fechaProceso",
      width: 160,
    },
    {
      title: "Despacho Completo",
      dataIndex: "codDespachoCompleto",
      key: "codDespachoCompleto",
      width: 210,
    },
    {
      title: "Despacho",
      dataIndex: "despacho",
      key: "DJ_despacho",
      width: 220,
    },
    { title: "Ponente", dataIndex: "ponente", key: "ponente", width: 180 },
    {
      title: "Tipo Proceso",
      dataIndex: "tipoProceso",
      key: "tipoProceso",
      width: 160,
    },
    {
      title: "Clase Proceso",
      dataIndex: "claseProceso",
      key: "claseProceso",
      width: 160,
    },
    {
      title: "Subclase Proceso",
      dataIndex: "subclaseProceso",
      key: "subclaseProceso",
      width: 170,
    },
    { title: "Recurso", dataIndex: "recurso", key: "recurso", width: 140 },
    {
      title: "Ubicacion",
      dataIndex: "ubicacion",
      key: "ubicacion",
      width: 160,
    },
    {
      title: "Contenido Radicacion",
      dataIndex: "contenidoRadicacion",
      key: "contenidoRadicacion",
      width: 360,
      ellipsis: true,
    },
    {
      title: "Fecha Consulta",
      dataIndex: "fechaConsulta",
      key: "fechaConsulta",
      width: 160,
    },
    {
      title: "Ultima Actualizacion",
      dataIndex: "ultimaActualizacion",
      key: "ultimaActualizacion",
      width: 180,
    },
  ];

  // arriba del return (puede ir después de tus useState)
  const norm = (s = "") =>
    s
      .toString()
      .normalize("NFD")
      .replace(/\p{Diacritic}/gu, "") // quita acentos
      .trim()
      .toUpperCase();

  const accion5Filtrada = React.useMemo(() => {
    const q = norm(nombreCompletoSearch);
    if (!q) return accion5Rows;
    return (accion5Rows || []).filter((r) =>
      norm(r?.nombreCompleto).includes(q)
    );
  }, [accion5Rows, nombreCompletoSearch]);

  const cargarDatosDesdeBD = async () => {
    try {
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway-rpa/juridicoBot_api/detalle/listar_agrupadoJuridico`
      );
      const { data } = await res.json();
      setExcelData(data);
    } catch (error) {
      console.error("Error exacto:", error.message);
      message.error("Error al cargar datos desde la base de datos");
    }
  };

  // mismo criterio en ambos lados
  const isFilaProcesada = (d) =>
    !!(
      d?.departamento ||
      d?.ciudad ||
      d?.especialidad ||
      d?.idNombres ||
      d?.idDetalleJuridico ||
      d?.idActuaciones
    );

  // -------------------- cargarAutomatizaciones --------------------
  const cargarAutomatizaciones = async () => {
    try {
      const res = await fetch(
        `${API_URL_GATEWAY}/gateway-rpa/Jurica/listarAutomatizacionesJuridico`
      );
      const data = await res.json();

      const automationsWithProgress = await Promise.all(
        (data || []).map(async (auto) => {
          const detalleRes = await fetch(
            `${API_URL_GATEWAY}/gateway-rpa/Jurica/listarAutomatizacionesDetalleJuridico?id_encabezado=${auto.idEncabezado}`
          );
          const detalleData = await detalleRes.json();

          const detalles = Array.isArray(detalleData?.detalles)
            ? detalleData.detalles
            : [];
          const procesados = detalles.filter(isFilaProcesada).length;

          // intenta varias fuentes para el total
          const total =
            Number(detalleData?.totalRegistros) ||
            Number(auto?.totalRegistros) ||
            detalles.length ||
            0;

          const porcentaje = total
            ? Math.min(100, Math.round((procesados / total) * 100))
            : 0;

          return {
            ...auto,
            procesados,
            totalRegistros: total,
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

  // -------------------- refrescarProgreso --------------------
  const refrescarProgreso = async (idEncabezado) => {
    try {
      const detalleRes = await fetch(
        `${API_URL_GATEWAY}/gateway-rpa/Jurica/listarAutomatizacionesDetalleJuridico?id_encabezado=${idEncabezado}`
      );
      const detalleData = await detalleRes.json();

      const detalles = Array.isArray(detalleData?.detalles)
        ? detalleData.detalles
        : [];
      const procesados = detalles.filter(isFilaProcesada).length;

      const total = Number(detalleData?.totalRegistros) || detalles.length || 0;

      const porcentaje = total
        ? Math.min(100, Math.round((procesados / total) * 100))
        : 0;

      // si terminó, notifica (opcional)
      if (porcentaje === 100) {
        try {
          const r = await fetch(
            `${API_URL_GATEWAY}/gateway-rpa/notificarFinalizacionJuridico`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ idEncabezado }),
            }
          );
          const j = await r.json();
          j?.success
            ? message.success("✅ Correo de finalización enviado")
            : message.warning("⚠️ No se pudo enviar el correo");
        } catch (e) {
          console.error("Error al enviar notificación:", e);
        }
      }

      setAutomatizaciones((prev) =>
        prev.map((a) =>
          a.idEncabezado === idEncabezado
            ? { ...a, procesados, totalRegistros: total, porcentaje }
            : a
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
      const [res5, res4] = await Promise.all([
        fetch(
          `${API_URL_GATEWAY}/gateway-rpa/Juridica/accion5?id_encabezado=${idEncabezado}`
        ),
        fetch(
          `${API_URL_GATEWAY}/gateway-rpa/Juridica/accion4?id_encabezado=${idEncabezado}`
        ),
      ]);
      if (!res5.ok || !res4.ok)
        throw new Error("Fallo en alguna de las respuestas del gateway");

      const [data5, data4] = await Promise.all([res5.json(), res4.json()]);

      const conteoPorPersona = Array.isArray(data5) ? data5 : data5?.data || [];
      const detallesAcc4Raw = Array.isArray(data4) ? data4 : data4?.data || [];

      const limpiarExcelValor = (valor) => {
        if (
          typeof valor === "string" &&
          valor.startsWith('="') &&
          valor.endsWith('"')
        ) {
          return valor.slice(2, -1); // quita el =" y el "
        }
        return valor;
      };

      const accion4Normalizada = (detallesAcc4Raw || []).map((r) => {
        const limpiado = {};
        for (const [key, value] of Object.entries(r)) {
          limpiado[key] = limpiarExcelValor(value);
        }
        return {
          ...limpiado,
          nombreCompleto:
            r?.nombreCompleto ??
            r?.NOMBRE_COMPLETO ??
            r?.nombre_completo ??
            "SIN_NOMBRE",
        };
      });

      setAccion4Rows(accion4Normalizada);

      const detallesProcesados = accion4Normalizada
        .filter(
          (d) =>
            d?.departamento ||
            d?.ciudad ||
            d?.especialidad ||
            d?.idNombres ||
            d?.idDetalleJuridico ||
            d?.idActuaciones
        )
        .filter((d) => (d?.actuacion || "").toLowerCase() !== "pausado");

      const agrupado = Object.entries(
        detallesProcesados.reduce((acc, item) => {
          const key = (item?.nombreCompleto || "SIN_NOMBRE").trim();
          if (!acc[key]) acc[key] = [];
          acc[key].push(item);
          return acc;
        }, {})
      ).map(([nombreCompleto, detalles]) => ({
        nombreCompleto,
        detalles: detalles.map((item, index) => ({
          ...item,
          numItem: index + 1,
        })),
      }));

      setAccion5Rows(conteoPorPersona);
      setDetalleAutomatizacion({ idEncabezado, detalles: detallesProcesados });
      setDetalleFiltrado(agrupado);
      setModalDetalleVisible(true);
    } catch (err) {
      console.error("Error al cargar acciones 4 y 5:", err);
      message.error("Error al obtener datos de la automatización");
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

  const detalleFiltradoPorNombreCompleto = (detalleFiltrado || []).filter(
    (registro) => {
      return (
        typeof registro?.nombreCompleto === "string" &&
        registro.nombreCompleto.includes(nombreCompletoSearch.trim())
      );
    }
  );

  const handlePause = async (id) => {
    await fetch(`${API_URL_GATEWAY}/gateway-rpa/juridicoBot_api/pausar/${id}`, {
      method: "POST",
    });
    setPausedEncabezado(id);
    cargarAutomatizaciones();
    message.success("Encabezado pausado");
  };

  const handleResume = async (id) => {
    await fetch(
      `${API_URL_GATEWAY}/gateway-rpa/juridicoBot_api/reanudar/${id}`,
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
          <h1 className="excel-tittle">RPA Jurídico</h1>
          <p className="excel-description">
            Automatización del proceso de consulta, seguimiento y registro de información jurídica.
          </p>
        </div>

        {/* Acciones */}
        <div className="rpa-actions">
          <div className="rpa-button-group">
            <Button
              className="rpa-btn-primary"
              onClick={() => {
                window.open(
                  `${API_URL_GATEWAY}/gateway-rpa/excel/plantillaJuridico`
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
                    `${API_URL_GATEWAY}/gateway-rpa/excel/guardarJuridico`,
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
            placeholder="Buscar por nombre..."
            allowClear
            value={nombreCompletoSearch}
            onChange={(e) => setNombreCompletoSearch(e.target.value)}
            style={{ width: 300 }}
            enterButton="Buscar"
          />
          {detalleAutomatizacion?.idEncabezado && (
            <Button
              className="rpa-btn-primary"
              onClick={() => {
                window.open(
                  `${API_URL_GATEWAY}/gateway-rpa/excel/exportar_resultadosJuridico?id_encabezado=${detalleAutomatizacion.idEncabezado}`
                );
              }}
            >
              Descargar Excel
            </Button>
          )}
        </div>

        <Tabs
          items={[
            {
              key: "accion5",
              label: "Resumen por persona",
              children: (
                <Table
                  className="rpa-table"
                  rowKey={(r) => r.nombreCompleto}
                  dataSource={accion5Filtrada}
                  size="small"
                  pagination={{ pageSize: 10 }}
                  columns={[
                    {
                      title: "Persona",
                      dataIndex: "nombreCompleto",
                      key: "nombreCompleto",
                    },
                    {
                      title: "Procesos",
                      dataIndex: "NumeroProcesos",
                      key: "NumeroProcesos",
                      width: 120,
                    },
                  ]}
                  expandable={{
                    expandRowByClick: true,
                    expandedRowRender: (record) => {
                      const norm = (s) =>
                        (s || "")
                          .toString()
                          .trim()
                          .toUpperCase()
                          .replace(/\s+/g, " ");
                      const detallesDeLaPersona = (accion4Rows || []).filter(
                        (d) =>
                          norm(d.nombreCompleto ?? d.NOMBRE_COMPLETO) ===
                          norm(record.nombreCompleto)
                      );

                      return (
                        <div style={{ maxWidth: 940, overflowX: "auto" }}>
                          <Table
                            className="rpa-table"
                            rowKey={(r) =>
                              r.idDetalle ||
                              r.idActuacionesJuridico ||
                              r.idDetalleJuridico ||
                              r.IDPROCESO ||
                              Math.random()
                            }
                            dataSource={detallesDeLaPersona}
                            size="small"
                            pagination={false}
                            columns={columnsAccion4}
                            tableLayout="fixed"
                          />
                        </div>
                      );
                    },
                  }}
                />
              ),
            },
          ]}
        />
      </Modal>
    </div>
  );
};

export default RpaJuridico;
