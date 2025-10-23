import React, { useEffect, useState } from "react";
import { Table, Tag, Typography, Space, Button, message, Badge, Spin } from "antd";
import { ReloadOutlined, ArrowLeftOutlined } from "@ant-design/icons";
import axios from "axios";
import { API_URL_GATEWAY } from "../../config";
import { useNavigate } from "react-router-dom";

const { Title } = Typography;

export default function EmailCargues() {
  const [encabezados, setEncabezados] = useState([]);
  const [encLoading, setEncLoading] = useState(false);

  // cache de detalles por encabezado
  const [detallesByEnc, setDetallesByEnc] = useState({});
  const [loadingDetalle, setLoadingDetalle] = useState({});

  const navigate = useNavigate();

  const fetchEncabezados = async () => {
    try {
      setEncLoading(true);
      const { data } = await axios.get(`${API_URL_GATEWAY}/gateway/correos/encabezados`);
      setEncabezados(data?.data || []);
    } catch (e) {
      console.error(e);
      message.error("No se pudieron cargar los encabezados");
    } finally {
      setEncLoading(false);
    }
  };

  const fetchDetalle = async (idEncabezado) => {
    setLoadingDetalle(prev => ({ ...prev, [idEncabezado]: true }));
    try {
      const { data } = await axios.get(`${API_URL_GATEWAY}/gateway/correos/detalle`, {
        params: { idEncabezado },
      });
      setDetallesByEnc(prev => ({ ...prev, [idEncabezado]: data?.data || [] }));
    } catch (e) {
      console.error(e);
      message.error(`No se pudo cargar el detalle del cargue #${idEncabezado}`);
    } finally {
      setLoadingDetalle(prev => ({ ...prev, [idEncabezado]: false }));
    }
  };

  useEffect(() => { fetchEncabezados(); }, []);

  const encabezadosCols = [
    { title: "Remitente", dataIndex: "descripcion" },
    { title: "Usuario", dataIndex: "idUsuario", width: 120 },
    { title: "Total", dataIndex: "totalRegistros", width: 90, render: (v) => <Badge count={v} /> },
    {
      title: "Estado",
      dataIndex: "estado",
      width: 140,
      render: (x) => {
        const color = x === "FINALIZADO" ? "green" : x === "PAUSADO" ? "orange" : "blue";
        return <Tag color={color}>{x}</Tag>;
      },
    }
  ];

  const detalleCols = [
    { title: "Destinatario", dataIndex: "email_destinatario" },
    { title: "Asunto", dataIndex: "asunto" },
    {
      title: "Estado Envío",
      dataIndex: "estado_envio",
      width: 150,
      render: (x) => {
        const color = x === "ENVIADO" ? "green" : x === "ERROR" ? "red" : "orange";
        return <Tag color={color}>{x}</Tag>;
      },
    },
    { title: "Registro", dataIndex: "fecha_registro", width: 180 },
    { title: "Envío", dataIndex: "fecha_envio", width: 180 },
    { title: "Error", dataIndex: "error_detalle" },
  ];

  return (
    <div style={{ padding: 24, marginTop:70}}>
      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)}>Volver</Button>
        <Title level={3} style={{ margin: 0 }}>Reporte de Correos (lista desplegable)</Title>
      </Space>

      <Table
        columns={encabezadosCols}
        dataSource={encabezados}
        rowKey="idEncabezado"
        loading={encLoading}
        bordered
        size="middle"
        pagination={{ pageSize: 10 }}
        expandable={{
          expandedRowRender: (record) => {
            const id = record.idEncabezado;
            const isLoading = !!loadingDetalle[id];
            const data = detallesByEnc[id];

            if (isLoading) {
              return (
                <div style={{ padding: 16, textAlign: "center" }}>
                  <Spin /> Cargando detalle...
                </div>
              );
            }
            if (!data) {
              // aún no cargado (esto casi no se verá porque cargamos onExpand)
              return <div style={{ padding: 16 }}>Sin datos</div>;
            }
            return (
              <Table
                columns={detalleCols}
                dataSource={data}
                rowKey="idDetalle"
                bordered
                size="small"
                pagination={false}
              />
            );
          },
          onExpand: (expanded, record) => {
            if (expanded) {
              const id = record.idEncabezado;
              // si no tengo cacheado, lo traigo
              if (!detallesByEnc[id]) {
                fetchDetalle(id);
              }
            }
          },
          rowExpandable: () => true,
        }}
      />
    </div>
  );
}
