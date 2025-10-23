import React, { useState, useMemo } from "react";
import { Upload, Button, Table, message, Card } from "antd";
import { UploadOutlined } from "@ant-design/icons";
import { API_URL_GATEWAY } from "../../../config";

const SubirExcelPrediccion = () => {
  const [file, setFile] = useState(null);
  const [rawData, setRawData] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) {
      message.warning("Selecciona un archivo Excel.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    try {
      const response = await fetch(`${API_URL_GATEWAY}/gateway/IA/subir_y_predecir`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("Error al procesar el archivo");

      const resultado = await response.json();
      setRawData(resultado);
      message.success("Archivo procesado correctamente");
    } catch (error) {
      console.error(error);
      message.error("Error al procesar el archivo");
    } finally {
      setLoading(false);
    }
  };

  const cargarPredicciones = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL_GATEWAY}/gateway/IA/predicciones`);
      if (!response.ok) throw new Error("Error al obtener predicciones");
      const data = await response.json();
      setRawData(data);
      message.success("Predicciones obtenidas correctamente");
    } catch (err) {
      console.error(err);
      message.error("Error al obtener predicciones");
    } finally {
      setLoading(false);
    }
  };
  const columns = [
    { title: "Teléfono", dataIndex: "telefono", key: "telefono" },
    { title: "Día", dataIndex: "dia", key: "dia" },
    { title: "Hora", dataIndex: "hora", key: "hora" },
    { title: "Probabilidad de Contacto", dataIndex: "probabilidad_contacto", key: "probabilidad_contacto", render: (val) => `${val.toFixed(1)}%` },
    { title: "Fecha Recomendada", dataIndex: "fecha_futura_recomendada", key: "fecha_futura_recomendada" },
  ];

  return (
    <Card>
      <h1 className="excel-tittle">Probabilidad de Contacto</h1>

      <Upload
        accept=".xlsx,.xls,.csv"
        beforeUpload={(file) => {
          setFile(file);
          return false;
        }}
        onRemove={() => setFile(null)}
        fileList={file ? [file] : []}
      >
        <Button icon={<UploadOutlined />}>Seleccionar Archivo</Button>
      </Upload>

      <Button
        type="primary"
        onClick={handleUpload}
        disabled={!file}
        loading={loading}
        style={{ marginTop: 16 }}
      >
        Subir y Predecir
      </Button>

      <Button
        type="default"
        onClick={cargarPredicciones}
        style={{ marginLeft: 8 }}
      >
        Cargar Predicciones
      </Button>

      <div style={{ marginTop: 32 }}>
        <Table
          columns={columns}
          dataSource={rawData.map((item, idx) => ({ ...item, key: idx }))}
          pagination={{ pageSize: 10 }}
        />
      </div>
    </Card>
  );
};

export default SubirExcelPrediccion;