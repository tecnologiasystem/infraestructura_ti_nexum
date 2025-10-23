import React, { useEffect, useState } from "react";
import { Card, Row, Col, Divider, Spin, message, Switch } from "antd";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { useNavigate } from "react-router-dom";
import * as AntIcons from "@ant-design/icons";
import { allowedColors, getGradient, isColorDark } from "../../config/colors";
import menuItems from "../../config/menuItems";
import "./InteligenciaArtificial.css"; // ✅ Asegúrate de tenerlo para que cada módulo tenga su propio CSS

const COLORS = ["#F39200", "#36A9E1", "#90BC1F", "#662483", "#000F9F"];

const dummyData = [
  { name: "Predicciones", value: 15 },
  { name: "Contactados", value: 10 },
  { name: "No Contactados", value: 5 },
];

const InteligenciaArtificial = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [userRole, setUserRole] = useState(null);
  const [mostrarGrafico, setMostrarGrafico] = useState(false); // 🔥 Por defecto apagado

  const getRandomColor = (index) => allowedColors[index % allowedColors.length];

  const iaSubItems = menuItems.find(item => item.key === 'ia')?.children || [];
  const iaMenuOptions = iaSubItems.filter(child => child.roles.includes(userRole));

  useEffect(() => {
    const rol = parseInt(localStorage.getItem("idRol")) || 0;
    setUserRole(rol);
  }, []);

  const handleSectionClick = (path) => {
    navigate(path);
  };

  const renderIcon = (iconName) => {
    const IconComponent = AntIcons[iconName];
    return IconComponent ? <IconComponent style={{ fontSize: "36px" }} /> : null;
  };

  return (
    <div className="inteligencia-container">
      <Row justify="space-between" align="middle" style={{ marginBottom: "16px" }}>
        <Col>
          <h1 style={{ fontWeight: "bold", fontSize: "26px", marginBottom: "10px" }}>Inteligencia Artificial</h1>
        </Col>
        {userRole === 1 && (
          <Col style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={{ fontWeight: 500 }}>Mostrar Gráficos</span>
            <Switch
              checked={mostrarGrafico}
              onChange={setMostrarGrafico}
              size="large"
            />
          </Col>
        )}
      </Row>

      <Row gutter={32}>
        <Col span={userRole === 1 && mostrarGrafico ? 6 : 24}>
          <Row gutter={[16, 16]}>
            {iaMenuOptions.map((item, index) => {
              const colorBase = getRandomColor(index);
              const gradient = getGradient(colorBase);
              const textColor = isColorDark(colorBase) ? "#ffffff" : "#333333";

              return (
                <Col xs={24} sm={12} md={12} lg={userRole === 1 && mostrarGrafico ? 24 : 6} key={item.key}>
                  <Card
                    hoverable
                    style={{
                      borderRadius: "20px",
                      background: gradient,
                      textAlign: "center",
                      boxShadow: "0px 4px 12px rgba(0, 0, 0, 0.1)",
                      color: textColor,
                      minHeight: "100px",
                      height: "100px",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "center",
                      cursor: "pointer",
                      transition: "all 0.3s ease-in-out",
                    }}
                    bodyStyle={{ padding: "12px" }}
                    className="custom-card"
                    onClick={() => handleSectionClick(item.path)}
                  >
                    {renderIcon(item.icon)}
                    <h3
                      style={{
                        marginTop: "8px",
                        fontFamily: "Montserrat",
                        fontWeight: "bold",
                        fontSize: "16px",
                        color: textColor,
                      }}
                    >
                      {item.label}
                    </h3>
                  </Card>
                </Col>
              );
            })}
          </Row>
        </Col>

        {userRole === 1 && mostrarGrafico && (
          <Col span={18}>
            <Card className="inteligencia-grafico">
              <h2 className="grafico-titulo">Distribución de Predicciones</h2>
              <Divider />
              {loading ? (
                <Spin size="large" />
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={dummyData}
                      dataKey="value"
                      nameKey="name"
                      outerRadius={120}
                      label
                      onClick={(data, index) => message.info(`Clic en ${data.name}`)}
                    >
                      {dummyData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </Card>
          </Col>
        )}
      </Row>
    </div>
  );
};

export default InteligenciaArtificial;
