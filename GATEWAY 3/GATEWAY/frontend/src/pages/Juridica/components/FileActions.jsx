import React from "react";
import { Upload, Button, Space, message } from "antd";
import { UploadOutlined, DownloadOutlined } from "@ant-design/icons";
import * as XLSX from "xlsx";
import mammoth from "mammoth";
import { API_URL_GATEWAY } from "../../../config";

const FileActions = ({ tabKey, onFileLoad, onVariablesLoad, onDataExtracted, onExcelNameLoad }) => {
  const handleExcelUpload = async ({ file, onSuccess, onError }) => {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const uploadResponse = await fetch(`${API_URL_GATEWAY}/gateway/juridica/upload_preforma_impulso`, {
        method: "POST",
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error("Error subiendo el archivo al servidor");
      }
      
      const result = await uploadResponse.json();
      const excelFilename = result.excelFilename || file.name;
      
      if (onExcelNameLoad) {
        onExcelNameLoad(excelFilename); 
      }
      
      message.success("✅ Archivo Excel subido correctamente");
      onSuccess();
      

      const reader = new FileReader();
      reader.onload = (e) => {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: "array" });
        const worksheet = workbook.Sheets[workbook.SheetNames[0]];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: "" });

        if (jsonData.length > 0) {
          const variables = jsonData[0]
          .filter((v) => !!v)
          .map(v => v.trim().toLowerCase().replace(/ /g, "_")); // 🛠️ Normalización          
          const dataRows = jsonData.slice(1);

          console.log("🔥 Variables detectadas:", variables);
          console.log("🔥 Datos detectados:", dataRows);
          console.log("📍 Estoy cargando archivo en TAB:", tabKey);

          console.log("🚀 Enviando variables al padre:", variables)
          onVariablesLoad(variables);
          onDataExtracted(dataRows);
        } else {
          message.error("El archivo debe tener encabezados visibles.");
        }
      };

      reader.readAsArrayBuffer(file);
    } catch (error) {
      console.error(error);
      message.error("❌ Error cargando Excel");
      onError(error);
    }
  };

  const handleWordUpload = async ({ file, onSuccess, onError }) => {
    try {
      const arrayBuffer = await file.arrayBuffer();
      const { value } = await mammoth.convertToHtml({ arrayBuffer });
      onFileLoad(value);
      onSuccess();
    } catch (error) {
      console.error(error);
      message.error("❌ Error leyendo el Word");
      onError(error);
    }
  };

  const downloadPlantilla = () => {
    const worksheet = XLSX.utils.aoa_to_sheet([
      ["Nombre", "Fecha", "Ciudad"],
      ["Nombre", "Fecha", "Ciudad"],
      ["Juan", "2025-04-30", "Bogotá"],
    ]);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Plantilla");
    XLSX.writeFile(workbook, "Plantilla_Impulso.xlsx");
  };

  return (
    <div style={{ textAlign: "center" }}>
      <Space wrap size="middle">
        <Upload customRequest={handleWordUpload} showUploadList={false}>
          <Button type="primary" icon={<UploadOutlined />} style={{ backgroundColor: "#662480", borderColor: "#662480" }}>
            Cargar Documento
          </Button>
        </Upload>

        <Button
          type="primary"
          icon={<DownloadOutlined />}
          onClick={downloadPlantilla}
          style={{ backgroundColor: "#90BC1F", borderColor: "#90BC1F" }}
        >
          Descargar Plantilla
        </Button>

        <Upload customRequest={handleExcelUpload} showUploadList={false}>
          <Button type="primary"   accept=".xlsx, .xls" icon={<UploadOutlined />} style={{ backgroundColor: "#EE8D00", borderColor: "#EE8D00" }}>
            Cargar Impulso
          </Button>
        </Upload>
      </Space>
    </div>
  );
};

export default FileActions;
