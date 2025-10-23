import React, { useState, useEffect } from "react";
import { Layout, Menu, Input, Modal, Button } from "antd";
import { Link, useLocation } from "react-router-dom";
import * as AntIcons from "@ant-design/icons";
import logo from "../assets/img/logo2.png";
import menuItems from "../config/menuItems";
import "./sidebar.css";
import { Base64 } from 'js-base64';
import { API_URL_LOGIN, API_GATEWAY_URL } from '../config/rutas';


const { Sider } = Layout;
const { Search } = Input;

const Sidebar = ({ collapsed, setCollapsed }) => {
  const [searchText, setSearchText] = useState("");
  const [username, setUsername] = useState(null);
  const [rolename, setRolename] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [permisosData, setPermisosData] = useState([]);

  const location = useLocation();

  useEffect(() => {
    const fetchUserData = async () => {
      const searchParams = new URLSearchParams(window.location.search);
      const encodedData = searchParams.get('data');

      if (encodedData) {
        const decoded = Base64.decode(encodedData);
        const parsedUserData = JSON.parse(decoded);
        try {
          const response = await fetch(`${API_GATEWAY_URL}/gateway/usuarios/darConID?idUsuario=${parsedUserData.idUsuario}`);
          const usuario = await response.json();
          const data = usuario[0];

          localStorage.setItem("idUsuario", data.idUsuarioApp);
          localStorage.setItem("nombre", data.nombre);
          localStorage.setItem("username", data.username);
          localStorage.setItem("idArea", data.idArea);
          localStorage.setItem("area", data.nombreArea);
          localStorage.setItem("idRol", data.idRol);
          localStorage.setItem("rol", data.rol);
          localStorage.setItem("cargo", data.cargo);

          setUsername(data.nombre);
          setRolename(data.rol);
          setUserRole(data.idRol);

          const permisosRes = await fetch(`${API_GATEWAY_URL}/gateway/porRol?idRol=${data.idRol}`);
          const permisos = await permisosRes.json();
          if (Array.isArray(permisos)) {
            setPermisosData(permisos);
            localStorage.setItem("permisos", JSON.stringify(permisos));
          } else {
            console.error("Permisos no es un array:", permisos);
            setPermisosData([]);
          }

        } catch (error) {
          console.error("Error obteniendo usuario:", error);
        }
      } else {
        // Cargar desde localStorage
        setUsername(localStorage.getItem('nombre'));
        setRolename(localStorage.getItem('rol'));
        const storedRole = localStorage.getItem('idRol');
        if (storedRole) {
          setUserRole(parseInt(storedRole));

          fetch(`${API_GATEWAY_URL}/gateway/porRol?idRol=${storedRole}`)
            .then(res => res.json())
            .then(data => setPermisosData(data))
            .catch(err => console.error("Error cargando permisos:", err));
        }
      }

      
    };

    fetchUserData();
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      const ahora = new Date();
      const horaLimite = new Date();
      horaLimite.setHours(19, 0, 0, 0); // 7:00 PM 

      if (ahora >= horaLimite) {
        Modal.warning({
          title: 'Sesión expirada',
          content: 'Tu sesión ha expirado. Serás redirigido al inicio de sesión.',
          okText: 'Aceptar',
          centered: true,
          onOk: () => {
            localStorage.clear();
            window.location.href = `${API_URL_LOGIN}`;
          },
        });
        clearInterval(interval); 
      }
    }, 60000);

    return () => clearInterval(interval);
  }, []);


  if (userRole === null) return null;

  const permisosDict = {};
  if (!Array.isArray(permisosData)) return null;
  permisosData.forEach(p => {
    if (p.ruta && p.permisoVer) {
      permisosDict[p.ruta] = p.descripcion || p.ruta;
    }
  });

  const aplicarDescripciones = (items) =>
    items.map(item => {
      const newItem = { ...item };
      if (newItem.children) {
        newItem.children = aplicarDescripciones(newItem.children).filter(Boolean);
        if (newItem.children.length === 0) return null;
      }
      if (permisosDict[newItem.path]) {
        newItem.label = permisosDict[newItem.path];
      }
      if (newItem.children || permisosDict[newItem.path]) {
        return newItem;
      }
      return null;
    }).filter(Boolean);

  const filteredItems = aplicarDescripciones(menuItems)
    .filter(item => item.label.toLowerCase().includes(searchText.toLowerCase()));

  const renderIcon = (iconName) => {
    const IconComponent = AntIcons[iconName];
    return IconComponent ? <IconComponent /> : null;
  };

  const handleLogoutClick = () => {
    Modal.confirm({
      title: '¿Deseas cerrar sesión?',
      content: 'Tu sesión se cerrará y deberás volver a iniciar sesión.',
      okText: 'Sí, salir',
      cancelText: 'Cancelar',
      okType: 'danger',
      centered: true,
      onOk: () => {
        localStorage.clear();
        window.location.href = `${API_URL_LOGIN}`;
      },
    });
  };

  const renderMenuItems = (items) =>
    items.map((item) => {
      if (item.children && item.children.length > 0) {
        return (
          <Menu.SubMenu
            key={item.key}
            icon={renderIcon(item.icon)}
            title={item.label}
          >
            {renderMenuItems(item.children)}
          </Menu.SubMenu>
        );
      }
  
      return (
        <Menu.Item key={item.key} icon={renderIcon(item.icon)}>
          <Link to={item.path}>{item.label}</Link>
        </Menu.Item>
      );
    });

      const getUserInitials = (name) => {
    if (!name) return 'U';
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  };

    const renderNavItems = (items, isDropdown = false) => {
    return items.map((item) => {
      const isActive = location.pathname === item.path;
      const hasChildren = item.children && item.children.length > 0;

      if (hasChildren) {
        return (
          <div key={item.key} className="navbar-dropdown">
            <div className={`navbar-item ${isActive ? 'active' : ''}`}>
              {renderIcon(item.icon)}
              <span>{item.label}</span>
              <AntIcons.DownOutlined style={{ fontSize: '10px', marginLeft: '4px' }} />
            </div>
            <div className="navbar-dropdown-content">
              {item.children.map(child => (
                <Link
                  key={child.key}
                  to={child.path}
                  className={`navbar-dropdown-item ${location.pathname === child.path ? 'active' : ''}`}
                >
                  {renderIcon(child.icon)}
                  <span>{child.label}</span>
                </Link>
              ))}
            </div>
          </div>
        );
      }

      if (isDropdown) {
        return (
          <Link
            key={item.key}
            to={item.path}
            className={`navbar-dropdown-item ${isActive ? 'active' : ''}`}
          >
            {renderIcon(item.icon)}
            <span>{item.label}</span>
          </Link>
        );
      }

      return (
        <Link
          key={item.key}
          to={item.path}
          className={`navbar-item ${isActive ? 'active' : ''}`}
        >
          {renderIcon(item.icon)}
          <span>{item.label}</span>
        </Link>
      );
    });
  };

  
  return (
    <>
      <nav className="navbar">
        <div className="navbar-container">
          {/* Logo Section */}
          <div className="navbar-logo-section">
              <img src={logo} alt="Logo" className="navbar-logo" />
          </div>

          {/* Navigation Menu */}
          <div className="navbar-menu">
            {renderNavItems(filteredItems)}
          </div>

          {/* User Section */}
          <div className="navbar-user-section">
            <div className="navbar-dropdown user-dropdown">
              <div className="navbar-user-trigger">
                <div className="navbar-user-avatar">
                  {getUserInitials(username)}
                </div>
              </div>
              <div className="navbar-dropdown-content user-dropdown-content">
                <div className="dropdown-user-info">
                  <div className="navbar-username">{username || 'Usuario'}</div>
                  <div className="navbar-role">{rolename || 'Rol'}</div>
                </div>
                <div className="navbar-dropdown-item" onClick={handleLogoutClick}>
                  <AntIcons.LogoutOutlined />
                  <span>Salir</span>
                </div>
              </div>
            </div>
          </div>

          {/* Mobile Menu Toggle */}
          <button
            className="navbar-mobile-toggle"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <AntIcons.MenuOutlined />
          </button>
        </div>
      </nav>

      {/* Content Offset */}
      <div className="main-content">
        {/* Tu contenido principal va aquí */}
      </div>
    </>
  );
};

export default Sidebar;