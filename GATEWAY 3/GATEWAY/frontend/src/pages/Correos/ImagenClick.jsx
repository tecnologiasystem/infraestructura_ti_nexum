import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import { FaTrash, FaUpload, FaImage, FaClock, FaPaperPlane, FaLink, FaCheck } from "react-icons/fa";
import {
  GlobalStyle,
  Container,
  Header,
  MainGrid,
  LeftColumn,
  RightColumn,
  Card,
  CardTitle,
  FileUploadArea,
  Input,
  TextArea,
  FormGroup,
  PrimaryButton,
  SecondaryButton,
  TertiaryButton,
  UrlList,
  UrlItem,
  UrlDot,
  UrlLink,
  DeleteButton,
  ImageContainer,
  Image,
  RemoveImageButton,
  ClickableArea,
  SelectedArea,
  UrlInputRow,
  UrlInput,
  SaveUrlButton
} from "./ImagenClick.styles";
import { Select, Space, Tooltip, Button } from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import * as XLSX from "xlsx";
import { API_URL_GATEWAY_RPA } from "../../config";
import { useNavigate } from "react-router-dom";

const { Option } = Select;


const ImagenClick = () => {
  const [areas, setAreas] = useState([]);
  const [imageSrc, setImageSrc] = useState(null);
  const [selectedArea, setSelectedArea] = useState(null);
  const [url, setUrl] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const imageRef = useRef(null);
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");
  const [emailContent, setEmailContent] = useState({ subject: "", body: "" });
  const [imageFile, setImageFile] = useState(null);
  const [scheduledTime, setScheduledTime] = useState("");
  const [senderOptions, setSenderOptions] = useState([]);
  const [senderEmail, setSenderEmail] = useState("");
  const [uploadedExcelName, setUploadedExcelName] = useState("");
  const [availableVars, setAvailableVars] = useState([]);
  const [excelRows, setExcelRows] = useState([]);

    const navigate = useNavigate();

  const subject = emailContent.subject;
const body = emailContent.body;

const setSubject = (valOrFn) => {
  setEmailContent((prev) => ({
    ...prev,
    subject: typeof valOrFn === "function" ? valOrFn(prev.subject) : valOrFn,
  }));
};

const setBody = (valOrFn) => {
  setEmailContent((prev) => ({
    ...prev,
    body: typeof valOrFn === "function" ? valOrFn(prev.body) : valOrFn,
  }));
};


  useEffect(() => {
  (async () => {
    try {
      const { data } = await axios.get(
        `${API_URL_GATEWAY_RPA}/gateway/correos/senders`
      );
      const emails = data?.emails || [];
      setSenderOptions(emails.map((e) => ({ label: e, value: e })));
      if (emails.length && !senderEmail) setSenderEmail(emails[0]);
    } catch (e) {
      console.warn("No se pudo cargar correos remitentes", e);
    }
  })();
}, []); 

const applyVars = (template, row) => {
  if (!template) return "";
  return template.replace(/\{([^}]+)\}/g, (_, key) => {
    const k = key.trim();
    return row?.[k] ?? row?.[k.toUpperCase()] ?? row?.[k.toLowerCase()] ?? "";
  });
};

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Selecciona un archivo xlsx.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
formData.append("senderEmail", senderEmail);


    try {
      const res = await axios.post(`${API_URL_GATEWAY_RPA}/gateway/emailclick/subir_excel`, formData, {
  headers: { "Content-Type": "multipart/form-data" },
});

setUploadedExcelName(res.data.excelFileName || "");
setAvailableVars(res.data.variables || []);
setExcelRows(res.data.rowsPreview || []);


      alert(res.data.message);
setMessage(res.data.message);

    } catch (error) {
      console.error("Error al subir el archivo:", error);
      alert("Error al enviar el archivo.");
    }
  };

  const handleSaveImage = async () => {
    if (!imageSrc) {
  alert("Sube una imagen.");
  return false;
}


    const formData = new FormData();
    formData.append("file", imageFile);
    formData.append("areas", JSON.stringify(areas));
formData.append("senderEmail", senderEmail);

    try {
      const response = await fetch(`${API_URL_GATEWAY_RPA}/gateway/emailclick/guardar_imagen`, {
        method: "POST",
        body: formData,
      });
      const result = await response.json();
      console.log("✅ Imagen guardada correctamente:", result);
      return true;
    } catch (error) {
      console.error("❌ Error al enviar la imagen:", error);
      alert("Error al guardar la imagen.");
      return false;
    }
  };

const handleSendEmailsImmediate = async () => {
  if (!emailContent.subject || !emailContent.body) {
    alert("Debes ingresar el asunto y el cuerpo del correo.");
    return;
  }
  if (!senderEmail) {
    alert("Debes seleccionar el correo remitente.");
    return;
  }

  const imageSaved = await handleSaveImage();
  if (!imageSaved) return;

  try {
    const payload = {
      ...emailContent,
      senderEmail,
    };

    const response = await fetch(
      `${API_URL_GATEWAY_RPA}/gateway/emailclick/enviar_correos`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );
    const result = await response.json();
    alert(result.message);
  } catch (error) {
    alert("Error al enviar correos.");
    console.error(error);
  }
};


  const handleScheduleEmails = async () => {
    if (!emailContent.subject || !emailContent.body) {
      alert("Debes ingresar el asunto y el cuerpo del correo.");
      return;
    }
    if (!scheduledTime) {
      alert("Debes seleccionar una fecha y hora para programar el envío.");
      return;
    }

    const selectedDateTime = new Date(scheduledTime);
    const currentDateTime = new Date();
    if (selectedDateTime <= currentDateTime) {
      alert("La fecha y hora de envío debe ser en el futuro.");
      return;
    }

    const imageSaved = await handleSaveImage();
    if (!imageSaved) return;

 const emailData = {
  subject: emailContent.subject,
  body: emailContent.body,
  fecha_envio: scheduledTime,
  senderEmail,
};
if (!senderEmail) {
  alert("Debes seleccionar el correo remitente.");
  return;
}

    try {
      const response = await fetch(`${API_URL_GATEWAY_RPA}/gateway/emailclick/programar_envio`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(emailData),
      });
      const result = await response.json();
      if (response.ok) alert(result.message);
      else alert("Error al programar el envío: " + result.message);
    } catch (error) {
      alert("Error al programar el envío.");
      console.error(error);
    }
  };

  const handleImageUpload = (event) => {
    const f = event.target.files[0];
    if (f) {
      const reader = new FileReader();
      reader.onload = () => setImageSrc(reader.result);
      reader.readAsDataURL(f);
      setImageFile(f);
    }
  };

  const handleRemoveImage = () => {
    setImageSrc(null);
    setAreas([]);
    setSelectedArea(null);
    setUrl("");
  };

  const handleMouseDown = (e) => {
    e.preventDefault();
    if (!imageRef.current) return;

    const rect = imageRef.current.getBoundingClientRect();
    const startX = e.clientX - rect.left;
    const startY = e.clientY - rect.top;

    setSelectedArea({ x: startX, y: startY, width: 0, height: 0, url: "" });
    setIsDragging(true);
  };

  const handleMouseMove = (e) => {
    if (!isDragging || !selectedArea) return;
    const rect = imageRef.current.getBoundingClientRect();
    const width = e.clientX - rect.left - selectedArea.x;
    const height = e.clientY - rect.top - selectedArea.y;
    setSelectedArea((prev) => ({ ...prev, width, height }));
  };

  const handleMouseUp = () => {
    if (!isDragging || !selectedArea) return;

    const newX = Math.min(selectedArea.x, selectedArea.x + selectedArea.width);
    const newY = Math.min(selectedArea.y, selectedArea.y + selectedArea.height);
    const newWidth = Math.abs(selectedArea.width);
    const newHeight = Math.abs(selectedArea.height);

    const newArea = { x: newX, y: newY, width: newWidth, height: newHeight, url: selectedArea.url };
    setSelectedArea(newArea);
    setIsDragging(false);
  };

  const handleSaveArea = () => {
    if (!selectedArea || !url) return;
    setAreas([...areas, { ...selectedArea, url }]);
    setSelectedArea(null);
    setUrl("");
  };

  const handleDeleteArea = (index) => {
    setAreas((prevAreas) => prevAreas.filter((_, i) => i !== index));
  };
    function downloadTemplate() {
      const wb = XLSX.utils.book_new();
      const ws = XLSX.utils.aoa_to_sheet([
        ["CORREO","CEDULA", "NOMBRE", "CAMPAÑA", "Var1", "Var2", "Var3", "Var4", "Var5"],
      ]);
  
      ws["!cols"] = [
        { wch: 20 },
        { wch: 15 },
        { wch: 25 },
        { wch: 15 },
        { wch: 10 },
        { wch: 15 },
        { wch: 20 },
        { wch: 15 }
      ];
  
      ws["!ref"] = "A1:F2";
      XLSX.utils.book_append_sheet(wb, ws, "Correos");
      XLSX.writeFile(wb, "plantilla_correos.xlsx");
    }
    

  const handleImageClick = (e) => {
    if (!imageRef.current) return;

    const rect = imageRef.current.getBoundingClientRect();
    const scaleX = imageRef.current.naturalWidth / rect.width;
    const scaleY = imageRef.current.naturalHeight / rect.height;

    const clickX = (e.clientX - rect.left) * scaleX;
    const clickY = (e.clientY - rect.top) * scaleY;

    const clickedArea = areas.find(
      (area) =>
        clickX >= area.x &&
        clickX <= area.x + area.width &&
        clickY >= area.y &&
        clickY <= area.y + area.height
    );

    if (clickedArea) window.open(clickedArea.url, "_blank");
  };

  return (
    <>
      <GlobalStyle />
      <Container>
        <Header>
          <h1>📧 Comunicación Masiva</h1>
          <p>Gestiona correos con imágenes</p>
        </Header>

        <MainGrid>
          {/* Columna Izquierda */}
          <LeftColumn>
            {/* Card 1: Base de Envío */}
            
            <Card>
              <Space wrap className="upload-actions">
                <Button
                            type="default"
                            style={{ marginBottom: "10px" }}
                            onClick={() => navigate("/email-reporte-imagenes")}
                          >
                            Ver Reporte de Envíos
                          </Button>
              </Space>
              
             
              <label>CORREO A USAR: </label>
                              <Select
                                placeholder="Selecciona el correo remitente"
                                options={senderOptions}
                                value={senderEmail || undefined}
                                onChange={(val) => setSenderEmail(val)}
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
              </Space>
              
              <CardTitle>
                
                
                <FaUpload /> Base de Envío (Destinatarios)
              </CardTitle>
              <FileUploadArea 
                hasFile={file}
                onClick={() => document.getElementById('fileInput').click()}
              >
                <FaUpload />
                <p>{file ? file.name : 'Seleccionar archivo Excel'}</p>
                <span>Formatos aceptados: .xlsx</span>
                <input
                  id="fileInput"
                  type="file"
                  accept=".xlsx"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                />
              </FileUploadArea>
              <div style={{ marginTop: '1rem' }}>
                <PrimaryButton onClick={handleUpload}>
                  <FaCheck /> Cargar Base de Datos
                </PrimaryButton>
              </div>
            </Card>

            {/* Card 2: Contenido del Email */}
            <Card>
              <CardTitle>
                <FaPaperPlane /> Contenido del Email
              </CardTitle>
              <FormGroup>
                <Space.Compact style={{ width: "100%" }}>
  <Input
    value={subject}
    onChange={(e) => setSubject(e.target.value)}
    placeholder="Asunto..."
  />
  <Select
    placeholder="Variables"
    onChange={(v) => setSubject((prev) => prev + `{${v}}`)}
    style={{ width: 180 }}
  >
    {availableVars.map((v) => (
      <Option key={v} value={v}>{v}</Option>
    ))}
  </Select>
</Space.Compact>

              </FormGroup>
              <FormGroup>
                <label>Cuerpo del mensaje</label>
                <TextArea
  rows={6}
  value={body}
  onChange={(e) => setBody(e.target.value)}
  placeholder="Escribe el cuerpo... usa {VARIABLE}"
/>

<Select
  placeholder="Insertar variable"
  onChange={(v) => setBody((prev) => prev + `{${v}}`)}
  style={{ width: "100%", marginTop: 8 }}
>
  {availableVars.map((v) => (
    <Option key={v} value={v}>{v}</Option>
  ))}
</Select>

              </FormGroup>
              <SecondaryButton onClick={handleSendEmailsImmediate}>
                <FaPaperPlane /> Enviar Ahora
              </SecondaryButton>
            </Card>

            {/* Card 3: Programar Envío */}
            <Card>
              <CardTitle>
                <FaClock /> Programar Envío
              </CardTitle>
              <FormGroup>
                <label>Fecha y hora de envío</label>
                <Input
                  type="datetime-local"
                  value={scheduledTime}
                  onChange={(e) => setScheduledTime(e.target.value)}
                />
                <small>Seleccione cuándo desea que se envíen los correos</small>
              </FormGroup>
              <TertiaryButton onClick={handleScheduleEmails}>
                <FaClock /> Programar Envío
              </TertiaryButton>
            </Card>
          </LeftColumn>

          {/* Columna Derecha */}
          <RightColumn>
            {/* Card 4: URLs Activas */}
            <Card>
              <CardTitle>
                <FaLink /> URL Activa
              </CardTitle>
              
              {selectedArea && (
                <UrlInputRow>
                  <UrlInput
                    type="text"
                    placeholder="https://ejemplo.com"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                  />
                  <SaveUrlButton onClick={handleSaveArea}>
                    <FaCheck /> Guardar
                  </SaveUrlButton>
                </UrlInputRow>
              )}

              {areas.length > 0 ? (
                <UrlList>
                  {areas.map((area, index) => (
                    <UrlItem key={index}>
                      <UrlDot />
                      <UrlLink href={area.url} target="_blank" rel="noopener noreferrer">
                        {area.url}
                      </UrlLink>
                      <DeleteButton onClick={() => handleDeleteArea(index)}>
                        <FaTrash />
                      </DeleteButton>
                    </UrlItem>
                  ))}
                </UrlList>
              ) : (
                <p style={{ color: '#718096', textAlign: 'center', padding: '2rem 0' }}>
                  No hay áreas clickeables definidas aún
                </p>
              )}
            </Card>

            {/* Sección de Imagen */}
            {!imageSrc ? (
              <Card style={{ textAlign: 'center' }}>
                <CardTitle style={{ justifyContent: 'center' }}>
                  <FaImage /> Imagen Interactiva
                </CardTitle>
                <FileUploadArea onClick={() => document.getElementById('imageInput').click()}>
                  <FaImage />
                  <p>Cargar imagen para crear áreas clickeables</p>
                  <span>Arrastra y suelta o haz clic para seleccionar</span>
                  <input
                    id="imageInput"
                    type="file"
                    accept="image/*"
                    onChange={handleImageUpload}
                    style={{ display: 'none' }}
                  />
                </FileUploadArea>
              </Card>
            ) : (
              <Card>
                <CardTitle>
                  <FaImage /> Imagen Interactiva - Dibuja áreas clickeables
                </CardTitle>
                <p style={{ color: '#718096', marginBottom: '1rem' }}>
                  Haz clic y arrastra sobre la imagen para crear áreas clickeables. Luego asigna una URL a cada área.
                </p>
                <ImageContainer>
                  <RemoveImageButton onClick={handleRemoveImage}>
                    ✕ Eliminar
                  </RemoveImageButton>
                  <Image
                    src={imageSrc}
                    alt="Interactiva"
                    ref={imageRef}
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onClick={handleImageClick}
                  />
                  {areas.map((area, index) => (
                    <ClickableArea
                      key={index}
                      x={area.x}
                      y={area.y}
                      width={area.width}
                      height={area.height}
                      onClick={(e) => {
                        e.preventDefault();
                        window.open(area.url, "_blank");
                      }}
                    />
                  ))}
                  {selectedArea && (
                    <SelectedArea
                      style={{
                        left: selectedArea.x,
                        top: selectedArea.y,
                        width: selectedArea.width,
                        height: selectedArea.height,
                      }}
                    />
                  )}
                </ImageContainer>
              </Card>
            )}
          </RightColumn>
        </MainGrid>
      </Container>
    </>
  );
};

export default ImagenClick;