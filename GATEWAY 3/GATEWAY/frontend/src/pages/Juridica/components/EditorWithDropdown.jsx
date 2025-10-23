import React, { useRef, useState, useEffect } from "react";
import { Row, Col, Select, Typography, message } from "antd";
import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";
import "react-quill/dist/quill.bubble.css";
import "../styles/font.css";

const { Option } = Select;
const { Text } = Typography;

const EditorWithDropdown = ({ editorContent, setEditorContent, availableVariables = [] }) => {
  const quillRef = useRef(null);
  const [savedRange, setSavedRange] = useState(null);

  useEffect(() => {
    console.log("📦 (Efecto) Variables actualizadas:", availableVariables);
  }, [availableVariables]);

  const modules = {
    toolbar: [
      [{ 'font': ['arial', 'times-new-roman', 'verdana', 'calibri'] }],
      [{ 'size': ['12px', '14px', '16px', '18px', '20px', '24px', '28px', '32px'] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ 'color': [] }, { 'background': [] }],
      [{ 'script': 'sub'}, { 'script': 'super' }],
      [{ 'header': 1 }, { 'header': 2 }, 'blockquote', 'code-block'],
      [{ 'list': 'ordered' }, { 'list': 'bullet' }, { 'indent': '-1' }, { 'indent': '+1' }],
      ['direction', { 'align': [] }],
      ['link', 'image', 'video'],
      ['clean']
    ]
  };

  const handleFocus = () => {
    const quill = quillRef.current.getEditor();
    const range = quill.getSelection();
    if (range) {
      setSavedRange(range);
    }
  };

  const handleInsertVariable = (variableName) => {
    const quill = quillRef.current.getEditor();
    const range = savedRange || quill.getSelection();

    if (range) {
      quill.deleteText(range.index, range.length);
      quill.insertText(range.index, `{${variableName}}`);
      quill.setSelection(range.index + `{${variableName}}`.length);
      message.success(`Variable "${variableName}" insertada correctamente`);
    } else {
      message.warning("Selecciona primero el texto donde quieras insertar la variable.");
    }
  };

  return (
    <div style={{ width: "100%" }}>
      <Row justify="end" style={{ marginBottom: "5px" }}>
        <Col span={8} style={{ textAlign: "right" }}>
          <Text style={{ marginRight: "8px" }}>Variables :</Text>
          <Select
            key={availableVariables.join(",")}  // 🔁 fuerza rerender si cambian

            style={{ width: "70%", height: "25px" }}
            placeholder="Seleccionar"
            onChange={handleInsertVariable}
            value={null}
            onDropdownVisibleChange={(open) => {
              if (open) handleFocus();
            }}
          >
            {(availableVariables || []).map((v, idx) => (
              <Option key={idx} value={v}>
                {v}
              </Option>
            ))}
          </Select>
        </Col>
      </Row>

      <ReactQuill
        ref={quillRef}
        theme="snow"
        value={editorContent}
        onChange={setEditorContent}
        modules={modules}
        style={{ height: "38vh", fontFamily: "Calibri, Arial, Times New Roman, sans-serif" }}
      />
    </div>
  );
};

export default EditorWithDropdown;
