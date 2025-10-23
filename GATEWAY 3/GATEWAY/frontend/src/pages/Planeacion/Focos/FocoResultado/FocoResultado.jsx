import React, { useState, useEffect } from "react";
import { Row,Col,Card,Input,Button,Table,Modal,message,Form,Select} from "antd";
import { SearchOutlined, DownloadOutlined, DeleteOutlined } from "@ant-design/icons";
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";
import "./FocoResultado.css";
import { API_URL_GATEWAY } from "../../../../config";

const { Option } = Select;

const formatoMoneda = (valor) =>
  new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP" }).format(valor);

const FocosResultado = () => {
  const [formData, setFormData] = useState({});
  const [datos, setDatos] = useState([]);
  const [resultadoModal, setResultadoModal] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [filtrosUsados, setFiltrosUsados] = useState({});
  const [desdeBoton, setDesdeBoton] = useState(false);
  const [productoSeleccionado, setProductoSeleccionado] = useState(null);
  const [entidadSeleccionada, setEntidadSeleccionada] = useState(null);

  const limpiarValor = (valor) => {
    if (!valor) return "";

    // Eliminar comas y puntos
    let limpio = valor.replace(/[.,]/g, "");

    // Eliminar decimales finales tipo ,00 o .00
    limpio = limpio.replace(/(00)$/, "");

    return limpio;
  };

  const handleChange = (campo, tipo, valor) => {
    const valorLimpio = limpiarValor(valor);

    setFormData((prev) => ({
      ...prev,
      [campo]: {
        ...prev[campo],
        [tipo]: valorLimpio,
      },
    }));
  };

  const handleLimpiarFiltros = () => {
    setFormData({});
    setProductoSeleccionado(null);
    setEntidadSeleccionada(null);
  };


  const handleConsultar = async () => {
    const filtros = {};
    Object.keys(formData).forEach((campo) => {
      filtros[campo] = `${formData[campo]?.inicio || ""}-${formData[campo]?.fin || ""}`;
    });

    setDesdeBoton(true);

    try {
      const response = await fetch(`${API_URL_GATEWAY}/gateway/focos/resultado/consultar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(filtros),
      });
      const resultado = await response.json();

      setDatos(resultado);
      setFiltrosUsados(filtros);
      if (desdeBoton) message.success("Consulta realizada exitosamente.");
    } catch (error) {
      console.error("Error:", error);
      message.error("Error al consultar resultados.");
    } finally {
      setDesdeBoton(false);
    }
  };

  useEffect(() => {
    handleConsultar();
  }, []);

  const productos = [...new Set(datos.map((item) => item.producto))];
  const entidades = [...new Set(datos.map((item) => item.entidad))];

  const datosFiltrados = datos.filter((item) =>
    (!productoSeleccionado || item.producto === productoSeleccionado) &&
    (!entidadSeleccionada || item.entidad === entidadSeleccionada)
  );

  const handleDescargarTabla = () => {
    const wb = XLSX.utils.book_new();
    const resultadosSheet = XLSX.utils.json_to_sheet(datosFiltrados);
    XLSX.utils.book_append_sheet(wb, resultadosSheet, "Resultados");

    const buffer = XLSX.write(wb, { bookType: "xlsx", type: "array" });
    const blob = new Blob([buffer], { type: "application/octet-stream" });
    saveAs(blob, "resultados_focos.xlsx");
  };

  const columnasResultados = [
    { title: "ID", dataIndex: "id", key: "id", width: 60 },
    { title: "Nombre Cliente", dataIndex: "nombreCliente", key: "nombreCliente", width: 150 },
    { title: "Cédula", dataIndex: "cedula", key: "cedula", width: 120 },
    { title: "Teléfono", dataIndex: "telefono", key: "telefono", width: 130 },
    { title: "Producto", dataIndex: "producto", key: "producto", width: 150 },
    { title: "Entidad", dataIndex: "entidad", key: "entidad", width: 180 },
    {
      title: "Saldo Total",
      dataIndex: "saldoTotal",
      key: "saldoTotal",
      render: (value) => formatoMoneda(value),
    },
    {
      title: "Capital",
      dataIndex: "capital",
      key: "capital",
      render: (value) => formatoMoneda(value),
    },
    {
      title: "Oferta 1",
      dataIndex: "oferta1",
      key: "oferta1",
      render: (value) => formatoMoneda(value),
    },
    {
      title: "Oferta 2",
      dataIndex: "oferta2",
      key: "oferta2",
      render: (value) => formatoMoneda(value),
    },
    {
      title: "Oferta 3",
      dataIndex: "oferta3",
      key: "oferta3",
      render: (value) => formatoMoneda(value),
    },
    {
      title: "3 Cuotas",
      dataIndex: "cuotas3",
      key: "cuotas3",
      render: (value) => formatoMoneda(value),
    },
    {
      title: "6 Cuotas",
      dataIndex: "cuotas6",
      key: "cuotas6",
      render: (value) => formatoMoneda(value),
    },
    {
      title: "12 Cuotas",
      dataIndex: "cuotas12",
      key: "cuotas12",
      render: (value) => formatoMoneda(value),
    },
  ];

  const camposFiltros = [
    "saldoTotal",
    "capital",
    "oferta1",
    "oferta2",
    "oferta3",
    "cuotas3",
    "cuotas6",
    "cuotas12",
  ];

  return (
    <div className="focos-resultado-container" style={{ marginTop: "-15px" }}>
      <h2 className="focos-titulo">Consulta por Resultado</h2>

      <Card className="focos-formulario" style={{ marginTop: "-10px" }}>
        <Form layout="vertical" style={{ maxWidth: "1200px", margin: "0 auto", marginTop: "-10px" }}>
          <Row gutter={[12, 12]} justify="start">
            {camposFiltros.map((campo) => (
              <Col xs={24} sm={12} md={12} lg={6} xl={6} key={campo}>
                <div className="focos-input-group" style={{ marginTop: "-8px" }}>
                  <label>{campo}</label>
                  <div style={{ display: "flex", gap: "6px" }}>
                    <Input
                      placeholder="Inicio"
                      style={{ width: "90px" }}
                      value={formData[campo]?.inicio || ""}
                      onChange={(e) =>
                        handleChange(campo, "inicio", e.target.value)
                      }
                    />
                    <Input
                      placeholder="Fin"
                      style={{ width: "90px" }}
                      value={formData[campo]?.fin || ""}
                      onChange={(e) =>
                        handleChange(campo, "fin", e.target.value)
                      }
                    />
                  </div>
                </div>
              </Col>
            ))}
          </Row>

          <Row gutter={[12, 12]} justify="start" style={{ marginTop: 0 }}>
            <Col xs={24} sm={12} md={6}>
              <label>Productos</label>
              <Select
                style={{ width: "100%" }}
                placeholder="Seleccione un producto"
                allowClear
                onChange={(value) => setProductoSeleccionado(value)}
              >
                {productos.map((prod) => (
                  <Option key={prod} value={prod}>
                    {prod}
                  </Option>
                ))}
              </Select>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <label>Entidades</label>
              <Select
                style={{ width: "100%" }}
                placeholder="Seleccione una entidad"
                allowClear
                onChange={(value) => setEntidadSeleccionada(value)}
              >
                {entidades.map((ent) => (
                  <Option key={ent} value={ent}>
                    {ent}
                  </Option>
                ))}
              </Select>
            </Col>
          </Row>

          <div style={{ textAlign: "right", marginTop: "-45px" }}>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              onClick={handleConsultar}
              style={{ marginRight: 8 }}
            >
              Consultar
            </Button>
            <Button icon={<DownloadOutlined />} onClick={handleDescargarTabla}>
              Descargar Excel
            </Button>
            <Button icon={<DeleteOutlined />} onClick={handleLimpiarFiltros}>
              Limpiar Filtros
            </Button>
          </div>
        </Form>
      </Card>

      <Card className="focos-tabla" style={{ maxHeight: 400, overflow: "hidden", marginTop: "-5px" }}>
        <Table
          size="small"
          dataSource={datosFiltrados}
          columns={columnasResultados}
          pagination={{
            pageSize: 5,
            showSizeChanger: true,
            pageSizeOptions: ["5", "10", "20", "50"],
          }}
          rowKey="id"
          scroll={{ x: 1800, y: 300 }}
        />
      </Card>

      <Modal
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={1000}
      >
        <Table
          dataSource={resultadoModal}
          columns={columnasResultados}
          pagination={false}
          rowKey="id"
          scroll={{ x: 1800, y: 400 }}
        />
      </Modal>
    </div>
  );
};

export default FocosResultado;
