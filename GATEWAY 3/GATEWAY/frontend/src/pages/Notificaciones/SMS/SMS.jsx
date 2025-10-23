// 1. SMS.jsx (Frontend React)

import React, { useState } from "react";
import { Card, Tabs, Input, Button, Upload, Modal, Table, Row, Col, message as antMessage } from "antd";
import { UploadOutlined, DownloadOutlined, SendOutlined, EyeOutlined } from "@ant-design/icons";
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";
import { API_URL_GATEWAY } from "../../../config"; // Asegúrate que tu config apunte al /gateway
import "./SMS.css";

const { TabPane } = Tabs;
const { TextArea } = Input;

const SMS = () => {
  const [fileList, setFileList] = useState([]);
  const [excelData, setExcelData] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [indicador, setIndicador] = useState("+57");
  const [numero, setNumero] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [resultados, setResultados] = useState([]);

  const handleDescargarPlantilla = () => {
    const workbook = XLSX.utils.book_new();
    const worksheetData = [["TEL1", "SMS"], ["+573002007388", "Texto del mensaje"]];
    const worksheet = XLSX.utils.aoa_to_sheet(worksheetData);
    XLSX.utils.book_append_sheet(workbook, worksheet, "PlantillaSMS");
    const excelBuffer = XLSX.write(workbook, { bookType: "xlsx", type: "array" });
    const data = new Blob([excelBuffer], { type: "application/octet-stream" });
    saveAs(data, "plantilla_sms.xlsx");
  };

  const handleUpload = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const data = new Uint8Array(e.target.result);
      const workbook = XLSX.read(data, { type: "array" });
      const worksheet = workbook.Sheets[workbook.SheetNames[0]];
      const jsonData = XLSX.utils.sheet_to_json(worksheet);
      setExcelData(jsonData);
    };
    reader.readAsArrayBuffer(file);
    setFileList([file]);
    return false;
  };

  const handleEnviarSMSIndividual = async () => {
    if (!indicador || !numero || !mensaje) {
      antMessage.warning("Por favor completa todos los campos");
      return;
    }
    try {
      const payload = { telefono: indicador + numero, mensaje: mensaje };
      const response = await fetch(`${API_URL_GATEWAY}/gateway/sms/enviar_individual`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (response.ok) {
        antMessage.success("SMS enviado exitosamente 🎉");
        setIndicador("+57");
        setNumero("");
        setMensaje("");
      } else {
        antMessage.error(`Error enviando SMS: ${data.error}`);
      }
    } catch (error) {
      antMessage.error("Error de conexión al enviar SMS 📡");
    }
  };

  const handleEnviarSMSMasivo = async () => {
    if (excelData.length === 0) {
      antMessage.warning("Primero sube un archivo de Excel");
      return;
    }
    const formData = new FormData();
    formData.append("archivo", fileList[0]);
    try {
      const response = await fetch(`${API_URL_GATEWAY}/sms/enviar_masivo`, {
        method: "POST",
        body: formData
      });
      const data = await response.json();
      if (response.ok) {
        antMessage.success("Envío masivo completado 🎉");
        setResultados(data.resultado || []);
      } else {
        antMessage.error(`Error en envío masivo: ${data.error}`);
      }
    } catch (error) {
      antMessage.error("Error de conexión al enviar SMS masivo 📡");
    }
  };

  return (
    <div className="sms-container">
      <h1 className="sms-titulo">Gestión de SMS</h1>

      <Card className="sms-card">
        <Tabs defaultActiveKey="1" centered>
          <TabPane tab="Envío Individual" key="1">
            <Row gutter={16} justify="center">
              <Col span={6}>
                <Input placeholder="+Indicador" value={indicador} onChange={(e) => setIndicador(e.target.value)} />
              </Col>
              <Col span={18}>
                <Input placeholder="Número de teléfono" value={numero} onChange={(e) => setNumero(e.target.value)} />
              </Col>
            </Row>
            <Row gutter={16} style={{ marginTop: 20 }} justify="center">
              <Col span={24}>
                <TextArea rows={4} placeholder="Escribe tu mensaje aquí..." value={mensaje} onChange={(e) => setMensaje(e.target.value)} />
                <div style={{ textAlign: "right", marginTop: "5px", color: "#555" }}>{mensaje.length} caracteres</div>
              </Col>
            </Row>
            <div className="sms-acciones">
              <Button type="primary" icon={<SendOutlined />} onClick={handleEnviarSMSIndividual}>Enviar SMS</Button>
            </div>
          </TabPane>

          <TabPane tab="Envío Masivo" key="2">
            <Row gutter={26} justify="center">
              <Col>
                <Button type="primary" icon={<DownloadOutlined />} onClick={handleDescargarPlantilla}>Descargar Plantilla</Button>
              </Col>
              <Col>
                <Upload beforeUpload={handleUpload} fileList={fileList} showUploadList={false}>
                  <Button icon={<UploadOutlined />}>Subir Archivo</Button>
                </Upload>
              </Col>
              {excelData.length > 0 && (
                <Col>
                  <Button type="default" icon={<EyeOutlined />} onClick={() => setIsModalVisible(true)}>Ver Registros</Button>
                </Col>
              )}
            </Row>

            <Row style={{ marginTop: 20 }} justify="center">
              <Col span={24} style={{ textAlign: "center" }}>
                <p>Registros cargados: <strong>{excelData.length}</strong></p>
              </Col>
            </Row>

            <div className="sms-acciones">
              <Button type="primary" icon={<SendOutlined />} onClick={handleEnviarSMSMasivo}>Enviar Masivo</Button>
            </div>

            {/* Mostrar resultados de envío masivo */}
            {resultados.length > 0 && (
              <Table
                columns={[
                  { title: "Teléfono", dataIndex: "telefono", key: "telefono" },
                  { title: "Mensaje", dataIndex: "mensaje", key: "mensaje" },
                  { title: "Estado", dataIndex: "estado", key: "estado" }
                ]}
                dataSource={resultados}
                rowKey={(record, index) => index}
                pagination={false}
              />
            )}
          </TabPane>
        </Tabs>
      </Card>

      <Modal
        title="Registros Cargados"
        visible={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
        width={800}
      >
        <div style={{ overflowX: "auto", overflowY: "auto", maxHeight: "500px" }}>
          <Table
            columns={excelData.length ? Object.keys(excelData[0]).map((key) => ({ title: key, dataIndex: key, key })) : []}
            dataSource={excelData}
            rowKey={(record, index) => index}
            pagination={false}
            scroll={{ x: "max-content" }}
          />
        </div>
      </Modal>
    </div>
  );
};

export default SMS;
