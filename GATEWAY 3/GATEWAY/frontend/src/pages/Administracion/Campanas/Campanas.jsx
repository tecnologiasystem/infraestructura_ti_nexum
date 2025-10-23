import React, { useState, useEffect } from "react";
import { Table, Button, Space, Input, Modal, Tooltip, notification } from "antd";
import { PlusOutlined, DeleteOutlined, EditOutlined } from "@ant-design/icons";
import { API_URL_GATEWAY } from "../../../config";
import "./Campanas.css";

const Campanas = () => {
  const [data, setData] = useState([]);
  const [newDescripcion, setNewDescripcion] = useState("");
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedCampaignId, setSelectedCampaignId] = useState(null);

  useEffect(() => {
    fetchCampanas();
  }, []);

const fetchCampanas = async () => {
  try {
    const response = await fetch(`${API_URL_GATEWAY}/gateway/campanas/dar`);
    const all = await response.json();
    const activas = (Array.isArray(all) ? all : []).filter(c => Number(c.estado) === 1);
    setData(activas);
  } catch (error) {
    console.error("Error al obtener campañas:", error);
  }
};


  const handleAdd = () => {
    setNewDescripcion("");
    setSelectedCampaignId(null);
    setModalVisible(true);
  };

  const handleEdit = (record) => {
    setSelectedCampaignId(record.idCampana);
    setNewDescripcion(record.descripcionCampana);
    setModalVisible(true);
  };

  const handleDelete = async (idCampana) => {
    try {
      const response = await fetch(`${API_URL_GATEWAY}/gateway/campanas/eliminar`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idCampana }),
      });

      if (response.ok) {
        notification.success({ message: "Campaña eliminada exitosamente" });
        fetchCampanas();
      } else {
        throw new Error("Error al eliminar la campaña");
      }
    } catch (error) {
      console.error("Error al eliminar campaña:", error);
      notification.error({ message: "Error al eliminar campaña" });
    }
  };

  const handleSave = async () => {
    try {
      if (!newDescripcion) {
        notification.error({ message: "La descripción no puede estar vacía." });
        return;
      }

      const payload = {
        descripcionCampana: newDescripcion,
        ...(selectedCampaignId && { idCampana: selectedCampaignId }),
      };

      const url = selectedCampaignId
        ? `${API_URL_GATEWAY}/gateway/campanas/editar`
        : `${API_URL_GATEWAY}/gateway/campanas/crear`;

      const method = selectedCampaignId ? "PUT" : "POST";

      const response = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        notification.success({
          message: selectedCampaignId
            ? "Campaña actualizada exitosamente"
            : "Campaña creada exitosamente",
        });
        setModalVisible(false);
        fetchCampanas();
      } else {
        throw new Error("Error al guardar la campaña");
      }
    } catch (error) {
      console.error("Error al guardar campaña:", error);
      notification.error({ message: "No se pudo guardar la campaña" });
    }
  };

  const handleCancel = () => {
    setModalVisible(false);
  };

  const columns = [
    {
      title: "Descripción Campaña",
      dataIndex: "descripcionCampana",
      key: "descripcionCampana",
    },
    {
      title: "Acciones",
      key: "acciones",
      render: (_, record) => (
        <Space>
          <Tooltip title="Editar campaña">
            <Button shape="circle" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          </Tooltip>
          <Tooltip title="Eliminar campaña">
            <Button
              danger
              shape="circle"
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record.idCampana)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="campanas-container">
      <h1 className="campanas-title">Gestión de Campañas</h1>
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          Crear Campaña
        </Button>
      </Space>

      <Table
        columns={columns}
        dataSource={data}
        rowKey="idCampana"
        pagination={{ pageSize: 5 }}
        bordered
      />

      <Modal
        title={selectedCampaignId ? "Editar Campaña" : "Crear Campaña"}
        visible={modalVisible}
        onOk={handleSave}
        onCancel={handleCancel}
        okText="Guardar"
        cancelText="Cancelar"
      >
        <label>Descripción:</label>
        <Input
          value={newDescripcion}
          onChange={(e) => setNewDescripcion(e.target.value)}
          placeholder="Nombre de la campaña"
        />
      </Modal>
    </div>
  );
};

export default Campanas;
