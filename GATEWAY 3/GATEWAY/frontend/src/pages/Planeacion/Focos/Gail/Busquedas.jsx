import React, { useState } from "react";
import {
  Card,
  Select,
  Table,
  Typography,
  message,
  Modal,
  Button,
  Input,
} from "antd";
import axios from "axios";
import { SearchOutlined, DownloadOutlined } from "@ant-design/icons";
import { PieChart, Pie, Cell, Tooltip, Legend } from "recharts";
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";

const { Title } = Typography;
const { Option } = Select;

const headers = {
  accept: "text/plain",
  "X-API-Key": "api-019635c2310270bf8696ca8da0fc5c73-aaIlCeOBlk-LKeCeKqlFWPpvGn9PGOP4YrnY6VR4rao",
};

const endpoints = [
  { label: "Campañas", value: "https://api.lula.com/v1/campaigns" },
  { label: "Secuencias", value: "https://api.lula.com/v1/sequences?status=active" },
  { label: "Redialing Rules", value: "https://api.lula.com/v1/redialing_rules?status=active" },
  { label: "Scripts", value: "https://api.lula.com/v1/scripts" },
  { label: "Casos de uso", value: "https://api.lula.com/v1/use_cases" },
  { label: "Organizaciones", value: "https://api.lula.com/v1/org" },
  { label: "Lista de contactos", value: "https://api.lula.com/v1/contact_lists" },
];

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042", "#A28EFF"];

const ResultadoGrafico = ({ data }) => (
  <PieChart width={600} height={300}>
    <Pie
      data={data}
      dataKey="value"
      nameKey="name"
      cx="40%"         // más a la izquierda para dejar espacio a la leyenda
      cy="50%"
      outerRadius={90}
      label
    >
      {data.map((entry, index) => (
        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
      ))}
    </Pie>
    <Tooltip />
    <Legend layout="vertical" align="right" verticalAlign="middle" />
  </PieChart>
);


const Busquedas = () => {
  const [selectedUrl, setSelectedUrl] = useState(null);
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [modalData, setModalData] = useState([]);
  const [modalTitle, setModalTitle] = useState("");
  const [chartData, setChartData] = useState([]);

  const handleChange = async (value) => {
    setSelectedUrl(value);
    try {
      const response = await axios.get(value, { headers });
      const raw = response.data;
      const items = Array.isArray(raw) ? raw : raw.items || [raw];

      if (items.length === 0) {
        setData([]);
        setColumns([]);
        return message.warning("No hay datos para mostrar.");
      }

      const flattened = items.map(flattenRow).filter(item => item?.id);
      const allKeys = new Set(flattened.flatMap((obj) => Object.keys(obj)));
      allKeys.delete("children");

      const cols = Array.from(allKeys).map((key) => ({
        title: key,
        dataIndex: key,
        key,
        ...getColumnSearchProps(key),
      }));

      setColumns(cols);
      setData(flattened);
    } catch (err) {
      console.error("❌ Error al consultar:", err);
      message.error("Error al obtener los datos del endpoint.");
      setColumns([]);
      setData([]);
    }
  };

  const procesarResultadosParaGrafico = (data) => {
    const resultadoContador = {};

    data.forEach(contacto => {
      contacto.touchpoints.forEach(tp => {
        const resultado = tp.outcome || "sin resultado";
        resultadoContador[resultado] = (resultadoContador[resultado] || 0) + 1;
      });
    });

    return Object.entries(resultadoContador).map(([name, value]) => ({ name, value }));
  };

  const exportarExcel = () => {
    const rows = modalData.flatMap(contacto =>
      contacto.touchpoints.map(tp => ({
        contactId: contacto.contactId,
        firstName: contacto.firstName,
        phone: tp.phone,
        outcome: tp.outcome,
        finishedAt: tp.finishedAt,
        type: tp.type,
      }))
    );
    const ws = XLSX.utils.json_to_sheet(rows);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Resultados");
    const excelBuffer = XLSX.write(wb, { bookType: "xlsx", type: "array" });
    const blob = new Blob([excelBuffer], { type: "application/octet-stream" });
    saveAs(blob, "contactos_campaña.xlsx");
  };

  const obtenerContactosDeCampana = async (nombre, campaignId) => {
    const url = `https://api.lula.com/v1/campaigns/${campaignId}/contacts/results?limit=50&page=1&size=50`;
    try {
      const response = await axios.get(url, { headers });
      const raw = response.data;
      if (!raw || raw.data.length === 0) {
        message.warning("No hay contactos disponibles para esta campaña.");
        return;
      }

      setModalTitle(`Contactos de la campaña ${nombre}`);
      setModalData(raw.data);
      const resumen = procesarResultadosParaGrafico(raw.data);
      setChartData(resumen);
      setModalVisible(true);
    } catch (err) {
      console.error("❌ Error al obtener contactos de la campaña:", err);
      message.error("Error al obtener los contactos de la campaña.");
    }
  };

  const flattenRow = (item) => {
  const flat = {};
  const children = [];

  for (const key in item) {
    const value = item[key];
    if (Array.isArray(value)) {
      const subRows = value
        .filter((subItem) => subItem?.id) // ✅ Filtra subfilas sin id
        .map((subItem, idx) => ({
          key: `${item.id || item.name || idx}-${key}-${idx}`,
          ...subItem,
        }));
      if (subRows.length > 0) {
        children.push(...subRows);
      }
    } else if (typeof value === "object" && value !== null) {
      flat[key] = (
        <a
          onClick={() => {
            setModalTitle(key);
            setModalData(value);
            setModalVisible(true);
          }}
        >
          Ver detalle
        </a>
      );
    } else {
      flat[key] = value;
    }
  }

  if (!item?.id && children.length === 0) return null; // ✅ Línea clave: no devuelve nada si no tiene id ni hijos válidos

  if (children.length > 0) flat.children = children;
  return flat;
};


  const getColumnSearchProps = (dataIndex) => ({
    filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
      <div style={{ padding: 8 }}>
        <Input
          placeholder={`Buscar ${dataIndex}`}
          value={selectedKeys[0]}
          onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
          onPressEnter={() => confirm()}
          style={{ marginBottom: 8, display: "block" }}
        />
        <Button
          type="primary"
          icon={<SearchOutlined />}
          onClick={() => confirm()}
          size="small"
          style={{ width: "100%" }}
        >
          Buscar
        </Button>
        <Button
          onClick={() => {
            clearFilters();
            confirm();
          }}
          size="small"
          style={{ width: "100%", marginTop: 4 }}
        >
          Limpiar
        </Button>
      </div>
    ),
    filterIcon: (filtered) => (
      <SearchOutlined style={{ color: filtered ? "#1890ff" : undefined }} />
    ),
    onFilter: (value, record) =>
      (record[dataIndex] ?? "")
        .toString()
        .toLowerCase()
        .includes(value.toLowerCase()),
  });

  return (
    <div style={{ padding: 20 }}>
        <h1 className="excel-tittle">Datos Gail</h1>
      <Select
        style={{ width: 300, marginBottom: 20 }}
        placeholder="Selecciona un GET"
        onChange={handleChange}
      >
        {endpoints.map((e) => (
          <Option key={e.value} value={e.value}>
            {e.label}
          </Option>
        ))}
      </Select>

      <Card bordered style={{ height: "400px", overflow: "hidden" }} bodyStyle={{ padding: 8 }}>
        <Table
          columns={[
            ...columns,
            ...(selectedUrl === "https://api.lula.com/v1/campaigns"
              ? [
                  {
                    title: "Acciones",
                    key: "actions",
                    render: (text, record) => (
                      <Button onClick={() => obtenerContactosDeCampana(record.description, record.id)}>
                        Ver Resultados
                      </Button>
                    ),
                  },
                ]
              : []),
          ]}
          dataSource={data}
          rowKey={(record) => record.id || record.name || JSON.stringify(record)}
          pagination={false}
          scroll={{ x: "max-content", y: 250 }}
          size="small"
        />
      </Card>

 <Modal
  title={null}
  visible={modalVisible}
  onCancel={() => setModalVisible(false)}
  footer={null}
  width={850}
  bodyStyle={{ padding: 32, backgroundColor: "#fafafa", borderRadius: 8 }}
>
  <div style={{ textAlign: "center", marginBottom: 24 }}>
    <Title level={4} style={{ marginBottom: 4 }}>
      Resultados de la campaña
    </Title>
    <Title level={5} type="secondary" style={{ margin: 0 }}>
      {modalTitle}
    </Title>
  </div>

  {chartData.length > 0 ? (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
      <ResultadoGrafico data={chartData} />

      <Button
        type="primary"
        icon={<DownloadOutlined />}
        onClick={exportarExcel}
        style={{ marginTop: 24, backgroundColor: "#1677ff" }}
      >
        Descargar Excel de detalles
      </Button>
    </div>
  ) : (
    <p style={{ textAlign: "center", color: "#999" }}>
      No hay datos de resultados para esta campaña.
    </p>
  )}
</Modal>

    </div>
  );
};

export default Busquedas;
