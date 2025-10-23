import React from "react";
import { Upload, Button, message } from "antd";
import { UploadOutlined } from "@ant-design/icons";
import * as XLSX from "xlsx";

const ExcelUploader = ({ onVariablesExtracted, onDataExtracted }) => {
  const props = {
    beforeUpload: (file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: "array" });

        const worksheet = workbook.Sheets[workbook.SheetNames[0]];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

        if (jsonData.length < 3) {
          message.error("El archivo Excel debe tener mínimo 3 filas (descripciones, variables, datos).");
          return;
        }

        const variables = jsonData[1]; // fila 2
        const dataRows = jsonData.slice(2); // de la fila 3 en adelante

        onVariablesExtracted(variables);
        onDataExtracted(dataRows);
      };
      reader.readAsArrayBuffer(file);
      return false;
    },
    showUploadList: false,
    accept: ".xlsx",
  };

  return (
    <Upload {...props}>
      <Button
        icon={<UploadOutlined />}
        style={{
          height: "40px",
          width: "190px",
          backgroundColor: "#EE8D00",
          borderColor: "#EE8D00",
          fontSize: "14px",
          color: "white",
          fontWeight: "bold"
        }}
      >
        Cargar Impulso (Excel)
      </Button>
    </Upload>
  );
};

export default ExcelUploader;
