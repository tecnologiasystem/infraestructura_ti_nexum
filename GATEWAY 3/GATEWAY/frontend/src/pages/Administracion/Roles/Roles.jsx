import React, { useState, useEffect } from "react";
import {
  Table,
  Button,
  Space,
  Input,
  Popconfirm,
  notification,
  Tooltip,
  Modal,
  Checkbox,
} from "antd";
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SaveOutlined,
  CloseOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { API_URL_GATEWAY } from "../../../config";
import "./Roles.css";

const Roles = () => {
  const [data, setData] = useState([]);
  const [editingRecord, setEditingRecord] = useState(null);
  const [editingRol, setEditingRol] = useState("");
  const [newRecord, setNewRecord] = useState(null);
  const [newRol, setNewRol] = useState("");
  const [searchText, setSearchText] = useState("");
  const [loading, setLoading] = useState(false);

  const [visiblePermisosModal, setVisiblePermisosModal] = useState(false);
  const [permisosRol, setPermisosRol] = useState([]);
  const [rolSeleccionado, setRolSeleccionado] = useState(null);
  const [editingPermiso, setEditingPermiso] = useState(null);

  const [permisoRuta, setPermisoRuta] = useState("");
  const [permisoDescripcion, setPermisoDescripcion] = useState("");
  const [permisoDetalle, setPermisoDetalle] = useState("");
  const [permisoCrear, setPermisoCrear] = useState(false);
  const [permisoEditar, setPermisoEditar] = useState(false);
  const [permisoEliminar, setPermisoEliminar] = useState(false);
  const [permisoVer, setPermisoVer] = useState(false);
  const fetchRoles = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_URL_GATEWAY}/gateway/roles/dar`);
      const json = await res.json();
      setData(Array.isArray(json.roles) ? json.roles : []);
    } catch (error) {
      console.error("Error al obtener roles:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPermisosPorRol = async (idRol) => {
    try {
      const res = await fetch(`${API_URL_GATEWAY}/gateway/porRol?idRol=${idRol}`);
      const permisos = await res.json();
      setPermisosRol(Array.isArray(permisos) ? permisos : []);
    } catch (error) {
      console.error("Error al obtener permisos por rol:", error);
    }
  };

  useEffect(() => {
    fetchRoles();
  }, []);

  const handleAdd = () => {
    setNewRecord({ key: Date.now(), rol: "", activo: 1 });
    setNewRol("");
    setEditingRecord(null);
  };

  const handleEdit = (record) => {
    setEditingRecord(record);
    setEditingRol(record.rol);
    setNewRecord(null);
  };

  const handleSave = async () => {
    const payload = {
      rol: editingRecord ? editingRol : newRol,
      ...(editingRecord && { idRol: editingRecord.idRol }),
    };
    const url = editingRecord
      ? `${API_URL_GATEWAY}/gateway/roles/editar`
      : `${API_URL_GATEWAY}/gateway/roles/crear`;
    const method = editingRecord ? "PUT" : "POST";

    try {
      await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      notification.success({ message: `Rol ${editingRecord ? "editado" : "creado"} correctamente` });
      handleCancel();
      fetchRoles();
    } catch (error) {
      console.error("Error guardando rol:", error);
      notification.error({ message: "Error al guardar rol" });
    }
  };

  const handleCancel = () => {
    setEditingRecord(null);
    setEditingRol("");
    setNewRecord(null);
    setNewRol("");
  };
  const handleDelete = async (idRol) => {
    try {
      await fetch(`${API_URL_GATEWAY}/gateway/roles/eliminar`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idRol }),
      });
      notification.success({ message: "Rol desactivado correctamente" });
      fetchRoles();
    } catch (error) {
      console.error("Error al desactivar rol:", error);
      notification.error({ message: "Error al desactivar rol" });
    }
  };

  const handleActivate = async (idRol) => {
    try {
      await fetch(`${API_URL_GATEWAY}/gateway/roles/activar`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idRol }),
      });
      notification.success({ message: "Rol activado correctamente" });
      fetchRoles();
    } catch (error) {
      console.error("Error al activar rol:", error);
      notification.error({ message: "Error al activar rol" });
    }
  };

  const openPermisosModal = async (record) => {
    setRolSeleccionado(record);
    await fetchPermisosPorRol(record.idRol);
    setVisiblePermisosModal(true);
  };

  const handleAddPermiso = () => {
    const nuevo = {
      id: null,
      ruta: "",
      descripcion: "",
      detalle: "",
      permisoCrear: false,
      permisoEditar: false,
      permisoEliminar: false,
      permisoVer: false,
      esNuevo: true, // 🔑 clave para detectar en la tabla
    };
    setPermisosRol((prev) => [nuevo, ...prev]);
    handleEditPermiso(nuevo);
  };

  const handleEditPermiso = (permiso) => {
    setEditingPermiso(permiso);
    setPermisoRuta(permiso.ruta);
    setPermisoDescripcion(permiso.descripcion);
    setPermisoDetalle(permiso.detalle || "");
    setPermisoCrear(permiso.permisoCrear ?? false);
    setPermisoEditar(permiso.permisoEditar ?? false);
    setPermisoEliminar(permiso.permisoEliminar ?? false);
    setPermisoVer(permiso.permisoVer ?? false);
  };

  const handleCancelPermiso = () => {
    setEditingPermiso(null);
    setPermisoRuta("");
    setPermisoDescripcion("");
    setPermisoDetalle("");
    setPermisoCrear(false);
    setPermisoEditar(false);
    setPermisoEliminar(false);
    setPermisoVer(false);
  };
  const handleSavePermiso = async () => {
    if (!permisoRuta || !permisoDescripcion) {
      return notification.warning({ message: "Ruta y descripción son requeridas" });
    }
  
    const isNuevo = !editingPermiso || !editingPermiso.id || editingPermiso.id === "nuevo";
  
    const payload = {
      ruta: permisoRuta,
      descripcion: permisoDescripcion,
      detalle: permisoDetalle,
      permisoCrear,
      permisoEditar,
      permisoEliminar,
      permisoVer,
      idRol: rolSeleccionado.idRol,
      ...(isNuevo ? {} : { id: editingPermiso.id }),
    };
  
    try {
      const res = await fetch(
        isNuevo
          ? `${API_URL_GATEWAY}/gateway/`
          : `${API_URL_GATEWAY}/gateway/${editingPermiso.id}`,
        {
          method: isNuevo ? "POST" : "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );
      
  
      if (!res.ok) throw new Error("Error HTTP");
  
      notification.success({ message: `Permiso ${isNuevo ? "creado" : "editado"} correctamente` });
      await fetchPermisosPorRol(rolSeleccionado.idRol);
      handleCancelPermiso();
    } catch (err) {
      console.error("Error al guardar permiso:", err);
      notification.error({ message: "Error al guardar permiso" });
    }
  };
  
  const handleDeletePermiso = async (permiso) => {
    try {
      await fetch(`${API_URL_GATEWAY}/gateway/${permiso.id}`, {
        method: "DELETE",
      });
      notification.success({ message: "Permiso eliminado correctamente" });
      await fetchPermisosPorRol(rolSeleccionado.idRol);
    } catch (err) {
      console.error("Error al eliminar permiso:", err);
      notification.error({ message: "Error al eliminar permiso" });
    }
  };

  const filteredData = (newRecord ? [newRecord, ...data] : data).filter((item) =>
    item.rol?.toLowerCase().includes(searchText.toLowerCase())
  );

  const columns = [
    {
      title: "Rol",
      dataIndex: "rol",
      key: "rol",
      sorter: (a, b) => a.rol.localeCompare(b.rol),
      render: (_, record) => {
        const isEditing = editingRecord && editingRecord.idRol === record.idRol;
        const isNew = newRecord && record.key === newRecord.key;

        if (isEditing) {
          return <Input value={editingRol} onChange={(e) => setEditingRol(e.target.value)} />;
        } else if (isNew) {
          return <Input value={newRol} onChange={(e) => setNewRol(e.target.value)} />;
        } else {
          return <span style={{ opacity: record.activo ? 1 : 0.5 }}>{record.rol}</span>;
        }
      },
    },
    {
      title: "Permisos",
      key: "permisos",
      render: (_, record) => (
        <Tooltip title="Gestionar permisos">
          <Button shape="primary" icon={<SettingOutlined />} onClick={() => openPermisosModal(record)}>Ver Permisos</Button>
        </Tooltip>
      ),
    },
    {
      title: "Acciones",
      key: "acciones",
      render: (_, record) => {
        const isEditing = editingRecord && editingRecord.idRol === record.idRol;
        const isNew = newRecord && record.key === newRecord.key;

        if (record.activo === 0) {
          return (
            <Popconfirm
              title="¿Seguro que quieres activar este rol?"
              onConfirm={() => handleActivate(record.idRol)}
              okText="Sí"
              cancelText="No"
            >
              <Button type="primary">Activar</Button>
            </Popconfirm>
          );
        }

        return isEditing || isNew ? (
          <Space>
            <Button type="primary" shape="circle" icon={<SaveOutlined />} onClick={handleSave} />
            <Button danger shape="circle" icon={<CloseOutlined />} onClick={handleCancel} />
          </Space>
        ) : (
          <Space>
            <Button shape="circle" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
            <Popconfirm
              title="¿Seguro que quieres desactivar este rol?"
              onConfirm={() => handleDelete(record.idRol)}
              okText="Sí"
              cancelText="No"
            >
              <Button danger shape="circle" icon={<DeleteOutlined />} />
            </Popconfirm>
          </Space>
        );
      },
    },
  ];
  const renderPermisosModal = () => (
    <Modal
      title={`Permisos del rol: ${rolSeleccionado?.rol}`}
      open={visiblePermisosModal}
      onCancel={() => {
        setVisiblePermisosModal(false);
        handleCancelPermiso();
      }}
      footer={null}
      width={1000}
    >
      <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between" }}>
        <Button
          icon={<PlusOutlined />}
          onClick={handleAddPermiso}
          type="primary"
          style={{ backgroundColor: "#0050b3", borderColor: "#0050b3", color: "#fff" }}
        >
          Agregar Permiso
        </Button>
      </div>
  
      <Table
        dataSource={permisosRol}
        rowKey={(record) => record.id || record.ruta}
        pagination={false}
        bordered
        scroll={{ y: 300 }}
        columns={[
          {
            title: "Ruta",
            dataIndex: "ruta",
            key: "ruta",
            render: (_, record) =>
              editingPermiso === record
                ? <Input value={permisoRuta} onChange={(e) => setPermisoRuta(e.target.value)} />
                : <span>{record.ruta}</span>
          },
          {
            title: "Descripción",
            dataIndex: "descripcion",
            key: "descripcion",
            render: (_, record) =>
              editingPermiso === record
                ? <Input value={permisoDescripcion} onChange={(e) => setPermisoDescripcion(e.target.value)} />
                : <span>{record.descripcion}</span>
          },
          {
            title: "Detalle",
            dataIndex: "detalle",
            key: "detalle",
            render: (_, record) =>
              editingPermiso === record
                ? <Input value={permisoDetalle} onChange={(e) => setPermisoDetalle(e.target.value)} />
                : <span>{record.detalle || <i style={{ color: "#ccc" }}>Sin detalle</i>}</span>
          },
          {
            title: "Permisos",
            children: [
              {
                title: "Ver",
                dataIndex: "permisoVer",
                key: "permisoVer",
                render: (_, record) =>
                  editingPermiso === record
                    ? <Checkbox checked={permisoVer} onChange={(e) => setPermisoVer(e.target.checked)} />
                    : <Checkbox checked={record.permisoVer} disabled />
              },
              {
                title: "Crear",
                dataIndex: "permisoCrear",
                key: "permisoCrear",
                render: (_, record) =>
                  editingPermiso === record
                    ? <Checkbox checked={permisoCrear} onChange={(e) => setPermisoCrear(e.target.checked)} />
                    : <Checkbox checked={record.permisoCrear} disabled />
              },
              {
                title: "Editar",
                dataIndex: "permisoEditar",
                key: "permisoEditar",
                render: (_, record) =>
                  editingPermiso === record
                    ? <Checkbox checked={permisoEditar} onChange={(e) => setPermisoEditar(e.target.checked)} />
                    : <Checkbox checked={record.permisoEditar} disabled />
              },
              {
                title: "Eliminar",
                dataIndex: "permisoEliminar",
                key: "permisoEliminar",
                render: (_, record) =>
                  editingPermiso === record
                    ? <Checkbox checked={permisoEliminar} onChange={(e) => setPermisoEliminar(e.target.checked)} />
                    : <Checkbox checked={record.permisoEliminar} disabled />
              },
            ]
          },
          {
            title: "Acciones",
            key: "acciones",
            width: 150,
            render: (_, record) => {
              const isEditing = editingPermiso === record;
              return isEditing ? (
                <Space>
                  <Button
                    shape="circle"
                    icon={<SaveOutlined />}
                    onClick={handleSavePermiso}
                    style={{ backgroundColor: "#0050b3", borderColor: "#0050b3", color: "#fff" }}
                  />
                  <Button
                    shape="circle"
                    icon={<CloseOutlined />}
                    onClick={handleCancelPermiso}
                    style={{ backgroundColor: "#a8071a", borderColor: "#a8071a", color: "#fff" }}
                  />
                </Space>
              ) : (
                <Space>
                  <Button
                    shape="circle"
                    icon={<EditOutlined />}
                    onClick={() => handleEditPermiso(record)}
                    style={{ backgroundColor: "#0050b3", borderColor: "#0050b3", color: "#fff" }}
                  />
                  <Popconfirm
                    title="¿Eliminar este permiso?"
                    onConfirm={() => handleDeletePermiso(record)}
                  >
                    <Button
                      shape="circle"
                      icon={<DeleteOutlined />}
                      style={{ backgroundColor: "#a8071a", borderColor: "#a8071a", color: "#fff" }}
                    />
                  </Popconfirm>
                </Space>
              );
            }
          }
        ]}
      />
    </Modal>
  );
  

  return (
    <div className="roles-container">
      <h1 className="roles-title">Gestión de Roles</h1>
      <p className="roles-description">Administra los roles de acceso de los usuarios en el sistema.</p>

      <div className="roles-toolbar">
        <Input.Search
          placeholder="Buscar rol..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          style={{ width: 250 }}
          allowClear
        />
        <Button
          type="primary"
          shape="circle"
          icon={<PlusOutlined />}
          onClick={handleAdd}
          title="Agregar Rol"
          style={{ backgroundColor: "#F39200", borderColor: "#F39200" }}
        />
      </div>

      <Table
        columns={columns}
        dataSource={filteredData}
        rowKey={(record) => record.idRol || record.key}
        pagination={{ pageSize: 5 }}
        bordered
        loading={loading}
      />

      {renderPermisosModal()}
    </div>
  );
};

export default Roles;
