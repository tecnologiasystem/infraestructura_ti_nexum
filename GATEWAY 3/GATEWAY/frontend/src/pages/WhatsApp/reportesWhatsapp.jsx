import React, { useEffect, useMemo, useState } from "react";
import {
  Card,
  Button,
  Space,
  Tag,
  message,
  Typography,
  Divider,
  Input,
  Tooltip,
  Pagination,
  Select,
} from "antd";
import { API_URL_GATEWAY } from "../../config";
import axios from "axios";
import * as XLSX from "xlsx";
import dayjs from "dayjs";
import {
  DownloadOutlined,
  ReloadOutlined,
  FileExcelOutlined,
} from "@ant-design/icons";
import "./reportesWhatsApp.css";

const { Text } = Typography;

export default function ReportesWhatsApp() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [q, setQ] = useState("");
  const [campanaFilter, setCampanaFilter] = useState("");

  // --- Estados de paginación ---
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const columns = useMemo(
    () => [
      { title: "Número", dataIndex: "Numero", width: 80 },
      { title: "Mensaje", dataIndex: "Mensaje", ellipsis: true },
      { title: "Archivo", dataIndex: "fileName", width: 160 },
      {
        title: "Adjunto",
        dataIndex: "Adjunto",
        width: 120,
        render: (v) =>
          v ? (
            <a href={v} target="_blank" rel="noreferrer">
              descargar
            </a>
          ) : (
            <span style={{ color: "#999" }}>—</span>
          ),
      },
      {
        title: "Fecha/Hora envío",
        dataIndex: "FechaHoraEnvio",
        width: 180,
        render: (v) => (v ? dayjs(v).format("YYYY-MM-DD HH:mm") : "—"),
      },
      {
        title: "Estado",
        dataIndex: "Estado",
        width: 120,
        render: (_, record) => {
          const v = computeEstado(record);
          return v ? <Tag color={estadoColor(v)}>{v}</Tag> : <span>—</span>;
        },
      },

      {
        title: "Tiene WhatsApp",
        dataIndex: "Tiene_Whatsapp",
        width: 140,
        render: (v) => {
          const s = String(v ?? "")
            .trim()
            .toLowerCase();
          if (s === "si" || s === "sí") return <Tag color="green">Sí</Tag>;
          if (s === "no") return <Tag color="red">No</Tag>;
          return <Tag>—</Tag>;
        },
      },
      { title: "Campaña", dataIndex: "Campana", width: 80 },
    ],
    []
  );

  const campaignOptions = useMemo(() => {
    const names = rows
      .map((r) => r.Campana)
      .filter((c) => c && c.trim() !== "");
    return Array.from(new Set(names)).sort();
  }, [rows]);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(
        `${API_URL_GATEWAY}/gateway-rpa/ClientesEnvioWhatsApp`
      );
      setRows(Array.isArray(data) ? data : []);
      setPage(1);
    } catch (e) {
      console.error(e);
      message.error("No pude cargar los datos del gateway");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const computeEstado = (r) => {
    const s = String(r?.Tiene_Whatsapp ?? "")
      .trim()
      .toLowerCase();
    if (s === "no") return "NO ENVIADO";
    return r?.Estado || "";
  };

  const estadoColor = (v) => {
    if (v === "ENVIADO") return "green";
    if (v === "PENDIENTE") return "geekblue";
    if (v === "ERROR") return "red";
    if (v === "NO ENVIADO") return "volcano";
    return "gold";
  };

  // Filtro rápido (client-side)
  const filtered = useMemo(() => {
    let result = rows;

    // Filtro por texto
    if (q) {
      const s = q.toLowerCase();
      result = result.filter((r) => {
        const estadoVisible = computeEstado(r).toLowerCase();
        return (
          String(r?.Numero ?? "")
            .toLowerCase()
            .includes(s) ||
          String(r?.Mensaje ?? "")
            .toLowerCase()
            .includes(s) ||
          String(r?.fileName ?? "")
            .toLowerCase()
            .includes(s) ||
          String(r?.Campana ?? "")
            .toLowerCase()
            .includes(s) || // Campaña también en búsqueda
          estadoVisible.includes(s)
        );
      });
    }

    // 👇 Filtro por campaña
    if (campanaFilter) {
      result = result.filter((r) => r.Campana === campanaFilter);
    }

    return result;
  }, [rows, q, campanaFilter]);

  useEffect(() => {
    setPage(1);
  }, [q]);

  // Paginación
  const total = filtered.length;
  const startIdx = (page - 1) * pageSize;
  const endIdx = Math.min(startIdx + pageSize, total);
  const pageData = useMemo(
    () => filtered.slice(startIdx, endIdx),
    [filtered, startIdx, endIdx]
  );

  // Exportar a Excel¿
  const exportExcel = () => {
    try {
      const exportRows = filtered.map((r) => ({
        Numero: r.Numero,
        Mensaje: r.Mensaje,
        Archivo: r.fileName,
        Adjunto: r.Adjunto,
        FechaHoraEnvio: r.FechaHoraEnvio
          ? dayjs(r.FechaHoraEnvio).format("YYYY-MM-DD HH:mm:ss")
          : "",
        Estado: computeEstado(r),
        Tiene_Whatsapp: r.Tiene_Whatsapp,
        Campana: r.Campana,
      }));
      const wb = XLSX.utils.book_new();
      const ws = XLSX.utils.json_to_sheet(exportRows);
      XLSX.utils.book_append_sheet(wb, ws, "Reporte");
      XLSX.writeFile(
        wb,
        `Reporte_EnvioWhatsApp_${dayjs().format("YYYYMMDD_HHmm")}.xlsx`
      );
    } catch (e) {
      console.error(e);
      message.error("No se pudo exportar a Excel");
    }
  };

  return (
    <div
      className="whatsapp-reports"
      style={{ maxWidth: 1400, margin: "0 auto" }}
    >
      <h1>Reportes — Envío WhatsApp</h1>
      <Text type="secondary">
        Vista de sólo lectura para análisis rápido y exportación.
      </Text>

      <Card style={{ marginTop: 16 }}>
        <Space direction="vertical" style={{ width: "100%" }} size="large">
          <Space wrap>
            <Tooltip title="Recargar datos desde el gateway">
              <Button
                icon={<ReloadOutlined />}
                onClick={load}
                loading={loading}
              >
                Recargar
              </Button>
            </Tooltip>

            <Tooltip title="Exportar a Excel (aplica el filtro de búsqueda)">
              <Button
                type="primary"
                icon={<FileExcelOutlined />}
                onClick={exportExcel}
              >
                Exportar Excel
              </Button>
            </Tooltip>

            <Input
              allowClear
              style={{ width: 400 }}
              placeholder="Buscar Número, Mensaje, Archivo, Estado, Campaña..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
              prefix={
                <DownloadOutlined rotate={180} style={{ color: "#999" }} />
              }
            />
            <Select
              allowClear
              placeholder="Campaña"
              style={{ width: 240 }}
              value={campanaFilter || undefined}
              onChange={(value) => setCampanaFilter(value || "")}
              options={campaignOptions.map((c) => ({ label: c, value: c }))}
            />
          </Space>

          <Divider style={{ margin: "8px 0" }} />

          {/* Tabla */}
          <div style={{ overflowX: "auto" }}>
            <table
              className="ant-table"
              style={{ width: "100%", borderCollapse: "collapse" }}
            >
              <thead className="ant-table-thead">
                <tr>
                  {columns.map((c) => (
                    <th
                      key={c.title}
                      className="ant-table-cell"
                      style={{ textAlign: "left", padding: 8 }}
                    >
                      {c.title}
                    </th>
                  ))}
                </tr>
              </thead>

              <tbody className="ant-table-tbody">
                {!loading && total === 0 && (
                  <tr>
                    <td
                      colSpan={columns.length}
                      style={{ padding: 16, color: "#999" }}
                    >
                      Sin resultados
                    </td>
                  </tr>
                )}

                {loading && (
                  <tr>
                    <td colSpan={columns.length} style={{ padding: 16 }}>
                      Cargando…
                    </td>
                  </tr>
                )}

                {!loading &&
                  pageData.map((r) => (
                    <tr key={r.id} className="ant-table-row">
                      <td className="ant-table-cell" style={{ padding: 8 }}>
                        {r.Numero}
                      </td>
                      <td
                        className="ant-table-cell"
                        style={{
                          padding: 8,
                          maxWidth: 420,
                          whiteSpace: "nowrap",
                          textOverflow: "ellipsis",
                          overflow: "hidden",
                        }}
                        title={r.Mensaje || ""}
                      >
                        {r.Mensaje || "—"}
                      </td>
                      <td className="ant-table-cell" style={{ padding: 8 }}>
                        {r.fileName || "—"}
                      </td>
                      <td className="ant-table-cell" style={{ padding: 8 }}>
                        {r.Adjunto ? (
                          <a href={r.Adjunto} target="_blank" rel="noreferrer">
                            descargar
                          </a>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="ant-table-cell" style={{ padding: 8 }}>
                        {r.FechaHoraEnvio
                          ? dayjs(r.FechaHoraEnvio).format("YYYY-MM-DD HH:mm")
                          : "—"}
                      </td>
                      <td className="ant-table-cell" style={{ padding: 8 }}>
                        {(() => {
                          const v = computeEstado(r);
                          return v ? (
                            <Tag color={estadoColor(v)}>{v}</Tag>
                          ) : (
                            "—"
                          );
                        })()}
                      </td>

                      <td className="ant-table-cell" style={{ padding: 8 }}>
                        {(() => {
                          const s = String(r.Tiene_Whatsapp ?? "")
                            .trim()
                            .toLowerCase();
                          if (s === "si" || s === "sí")
                            return <Tag color="green">Sí</Tag>;
                          if (s === "no") return <Tag color="red">No</Tag>;
                          return <Tag>—</Tag>;
                        })()}
                      </td>
                      <td className="ant-table-cell" style={{ padding: 8 }}>
                        {r.Campana || "—"}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>

          {/* Footer: rango + paginación */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 16,
              flexWrap: "wrap",
            }}
          >
            <Text type="secondary">
              {total > 0 ? (
                <>
                  Mostrando <b>{startIdx + 1}</b>–<b>{endIdx}</b> de{" "}
                  <b>{total}</b> registros (filtrados de {rows.length}).
                </>
              ) : (
                <>
                  Mostrando <b>0</b> de <b>{rows.length}</b> registros.
                </>
              )}
            </Text>

            <Pagination
              current={page}
              pageSize={pageSize}
              total={total}
              showSizeChanger
              pageSizeOptions={[10, 20, 50, 100]}
              onChange={(p, ps) => {
                setPage(p);
                if (ps !== pageSize) {
                  setPageSize(ps);
                  const newMaxPage = Math.max(1, Math.ceil(total / ps));
                  if (p > newMaxPage) setPage(newMaxPage);
                }
              }}
              showTotal={(t, range) => `${range[0]}–${range[1]} de ${t}`}
            />
          </div>
        </Space>
      </Card>
    </div>
  );
}
