import React from "react";
import { Button, Space, message } from "antd";
import { FilePdfOutlined, FileWordOutlined, SendOutlined } from "@ant-design/icons";
import { saveAs } from "file-saver";
import { API_URL_GATEWAY } from "../../../config";
import { useNavigate } from "react-router-dom";

const ActionButtons = ({ editorContent, excelData, variables, processId, excelFilename }) => {
  const navigate = useNavigate();

  const handleGenerateDocuments = async (format) => {
    if (!excelData || !excelData.length || !editorContent || !processId || !excelFilename) {
      message.error("Faltan datos requeridos. Verifica que hayas cargado el Excel y escrito el contenido.");
      return;
    }

    console.log("📦 Enviando a backend:", {
      content: editorContent,
      processId: processId,
      excelFilename: excelFilename,
      output: format
    });

    try {
      const response = await fetch(`${API_URL_GATEWAY}/gateway/juridica/generar_documentos?output=${format}&preforma=1`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          content: editorContent,
          processId: processId,
          excelFilename: excelFilename
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Error generando los documentos");
      }

      const result = await response.json();
      message.success(result.message || "Documentos generados correctamente");

      // Descargar ZIP
      const zipResponse = await fetch(`${API_URL_GATEWAY}/gateway/juridica/exportar_cartas_impulso?processId=${processId}`);
      if (!zipResponse.ok) throw new Error("No se pudo descargar el ZIP");

      const zipBlob = await zipResponse.blob();
      saveAs(zipBlob, `Cartas_Impulso_${format}.zip`);
    } catch (error) {
      console.error("❌ Error:", error);
      message.error(error.message || "Error generando documentos");
    }
  };

  const handleSendProcess = () => {
    if (!processId) {
      message.error("No se ha generado un proceso aún.");
      return;
    }

    navigate(`/impulsoEmail?processId=${processId}`);
  };

  return (
    <div style={{ textAlign: "center", marginTop: "30px" }}>
      <Space size="large" wrap>
        <Button type="primary" icon={<FilePdfOutlined />} onClick={() => handleGenerateDocuments("pdf")}>
          Guardar PDF
        </Button>
        <Button type="primary" icon={<FileWordOutlined />} onClick={() => handleGenerateDocuments("word")}>
          Guardar DOCX
        </Button>
        <Button type="primary" icon={<SendOutlined />} onClick={handleSendProcess}>
          Enviar / Procesar
        </Button>
      </Space>
    </div>
  );
};

export default ActionButtons;
