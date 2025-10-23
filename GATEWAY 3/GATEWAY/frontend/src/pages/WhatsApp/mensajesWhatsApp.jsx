import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";
import React, { useMemo, useRef, useState } from "react";
import * as XLSX from "xlsx";
import axios from "axios";
import "./mensajesWhatsApp.css";
import Picker from "@emoji-mart/react";
import data from "@emoji-mart/data";
import { message } from "antd";
import { useNavigate } from "react-router-dom";

import { API_URL_GATEWAY } from "../../config";

const TEMPLATES = [
  { key: "none", name: "Seleccionar plantilla...", html: "" },
  {
    key: "promo1",
    name: "Recordatorio de pago 01",
    html: `
    <p>Hola👋</p><br />
    <p>Desde Systemgroup te recordamos que el próximo [FECHA] vence tu acuerdo de pago.</p><br />
    <p>Aprovecha tu descuento especial de [MONTO] y sal de reportes sin complicaciones.</p><br />
    <p>Si necesitas ayuda, estamos aquí para apoyarte 💬</p>
  `,
  },
  {
    key: "promo2",
    name: "Recordatorio de pago 02",
    html: `
    <p>Hola. Systemgroup te informa que tu acuerdo vence el [FECHA] y cuentas con un descuento de [MONTO] válido hasta esa fecha.</p><br />
    <p>Es una gran oportunidad para ponerte al día y mantener tu historial limpio. ¿Te ayudamos con el proceso?</p>
  `,
  },
  {
    key: "promo3",
    name: "Recordatorio de pago 03",
    html: `
    <p>¡Mañana vence tu acuerdo con Systemgroup!</p><br />
    <p>Aprovecha tu descuento de [MONTO] antes de que se pierda. Haz tu pago y asegura los beneficios que ya tienes activos.</p><br />
    <p>Es fácil y rápido. Escríbenos si necesitas apoyo ✅</p>
  `,
  },

  {
    key: "promo4",
    name: "Recordatorio de pago 04",
    html: `
    <p>Hola. A veces el ritmo diario no nos deja cumplir todo, lo entendemos.</p><br />
    <p>Solo queremos recordarte que mañana vence tu acuerdo con Systemgroup.</p><br />
    <p>Tu descuento de [MONTO] aún está activo.</p><br />
    <p>Aquí estamos si necesitas una mano con el proceso.</p>
  `,
  },
  {
    key: "promo5",
    name: "Recordatorio de pago 05",
    html: `
    <p>¡Último día!</p><br />
    <p>Hoy vence tu acuerdo con Systemgroup y con él se va tu descuento de [MONTO].</p><br />
    <p>Haz tu pago a tiempo y mantén todos tus beneficios</p><br />
    <p>Este es tu momento de cerrar esa deuda sin pagar de más.</p>
  `,
  },
  {
    key: "promo9",
    name: "Saludo Cliente 01",
    html: `
    <p>¡Hola [NOMBRE]! 👋 Espero que estés muy bien </p><br />
    <p>Desde Systemgroup te escribimos porque identificamos un saldo pendiente con el banco [NOMBRE DEL BANCO].</p><br />
    <p>Nos gustaría conversar contigo y presentarte una oferta personalizada que te ayude a resolverlo de forma sencilla.</p><br />
    <p>¿Te parece si lo hablamos? Estoy para ayudarte 😊</p><br />
    <p><strong>📞 Puedes contactarnos al [NÚMERO DE TELÉFONO PRINCIPAL]</strong></p>
  `,
  },

  {
    key: "promo10",
    name: "Saludo Cliente 02",
    html: `
    <p>¡Hola [NOMBRE]! 😊 ¿Cómo estás?</p><br />
    <p>Te hablo desde Systemgroup porque vimos que tienes un saldo pendiente con el banco [NOMBRE DEL BANCO], y queremos ofrecerte una propuesta que se ajuste a ti.</p><br />
    <p>La idea es ayudarte a solucionar esto sin complicaciones. ¿Te gustaría que lo revisemos juntos?🤝</p><br />
    <p><strong>📞 Puedes contactarnos al [NÚMERO DE TELÉFONO PRINCIPAL]</strong></p>
  `,
  },
  {
    key: "promo11",
    name: "Saludo Cliente 03",
    html: `
    <p>Hola [NOMBRE], buen día 👋</p><br />
    <p>Desde Systemgroup nos comunicamos contigo porque hemos identificado un saldo pendiente con el banco [NOMBRE DEL BANCO].</p><br />
    <p>Queremos brindarte una alternativa personalizada para que puedas regularizar tu situación de forma cómoda y sin presiones.</p><br />
    <p>Quedo atento(a) para comentarte más detalles si estás de acuerdo.</p><br />
    <p><strong>📞 Puedes contactarnos al [NÚMERO DE TELÉFONO PRINCIPAL]</strong></p>
  `,
  },
  {
    key: "promo12",
    name: "Oferta para cliente",
    html: `
    <p>¡Hola! Te saludamos desde SystemGroup.</p><br />
    <p>📢 Actualmente gestionamos la deuda que tienes con el Banco {{1}}.</p><br />
    <p>👉 Por favor, confirma si eres {{2}} para continuar.</p><br />
    <p>🎯 Oferta especial por tiempo limitado:</p><br />
    <p>De un total de {{3}}, solo necesitas pagar {{4}} para ponerte al día.</p>
  `,
  },
];

function uniqueClean(list) {
  const set = new Set();
  list.forEach((raw) => {
    const s = String(raw || "")
      .replace(/\s+/g, "")
      .replace(/[^\d+]/g, "")
      .trim();
    if (s) set.add(s);
  });
  return Array.from(set);
}

function normalizeCellToString(val) {
  if (val == null) return "";

  // Si es numérico, conviértelo con Intl.NumberFormat o toFixed para evitar notación científica
  if (typeof val === "number" && Number.isFinite(val)) {
    return val.toString().replace(/\.0+$/, ""); // quita .0 finales si los hay
  }

  let s = String(val).trim();

  // detectar notación científica y expandirla
  const sci = s.replace(",", ".");
  if (/^\d+(\.\d+)?[eE][+-]?\d+$/.test(sci)) {
    const n = Number(sci);
    if (Number.isFinite(n)) {
      return n.toLocaleString("en-US", {
        useGrouping: false,
        maximumFractionDigits: 20,
      });
    }
  }

  return s;
}

// 👇 detecta separador SOLO si aparece en el header.
//    Si el header no tiene separador, asumimos 1 sola columna (no partimos por comas dentro del dato)
function detectDelimiterFromHeader(headerLine) {
  if (headerLine.includes(";")) return ";";
  if (headerLine.includes("\t")) return "\t";
  if (headerLine.includes(",")) return ",";
  return null; // una sola columna
}

function parseCSV(text) {
  const lines = text
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  if (!lines.length) return [];

  const header = lines[0];
  const delimiter = detectDelimiterFromHeader(header);

  // ¿saltear header?
  const hasHeader = /^(numero|número|phone|telefono|tel)$/i.test(header);
  const startIdx = hasHeader ? 1 : 0;

  const out = [];
  for (let i = startIdx; i < lines.length; i++) {
    const line = lines[i];

    if (!delimiter) {
      // CSV de una columna => la línea completa es el valor
      const v = normalizeCellToString(line);
      if (v) out.push(v);
      continue;
    }

    // multi-columna: tomamos la PRIMERA columna
    const first = line.split(delimiter)[0]?.trim();
    if (!first) continue;

    const v = normalizeCellToString(first);
    if (v) out.push(v);
  }

  return out;
}

async function readExcelFile(file) {
  const ext = (file.name.split(".").pop() || "").toLowerCase();
  if (ext === "csv") {
    const text = await file.text();
    return parseCSV(text);
  }
  // XLSX/XLS
  const data = await file.arrayBuffer();
  const wb = XLSX.read(data, { type: "array" });
  const sheet = wb.Sheets[wb.SheetNames[0]];
  // raw:true => valores "numéricos" como number (evita textos con 'e')
  const rows = XLSX.utils.sheet_to_json(sheet, {
    header: 1,
    raw: false,
    defval: "",
  });

  const out = [];
  let numCol = 0;

  if (rows.length) {
    const header = (rows[0] || []).map((x) => String(x || "").toLowerCase());
    const idx = header.findIndex((h) =>
      /^(numero|número|phone|telefono|tel)$/.test(h)
    );
    if (idx >= 0) numCol = idx;
  }

  for (let i = 0; i < rows.length; i++) {
    const cell = rows[i]?.[numCol];
    if (cell == null) continue;

    // evitar confundir header
    const asText = String(cell).trim();
    if (/^(numero|número|phone|telefono|tel)$/i.test(asText)) continue;

    const v = normalizeCellToString(cell);
    if (v) out.push(v);
  }
  return out;
}

function htmlToWhatsAppText(html) {
  if (!html) return "";

  // 1) manejar spans de plugins de emoji si quedaran (fallback)
  html = html.replace(
    /<span[^>]*class="[^"]*ql-emojiblot[^"]*"[^>]*>(.*?)<\/span>/gis,
    (_m, inner) => {
      const d = document.createElement("div");
      d.innerHTML = inner;
      return d.textContent || ""; // intenta sacar el emoji si está como texto
    }
  );

  // 2) formatos básicos
  let s = html;
  s = s.replace(/<(strong|b)>(.*?)<\/\1>/gis, "*$2*");
  s = s.replace(/<(em|i)>(.*?)<\/\1>/gis, "_$2_");
  s = s.replace(/<(s|del|strike)>(.*?)<\/\1>/gis, "~$2~");
  s = s.replace(/<code>(.*?)<\/code>/gis, "`$1`");

  // 3) listas
  s = s.replace(/<ul[^>]*>(.*?)<\/ul>/gis, (_m, inner) =>
    inner.replace(/<li[^>]*>(.*?)<\/li>/gis, "- $1\n")
  );
  s = s.replace(/<ol[^>]*>(.*?)<\/ol>/gis, (_m, inner) => {
    let i = 1;
    return inner.replace(
      /<li[^>]*>(.*?)<\/li>/gis,
      (_m2, item) => `${i++}. ${item}\n`
    );
  });

  // 4) saltos y limpieza
  s = s
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/p>/gi, "\n")
    .replace(/<p[^>]*>/gi, "");
  s = s.replace(/<[^>]+>/g, ""); // quita cualquier tag restante

  // 5) decodifica entidades &nbsp; &amp; etc.
  const txt = document.createElement("textarea");
  txt.innerHTML = s;
  return txt.value
    .replace(/\u00a0/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function quillIsEmpty(html) {
  const text = html
    ?.replace(/<br\s*\/?>/gi, "\n")
    .replace(/<[^>]+>/g, "")
    .replace(/\u00a0/g, " ")
    .trim();
  return !text;
}

function toBase64(file) {
  return new Promise((resolve, reject) => {
    const fr = new FileReader();
    fr.onload = () => {
      const res = String(fr.result || "");
      const parts = res.split(",");
      resolve({
        filename: file.name,
        mimetype: file.type || "application/octet-stream",
        base64: parts.length > 1 ? parts[1] : "",
      });
    };
    fr.onerror = reject;
    fr.readAsDataURL(file);
  });
}

export default function MensajesWhatsapp() {
  // números y archivo Excel
  const [records, setRecords] = useState([]);
  const excelInputRef = useRef(null);
  const navigate = useNavigate();

  // mensaje y formatos
  const [messageHtml, setMessageHtml] = useState("");
  const [attachments, setAttachments] = useState([]);
  const attachInputRef = useRef(null);
  const [loading, setLoading] = useState(false);

  const [campana, setCampana] = useState("NPL");

  const quillRef = useRef(null);
  const [showEmoji, setShowEmoji] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState("none");

  const contactCount = records.length;

  const MAX_VARS = 5;

  function resolveTemplate(template, varsObj) {
    let out = String(template || "");
    for (let i = 1; i <= MAX_VARS; i++) {
      const vKey = `v${i}`;
      const varKey = `var${i}`;
      const rxV = new RegExp(`\\{\\{\\s*${vKey}\\s*\\}\\}`, "gi");
      const rxVar = new RegExp(`\\{\\{\\s*${varKey}\\s*\\}\\}`, "gi");
      const v = varsObj[vKey] ?? "";
      out = out.replace(rxV, v);
      out = out.replace(rxVar, varsObj[varKey] ?? v);
    }
    return out;
  }

  function addNumberManually() {
    const input = document.getElementById("numberInput");
    const val = (input?.value || "").trim();
    if (!val) return;
    // fusiona por número (si existe, lo sobreescribe)
    const map = new Map((records || []).map((r) => [r.numero, r]));
    if (!map.has(val)) {
      map.set(val, { numero: val, vars: {} });
    }
    setRecords(Array.from(map.values()));
    if (input) input.value = "";
  }

  function removeNumber(idx) {
    const next = records.slice();
    next.splice(idx, 1);
    setRecords(next);
  }

  function applyTemplate(key) {
    const tpl = TEMPLATES.find((t) => t.key === key);
    if (!tpl) return;
    // Si ya hay contenido, confirmamos reemplazar
    if (messageHtml && key !== "none") {
      const ok = window.confirm(
        "¿Reemplazar el contenido actual por la plantilla seleccionada?"
      );
      if (!ok) return;
    }
    setSelectedTemplate(key);
    setMessageHtml(tpl.html || "");
  }

  async function readExcelRecords(file) {
    const data = await file.arrayBuffer();
    const wb = XLSX.read(data, { type: "array" });
    const sheet = wb.Sheets[wb.SheetNames[0]];
    const rows = XLSX.utils.sheet_to_json(sheet, {
      header: 1,
      raw: false,
      defval: "",
    });

    if (!rows.length) return [];

    const headers = (rows[0] || []).map((h) => String(h || "").trim());
    const body = rows.slice(1);

    // Detectar columna Número por nombre
    let numIdx = headers.findIndex((h) =>
      /^(numero|número|phone|telefono|tel|celular|movil|móvil)$/i.test(h)
    );
    if (numIdx < 0) numIdx = 0; // fallback: primera columna

    // Tomar las primeras 5 columnas "no-numero" como variables
    const varIdxs = headers
      .map((h, i) => ({ h, i }))
      .filter(({ i }) => i !== numIdx)
      .slice(0, MAX_VARS)
      .map((x) => x.i);

    const out = [];
    for (const r of body) {
      const numeroRaw = r?.[numIdx];
      if (numeroRaw == null || String(numeroRaw).trim() === "") continue;
      const numero = normalizeCellToString(numeroRaw);

      const vars = {};
      for (let k = 0; k < varIdxs.length; k++) {
        const val = r?.[varIdxs[k]];
        const clean = normalizeCellToString(val);
        vars[`v${k + 1}`] = clean;
        vars[`var${k + 1}`] = clean; // compatibilidad con {{varN}}
      }
      out.push({ numero, vars });
    }
    return out;
  }

  async function onExcelFiles(e) {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    const all = [];
    for (const f of files) {
      try {
        const recs = await readExcelRecords(f);
        all.push(...recs);
      } catch (err) {
        console.error("Error leyendo", f.name, err);
        message.error("No se pudo leer el archivo: " + f.name);
      }
    }
    const byNumero = new Map((records || []).map((r) => [r.numero, r]));
    for (const r of all) byNumero.set(r.numero, r);
    setRecords(Array.from(byNumero.values()));

    e.target.value = "";
  }

  function downloadTemplate() {
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet([
      ["NUMERO", "Var1", "Var2", "Var3", "Var4", "Var5"],
    ]);

    // Ajusta ancho de columnas
    ws["!cols"] = [
      { wch: 20 }, // NUMERO
      { wch: 15 }, // Var1
      { wch: 25 }, // Var2
      { wch: 15 }, // Var3
      { wch: 10 }, // Var4
      { wch: 15 }, // Var5
    ];

    // Rango: de A1 a F2 (fila de headers + 1 ejemplo)
    ws["!ref"] = "A1:F2";

    XLSX.utils.book_append_sheet(wb, ws, "Contactos");
    XLSX.writeFile(wb, "plantilla_contactos.xlsx");
  }

  function onAttachFiles(e) {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    const map = new Map(attachments.map((a) => [a.name, a]));
    files.forEach((f) => map.set(f.name, f));
    setAttachments(Array.from(map.values()));
  }

  const previewHtml = useMemo(() => messageHtml || "", [messageHtml]);

  const previewText = useMemo(() => {
    const base = htmlToWhatsAppText(messageHtml || "");
    // toma hasta 3 previews concatenados
    const sample = records
      .slice(0, 50000)
      .map((r) => resolveTemplate(base, r.vars || {}));
    return sample.join("\n\n— — —\n\n") || base;
  }, [messageHtml, records]);

  async function onSend() {
    if (!records.length) {
      message.error("Agrega al menos un contacto (Excel o manual).");
      return;
    }
    if (quillIsEmpty(messageHtml)) {
      message.error("Escribe un mensaje.");
      return;
    }

    setLoading(true);
    const baseText = htmlToWhatsAppText(messageHtml); // mensaje base sin HTML

    let ok = 0,
      fail = 0;

    // Enviar uno a uno (secuencial para no saturar)
    for (const r of records) {
      try {
        const personalizado = resolveTemplate(baseText, r.vars || {});
        const fd = new FormData();
        fd.append("numeros", r.numero);
        fd.append("mensaje", personalizado);
        fd.append("campana", campana);
        attachments.forEach((f) => fd.append("adjuntos", f));

        const userId = localStorage.getItem("idUsuario");
        if (userId && /^\d+$/.test(userId)) {
          fd.append("idUsuarioApp", userId);
        }

        const { data } = await axios.post(
          `${API_URL_GATEWAY}/gateway-rpa/MensajeWhatsApp/registrar`,
          fd
        );

        // opcional: usa data.insertados si tu backend lo retorna
        ok += 1;
      } catch (e) {
        console.error("Error enviando a", r.numero, e);
        fail += 1;
      }
    }

    setLoading(false);
    if (fail === 0) {
      message.success(`Enviados ${ok} registro(s).`);
    } else {
      message.warning(
        `OK: ${ok}, Fallidos: ${fail}. Revisa consola para detalles.`
      );
    }
  }

  const quillModules = {
    toolbar: {
      container: [["bold"], [{ list: "ordered" }, { list: "bullet" }]],
    },
  };
  const quillFormats = ["header", "bold", "list"];

  const [selectedPlaceholder, setSelectedPlaceholder] = useState("{{v1}}");

  function insertPlaceholderIntoQuill() {
    const quill = quillRef.current?.getEditor?.();
    if (!quill) return;
    const ph = selectedPlaceholder;
    const range = quill.getSelection(true);
    const pos = range?.index ?? quill.getLength();
    quill.insertText(pos, ph);
    quill.setSelection(pos + ph.length, 0);
  }

  return (
    <div className="wpp-root">
      <header className="wpp-header">
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
          }}
        >
          <div>
            <h1 style={{ marginBottom: 4 }}>🚀 RPA Mensajes WhatsApp</h1>
            <p style={{ margin: 0 }}>
              Sistema de Automatización para Envío Masivo de Mensajes
            </p>
          </div>
          <button
            className="btn btn-secondary"
            onClick={() => navigate("/reportesWhatsApp")}
            title="Ir a Reportes"
          >
            📊 Reportes
          </button>
        </div>
      </header>

      <div className="wpp-grid">
        {/* Panel izquierdo: NÚMEROS */}
        <section className="panel">
          <div className="panel-header">📱 Gestión de Números</div>
          <div className="panel-content">
            <div className="panel-header">
              <div style={{ marginBottom: 12 }}>
                <label style={{ fontWeight: 600, marginRight: 8 }}>
                  Campaña:
                </label>
                <label style={{ marginRight: 12 }}>
                  <input
                    type="radio"
                    name="campana"
                    value="NPL"
                    checked={campana === "NPL"}
                    onChange={() => setCampana("NPL")}
                  />{" "}
                  NPL
                </label>
                <label>
                  <input
                    type="radio"
                    name="campana"
                    value="JCAP"
                    checked={campana === "JCAP"}
                    onChange={() => setCampana("JCAP")}
                  />{" "}
                  JCAP
                </label>
              </div>
            </div>
            <div className="upload-section">
              <div className="upload-buttons">
                <button
                  className="btn btn-primary"
                  onClick={() => excelInputRef.current?.click()}
                >
                  📁 Cargar Excel
                </button>
                <input
                  ref={excelInputRef}
                  type="file"
                  accept=".xlsx,.xls" // quita .csv si no lo quieres
                  style={{ display: "none" }}
                  onChange={onExcelFiles}
                />
                <button
                  className="btn btn-secondary"
                  onClick={downloadTemplate}
                >
                  📋 Plantilla
                </button>
              </div>

              <div className="number-input">
                <input
                  id="numberInput"
                  type="text"
                  placeholder="Ej: 573001234567"
                  onKeyDown={(e) => e.key === "Enter" && addNumberManually()}
                />
                <button className="btn btn-primary" onClick={addNumberManually}>
                  Agregar
                </button>
              </div>
            </div>

            <div className="number-list">
              {records.map((r, idx) => (
                <div key={r.numero + idx} className="number-item">
                  <span>{r.numero}</span>
                  <button
                    className="remove-btn"
                    onClick={() => {
                      const next = records.slice();
                      next.splice(idx, 1);
                      setRecords(next);
                    }}
                    title="Quitar"
                  >
                    ✕
                  </button>
                </div>
              ))}

              {!records.length && (
                <div style={{ color: "#777", fontSize: 13 }}>
                  Sin contactos. Carga un Excel/CSV o agrega manualmente.
                </div>
              )}
            </div>

            <div className="stats">
              <strong>
                📊 Total de contactos: <span>{contactCount}</span>
              </strong>
              <br />
              <small>Listos para guardarse y enviar luego por RPA</small>
            </div>
          </div>
        </section>

        {/* Panel centro: MENSAJE */}
        <section className="panel">
          <div className="panel-header">✏️ Composición de Mensaje</div>
          <div className="panel-content">
            <select
              className="template-select"
              value={selectedTemplate}
              onChange={(e) => applyTemplate(e.target.value)}
            >
              {TEMPLATES.map((t) => (
                <option key={t.key} value={t.key} disabled={t.key === "none"}>
                  {t.name}
                </option>
              ))}
            </select>

            <div
              className="placeholder-toolbar"
              style={{ display: "flex", gap: 8, marginBottom: 8 }}
            >
              <select
                value={selectedPlaceholder}
                onChange={(e) => setSelectedPlaceholder(e.target.value)}
              >
                {Array.from(
                  { length: MAX_VARS },
                  (_, i) => `{{Var${i + 1}}}`
                ).map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
              <button
                className="btn btn-secondary"
                onClick={insertPlaceholderIntoQuill}
              >
                Insertar variable
              </button>
            </div>
            <ReactQuill
              ref={quillRef}
              theme="snow"
              value={messageHtml}
              onChange={setMessageHtml}
              modules={quillModules}
              formats={quillFormats}
              placeholder="Escribe tu mensaje… (usa la toolbar para negrita, emoji, listas, etc.)"
            />
            <button
              className="format-btn"
              onClick={() => setShowEmoji((v) => !v)}
            >
              😀 Emoji
            </button>
            {showEmoji && (
              <div className="emoji-popover">
                <Picker
                  data={data}
                  onEmojiSelect={(emoji) => {
                    const native = emoji?.native || "";
                    const quill = quillRef.current?.getEditor();
                    if (!quill || !native) return;
                    const range = quill.getSelection(true);
                    const pos = range?.index ?? quill.getLength();
                    quill.insertText(pos, native); // inserta el emoji como texto real
                    quill.setSelection(pos + native.length, 0);
                    setShowEmoji(false);
                  }}
                />
              </div>
            )}

            <div className="attachment-section">
              <label
                className="attachment-btn"
                onClick={() => attachInputRef.current?.click()}
              >
                📎 Adjuntar archivos
              </label>
              <input
                ref={attachInputRef}
                type="file"
                multiple
                style={{ display: "none" }}
                onChange={onAttachFiles}
              />
              <small className="attachment-hint">
                Formatos soportados: PDF, JPG, PNG, DOC (recomendado &lt; 8MB
                c/u)
              </small>

              {!!attachments.length && (
                <ul className="attachment-list">
                  {attachments.map((a) => (
                    <li key={a.name}>
                      {a.name}{" "}
                      <span className="muted">({a.type || "mime?"})</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="send-section">
              <button
                className="send-btn"
                onClick={onSend}
                disabled={loading}
                title="Guardar en BD para envío por RPA"
              >
                {loading ? "Guardando..." : "💾 Enviar"}
              </button>
              <div style={{ marginTop: 8 }}>
                <small>
                  Se guardarán <strong>{contactCount}</strong> registro(s)
                </small>
              </div>
            </div>
          </div>
        </section>

        {/* Panel derecho: PREVIEW */}
        <section className="panel">
          <div className="panel-header">👁️ Vista Previa</div>
          <div className="panel-content">
            <div className="preview-label">
              Así verán el mensaje tus contactos:
            </div>
            <div className="phone-mockup">
              <div className="phone-screen">
                <div className="whatsapp-header">
                  <div className="contact-avatar">TU</div>
                  <div className="contact-info">
                    <h4>Tu Empresa</h4>
                    <p>en línea</p>
                  </div>
                </div>
                <div className="chat-area">
                  <div
                    className="message-bubble"
                    dangerouslySetInnerHTML={{
                      __html:
                        (previewText || "").replace(/\n/g, "<br/>") +
                        '<div class="message-time">' +
                        new Date().toLocaleTimeString().slice(0, 5) +
                        "</div>",
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
