import React, { useEffect, useState } from "react";
import { API_URL_GATEWAY } from "../../config";
import { Line } from "react-chartjs-2";
import axios from "axios";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const GraficoCommitment = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    axios.get(`${API_URL_GATEWAY}/gateway/embudo/commitments-acumulados`)
      .then(res => setData(res.data));
  }, []);

  const labels = data.map(d => `${d.hora}:00`);
  const today = data.map(d => d.cumsum_today);
  const twoWeeks = data.map(d => d.cumsum_2weeks);

  const chartData = {
    labels,
    datasets: [
      {
        label: "Compromisos Hoy",
        data: today,
        borderColor: "green",
        backgroundColor: "green",
        fill: false,
        tension: 0.3
      },
      {
        label: "Compromisos hace 2 Semanas",
        data: twoWeeks,
        borderColor: "purple",
        backgroundColor: "rgba(128, 0, 128, 0.3)",
        fill: true,
        tension: 0.3
      }
    ]
  };

  return (
    <div style={{ width: "90%", margin: "0 auto" }}>
      <h3 style={{ textAlign: "center" }}>% Acumulativo de Compromisos</h3>
      <Line data={chartData} />
    </div>
  );
};

export default GraficoCommitment;
