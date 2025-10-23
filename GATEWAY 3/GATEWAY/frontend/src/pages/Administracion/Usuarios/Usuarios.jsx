import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import {
  Table,
  Button,
  Space,
  Input,
  Tooltip,
  Select,
  Popconfirm,
  Checkbox,
  Modal,
  Form,
  notification
} from "antd";
import message from 'antd/lib/message';
import {
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  CloseOutlined,
  CheckOutlined
} from "@ant-design/icons";
import { API_URL_GATEWAY } from "../../../config";
import "./usuarios.css";

const { Search } = Input;

const ListarUsuarios = () => {
  const [usuarios, setUsuarios] = useState([]);
  const [campanas, setCampanas] = useState([]);
  const [rolesData, setRolesData] = useState({ roles: [] });
  const [areasData, setAreasData] = useState({ areas: [] });
  const [usuariosCampanas, setUsuariosCampanas] = useState([]);
  const [formData, setFormData] = useState({});
  const [modalVisible, setModalVisible] = useState(false);
  const [searchText, setSearchText] = useState("");
  const [isEditMode, setIsEditMode] = useState(false);
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


  const fetchAllData = async () => {
    try {
      const [resUsuarios, resCampanas, resRoles, resAreas, resUsuariosCampanas] = await Promise.all([
        fetch(`${API_URL_GATEWAY}/gateway/usuarios/dar`),
        fetch(`${API_URL_GATEWAY}/gateway/campanas/dar`),
        fetch(`${API_URL_GATEWAY}/gateway/roles/dar`),
        fetch(`${API_URL_GATEWAY}/gateway/areas/dar`),
        fetch(`${API_URL_GATEWAY}/gateway/usuariosCampanas/dar`)
      ]);

      const [dataUsuarios, dataCampanas, dataRoles, dataAreas, dataUsuariosCampanas] = await Promise.all([
        resUsuarios.ok ? resUsuarios.json() : [],
        resCampanas.ok ? resCampanas.json() : [],
        resRoles.ok ? resRoles.json() : { roles: [] },
        resAreas.ok ? resAreas.json() : { areas: [] },
        resUsuariosCampanas.ok ? resUsuariosCampanas.json() : [],
      ]);

      setUsuarios(Array.isArray(dataUsuarios) ? dataUsuarios : []);
      setCampanas(Array.isArray(dataCampanas) ? dataCampanas : []);
      setRolesData(dataRoles);
      setAreasData(dataAreas);
      setUsuariosCampanas(Array.isArray(dataUsuariosCampanas) ? dataUsuariosCampanas : []);

    } catch (error) {
      console.error("Error al cargar datos:", error);
      notification.error({ message: "Error al cargar los datos" });
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  const handleAdd = () => {
    setFormData({
      nombre: "",
      username: "",
      correo: "",
      password: "",
      confirmPassword: "",
      idRol: null,
      idArea: null,
      campanas: []
    });
    setIsEditMode(false);
    setModalVisible(true);
  };

  const handleEdit = (record) => {
    setFormData({
      idUsuarioApp: record.idUsuarioApp,
      nombre: record.nombre,
      correo: record.correo,
      username: record.username,
      password: record.password,
      confirmPassword: record.password,
      idRol: record.idRol,
      idArea: record.idArea,
      campanas: usuariosCampanas
        .filter(c => c.idUsuarioApp === record.idUsuarioApp)
        .map(c => c.idCampana)
    });
    setIsEditMode(true);
    setModalVisible(true);
  };


  const handleSaveNewUser = async () => {
    try {
      // Validaciones comunes
      if (
        !formData.nombre ||
        !formData.correo ||
        !formData.username ||
        !formData.idRol ||
        !formData.idArea
      ) {
        notification.warning({ message: "Por favor completa todos los campos obligatorios..." });
        return;
      }

      // Validaciones de contraseña solo en modo creación
      if (!isEditMode) {
        if (!formData.password || !formData.confirmPassword) {
          message.error("Debes ingresar la contraseña y confirmarla.");
          return;
        }
        if (formData.password !== formData.confirmPassword) {
          message.error("Las contraseñas no coinciden.");
          return;
        }
        const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
        if (!passwordRegex.test(formData.password)) {
          message.error("La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número.");
          return;
        }

      }

      // 🆕 MODO CREACIÓN
      const responseUser = await fetch(`${API_URL_GATEWAY}/gateway/usuarios/crear`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nombre: formData.nombre,
          username: formData.username,
          correo: formData.correo,
          password: formData.password,
          idRol: formData.idRol,
          idArea: formData.idArea,
          cargo: "",
          activo: 1,
          campanas: formData.campanas
        })
      });

      if (!responseUser.ok) throw new Error("Error al crear usuario");
      message.success("Usuario creado exitosamente");


      setModalVisible(false);
      fetchAllData();

    } catch (error) {
      console.error("Error guardando usuario:", error);
      message.error(`Error: ${error.message}`);
    }
  };

  const handleSaveEditUser = async () => {
    try {
      if (!formData.nombre || !formData.username || !formData.idRol || !formData.idArea) {
        notification.warning({ message: "Por favor completa todos los campos obligatorios..." });
        return;
      }
      if (formData.password || formData.confirmPassword) {
        if (formData.password !== formData.confirmPassword) {
          message.error("Las contraseñas no coinciden.");
          return;
        }
      
        const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
        if (!passwordRegex.test(formData.password)) {
          message.error("La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número.");
          return;
        }
      }      
      
      const response = await fetch(`${API_URL_GATEWAY}/gateway/usuarios/editar`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          idUsuarioApp: formData.idUsuarioApp, // 🔥 sin esto no puede editar
          nombre: formData.nombre,
          username: formData.username,
          correo: formData.correo, // aunque esté deshabilitado, debes enviarlo
          cargo: "", // opcional, si no lo usas déjalo como string vacío
          idRol: formData.idRol,
          idArea: formData.idArea,
          campanas: formData.campanas,
          ...(formData.password && { password: formData.password }) // ✅ ESTA LÍNEA

        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Error desconocido");
      }

      message.success("Usuario actualizado correctamente");
      setModalVisible(false);
      fetchAllData();
    } catch (error) {
      console.error("Error actualizando usuario:", error);
      message.error("Error al actualizar usuario: " + error.message);
    }
  };


  const handleActivateToggle = async (record) => {
    try {
      const endpoint = record.activo ? "eliminar" : "activar";
      await fetch(`${API_URL_GATEWAY}/gateway/usuarios/${endpoint}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idUsuarioApp: record.idUsuarioApp })
      });
      notification.success({ message: `Usuario ${record.activo ? "desactivado" : "activado"} exitosamente` });
      fetchAllData();
    } catch (error) {
      console.error("Error actualizando usuario:", error);
      notification.error({ message: "Error al actualizar estado" });
    }
  };

  const expandedRowRender = (record) => (
    <div style={{ padding: "0 20px", fontSize: "12px", background: "#fafafa" }}>
      <p><b>Username:</b> {record.username}</p>
      <p><b>Correo:</b> {record.correo || "No especificado"}</p>
      <p><b>Contraseña:</b> {record.password || "No especificada"}</p>
    </div>
  );

  const columns = [
    {
      title: "Nombre",
      dataIndex: "nombre",
      key: "nombre"
    },
    {
      title: "Rol",
      key: "rol",
      render: (_, record) => rolesData.roles.find(r => r.idRol === record.idRol)?.rol || ""
    },
    {
      title: "Área",
      key: "area",
      render: (_, record) => areasData.areas.find(a => a.idArea === record.idArea)?.nombreArea || ""
    },
    {
      title: "Campañas",
      key: "campanas",
      render: (_, record) => {
        const userCampanas = usuariosCampanas
          .filter(uc => uc.idUsuarioApp === record.idUsuarioApp)
          .map(uc => uc.idCampana);

        const nombresCampanas = campanas
          .filter(c => userCampanas.includes(c.idCampana))
          .map(c => c.descripcionCampana);

        return nombresCampanas.length > 0
          ? nombresCampanas.join(', ')
          : <span style={{ color: 'gray' }}>Ninguna</span>;
      }
    }
    ,
    {
      title: "Estado",
      key: "activo",
      render: (_, record) => (
        <span style={{ color: record.activo ? "green" : "red" }}>
          {record.activo ? "Activo" : "Inactivo"}
        </span>
      )
    },
    {
      title: "Acciones",
      key: "acciones",
      render: (_, record) => (
        <Space>
          {/* Botón Editar */}
          {permisos.editar && (
            <Tooltip title="Editar usuario">
              <Button
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
              />
            </Tooltip>
          )}


          {/* Botón Activar/Desactivar */}
          {permisos.eliminar && (
            <Tooltip title={record.activo ? "Desactivar usuario" : "Activar usuario"}>
              <Popconfirm
                title={`¿Seguro que deseas ${record.activo ? "desactivar" : "activar"} este usuario?`}
                onConfirm={() => handleActivateToggle(record)}
              >
                <Button
                  icon={record.activo ? <CloseOutlined /> : <CheckOutlined />}
                  danger={record.activo}
                />
              </Popconfirm>
            </Tooltip>
          )}

        </Space>
      )
    }

  ];

  const filteredUsuarios = usuarios.filter(user =>
    (user.nombre?.toLowerCase() ?? '').includes(searchText.toLowerCase()) ||
    (user.username?.toLowerCase() ?? '').includes(searchText.toLowerCase()) ||
    (user.correo?.toLowerCase() ?? '').includes(searchText.toLowerCase())
  );

  const handleEmailChange = (e) => { // Mueve esta función aquí
    const { value } = e.target;
    setFormData({ ...formData, correo: value });
    const atIndex = value.indexOf('@');
    if (atIndex > 0 && !formData.username) {
      setFormData({ ...formData, correo: value, username: value.substring(0, atIndex) });
    }
  };

  return (
    <div className="usuarios-container">
      <div className="usuarios-main-card">
        <div className="usuarios-header">
          <h1 className="usuarios-title">Gestión de Usuarios</h1>
          <p className="usuarios-description">Administra los Usuarios en el sistema.</p>
        </div>
        <div className="usuarios-actions">
          <div className="usuarios-button-group">
            <div className="usuarios-search-container">
              <Search
                className="usuarios-search"
                placeholder="Buscar usuarios..."
                allowClear
                onChange={(e) => setSearchText(e.target.value)}
                style={{ width: 300 }}
              />
            </div>
            {permisos.crear && (
              <Button className="usuarios-btn-primary" icon={<PlusOutlined />} onClick={handleAdd}>
                Nuevo Usuario
              </Button>
            )}
          </div>
        </div>
        <Table
          className="usuarios-table"
          columns={columns}
          dataSource={usuarios.filter(user =>
            user.nombre?.toLowerCase().includes(searchText.toLowerCase()) ||
            user.username?.toLowerCase().includes(searchText.toLowerCase()) ||
            user.correo?.toLowerCase().includes(searchText.toLowerCase())
          )}
          rowKey="idUsuarioApp"
          expandable={{ expandedRowRender }}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 10, y: 300 }}
        />
      </div>
      <Modal
        className="usuarios-modal"
        title={<h3 className="usuarios-title" style={{ fontSize: '1.2em', fontWeight: 'bold', margin: 0 }}>{isEditMode ? 'Editar Usuario' : 'Crear Nuevo Usuario'}</h3>}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={isEditMode ? handleSaveEditUser : handleSaveNewUser}
        okText="Guardar"
        cancelText="Cancelar"
        width={500}
        destroyOnClose
      >
        <Form layout="vertical">
          <Form.Item label="Nombre" style={{ marginBottom: 8 }}>
            <Input
              size="middle"
              style={{ height: '32px' }}
              value={formData.nombre}
              onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
            />
          </Form.Item>
          <Form.Item label="Correo" style={{ marginBottom: 8 }}>
            <Input
              size="middle"
              style={{ height: '32px' }}
              value={formData.correo}
              disabled={isEditMode}
              onChange={handleEmailChange}
            />
          </Form.Item>
          <Form.Item label="Username" style={{ marginBottom: 8 }}>
            <Input
              size="middle"
              style={{ height: '32px' }}
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            />
          </Form.Item>
          <Form.Item label="Contraseña" style={{ marginBottom: 8 }}>
            <Space direction="horizontal" size="small" style={{ display: "flex" }}>
              <Input.Password
                size="middle"
                style={{ height: '32px', width: "100%" }}
                placeholder="Contraseña"
                disabled={false}
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              />
              <Input.Password
                size="middle"
                style={{ height: '32px', width: "100%" }}
                placeholder="Confirmar"
                disabled={false}
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              />
            </Space>
          </Form.Item>
          <Form.Item label="Rol" style={{ marginBottom: 8 }}>
            <Select
              size="middle"
              style={{ height: '32px' }}
              value={formData.idRol}
              onChange={(value) => setFormData({ ...formData, idRol: value })}
              options={rolesData.roles.map(r => ({ label: r.rol, value: r.idRol }))}
            />
          </Form.Item>
          <Form.Item label="Área" style={{ marginBottom: 8 }}>
            <Select
              size="middle"
              style={{ height: '32px' }}
              value={formData.idArea}
              onChange={(value) => setFormData({ ...formData, idArea: value })}
              options={areasData.areas.map(a => ({ label: a.nombreArea, value: a.idArea }))}
            />
          </Form.Item>
          <Form.Item label="Campañas" style={{ marginBottom: 8 }}>
            <Select
              mode="multiple"
              size="middle"
              style={{ width: '100%' }}
              value={formData.campanas}
              onChange={(value) => setFormData({ ...formData, campanas: value })}
              options={campanas.map(c => ({ label: c.descripcionCampana, value: c.idCampana }))}
              placeholder="Selecciona campañas"
              allowClear
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ListarUsuarios;