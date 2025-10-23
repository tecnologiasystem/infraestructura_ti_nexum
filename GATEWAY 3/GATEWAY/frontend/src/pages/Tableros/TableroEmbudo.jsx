import React, { useState } from "react";
import { Tabs } from "antd";
import DonutCampaign from "./DonuntCampaign";
import EmbudoContactabilidad from "./Embudo";
import GraficoCommitment from "./GraficoCompromisos";
import Mapa from "./MapaCalor";

const { TabPane } = Tabs;

const TableroEmbudo = () => {
  const [activeKey, setActiveKey] = useState("donut");

  const renderContent = () => {
    switch (activeKey) {
      case "donut":
        return <DonutCampaign />;
      case "embudo":
        return <EmbudoContactabilidad />;
      case "commitment":
        return <GraficoCommitment />;
      case "mapa":
        return <Mapa />;
      default:
        return null;
    }
  };

  return (
    <div style={{ padding: '1rem' }}>
      <h1 style={{ textAlign: 'center', color:'#000F9F' }}>Tablero de Control Contacto</h1>
      <Tabs
        defaultActiveKey="donut"
        onChange={(key) => setActiveKey(key)}
        centered
        type="card"
      >
        <TabPane tab="Campañas" key="donut" />
        <TabPane tab="Embudo" key="embudo" />
        <TabPane tab="Compromisos" key="commitment" />
        <TabPane tab="Mapa Calor" key="mapa" />
      </Tabs>

      <div style={{ marginTop: "2rem" }}>
        {renderContent()}
      </div>
    </div>
  );
};

export default TableroEmbudo;
