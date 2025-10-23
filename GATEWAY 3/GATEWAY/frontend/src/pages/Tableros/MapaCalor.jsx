import React, { useEffect, useState } from "react";
import { Table } from "antd";
import axios from "axios";
import { API_URL_GATEWAY } from "../../config";


// Colores según valor
const getBackgroundColor = (value) => {
  if (value >= 50) return "#b7eb8f";     // verde claro
  if (value >= 20) return "#ffe58f";     // amarillo claro
  return "#ffa39e";                      // rojo claro
};

// Definición de columnas compactas
const columns = [
  {
    title: "Hora",
    dataIndex: "hora",
    key: "hora",
    align: "center",
    width: 50,
    render: (v) => (
      <div style={{ padding: "2px", fontSize: "12px", textAlign: "center" }}>
        {v}
      </div>
    )
  },
  {
    title: "% Contestadas",
    dataIndex: "contestadas_pct",
    width: 80,
    render: (v) => (
      <div style={{
        backgroundColor: getBackgroundColor(v),
        padding: "2px",
        textAlign: "center",
        fontSize: "12px"
      }}>
        {Math.round(v)}%
      </div>
    )
  },
  {
    title: "% Abandonadas",
    dataIndex: "abandonadas_pct",
    width: 80,
    render: (v) => (
      <div style={{
        backgroundColor: getBackgroundColor(100 - v),
        padding: "2px",
        textAlign: "center",
        fontSize: "12px"
      }}>
        {Math.round(v)}%
      </div>
    )
  },
  {
    title: "% Contacto Efectivo",
    dataIndex: "contacto_efectivo_pct",
    width: 80,
    render: (v) => (
      <div style={{
        backgroundColor: getBackgroundColor(v),
        padding: "2px",
        textAlign: "center",
        fontSize: "12px"
      }}>
        {Math.round(v)}%
      </div>
    )
  },
  {
    title: "% Promesas de Pago",
    dataIndex: "promesas_pago_pct",
    width: 80,
    render: (v) => (
      <div style={{
        backgroundColor: getBackgroundColor(v),
        padding: "2px",
        textAlign: "center",
        fontSize: "12px"
      }}>
        {Math.round(v)}%
      </div>
    )
  },
];

// Componente principal
const Mapa = () => {
  const [datos, setDatos] = useState([]);

  useEffect(() => {
    axios.get(`${API_URL_GATEWAY}/gateway/embudo/efectividad-por-hora`)
      .then((res) => setDatos(res.data))
      .catch((err) => console.error("Error cargando datos:", err));
  }, []);

  return (
    <div style={{ margin: "20px" }}>
        <h3 style={{ textAlign: "center" }}>Mapa de Calor x Hora</h3>
      <Table
        columns={columns}
        dataSource={datos}
        rowKey="hora"
        pagination={false}
        size="small"
        scroll={{ x: 400 }}
      />
    </div>
  );
};

export default Mapa;
