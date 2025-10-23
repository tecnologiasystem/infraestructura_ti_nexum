// ImpulsoProcesalPage.jsx
import React, { useState } from "react";
import { Tabs, Button, Typography, Space, Input, message } from "antd";
import { PlusOutlined, FileZipOutlined } from "@ant-design/icons";
import FileActions from "../components/FileActions";
import EditorWithDropdown from "../components/EditorWithDropdown";
import ActionButtons from "../components/ActionButtons";
import "../styles/impulsoStyles.css";
import { v4 as uuidv4 } from "uuid";
import { API_URL_GATEWAY } from "../../../config";

const { Title } = Typography;
const { TabPane } = Tabs;
const COLORS = ["#EE8D00", "#36A2DA", "#90BC1F", "#662480", "#000F9F"];

const ImpulsoProcesalPage = () => {
  const randomColor = COLORS[Math.floor(Math.random() * COLORS.length)];
  
  const [tabs, setTabs] = useState([
    { key: "1", label: "Impulso 1", content: "", color: randomColor, variables: [], excelData: [] }
  ]);
  const [variables, setVariables] = useState([]);
  const [excelFilename, setExcelFilename] = useState("");


  const [activeKey, setActiveKey] = useState("1");
  const [processId] = useState(uuidv4().slice(0,6));

  const addTab = () => {
    const newKey = `${Date.now()}`;
    const randomColor = COLORS[Math.floor(Math.random() * COLORS.length)];
    const newTabs = [...tabs, { key: newKey, label: "Nuevo Impulso", content: "", color: randomColor, variables: [], excelData: [] }];
    setTabs(newTabs);
    setActiveKey(newKey);
  };

  const removeTab = (targetKey) => {
    let newActiveKey = activeKey;
    let lastIndex = -1;
    tabs.forEach((tab, i) => {
      if (tab.key === targetKey) lastIndex = i - 1;
    });
    const newTabs = tabs.filter((tab) => tab.key !== targetKey);
    if (newTabs.length && newActiveKey === targetKey) {
      newActiveKey = lastIndex >= 0 ? newTabs[lastIndex].key : newTabs[0].key;
    }
    setTabs(newTabs);
    setActiveKey(newActiveKey);
  };

  const updateTabLabel = (e, key) => {
    const newTabs = tabs.map((tab) =>
      tab.key === key ? { ...tab, label: e.target.value } : tab
    );
    setTabs(newTabs);
  };

  const updateTabContent = (key, content) => {
    const newTabs = tabs.map((tab) =>
      tab.key === key ? { ...tab, content } : tab
    );
    setTabs(newTabs);
  };

  const updateTabVariables = (key, variables) => {
    const cleanedVars = variables.map(v => v.trim());
    console.log("🧪 Recibo en updateTabVariables:", cleanedVars); // <<<<<< agrega esto

    setTabs(prevTabs => 
      prevTabs.map(tab => 
        tab.key === key ? { 
          ...tab, 
          variables: [...new Set(cleanedVars)]
        } : tab
      )
    );
  };
  
  const updateTabExcelData = (key, excelData) => {
    const newTabs = tabs.map((tab) =>
      tab.key === key ? { ...tab, excelData } : tab
    );
    setTabs(newTabs);
  };

  const handleZipDownload = async () => {
    try {
      const response = await fetch(`${API_URL_GATEWAY}/juridica/exportar_cartas_impulso?processId=${processId}`);
      if (!response.ok) throw new Error("Error descargando ZIP");

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `CartasImpulso_${processId}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();

      message.success("ZIP descargado correctamente");
    } catch (error) {
      console.error(error);
      message.error("Error descargando ZIP");
    }
  };

  return (
    <div className="container">
      <div className="header-top">
        <Title level={2}>Gestión de Impulsos Procesales</Title>
        <Space>
          <Button
            type="primary"
            icon={<FileZipOutlined />}
            onClick={handleZipDownload}
            style={{
              height: "30px",
              width: "160px",
              backgroundColor: "#36A2DA",
              borderColor: "#36A2DA",
              fontSize: "14px",
            }}
          >
            Exportar ZIP
          </Button>
        </Space>
      </div>

      <Tabs
        type="editable-card"
        onChange={(key) => setActiveKey(key)}
        activeKey={activeKey}
        onEdit={(targetKey, action) => {
          if (action === "add") addTab();
          else removeTab(targetKey);
        }}
        addIcon={<PlusOutlined />}
        className="custom-tabs"
      >
        {tabs.map((tab) => (
          <TabPane
            tab={
              <div
                style={{
                  backgroundColor: tab.color,
                  borderRadius: "6px",
                  color: "white",
                  fontWeight: "bold",
                  textAlign: "center",
                  minWidth: "120px",
                  height: "4vh"
                }}
              >
                <Input
                  value={tab.label}
                  onChange={(e) => updateTabLabel(e, tab.key)}
                  bordered={false}
                  style={{
                    backgroundColor: "transparent",
                    color: "white",
                    textAlign: "center",
                    marginTop: "-5px",
                  }}
                />
              </div>
            }
            key={tab.key}
          >
            <Space direction="vertical" size="large" style={{ width: "100%" }}>
              <FileActions
                tabKey={tab.key}
                onFileLoad={(content) => updateTabContent(tab.key, content)}
                onVariablesLoad={(vars) => setVariables(vars)}  // ✅ actualiza el estado global directamente
                onDataExtracted={(rows) => updateTabExcelData(tab.key, rows)}
                onExcelNameLoad={(name) => setExcelFilename(name)}
              />

              <EditorWithDropdown
                  key={`editor-${tab.key}-${tab.variables.join("-")}`} // 👈 fuerza re-render cuando cambian

                editorContent={tab.content}
                setEditorContent={(content) => updateTabContent(tab.key, content)}
                availableVariables={variables}  // ✅ ahora viene del estado global
                />

              <ActionButtons
                editorContent={tab.content}
                excelData={tab.excelData}
                variables={tab.variables}
                processId={processId}
                excelFilename={excelFilename}
              />
            </Space>
          </TabPane>
        ))}
      </Tabs>
    </div>
  );
};

export default ImpulsoProcesalPage;
