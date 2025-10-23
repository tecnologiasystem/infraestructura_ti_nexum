import React, { useState, useEffect } from "react";
import { Button, Spin, message, Row, Col, Card, Typography } from "antd";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LabelList} from "recharts";
import axios from "axios";
import { API_URL_GATEWAY } from "../../config";  // Asegúrate de tener la URL de tu API correctamente configurada

const { Title } = Typography;

const FocoDataChart = () => {
  const [focoTrabajableCount, setFocoTrabajableCount] = useState(0);
  const [focoResultadoCount, setFocoResultadoCount] = useState(0);
  const [loading, setLoading] = useState(false);

  // Fetch data from both endpoints
  const fetchFocoData = async () => {
    setLoading(true);
    try {
      const filtros = {};  // Asegúrate de pasar los filtros correctos
      const [focoTrabajableRes, focoResultadoRes] = await Promise.all([
        axios.post(`${API_URL_GATEWAY}/gateway/focos/trabajable/consultar`, filtros),
        axios.post(`${API_URL_GATEWAY}/gateway/focos/resultado/consultar`, filtros),
      ]);

      // Suponiendo que los endpoints retornan los resultados en un array
      setFocoTrabajableCount(focoTrabajableRes.data.length); // Cantidad de registros de foco trabajable
      setFocoResultadoCount(focoResultadoRes.data.length);  // Cantidad de registros de foco resultado

      message.success("Datos cargados correctamente");
    } catch (error) {
      console.error(error);
      message.error("Error al cargar los datos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFocoData();
  }, []);

  // Datos para el gráfico
  const chartData = [
    { name: "Foco Trabajable", registros: focoTrabajableCount },
    { name: "Foco Resultado", registros: focoResultadoCount },
  ];

  return (
    <div style={{ padding: "20px" }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: "16px" }}>
        <Col>
          <Title level={3}>Análisis de Foco</Title>
        </Col>
        <Col>
          <Button 
            type="primary" 
            onClick={fetchFocoData} 
            loading={loading}
            style={{ marginBottom: '20px' }}
          >
            Cargar Datos
          </Button>
        </Col>
      </Row>

      <Row gutter={32}>
        <Col span={24}>
          <Card>
            <Title level={4}>Distribución de Foco</Title>
            {loading ? (
              <Spin size="large" />
            ) : (
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="registros" fill="#8884d8">
                    <LabelList dataKey="registros" position="top" />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default FocoDataChart;
