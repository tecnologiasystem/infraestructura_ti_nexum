import React, { useEffect, useState } from 'react';
import {
  FunnelChart,
  Funnel,
  Tooltip,
  ResponsiveContainer
} from 'recharts';
import { API_URL_GATEWAY } from "../../config";


export default function EmbudoContactabilidad() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_URL_GATEWAY}/gateway/embudo/funnel`)
      .then(res => { if (!res.ok) throw new Error(`Error ${res.status}`); return res.json(); })
      .then(json => {
        const ordered = json.sort((a, b) => b.cnt - a.cnt);
        setData(ordered);
        setLoading(false);
      })
      .catch(err => { setError(err.message); setLoading(false); });
  }, []);

  if (loading) return <div style={{ textAlign: 'center', padding: '2rem' }}>Cargando embudo...</div>;
  if (error) return <div style={{ textAlign: 'center', color: 'red', padding: '2rem' }}>Error: {error}</div>;

  const total = data[0]?.cnt || 0;
  const displayData = data.map(item => ({
    name: item.etapa,
    value: item.cnt,
    percent: total ? (item.cnt / total) * 100 : 0
  }));

  return (
    <div style={{ maxWidth: 900, margin: '2rem auto', padding: '2rem', backgroundColor: '#fff', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
      <h2 style={{ textAlign: 'center', marginBottom: '1.5rem', color: '#333' }}>Embudo</h2>
      {/* Contenedor para rotar solo el embudo 90° a la izquierda */}
      <div style={{ position: 'relative', width: '100%', height: 300, overflow: 'hidden' }}>
        <div style={{
          position: 'absolute',
          top: '25%',
          left: '50%',
          width: '55%',
          height: '300%',
          transform: 'translate(-50%, -50%) rotate(-90deg)',
          transformOrigin: 'center center'
        }}>
          <ResponsiveContainer width="100%" height="100%">
            <FunnelChart layout="horizontal" margin={{ top: 20, bottom: 20, left: 50, right: 50 }}>
              <defs>
                <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#2563eb" stopOpacity={0.8}/>
                  <stop offset="100%" stopColor="#60a5fa" stopOpacity={0.8}/>
                </linearGradient>
              </defs>
              <Tooltip
                cursor={false}
                formatter={(value, name) => [name === 'value' ? value.toLocaleString() : `${value.toFixed(1)}%`, name === 'value' ? 'Cantidad' : 'Porcentaje']}
                labelFormatter={() => ''}
              />
              <Funnel
                dataKey="value"
                data={displayData}
                isAnimationActive
                stroke="#fff"
                fill="url(#grad)"
                orientation="horizontal"
                label={false}
              />
            </FunnelChart>
          </ResponsiveContainer>
        </div>
      </div>
      {/* Leyenda sin rotación */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1rem' }}>
        {displayData.map((item, idx) => (
          <div key={idx} style={{ textAlign: 'center', flex: 1 }}>
            <div style={{ fontSize: '1rem', fontWeight: 600, color: '#1e293b' }}>{item.percent.toFixed(1)}%</div>
            <div style={{ fontSize: '0.9rem', color: '#475569', marginTop: 4 }}>{item.value.toLocaleString()}</div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: 4 }}>{item.name}</div>
          </div>
        ))}
      </div>
    </div>
  );
}