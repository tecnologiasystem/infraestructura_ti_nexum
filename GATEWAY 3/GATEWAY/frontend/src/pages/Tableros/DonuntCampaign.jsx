// src/components/DonutCampaign.jsx
import React, { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { API_URL_GATEWAY } from "../../config";


export default function DonutCampaign() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Aquí tu paleta exacta de colors.js:
  const COLORS = [
    '#36A2DA', // Azul claro
    '#EE8D00', // Naranja
    '#90BC1F', // Verde
    '#662480', // Morado
  ];

useEffect(() => {
  const idUsuario = localStorage.getItem("idUsuario");
  const rol = localStorage.getItem("rol");

  console.log("idUsuario:", idUsuario, "rol:", rol);

  if (!idUsuario || !rol) {
    console.error("❌ idUsuario o rol no están definidos en localStorage");
    return;
  }

  fetch(`${API_URL_GATEWAY}/gateway/embudo/by-campaign?idUsuario=${idUsuario}&rol=${rol}`)
    .then(res => {
      if (!res.ok) throw new Error(`Error ${res.status}`);
      return res.json();
    })
    .then(json => {
      setData(json);
      setLoading(false);
    })
    .catch(err => {
      setError(err.message);
      setLoading(false);
    });
}, []);


  if (loading) return <div style={{ textAlign: 'center', padding: '2rem' }}>Cargando datos...</div>;
  if (error)   return <div style={{ textAlign: 'center', color: 'red', padding: '2rem' }}>Error: {error}</div>;

  return (
    <div style={{
      maxWidth: 800, margin: '2rem auto',
      backgroundColor: '#fff', padding: '2rem',
      borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
    }}>
      <h3 style={{ textAlign: 'center', marginBottom: '1rem', color: '#333' }}>
        Asiganciones del día por Campaña Cliente
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={80}
            outerRadius={120}
            paddingAngle={2}
            label={({ percent }) => `${(percent * 100).toFixed(1)}%`}
            labelLine={false}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip formatter={(value) => value.toLocaleString()} />
          <Legend
            layout="vertical"
            align="left"
            verticalAlign="middle"
            iconType="circle"
            wrapperStyle={{ left: 0, top: '10%' }}
            formatter={(value) => {
              const item = data.find(d => d.name === value);
              return `${item.value.toLocaleString()}  ${value}`;
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
