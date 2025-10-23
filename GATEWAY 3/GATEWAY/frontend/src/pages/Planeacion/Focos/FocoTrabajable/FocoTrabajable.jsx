import React, { useEffect, useState } from "react";
import {
  Table,
  Input,
  Button,
  Card,
  Row,
  Col,
  Form,
  message,
  Collapse,
  Select,
  Modal,
} from "antd";
import { SearchOutlined, ReloadOutlined, SendOutlined } from "@ant-design/icons";
import { API_URL_GATEWAY } from "../../../../config";

const { Panel } = Collapse;
const { Option } = Select;

const formatter = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  minimumFractionDigits: 0,
});

const CargueFocos = () => {
  const [form] = Form.useForm();
  const [data, setData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL_GATEWAY}/gateway/focos/trabajable/consultar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });

      const result = await response.json();
      if (Array.isArray(result)) {
        setData(result);
        setFilteredData(result);
      } else if (Array.isArray(result?.data)) {
        setData(result.data);
        setFilteredData(result.data);
      } else {
        message.warning("No se pudieron cargar los datos.");
      }
    } catch (error) {
      message.error("Error al consultar los datos.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleBuscar = async () => {
    try {
      const filtros = await form.validateFields();
      const filtrados = data.filter((item) => {
        return Object.entries(filtros).every(([campo, valor]) => {
          if (valor === undefined || valor === "") return true;
          const itemVal = item[campo];
          if (campo === "juridico" || campo === "insolvencia") {
            return itemVal === (valor === "1");
          }
          if (!isNaN(valor) && typeof itemVal === "number") {
            return Number(itemVal) === Number(valor);
          }
          return String(itemVal || "").toLowerCase().includes(String(valor).toLowerCase());
        });
      });
      setFilteredData(filtrados);
    } catch {
      message.warning("Completa los campos correctamente");
    }
  };

  const handleLimpiar = () => {
    form.resetFields();
    setFilteredData(data);
  };

  const handleEnviar = async () => {
    if (filteredData.length === 0) {
      message.warning("No hay datos filtrados para enviar.");
      return;
    }

    if (filteredData.length === data.length) {
      Modal.confirm({
        title: "¿Está seguro de enviar todos los registros?",
        content: `Se van a enviar ${filteredData.length} registros.`,
        onOk: () => enviarDatos(),
      });
    } else {
      enviarDatos();
    }
  };

  const enviarDatos = async () => {
    try {
      const payload = filteredData.map((d) => ({
        nombreCliente: d.nombre,
        cedula: d.cedula,
        telefono: d.celular || "",
        producto: "",
        entidad: "",
        saldoTotal: d.Total,
        capital: d.capital,
        oferta1: 0,
        oferta2: 0,
        oferta3: 0,
        cuotas3: 0,
        cuotas6: 0,
        cuotas12: 0,
      }));

      for (const row of payload) {
        await fetch(`${API_URL_GATEWAY}/gateway/focos/resultado/insertar`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(row),
        });
      }
      message.success("Registros enviados exitosamente.");
    } catch (err) {
      console.error(err);
      message.error("Error al enviar registros.");
    }
  };

  const columns = [
    { title: "Nombre", dataIndex: "nombre", key: "nombre" },
    { title: "Cédula", dataIndex: "cedula", key: "cedula" },
    {
      title: "Capital",
      dataIndex: "capital",
      key: "capital",
      render: (val) => formatter.format(val),
    },
    { title: "Clasificación", dataIndex: "idClasificacion", key: "idClasificacion" },
    { title: "Portafolio", dataIndex: "idPortafolio", key: "idPortafolio" },
  ];

  const expandedRowRender = (record) => (
    <div style={{ paddingLeft: 20 }}>
      <Card type="inner" title="Cliente">
        <Row gutter={12}>
          <Col span={6}><strong>Asignación:</strong> {record.idAsignacion}</Col>
          <Col span={6}><strong>Total Deuda:</strong> {formatter.format(record.TotalDeudaAdquirida)}</Col>
          <Col span={6}><strong>Total:</strong> {formatter.format(record.Total)}</Col>
        </Row>
      </Card>

      <Card type="inner" title="Judicial" style={{ marginTop: 12 }}>
        <Row gutter={12}>
          <Col span={6}><strong>Jurídico:</strong> {record.juridico ? "Sí" : "No"}</Col>
          <Col span={6}><strong>Insolvencia:</strong> {record.insolvencia ? "Sí" : "No"}</Col>
          <Col span={6}><strong>Asesor:</strong> {record.asesor_juridico}</Col>
          <Col span={6}><strong>Honorarios:</strong> {formatter.format(record.honorarios)}</Col>
        </Row>
      </Card>

      <Card type="inner" title="Planeación y Pagos" style={{ marginTop: 12 }}>
        <Row gutter={12}>
          <Col span={6}><strong>Pago 1:</strong> {formatter.format(record.pago)}</Col>
          <Col span={6}><strong>Pago 2:</strong> {formatter.format(record.pago2)}</Col>
          <Col span={6}><strong>Pagos Consolidados:</strong> {formatter.format(record.pagos_consolidados)}</Col>
          <Col span={6}><strong>Recaudo:</strong> {formatter.format(record.valor_recaudo)}</Col>
          <Col span={6}><strong>Fecha Recaudo:</strong> {record.fecha_recaudo?.substring(0, 10)}</Col>
          <Col span={6}><strong>Contacto:</strong> {record.contacto ? "Sí" : "No"}</Col>
          <Col span={6}><strong>Negociación:</strong> {record.negociacion ? "Sí" : "No"}</Col>
        </Row>
      </Card>
    </div>
  );

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Form form={form} layout="vertical">
          <Collapse defaultActiveKey={["credito"]}>
            <Panel header="Crédito" key="credito">
              <Row gutter={16}>
                <Col span={6}><Form.Item label="Nombre" name="nombre"><Input /></Form.Item></Col>
                <Col span={6}><Form.Item label="Cédula" name="cedula"><Input /></Form.Item></Col>
                <Col span={6}><Form.Item label="Capital" name="capital"><Input /></Form.Item></Col>
                <Col span={6}><Form.Item label="Saldo Capital" name="SaldoCapital"><Input /></Form.Item></Col>
                <Col span={6}><Form.Item label="Intereses Corrientes" name="InteresesCorrientes"><Input /></Form.Item></Col>
                <Col span={6}><Form.Item label="Clasificación" name="idClasificacion"><Input /></Form.Item></Col>
              </Row>
            </Panel>

            <Panel header="Planeación y Pagos" key="planeacion">
              <Row gutter={16}>
                <Col span={6}><Form.Item label="Pago Mes 1" name="pago"><Input /></Form.Item></Col>
                <Col span={6}><Form.Item label="Pago Mes 2" name="pago2"><Input /></Form.Item></Col>
                <Col span={6}><Form.Item label="Valor Recaudo" name="valor_recaudo"><Input /></Form.Item></Col>
              </Row>
            </Panel>

            <Panel header="Judicial" key="judicial">
              <Row gutter={16}>
                <Col span={6}><Form.Item label="¿Está en Jurídico?" name="juridico">
                  <Select allowClear>
                    <Option value="1">Sí</Option>
                    <Option value="0">No</Option>
                  </Select>
                </Form.Item></Col>
                <Col span={6}><Form.Item label="¿Insolvencia?" name="insolvencia">
                  <Select allowClear>
                    <Option value="1">Sí</Option>
                    <Option value="0">No</Option>
                  </Select>
                </Form.Item></Col>
              </Row>
            </Panel>
          </Collapse>

          <Row justify="end" style={{ marginTop: 20 }} gutter={8}>
            <Col>
              <Button icon={<ReloadOutlined />} onClick={handleLimpiar}>
                Limpiar Filtros
              </Button>
            </Col>
            <Col>
              <Button type="default" icon={<SendOutlined />} onClick={handleEnviar}>
                Enviar
              </Button>
            </Col>
            <Col>
              <Button type="primary" icon={<SearchOutlined />} onClick={handleBuscar}>
                Consultar
              </Button>
            </Col>
          </Row>
        </Form>
      </Card>

      <Table
        columns={columns}
        dataSource={filteredData}
        rowKey="idTrabajable"
        loading={loading}
        expandable={{ expandedRowRender }}
        pagination={{ pageSize: 10 }}
        scroll={{ x: "max-content" }}
      />
    </div>
  );
};

export default CargueFocos;
