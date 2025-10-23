import React, { useState, useEffect, useMemo } from "react";
import { Typography } from "antd";
import { useNavigate, useLocation } from "react-router-dom";
import * as AntIcons from '@ant-design/icons';
import menuItems from '../config/menuItems';
import { API_GATEWAY_URL } from "../config/rutas";
import "./homepage.css";

const { Title } = Typography;

const HomePage = () => {
  // === Estado base ===
  const [allModules, setAllModules] = useState([]);     // módulos sin filtrar (desde menuItems)
  const [modules, setModules] = useState([]);           // módulos filtrados por permisos
  const [allowedRoutes, setAllowedRoutes] = useState(null); // Set<string> de rutas permitidas
  const [selectedModule, setSelectedModule] = useState(null);
  const [loading, setLoading] = useState(true);

  // Carrusel
  const [currentCarouselIndex, setCurrentCarouselIndex] = useState(0);
  const [ringOffset, setRingOffset] = useState(0);
  const [visibleItems] = useState(6);
  

  const navigate = useNavigate();
  const location = useLocation();

  // Regresar a “Bienvenido” cuando se entra a /home
  useEffect(() => {
    if (location.pathname === "/home") setSelectedModule(null);
  }, [location.pathname]);

  // Mapeo de íconos
  const iconMapping = {
    appstoreoutlined: <AntIcons.AppstoreOutlined />,
    fileoutlined: <AntIcons.FileOutlined />,
    tooloutlined: <AntIcons.ToolOutlined />,

    administracion: <AntIcons.SettingOutlined />,
    usuarios: <AntIcons.TeamOutlined />,
    roles: <AntIcons.SafetyCertificateOutlined />,

    automatizacion: <AntIcons.RobotOutlined />,
    procesos: <AntIcons.ApiOutlined />,
    tareas: <AntIcons.ThunderboltOutlined />,

    gail: <AntIcons.CloudServerOutlined />,
    integracion: <AntIcons.ApiOutlined />,
    logs: <AntIcons.DatabaseOutlined />,

    tableros: <AntIcons.DashboardOutlined />,
    reportes: <AntIcons.AreaChartOutlined />,
    analisis: <AntIcons.FundOutlined />,

    notificaciones: <AntIcons.BellOutlined />,
    mensajes: <AntIcons.MessageOutlined />,
    alertas: <AntIcons.AlertOutlined />,

    planeacion: <AntIcons.ScheduleOutlined />,
    calendario: <AntIcons.CalendarOutlined />,
    proyectos: <AntIcons.ProjectOutlined />,

    juridica: <AntIcons.SolutionOutlined />,
    contratos: <AntIcons.FileProtectOutlined />,
    documentos: <AntIcons.FileTextOutlined />,

    default: <AntIcons.AppstoreOutlined />
  };

  const getModuleIcon = (moduleName, iconName) => {
    const key = (moduleName || iconName || '').toLowerCase();
    return iconMapping[key] || iconMapping.default;
  };

  const renderIcon = (iconName) => {
    if (!iconName) return iconMapping.default;
    const IconComponent = AntIcons[iconName];
    return IconComponent ? <IconComponent /> : iconMapping.default;
  };

  // Convierte tu menuItems en módulos (sin filtrar)
  const processMenuItems = (items) => {
    const processedModules = [];

    items.forEach(item => {
      if (item.children) {
        const moduleKey = item.key.toLowerCase();
        processedModules.push({
          id: moduleKey,
          title: item.label,
          icon: item.icon || 'AppstoreOutlined',
          description: `Gestiona y controla ${item.label.toLowerCase()}`,
          items: item.children.map(child => ({
            id: child.key,
            title: child.label,
            description: child.description || `Accede a ${child.label.toLowerCase()}`,
            icon: child.icon || 'FileOutlined',
            path: child.path
          }))
        });
      } else {
        // Ítems sueltos → “Herramientas”
        let toolsModule = processedModules.find(m => m.id === 'herramientas');
        if (!toolsModule) {
          toolsModule = {
            id: 'herramientas',
            title: 'Herramientas',
            icon: 'ToolOutlined',
            description: 'Utilidades y herramientas adicionales',
            items: []
          };
          processedModules.push(toolsModule);
        }
        toolsModule.items.push({
          id: item.key,
          title: item.label,
          description: item.description || `Accede a ${item.label.toLowerCase()}`,
          icon: item.icon || 'FileOutlined',
          path: item.path
        });
      }
    });

    return processedModules;
  };

  // Filtra módulos/ítems por rutas permitidas
  const filterModulesByRoutes = (rawModules, routeSet) => {
    if (!routeSet) return [];
    const lower = (s) => (s || '').toLowerCase();

    const filtered = rawModules.reduce((acc, mod) => {
      const items = (mod.items || []).filter(it => it.path && routeSet.has(lower(it.path)));
      if (items.length) acc.push({ ...mod, items });
      return acc;
    }, []);

    return filtered;
  };

  // Carga permisos por rol y actualiza allowedRoutes
  const loadPermissions = async (rol) => {
    try {
      const res = await fetch(`${API_GATEWAY_URL}/gateway/porRol?idRol=${rol}`);
      const data = await res.json();

      // Filtramos permisos con permisoVer = true y descartamos /home
      const excludedRoutes = ["/home"];
      const filtered = Array.isArray(data)
        ? data.filter(item => item?.permisoVer && item?.ruta && !excludedRoutes.includes(item.ruta))
        : [];

      // Normalizamos a minúscula para comparar con paths
      const routesSet = new Set(filtered.map(p => (p.ruta || '').toLowerCase()));
      setAllowedRoutes(routesSet);
    } catch (err) {
      console.error("Error loading permissions:", err);
      // En caso de error: no mostrar nada (cumple “solo lo asignado”)
      setAllowedRoutes(new Set()); 
    }
  };

  // Init: armar módulos y pedir permisos
  useEffect(() => {
    setLoading(true);
    const processed = processMenuItems(menuItems);
    setAllModules(processed);

    const rol = localStorage.getItem("idRol");
    if (rol) {
      loadPermissions(rol);
    } else {
      // Espera breve a que aparezca idRol en localStorage
      const interval = setInterval(() => {
        const savedRole = localStorage.getItem("idRol");
        if (savedRole) {
          clearInterval(interval);
          loadPermissions(savedRole);
        }
      }, 800);
      // timeout de seguridad
      setTimeout(() => clearInterval(interval), 5000);
    }
  }, []);

  // Cuando hay módulos y rutas permitidas, aplicamos el filtro
  useEffect(() => {
    if (allowedRoutes !== null) {
      const filtered = filterModulesByRoutes(allModules, allowedRoutes);
      setModules(filtered);
      setLoading(false);
    }
  }, [allModules, allowedRoutes]);

  // Si cambia el set de módulos (por permisos), recalibrar carrusel/selección
  useEffect(() => {
    setCurrentCarouselIndex(0);
    setRingOffset(0);

    if (selectedModule && !modules.some(m => m.id === selectedModule.id)) {
      setSelectedModule(null);
    }
  }, [modules]); // eslint-disable-line react-hooks/exhaustive-deps

  // Navegación del carrusel
  const stepDeg = useMemo(() => (modules.length ? 360 / modules.length : 0), [modules.length]);
  const rotateCarousel = (dir = 1) => setRingOffset(prev => prev + dir * stepDeg);
  const nextCarousel = () => {
    if (!modules.length) return;
    setCurrentCarouselIndex(prev => (prev + 1) % modules.length);
    setRingOffset(prev => prev + (360 / modules.length));
  };
  const prevCarousel = () => {
    if (!modules.length) return;
    setCurrentCarouselIndex(prev => (prev - 1 + modules.length) % modules.length);
    setRingOffset(prev => prev - (360 / modules.length));
  };

  // Teclado
  useEffect(() => {
    const handleKeyPress = (event) => {
      if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
        event.preventDefault(); prevCarousel();
      } else if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {
        event.preventDefault(); nextCarousel();
      } else if (event.key >= '1' && event.key <= '9') {
        const index = parseInt(event.key) - 1;
        if (index < modules.length) setSelectedModule(modules[index]);
      }
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [modules]);

  // Utilidades UI
  const handleModuleSelect = (module) => setSelectedModule(module);
  const handleNavigation = (path) => { if (path) navigate(path); };

  const getClosestIndex = () => {
    if (!modules.length) return 0;
    let minDiff = 9999, idx = 0;
    modules.forEach((_, i) => {
      let itemAngle = (i * stepDeg + ringOffset) % 360;
      itemAngle = ((itemAngle + 540) % 360) - 180; // normaliza [-180, 180]
      if (Math.abs(itemAngle) < minDiff) { minDiff = Math.abs(itemAngle); idx = i; }
    });
    return idx;
  };
  const selectedIdx = getClosestIndex();

  // (Opcional) visibleItems del carrusel: mantenemos tu API aunque no es crítico para el grid
  const getVisibleModules = () => {
    const buffer = 2;
    const total = modules.length;
    const renderCount = Math.min(visibleItems + (buffer * 2), total);
    let indices = [];
    for (let i = 0; i < renderCount; i++) {
      const index = (currentCarouselIndex - buffer + i + total) % total;
      indices.push(index);
    }
    return indices.map(i => modules[i]);
  };

  return (
    <div className="carousel-homepage">
      {/* Fondo animado conservado */}
      <div className="cosmic-bg">
        <div className="cosmic-orb orb-1"></div>
        <div className="cosmic-orb orb-2"></div>
        <div className="cosmic-orb orb-3"></div>
      </div>

      {/* Carrusel en esquina */}
      <div className="corner-carousel">
        <div className="carousel-nav">
          <button className="nav-arrow up" onClick={() => rotateCarousel(-1)}>
            <AntIcons.UpOutlined />
          </button>
          <button className="nav-arrow down" onClick={() => rotateCarousel(1)}>
            <AntIcons.DownOutlined />
          </button>
        </div>

        <div className="carousel-ring" style={{ '--offset': `${ringOffset}deg` }}>
          {modules.map((module, i) => {
            const angle = (360 / modules.length) * i;
            const isActive = selectedModule?.id === module.id || i === selectedIdx;
            return (
              <div
                key={`${module.id}-${i}`}
                className={`carousel-item ${isActive ? 'active' : ''}`}
                style={{ '--angle': `${angle}deg` }}
                onClick={() => handleModuleSelect(module)}
                title={module.title}
              >
                <div className="item-icon">{getModuleIcon(module.id, module.icon)}</div>
                <div className="item-label">{module.title}</div>
              </div>
            );
          })}
        </div>

        <div className="carousel-center" onClick={() => setSelectedModule(null)}>
          <AntIcons.AppstoreOutlined />
        </div>
      </div>

      {/* Contenido principal */}
      <div className="main-content-area">
        {selectedModule ? (
          <>
            <div className="content-header">
              <h1 className="content-title">{selectedModule.title}</h1>
              <p className="content-subtitle">
                {selectedModule.description} • {selectedModule.items.length} herramientas disponibles
              </p>
            </div>

            <div className="items-grid">
              {selectedModule.items.map((item, index) => (
                <div
                  key={item.id}
                  className="content-item slide-in"
                  style={{ animationDelay: `${index * 0.1}s` }}
                  onClick={() => handleNavigation(item.path)}
                >
                  <div className="item-header">
                    <div className="item-icon-wrapper">
                      {renderIcon(item.icon)}
                    </div>
                    <div className="item-text">
                      <h3 className="item-title">{item.title}</h3>
                      <p className="item-description">{item.description}</p>
                    </div>
                  </div>
                  <div className="item-arrow">
                    <AntIcons.ArrowRightOutlined />
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="welcome-state">
            <div className="welcome-icon">
              <AntIcons.RocketOutlined />
            </div>
            <div className="welcome-text">
              <h2>Bienvenido a Nexum</h2>
              <p>
                Usa las flechas para navegar por los módulos y selecciona uno para ver
                sus herramientas asignadas a tu rol.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="loading-overlay">
          <div className="loading-content">
            <AntIcons.LoadingOutlined className="loading-icon" />
            <div>Cargando módulos...</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;
