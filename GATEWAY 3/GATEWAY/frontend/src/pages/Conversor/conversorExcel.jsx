import React, { useState } from "react";
import {
  Alert,
  Upload,
  Button,
  Typography,
  message,
  Switch,
  Table,
  Space,
  Spin,
  Radio,
} from "antd";
import { UploadOutlined, DownloadOutlined } from "@ant-design/icons";
import { API_URL_GATEWAY } from "../../config";
import axios from "axios";
import * as XLSX from "xlsx";
import "./conversorExcel.css";

const { Title } = Typography;

const ConversorExcel = () => {
  const [archivo, setArchivo] = useState(null);
  const [modoProcesado, setModoProcesado] = useState(false);
  const [modoTransformacion, setModoTransformacion] = useState("numerico");
  const [datosOriginales, setDatosOriginales] = useState([]);
  const [datosProcesados, setDatosProcesados] = useState([]);
  const [columnas, setColumnas] = useState([]);
  const [columnasConvertir, setColumnasConvertir] = useState([]);
  const [cargando, setCargando] = useState(false);

  const leerExcelLocal = (file) => {
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const data = new Uint8Array(e.target.result);
      const workbook = XLSX.read(data, { type: "array" });
      const sheetName = workbook.SheetNames[0];
      const sheet = workbook.Sheets[sheetName];
      const json = XLSX.utils.sheet_to_json(sheet, { defval: "" });

      if (json.length === 0) {
        message.warning("El archivo Excel está vacío.");
        return;
      }

      setDatosOriginales(json);

      const columnasObjetivo = [
        "Saldo total",
        "Intereses",
        "Capital",
        "Oferta 1",
        "Oferta 2",
        "Oferta 3",
        "Hasta 3 cuotas",
        "Hasta 6 cuotas",
        "Hasta 12 cuotas",
        "Pago Flexible",
        "Cap consolidado",
        "Saldo Total Cons",
        "6 Cuotas",
        "12 cuotas",
      ];

      const columnasDisponibles = Object.keys(json[0]);
      const columnasAConvertir = columnasObjetivo.filter((colObjetivo) =>
        columnasDisponibles.find(
          (colDisponible) =>
            colDisponible.trim().toLowerCase() ===
            colObjetivo.trim().toLowerCase()
        )
      );

      setColumnasConvertir(columnasAConvertir);

      setColumnas(
        columnasDisponibles.map((key) => ({
          title: key,
          dataIndex: key,
          key,
        }))
      );
    };
    reader.readAsArrayBuffer(file);
  };

  const handleFileChange = ({ fileList }) => {
    if (fileList.length > 0) {
      const realFile = fileList[0].originFileObj || fileList[0];
      if (realFile && realFile.type?.includes("sheet")) {
        setArchivo(realFile);
        leerExcelLocal(realFile);
      } else {
        message.error("Debe ser un archivo Excel válido (.xlsx)");
      }
    } else {
      setArchivo(null);
      setDatosOriginales([]);
      setDatosProcesados([]);
      setModoProcesado(false);
      setColumnas([]);
      setColumnasConvertir([]);
    }
  };

  const handleUpload = async () => {
    if (!archivo) {
      message.warning("Por favor selecciona un archivo.");
      return;
    }

    const formData = new FormData();
    formData.append("archivo", archivo);
    formData.append("columnas", columnasConvertir.join(","));
    formData.append("modo", modoTransformacion);

    if (modoTransformacion === "nombres") {
      formData.append("columnas", "");
    } else if (modoTransformacion === "completo") {
      formData.append("columnas", columnasConvertir.join(",")); // solo si incluye columnas numéricas
    } else {
      formData.append("columnas", columnasConvertir.join(","));
    }


    setCargando(true);

    try {
      const response = await axios.post(
        `${API_URL_GATEWAY}/gateway/excel/conversor`,
        formData,
        {
          responseType: "arraybuffer",
          timeout: 600000,
        }
      );

      const workbook = XLSX.read(response.data, { type: "array" });
      const sheetName = workbook.SheetNames[0];
      const sheet = workbook.Sheets[sheetName];
      const json = XLSX.utils.sheet_to_json(sheet, { defval: "" });

      setDatosProcesados(json);
      message.success("Archivo procesado correctamente.");
      setModoProcesado(true);

      const blob = new Blob([response.data], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "archivo_procesado.xlsx");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error(error);
      message.error("Error procesando el archivo.");
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="conversor-container">
      <h1 className="excel-tittle">Conversor</h1>
      <Spin spinning={cargando} tip="Procesando archivo...">
        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          <Radio.Group
            value={modoTransformacion}
            onChange={(e) => setModoTransformacion(e.target.value)}
          >
            <Radio.Button value="numerico">Solo números</Radio.Button>
            <Radio.Button value="nombres">Solo nombres</Radio.Button>
            <Radio.Button value="completo">Todo (numeros y nombres)</Radio.Button>
          </Radio.Group>

        {["nombres", "completo"].includes(modoTransformacion) && (
          <Alert
            type="warning"
            message={
            <span style={{ fontSize: "13px", fontWeight: "normal" }}>
              Este modo puede tardar más tiempo. Por cada 1.000 registros, el procesamiento puede demorar hasta 2 minutos.
            </span>
          }
            showIcon
            style={{
              fontSize: "15px",
              padding: "3px 12px 4px",
              marginTop: 4,
              maxWidth: 700,
            }}
          />
        )}

          <Upload
            accept=".xlsx"
            beforeUpload={() => false}
            showUploadList={{ showRemoveIcon: true }}
            onChange={handleFileChange}
            onRemove={() => {
              setArchivo(null);
              setDatosOriginales([]);
              setDatosProcesados([]);
              setModoProcesado(false);
              setColumnas([]);
              setColumnasConvertir([]);
            }}
          >
            <Button icon={<UploadOutlined />}>Seleccionar Excel</Button>
          </Upload>

          <Button
            type="primary"
            icon={<DownloadOutlined />}
            onClick={handleUpload}
            disabled={!archivo}
          >
            Procesar
          </Button>

          <Switch
            checked={modoProcesado}
            onChange={(val) => setModoProcesado(val)}
            checkedChildren="Procesado"
            unCheckedChildren="Original"
            disabled={datosProcesados.length === 0}
          />

          <Table
            columns={columnas}
            dataSource={modoProcesado ? datosProcesados : datosOriginales}
            scroll={{ x: "max-content" }}
            size="small"
            pagination={{ pageSize: 10 }}
          />
        </Space>
      </Spin>
    </div>
  );
};

export default ConversorExcel;
