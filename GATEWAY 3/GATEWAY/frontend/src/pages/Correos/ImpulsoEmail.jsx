import React, { useState, useRef, useMemo, useEffect } from "react";
import {
  Card,
  Input,
  Button,
  Select,
  Typography,
  Row,
  Col,
  Divider,
  Upload,
  message,
  Tag,
  Space,
  Badge,
  Tooltip,
  Progress,
  Alert,
} from "antd";
import {
  UploadOutlined,
  PaperClipOutlined,
  FileExcelOutlined,
  SendOutlined,
  DeleteOutlined,
  EyeOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  ThunderboltOutlined,
  MailOutlined,
} from "@ant-design/icons";
import axios from "axios";
import * as XLSX from "xlsx";
import { API_URL_GATEWAY } from "../../config";
import "./impulsoEmail.css";
import { useNavigate } from "react-router-dom";

const { TextArea } = Input;
const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

// --- Helpers ---
function getHeadersFromSheet(sheet) {
  const rows = XLSX.utils.sheet_to_json(sheet, {
    header: 1,
    raw: false,
    defval: "",
  });
  const headers = (rows?.[0] || []).map((h) => String(h || "").trim());
  const seen = new Set();
  return headers.filter((h) => h && !seen.has(h) && (seen.add(h) || true));
}

function highlightVariables(text) {
  if (!text) return "";
  return text.replace(
    /\{([^}]+)\}/g,
    (m) => `<span class="variable-highlight">${m}</span>`
  );
}

const isImage = (name) => /\.(png|jpe?g|gif|webp|bmp|svg)$/i.test(name);

export default function EmailMasivo() {
  const [emailContent, setEmailContent] = useState({ subject: "", body: "" });
  const [availableVars, setAvailableVars] = useState([
    "cedula",
    "nombre",
    "correo",
  ]);
  const [uploadedExcelName, setUploadedExcelName] = useState("");
  const [localAttachments, setLocalAttachments] = useState([]);
  const [serverAttachments, setServerAttachments] = useState([]);
  const [loadingUploadExcel, setLoadingUploadExcel] = useState(false);
  const [loadingUploadAdj, setLoadingUploadAdj] = useState(false);
  const [sending, setSending] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [perDocPattern, setPerDocPattern] = useState("documento_{Var1}.pdf");
  const [perDocFolder, setPerDocFolder] = useState("");
  const [localAttachmentsUI, setLocalAttachmentsUI] = useState([]);

  const [senderEmail, setSenderEmail] = useState("");
const [senderOptions, setSenderOptions] = useState([]);

  const navigate = useNavigate();

  const excelInputRef = useRef(null);
  useEffect(() => {
    try {
      const savedVars = sessionStorage.getItem("emailVars");
      const savedExcel = sessionStorage.getItem("excelName");
      const savedPat = sessionStorage.getItem("perDocPattern");
      const savedFolder = sessionStorage.getItem("perDocFolder");

      if (savedVars) setAvailableVars(JSON.parse(savedVars));
      if (savedExcel) setUploadedExcelName(savedExcel);
      if (savedPat) setPerDocPattern(savedPat);
      if (savedFolder) setPerDocFolder(savedFolder);
    } catch {}
  }, []);

  useEffect(() => {
  (async () => {
    try {
      const { data } = await axios.get(`${API_URL_GATEWAY}/gateway/correos/senders`);
      const emails = data?.emails || [];
      setSenderOptions(emails.map(e => ({ label: e, value: e })));
      if (emails.length && !senderEmail) setSenderEmail(emails[0]);
    } catch (e) {
      console.warn("No se pudo cargar correos remitentes", e);
    }
  })();
}, []);

  const previewHtml = useMemo(() => {
    return `
      <div class="email-preview">
        <div class="email-header">
          <h3 class="email-subject">${
            highlightVariables(emailContent.subject) ||
            '<span class="placeholder">Asunto del correo</span>'
          }</h3>
        </div>
        <div class="email-body">${
          highlightVariables(emailContent.body) ||
          '<span class="placeholder">Cuerpo del correo...</span>'
        }</div>
      </div>
    `;
  }, [emailContent]);

  const handleChange = (section, value) => {
    setEmailContent((prev) => ({ ...prev, [section]: value }));
  };

  const insertVar = (section, v) => {
    setEmailContent((prev) => ({
      ...prev,
      [section]: `${prev[section] || ""}{${v}}`,
    }));
  };

  function downloadTemplate() {
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet([
      ["CORREO", "Var1", "Var2", "Var3", "Var4", "Var5"],
    ]);

    ws["!cols"] = [
      { wch: 20 },
      { wch: 15 },
      { wch: 25 },
      { wch: 15 },
      { wch: 10 },
      { wch: 15 },
    ];

    ws["!ref"] = "A1:F2";
    XLSX.utils.book_append_sheet(wb, ws, "Correos");
    XLSX.writeFile(wb, "plantilla_correos.xlsx");
  }

  async function onPickExcel(e) {
    const file = e?.target?.files?.[0];
    if (!file) return;

    try {
      setUploadProgress(0);
      const buf = await file.arrayBuffer();
      setUploadProgress(30);

      const wb = XLSX.read(buf, { type: "array" });
      const sheet = wb.Sheets[wb.SheetNames[0]];
      const headers = getHeadersFromSheet(sheet);
      setUploadProgress(60);

      if (!headers.length) {
        message.warning("No se detectaron encabezados en la primera fila.");
      } else {
        setAvailableVars(headers);
        sessionStorage.setItem("emailVars", JSON.stringify(headers));
        message.success(`Variables detectadas: ${headers.length}`);
      }

      setLoadingUploadExcel(true);
      const fd = new FormData();
      fd.append("file", file);

      const { data } = await axios.post(
        `${API_URL_GATEWAY}/gateway/correos/email/upload_excel`,
        fd,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      setUploadProgress(100);
      setUploadedExcelName(data?.serverFileName || "");
      sessionStorage.setItem("excelName", data?.serverFileName || "");

      if (!data?.serverFileName)
        throw new Error("El gateway no devolvió serverFileName");
      message.success(`Excel subido: ${data.serverFileName}`);
    } catch (err) {
      console.error(err);
      message.error("Error al procesar/subir el Excel");
      setUploadProgress(0);
    } finally {
      setLoadingUploadExcel(false);
      if (excelInputRef.current) excelInputRef.current.value = "";
      setTimeout(() => setUploadProgress(0), 2000);
    }
  }

  async function onUploadAttachments() {
    if (!localAttachments.length) {
      message.info("Selecciona archivos primero");
      return;
    }
    try {
      setLoadingUploadAdj(true);
      const fd = new FormData();
      localAttachments.forEach((f) => fd.append("files", f));

      const { data } = await axios.post(
        `${API_URL_GATEWAY}/gateway/correos/adjuntos/subir`,
        fd,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      const saved = Array.isArray(data?.saved) ? data.saved : [];
      setServerAttachments(saved);
      message.success(`Adjuntos guardados (${saved.length})`);
    } catch (err) {
      console.error(err);
      message.error("Error subiendo adjuntos");
    } finally {
      setLoadingUploadAdj(false);
    }
  }

  async function sendBulkEmail() {
    if (!uploadedExcelName) {
      message.error("Primero carga el Excel y espera a que se suba.");
      return;
    }
    if (!emailContent.subject.trim() || !emailContent.body.trim()) {
      message.error("Asunto y cuerpo son obligatorios.");
      return;
    }

    setSending(true);
    try {
      const payload = {
        excelFileName: uploadedExcelName,
        subject: emailContent.subject,
        body: emailContent.body,
        attachments: serverAttachments,
        attachmentsMode: "row",
        perDocPattern,
        perDocFolder,
        senderEmail,
      };

      const { data } = await axios.post(
        `${API_URL_GATEWAY}/gateway/correos/Email`,
        payload,
        { headers: { "Content-Type": "application/json" } }
      );
      message.success(data?.message || "Correos encolados para envío");
    } catch (err) {
      console.error(err);
      message.error("Error al enviar correos");
    } finally {
      setSending(false);
    }
  }

  const insertVarIntoPattern = (v) => {
    setPerDocPattern((prev) => {
      // si el patrón ya termina en .pdf, insertamos antes de la extensión
      const m = prev.match(/^(.*?)(\.pdf)$/i);
      if (m) {
        return `${m[1]}{${v}}${m[2]}`;
      }
      return `${prev}{${v}}`;
    });
  };

  const isReadyToSend =
    uploadedExcelName &&
    emailContent.subject.trim() &&
    emailContent.body.trim();

  return (
    <div className="email-masivo-container">
      {/* Header con gradiente */}
      <div className="page-header">
        <div className="header-content">
          <div className="header-icon">
            <ThunderboltOutlined />
          </div>
          <div>
            <Title level={2} className="page-title">
              Email Masivo
            </Title>
            <Text className="page-subtitle">
              Envía correos personalizados a múltiples destinatarios
            </Text>
            <Button
  type="default"
  style={{ marginTop: "16px" }}
  onClick={() => navigate("/email-reporte")}
>
  Ver Reporte de Envíos
</Button>

          </div>
        </div>
      </div>

      <Row gutter={[24, 24]} className="main-content">
        {/* IZQUIERDA: Configuración */}
        <Col xs={24} lg={14}>
          <div className="config-section">
            {/* Paso 1: Excel */}
            <Card className="step-card" size="small">
              <div className="step-header">
                <Badge count={1} className="step-number" />
                <Title level={4} className="step-title">
                  Datos de destinatarios
                </Title>
              </div>

              <label>CORREO A USAR: </label>
<Select
  placeholder="Selecciona el correo remitente"
  options={senderOptions}
  value={senderEmail || undefined}
  onChange={(val) => setSenderEmail(val)}
/>


              <Alert
                message="Carga un archivo Excel con los datos de tus destinatarios"
                type="info"
                showIcon
                className="step-alert"
              />

              <Space wrap className="upload-actions">
                <Tooltip title="Descarga una plantilla base para empezar">
                  <Button
                    icon={<DownloadOutlined />}
                    onClick={downloadTemplate}
                    className="secondary-btn"
                  >
                    Descargar Plantilla
                  </Button>
                </Tooltip>

                <Button
                  type="primary"
                  icon={<FileExcelOutlined />}
                  onClick={() => excelInputRef.current?.click()}
                  loading={loadingUploadExcel}
                  size="large"
                  className="upload-btn"
                >
                  Cargar Excel
                </Button>

                <Button
                  type="default"
                  icon={<PaperClipOutlined />}
                  onClick={() => {
                    if (!uploadedExcelName) {
                      message.warning("Primero carga el Excel.");
                      return;
                    }
                    sessionStorage.setItem("excelName", uploadedExcelName);
                    sessionStorage.setItem(
                      "emailVars",
                      JSON.stringify(availableVars || [])
                    );
                    navigate(
                      `/documentos?excel=${encodeURIComponent(
                        uploadedExcelName
                      )}`
                    );
                  }}
                >
                  Personalizar documentos
                </Button>

                <input
                  ref={excelInputRef}
                  type="file"
                  accept=".xlsx,.xls"
                  style={{ display: "none" }}
                  onChange={onPickExcel}
                />
              </Space>

              {uploadProgress > 0 && uploadProgress < 100 && (
                <Progress
                  percent={uploadProgress}
                  size="small"
                  className="upload-progress"
                />
              )}

              {uploadedExcelName && (
                <div className="upload-success">
                  <CheckCircleOutlined className="success-icon" />
                  <Tag color="success" className="file-tag">
                    {uploadedExcelName}
                  </Tag>
                  <Text type="secondary">
                    Variables disponibles: {availableVars.length}
                  </Text>
                </div>
              )}
            </Card>

            {/* Paso 2: Contenido */}
            <Card className="step-card">
              <div className="step-header">
                <Badge count={2} className="step-number" />
                <Title level={4} className="step-title">
                  Contenido del correo
                </Title>
              </div>

              <div className="form-group">
                <label className="form-label">
                  <MailOutlined /> Asunto
                </label>
                <Space.Compact className="input-with-vars">
                  <Input
                    placeholder="Escribe el asunto del correo..."
                    value={emailContent.subject}
                    onChange={(e) => handleChange("subject", e.target.value)}
                    size="large"
                  />
                  <Select
                    placeholder="Variables"
                    onChange={(v) => insertVar("subject", v)}
                    className="var-selector"
                    size="large"
                  >
                    {availableVars.map((v) => (
                      <Option key={v} value={v}>
                        <Tag color="orange">{v}</Tag>
                      </Option>
                    ))}
                  </Select>
                </Space.Compact>
              </div>

              <div className="form-group">
                <label className="form-label">Cuerpo del mensaje</label>
                <TextArea
                  rows={8}
                  placeholder="Escribe el contenido de tu correo... Usa {variables} para personalizar"
                  value={emailContent.body}
                  onChange={(e) => handleChange("body", e.target.value)}
                  className="body-textarea"
                />
                <Select
                  placeholder="Insertar variable"
                  onChange={(v) => insertVar("body", v)}
                  className="var-selector-full"
                >
                  {availableVars.map((v) => (
                    <Option key={v} value={v}>
                      <Tag color="orange">{v}</Tag>
                    </Option>
                  ))}
                </Select>
              </div>
            </Card>

            {/* Paso 3: Adjuntos */}
            <Card className="step-card">
              <div className="step-header">
                <Badge count={3} className="step-number" />
                <Title level={4} className="step-title">
                  Adjuntos (opcional)
                </Title>
              </div>

              <Upload
                multiple
                beforeUpload={() => false}
                fileList={localAttachmentsUI}
                onChange={({ file, fileList }) => {
                  setLocalAttachmentsUI(fileList);
                  const files = fileList
                    .map((f) => f.originFileObj)
                    .filter(Boolean);
                  setLocalAttachments(files);
                }}
                className="upload-area"
              >
                <Button
                  icon={<PaperClipOutlined />}
                  size="large"
                  block
                  className="select-files-btn"
                >
                  Seleccionar archivos
                </Button>
              </Upload>

              {localAttachments.length > 0 && (
                <Space className="attachment-actions">
                  <Button
                    type="primary"
                    icon={<UploadOutlined />}
                    onClick={onUploadAttachments}
                    loading={loadingUploadAdj}
                  >
                    Subir archivos ({localAttachments.length})
                  </Button>

                  {serverAttachments.length > 0 && (
                    <Button
                      danger
                      icon={<DeleteOutlined />}
                      onClick={() => setServerAttachments([])}
                    >
                      Limpiar
                    </Button>
                  )}
                </Space>
              )}

              {serverAttachments.length > 0 && (
  <div className="uploaded-files">
    <Text strong>Archivos subidos:</Text>
    <div className="file-tags">
      {serverAttachments.map((p, i) => (
        <Space key={i} style={{ marginBottom: 8 }}>
          <Tag icon={<PaperClipOutlined />} color={isImage(p) ? "green" : "blue"}>
            {p}
          </Tag>
          {isImage(p) && (
            <Button
              size="small"
              onClick={() =>
                setEmailContent(prev => ({
                  ...prev,
                  body: `${prev.body || ""}\n<img src="${p}" style="max-width:100%;height:auto;" />`
                }))
              }
            >
              Insertar en cuerpo
            </Button>
          )}
        </Space>
      ))}
    </div>
  </div>
)}
            </Card>
            <Card className="step-card" size="small" style={{ marginTop: 12 }}>
              <div className="step-header">
                <Badge count={"⇢"} className="step-number" />
                <Title level={5} className="step-title">
                  Adjunto por persona (nombre)
                </Title>
              </div>

              <Space direction="vertical" style={{ width: "100%" }}>
                <Space.Compact style={{ width: "100%" }}>
                  <Input
                    addonBefore="Nombre del archivo"
                    value={perDocPattern}
                    onChange={(e) => setPerDocPattern(e.target.value)}
                  />
                  <Select
                    style={{ minWidth: 220 }}
                    placeholder="Insertar variable"
                    onChange={insertVarIntoPattern}
                    dropdownMatchSelectWidth={false}
                  >
                    {availableVars.map((v) => (
                      <Select.Option key={v} value={v}>
                        {v}
                      </Select.Option>
                    ))}
                  </Select>
                </Space.Compact>

                <Typography.Text type="secondary">
                  Escribe o construye el nombre del archivo con el selector.
                  Ejemplo: <code>documento_{"{Var1}"}.pdf</code>. Se buscará el
                  PDF por cada fila usando el valor de la variable seleccionada.
                </Typography.Text>
              </Space>
            </Card>

            {/* Botón de envío */}
            <Card className="send-card">
              <Button
                type="primary"
                icon={<SendOutlined />}
                onClick={sendBulkEmail}
                loading={sending}
                size="large"
                block
                className={`send-btn ${isReadyToSend ? "ready" : "not-ready"}`}
                disabled={!isReadyToSend}
              >
                {sending ? "Enviando correos..." : "Enviar correos"}
              </Button>

              {!isReadyToSend && (
                <Text type="secondary" className="send-requirements">
                  <InfoCircleOutlined /> Completa todos los pasos para enviar
                </Text>
              )}
            </Card>
          </div>
        </Col>

        {/* DERECHA: Vista previa */}
        <Col xs={24} lg={10}>
          <div className="preview-section sticky">
            <Card
              title={
                <Space>
                  <EyeOutlined />
                  Vista previa
                </Space>
              }
              className="preview-card"
              extra={
                <Badge
                  count={availableVars.length}
                  showZero
                  color="#f50"
                  title="Variables disponibles"
                />
              }
            >
              <div
                className="email-preview-container"
                dangerouslySetInnerHTML={{ __html: previewHtml }}
              />

              {availableVars.length > 0 && (
                <div className="variables-info">
                  <Divider />
                  <Text strong>Variables disponibles:</Text>
                  <div className="variable-tags">
                    {availableVars.map((v) => (
                      <Tag key={v} color="orange" className="variable-tag">
                        {`{${v}}`}
                      </Tag>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          </div>
        </Col>
      </Row>
    </div>
  );
}
