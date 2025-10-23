import React, { useEffect, useMemo, useRef, useState } from "react";
import { Card, Button, Space, Tag, message, Typography, Divider, Select, Input, Tooltip } from "antd";
import ReactQuill from "react-quill";
import 'react-quill/dist/quill.snow.css';
import { API_URL_GATEWAY } from "../../config";
import axios from "axios";
import * as XLSX from "xlsx";
import { useSearchParams } from "react-router-dom";
import { useNavigate } from "react-router-dom";

import { DownloadOutlined, CheckCircleOutlined, FieldStringOutlined } from "@ant-design/icons";

const { Title, Text } = Typography;
const { Option } = Select;

const quillModules = {
  toolbar: [
    [{ header: [1,2,3,false] }],
    ['bold','italic','underline','strike'],
    [{ 'align': [] }],
    [{ 'list': 'ordered' }, { 'list': 'bullet' }],
    ['link'],
    ['clean']
  ]
};

const quillFormats = [
  'header','bold','italic','underline','strike',
  'align','list','bullet','link'
];

export default function DocumentPersonalizer() {
  const [params] = useSearchParams();
  const excelServerName = params.get("excel"); // viene de la otra pantalla
  const [variables, setVariables] = useState([]);
  const [templateHtml, setTemplateHtml] = useState("<p><strong>Hola {Var1}</strong>,</p><p>Tu dirección es {Var3}.</p>");
  const [fileNameTemplate, setFileNameTemplate] = useState("documento_{Var1}.pdf");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();


  // Trae headers del Excel ya subido (lo descargamos, leemos headers y listo)
  useEffect(() => {
    if (!excelServerName) return;
    // Si ya tienes los headers en estado global, úsalo. Aquí lo leemos simple:
    (async () => {
      try {
        // endpoint opcional: si no lo tienes, puedes omitir y pedir al BE que te devuelva headers
        const res = await axios.get(`${API_URL_GATEWAY}/gateway/correos/email/download_excel`, {
          params: { file: excelServerName },
          responseType: "arraybuffer"
        });
        const wb = XLSX.read(res.data, { type: "array" });
        const sheet = wb.Sheets[wb.SheetNames[0]];
        const rows = XLSX.utils.sheet_to_json(sheet, { header: 1, raw: false, defval: "" });
        const headers = (rows?.[0] || []).map(h => String(h || "").trim()).filter(Boolean);
        setVariables(headers);
      } catch (e) {
        console.error(e);
        message.warning("No pude leer variables del Excel. Igual puedes escribirlas manualmente.");
      }
    })();
  }, [excelServerName]);

  const insertVar = (v) => {
    setTemplateHtml(prev => {
      // insertar marcador simple al final. Si quieres al cursor, usa Quill API.
      return prev + `{${v}}`;
    });
  };

  const preview = useMemo(() => {
    return (
      <div style={{border:"1px solid #eee", borderRadius:8, padding:16, background:"#fff"}}>
        <div dangerouslySetInnerHTML={{ __html: templateHtml }} />
      </div>
    );
  }, [templateHtml]);

  const generateDocs = async () => {
    if (!excelServerName) return message.error("Falta Excel");
    if (!templateHtml || !templateHtml.trim()) return message.error("La plantilla no puede estar vacía");

    setLoading(true);
    try {
      const payload = {
        excelFileName: excelServerName,
        templateHtml,
        fileNameTemplate,  // ejemplo: documento_{Var1}.pdf
        output: "pdf"
      };
      const { data } = await axios.post(
        `${API_URL_GATEWAY}/gateway/docs/generar`,
        payload,
        { responseType: "blob" } // recibimos ZIP
      );
      const blob = new Blob([data], { type: "application/zip" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `documentos_personalizados.zip`;
      a.click();
      window.URL.revokeObjectURL(url);
      message.success("Documentos generados");
    } catch (e) {
      console.error(e);
      message.error("Error generando documentos");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{maxWidth: 1200, margin: "0 auto"}}>
      <Title level={3}>Personalizar documentos</Title>
      <Text type="secondary">Plantilla enriquecida con variables por persona.</Text>

      <Card style={{marginTop: 16}}>
        <Space direction="vertical" style={{width:"100%"}}>
          <div>
            <Text strong>Excel:</Text>{" "}
            <Tag color="green"><CheckCircleOutlined/> {excelServerName || "—"}</Tag>
          </div>

          <div>
            <Text strong>Variables:</Text>{" "}
            <Space wrap>
              {variables.map(v => (
                <Tag key={v} icon={<FieldStringOutlined />} color="blue" onClick={() => insertVar(v)} style={{cursor:"pointer"}}>
                  {`{${v}}`}
                </Tag>
              ))}
            </Space>
          </div>

          <div>
            <Text strong>Nombre del archivo por persona</Text>
            <Tooltip title="Puedes usar variables como {Var1}. Debe terminar en .pdf">
              <Input
                value={fileNameTemplate}
                onChange={e => setFileNameTemplate(e.target.value)}
                placeholder="documento_{Var1}.pdf"
              />
            </Tooltip>
          </div>

          <Divider/>

          <Text strong>Editor Documentos</Text>
          <ReactQuill
            theme="snow"
            value={templateHtml}
            onChange={setTemplateHtml}
            modules={quillModules}
            formats={quillFormats}
            style={{height: 300, marginBottom: 24}}
          />

        

          <Divider/>
          <Space>
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={generateDocs}
              loading={loading}
            >
              Generar PDFs
            </Button>
              <Button onClick={() => navigate(-1)}>Volver para enviar correo</Button>
          </Space>
        </Space>
      </Card>
    </div>
  );
}
