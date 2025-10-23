import React, { useState } from "react";
import {
  Upload,
  Button,
  message,
  Table,
  Card,
  Space,
  Typography,
  Divider
} from "antd";
import { UploadOutlined, SendOutlined } from "@ant-design/icons";
import * as XLSX from 'xlsx';
import { API_URL_GATEWAY } from "../../config";
import "./AcuerdoPago.css";

const { Title, Text } = Typography;

const AcuerdoPago = () => {
  const [excelData, setExcelData] = useState([]);
  const [excelColumns, setExcelColumns] = useState([]);
  const [fileName, setFileName] = useState("");
  const [fileToSend, setFileToSend] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [enviando, setEnviando] = useState(false);

  // Función para procesar el archivo Excel
  const procesarArchivoExcel = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const data = new Uint8Array(e.target.result);
          const workbook = XLSX.read(data, { type: 'array' });
          const sheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[sheetName];
          const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });

          if (jsonData.length === 0) {
            reject(new Error('El archivo está vacío'));
            return;
          }

          // Primera fila como headers
          const headers = jsonData[0];
          const dataRows = jsonData.slice(1);

          // Crear columnas para la tabla
          const columns = headers.map((header, index) => ({
            title: header || `Columna ${index + 1}`,
            dataIndex: `col_${index}`,
            key: `col_${index}`,
            width: 150,
            ellipsis: true,
          }));

          // Crear datos para la tabla
          const tableData = dataRows.map((row, rowIndex) => {
            const rowData = { key: rowIndex };
            headers.forEach((_, colIndex) => {
              rowData[`col_${colIndex}`] = row[colIndex] || '';
            });
            return rowData;
          });

          resolve({ columns, data: tableData });
        } catch (error) {
          reject(error);
        }
      };

      reader.onerror = () => reject(new Error('Error al leer el archivo'));
      reader.readAsArrayBuffer(file);
    });
  };

  // Función para cargar y previsualizar el archivo
  const cargarArchivo = async (file) => {
    setCargando(true);
    try {
      const { columns, data } = await procesarArchivoExcel(file);
      setExcelColumns(columns);
      setExcelData(data);
      setFileName(file.name);
      setFileToSend(file);
      message.success(`Archivo "${file.name}" cargado correctamente`);
    } catch (error) {
      console.error('Error al procesar el archivo:', error);
      message.error('Error al procesar el archivo Excel');
    } finally {
      setCargando(false);
    }
  };

  // Función para enviar al backend
  const enviarArchivo = async () => {
    if (!fileToSend) {
      message.error('No hay archivo para enviar');
      return;
    }

    setEnviando(true);
    try {
      const myId = localStorage.getItem("idUsuario");
      const formData = new FormData();
      formData.append("file", fileToSend);
      formData.append("idUsuario", myId);

      const res = await fetch(
        `${API_URL_GATEWAY}/gateway-rpa/excel/guardarAcuerdoPago`,
        {
          method: "POST",
          body: formData,
        }
      );

      let data;
      try {
        data = await res.json();
      } catch {
        data = null;
      }

      if (res.ok) {
        message.success("Archivo subido correctamente");
        // Limpiar el estado después del envío exitoso
        limpiarDatos();
      } else {
        console.error("Respuesta del servidor:", data);
        message.error("Error al enviar el archivo al servidor");
      }
    } catch (error) {
      console.error("Error al enviar:", error);
      message.error("Error al enviar el archivo");
    } finally {
      setEnviando(false);
    }
  };

  // Función para limpiar los datos
  const limpiarDatos = () => {
    setExcelData([]);
    setExcelColumns([]);
    setFileName("");
    setFileToSend(null);
  };

  return (
    <div className="rpa-vigilancia-container">
      <div className="acuerdo-pago-wrapper">
        {/* Sección de carga de archivo */}
        <Card className="upload-card">
          <Title level={4}>
            Acuerdos de Pago
          </Title>
          
          <div className="upload-section">
            <Upload
              beforeUpload={(file) => {
                cargarArchivo(file);
                return false; // Prevenir upload automático
              }}
              accept=".xlsx,.xls"
              showUploadList={false}
              multiple={false}
            >
              <Button
                className="rpa-btn-primary upload-btn"
                icon={<UploadOutlined />}
                loading={cargando}
                size="large"
              >
                {cargando ? 'Cargando...' : 'Seleccionar archivo Excel'}
              </Button>
            </Upload>

            {fileName && (
              <div className="file-info">
                <Text type="success">
                  📄 Archivo cargado: <strong>{fileName}</strong>
                </Text>
                <Button 
                  type="link" 
                  size="small" 
                  onClick={limpiarDatos}
                  className="clear-btn"
                >
                  Limpiar
                </Button>
              </div>
            )}
          </div>
        </Card>

        {/* Sección de preview */}
        {excelData.length > 0 && (
          <Card className="preview-card">
            <div className="preview-header">
              <Title level={4}>Vista Previa de Datos</Title>
              <Text type="secondary">
                Mostrando {excelData.length} filas y {excelColumns.length} columnas
              </Text>
            </div>

            <div className="table-container">
              <Table
                columns={excelColumns}
                dataSource={excelData.slice(0, 100)} // Mostrar máximo 100 filas
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `Total ${total} filas`,
                }}
                scroll={{ x: 'max-content', y: 400 }}
                size="small"
                bordered
              />
            </div>

            <Divider />

            {/* Botón de envío */}
            <div className="send-section">
              <Space size="large">
                <Button
                  type="primary"
                  icon={<SendOutlined />}
                  loading={enviando}
                  onClick={enviarArchivo}
                  size="large"
                  className="rpa-btn-secondary send-btn"
                >
                  {enviando ? 'Subiendo...' : 'Subir'}
                </Button>
                <Text type="secondary">
                  Los datos se enviarán para su procesamiento
                </Text>
              </Space>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

export default AcuerdoPago;