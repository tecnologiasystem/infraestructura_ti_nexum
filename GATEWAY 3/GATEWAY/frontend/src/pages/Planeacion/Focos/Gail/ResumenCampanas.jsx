import React, { useEffect, useState } from "react";
import { Table, Spin, Checkbox } from "antd";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

const LULA_API_KEY = "api-019635c2310270bf8696ca8da0fc5c73-aaIlCeOBlk-LKeCeKqlFWPpvGn9PGOP4YrnY6VR4rao";

const ResumenCampañas = () => {
  const [campañasActivasGail, setCampañasActivasGail] = useState([]);
  const [resumen, setResumen] = useState([]);
  const [loading, setLoading] = useState(false);
  const [outcomesDisponibles, setOutcomesDisponibles] = useState([]);
  const [outcomesSeleccionados, setOutcomesSeleccionados] = useState([]);

  useEffect(() => {
    const fetchCampañas = async () => {
      try {
        const response = await fetch("https://api.lula.com/v1/campaigns", {
          headers: {
            accept: "text/plain",
            "X-API-Key": LULA_API_KEY,
          },
        });
        const campaigns = await response.json();
        const activas = campaigns.filter(c => c.status === "active");
        setCampañasActivasGail(activas);

        // Buscar outcomes disponibles al cargar campañas
        const touchpointsPorCampaña = await Promise.all(
          activas.map(async (campana) => {
            const res = await fetch(
              `https://api.lula.com/v1/campaigns/${campana.id}/touchpoints?limit=1000&page=1`,
              {
                headers: {
                  accept: "text/plain",
                  "X-API-Key": LULA_API_KEY,
                },
              }
            );
            const json = await res.json();
            return json.data || [];
          })
        );
        const allTouchpoints = touchpointsPorCampaña.flat();
        const outcomesUnicos = Array.from(new Set(allTouchpoints.map(tp => tp.outcome?.toLowerCase()).filter(Boolean)));
        setOutcomesDisponibles(outcomesUnicos);
      } catch (error) {
        console.error("Error al cargar campañas:", error);
      }
    };
    fetchCampañas();
  }, []);

  useEffect(() => {
    const fetchTouchpoints = async () => {
      if (outcomesSeleccionados.length === 0 || campañasActivasGail.length === 0) {
        setResumen([]);
        return;
      }

      setLoading(true);
      const resultados = await Promise.all(
        campañasActivasGail.map(async (campana) => {
          const res = await fetch(
            `https://api.lula.com/v1/campaigns/${campana.id}/touchpoints?limit=1000&page=1`,
            {
              headers: {
                accept: "text/plain",
                "X-API-Key": LULA_API_KEY,
              },
            }
          );
          const touchpoints = await res.json();
          const data = touchpoints.data || [];

          const coincidencias = data.filter(tp =>
            outcomesSeleccionados.includes(tp.outcome?.toLowerCase())
          );

          return {
            campana: campana.name,
            total: data.length,
            coincidencias: coincidencias.length,
            porcentaje: data.length > 0 ? `${((coincidencias.length / data.length) * 100).toFixed(0)}%` : "0%",
          };
        })
      );

      const ordenado = resultados.sort((a, b) => b.coincidencias - a.coincidencias);
      setResumen(ordenado);
      setLoading(false);
    };

    fetchTouchpoints();
  }, [outcomesSeleccionados]);

  const columns = [
    { title: "Campaña", dataIndex: "campana", key: "campana" },
    { title: "Contactos Totales", dataIndex: "total", key: "total" },
    { title: "Coincidencias", dataIndex: "coincidencias", key: "coincidencias" },
    { title: "% Resultado", dataIndex: "porcentaje", key: "porcentaje" },
  ];

  return (
    <div>
      <h2>Resumen filtrado por Outcomes</h2>

      <div style={{ marginBottom: 24 }}>
        <Checkbox.Group
          options={outcomesDisponibles.map(o => ({ label: o, value: o }))}
          value={outcomesSeleccionados}
          onChange={setOutcomesSeleccionados}
        />
      </div>

      <Spin spinning={loading} tip="Cargando campañas y resultados...">
        <Table
          dataSource={resumen}
          columns={columns}
          rowKey="campana"
          pagination={false}
          bordered
        />

        {resumen.length > 0 && (
          <>
            <h3 style={{ marginTop: 32 }}>Comparativo visual</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={resumen}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="campana" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="coincidencias" fill="#1890ff" />
              </BarChart>
            </ResponsiveContainer>
          </>
        )}
      </Spin>
    </div>
  );
};

export default ResumenCampañas;