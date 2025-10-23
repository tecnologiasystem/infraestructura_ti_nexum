import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import {
  Table,
  Button,
  Space,
  Input,
  Popconfirm,
  notification,
  Tooltip
} from "antd";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SaveOutlined,
  CloseOutlined
} from "@ant-design/icons";
import { API_URL_GATEWAY } from "../../../config";
import "./Areas.css";

const Areas = () => {
  const [data, setData] = useState([]);
  const [editingRecord, setEditingRecord] = useState(null);
  const [editingNombre, setEditingNombre] = useState("");
  const [newRecord, setNewRecord] = useState(null);
  const [newNombre, setNewNombre] = useState("");
  const [searchText, setSearchText] = useState("");
  const [loading, setLoading] = useState(false);
  const [permisos, setPermisos] = useState({});

  const location = useLocation();

  useEffect(() => {
    const idRol = localStorage.getItem("idRol");
    if (!idRol) return;

    const currentPath = location.pathname;

    fetch(`${API_URL_GATEWAY}/gateway/porRol?idRol=${idRol}`)
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          const permisoRuta = data.find(p => p.ruta === currentPath);
          if (permisoRuta) {
            setPermisos({
              crear: permisoRuta.permisoCrear,
              editar: permisoRuta.permisoEditar,
              eliminar: permisoRuta.permisoEliminar,
              ver: permisoRuta.permisoVer
            });
          }
        }
      })
      .catch(err => {
        console.error("❌ Error cargando permisos desde gateway:", err);
      });
  }, []);

  const fetchAreas = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL_GATEWAY}/gateway/areas/dar`);
      const areas = await response.json();
      if (Array.isArray(areas.areas)) {
        setData(areas.areas);
      } else if (Array.isArray(areas)) {
        setData(areas);
      } else {
        console.error('No se recibieron áreas correctamente:', areas);
      }
    } catch (error) {
      console.error('Error al obtener áreas:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAreas();
  }, []);

  const handleAdd = () => {
    setNewRecord({ key: Date.now(), nombreArea: "", activo: 1 });
    setNewNombre("");
    setEditingRecord(null);
  };

  const handleEdit = (record) => {
    setEditingRecord(record);
    setEditingNombre(record.nombreArea);
    setNewRecord(null);
  };

  const handleSave = async () => {
    try {
      if (newRecord) {
        await fetch(`${API_URL_GATEWAY}/gateway/areas/crear`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ nombreArea: newNombre }),
        });
        notification.success({ message: "Área creada exitosamente" });
      } else if (editingRecord) {
        await fetch(`${API_URL_GATEWAY}/gateway/areas/editar`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ idArea: editingRecord.idArea, nombreArea: editingNombre }),
        });
        notification.success({ message: "Área actualizada exitosamente" });
      }
      setEditingRecord(null);
      setEditingNombre("");
      setNewRecord(null);
      setNewNombre("");
      fetchAreas();
    } catch (error) {
      console.error("Error al guardar:", error);
      notification.error({ message: "Error al guardar área" });
    }
  };

  const handleCancel = () => {
    setEditingRecord(null);
    setEditingNombre("");
    setNewRecord(null);
    setNewNombre("");
  };

  const handleDelete = async (idArea) => {
    try {
      await fetch(`${API_URL_GATEWAY}/gateway/areas/eliminar`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idArea }),
      });
      notification.success({ message: "Área desactivada exitosamente" });
      fetchAreas();
    } catch (error) {
      console.error("Error al eliminar:", error);
      notification.error({ message: "Error al desactivar área" });
    }
  };

  const handleActivate = async (idArea) => {
    try {
      await fetch(`${API_URL_GATEWAY}/gateway/areas/activar`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idArea }),
      });
      notification.success({ message: "Área activada exitosamente" });
      fetchAreas();
    } catch (error) {
      console.error("Error al activar:", error);
      notification.error({ message: "Error al activar área" });
    }
  };

  const filteredData = (newRecord ? [newRecord, ...data] : data).filter((item) =>
    item.nombreArea?.toLowerCase().includes(searchText.toLowerCase())
  );

  const columns = [
    {
      title: "Nombre Área",
      dataIndex: "nombreArea",
      key: "nombreArea",
      sorter: (a, b) => a.nombreArea.localeCompare(b.nombreArea),
      render: (_, record) => {
        const isEditing = editingRecord && editingRecord.idArea === record.idArea;
        const isNew = newRecord && record.key === newRecord.key;

        if (isEditing) {
          return (
            <Input
              value={editingNombre}
              onChange={(e) => setEditingNombre(e.target.value)}
            />
          );
        } else if (isNew) {
          return (
            <Input
              value={newNombre}
              onChange={(e) => setNewNombre(e.target.value)}
            />
          );
        } else {
          return (
            <span style={{ opacity: record.activo ? 1 : 0.5 }}>
              {record.nombreArea}
            </span>
          );
        }
      },
    },
    {
      title: "Acciones",
      key: "acciones",
      width: 180,
      render: (_, record) => {
        const isEditing = editingRecord && editingRecord.idArea === record.idArea;
        const isNew = newRecord && record.key === newRecord.key;

        if (!record.activo && permisos.eliminar) {
          return (
            <Space>
              <Popconfirm
                title="¿Seguro que quieres activar esta área?"
                onConfirm={() => handleActivate(record.idArea)}
              >
                <Button type="primary">Activar</Button>
              </Popconfirm>
            </Space>
          );
        }

        return (isEditing || isNew) ? (
          <Space>
            {permisos.crear || permisos.editar ? (
              <>
                <Tooltip title="Guardar cambios">
                  <Button type="primary" shape="circle" icon={<SaveOutlined />} onClick={handleSave} />
                </Tooltip>
                <Tooltip title="Cancelar">
                  <Button danger shape="circle" icon={<CloseOutlined />} onClick={handleCancel} />
                </Tooltip>
              </>
            ) : null}
          </Space>
        ) : (
          <Space>
            {permisos.editar && (
              <Tooltip title="Editar área">
                <Button shape="circle" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
              </Tooltip>
            )}
            {permisos.eliminar && (
              <Popconfirm
                title="¿Seguro que quieres desactivar esta área?"
                onConfirm={() => handleDelete(record.idArea)}
              >
                <Tooltip title="Desactivar área">
                  <Button danger shape="circle" icon={<DeleteOutlined />} />
                </Tooltip>
              </Popconfirm>
            )}
          </Space>
        );
      },
    },
  ];

  return (
    <div className="areas-container">
      <h1 className="areas-title">Gestión de Áreas</h1>
      <p className="areas-description">Administra las áreas organizacionales de tu empresa.</p>

      <div className="areas-toolbar">
        <Input.Search
          placeholder="Buscar área..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ width: 250 }}
          allowClear
        />
        {permisos.crear && (
          <Button
            type="primary"
            shape="circle"
            icon={<PlusOutlined />}
            onClick={handleAdd}
            title="Agregar Área"
            style={{ backgroundColor: "#F39200", borderColor: "#F39200" }}
          />
        )}
      </div>

      <Table
        columns={columns}
        dataSource={filteredData}
        rowKey={(record) => record.idArea || record.key}
        pagination={{ pageSize: 5 }}
        bordered
        loading={loading}
      />
    </div>
  );
};

export default Areas;
