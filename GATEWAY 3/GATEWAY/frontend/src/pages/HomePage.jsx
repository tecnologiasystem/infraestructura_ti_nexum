import React, { useState, useEffect, useMemo } from "react";
import { Typography, Button, Modal, Space, Tag, Statistic, message, Input } from "antd";
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
  const [estadisticasVisible, setEstadisticasVisible] = useState(false);
  const [idEncabezadoVisible, setIdEncabezadoVisible] = useState(false);
  const [idEncabezado, setIdEncabezado] = useState('');
  const [estadisticas, setEstadisticas] = useState({
    procesados: 0,
    pendientes: 0,
    total: 0
  });

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

  // Cargar estadísticas de WhatsApp
  const cargarEstadisticas = async (encabezadoId) => {
    try {
      const res = await fetch(`${API_GATEWAY_URL}/api/whatsapp/estadisticas?idEncabezado=${encabezadoId}`);
      const data = await res.json();
      
      console.log("Respuesta del backend:", data); // Para debug
      
      // La respuesta viene en data.estadisticas con guiones bajos
      const stats = data?.estadisticas || {};
      const total = stats.total || 0;
      const validados = stats.con_whatsapp || 0;
      const pendientes = stats.vacios || 0;
      
      setEstadisticas({
        procesados: validados,
        pendientes: pendientes,
        total: total
      });
      
      console.log("Estadísticas cargadas:", { total, validados, pendientes }); // Para debug
    } catch (error) {
      console.error("Error al cargar estadísticas:", error);
      message.error("Error al cargar estadísticas de WhatsApp");
    }
  };

  // Manejar búsqueda por ID de encabezado
  const handleBuscarEncabezado = () => {
    if (!idEncabezado || idEncabezado.trim() === '') {
      message.warning("Por favor ingresa un ID de encabezado");
      return;
    }
    setIdEncabezadoVisible(false);
    setEstadisticasVisible(true);
    cargarEstadisticas(idEncabezado);
  };

  // Exportar a Excel desde el backend
  const exportarExcel = async () => {
    try {
      message.loading({ content: 'Descargando Excel...', key: 'download' });
      
      const url = `${API_GATEWAY_URL}/api/whatsapp/descargar-excel?idEncabezado=${idEncabezado}`;
      
      // Hacer fetch para obtener el archivo
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error('Error al descargar el archivo');
      }
      
      // Convertir la respuesta a blob
      const blob = await response.blob();
      
      // Crear URL del blob
      const blobUrl = window.URL.createObjectURL(blob);
      
      // Crear enlace temporal para descargar
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `Numeros_WhatsApp_ID${idEncabezado}_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(link);
      link.click();
      
      // Limpiar
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
      
      message.success({ content: `Excel del encabezado ${idEncabezado} descargado correctamente`, key: 'download' });
    } catch (error) {
      console.error("Error al exportar:", error);
      message.error({ content: "No se pudo descargar el Excel", key: 'download' });
    }
  };

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

      {/* Botón de Estadísticas WhatsApp (visible solo si tiene acceso a RPA WhatsApp) */}
      {allowedRoutes?.has("/rpawhatsapp") && (
        <>
          <Button
            className="whatsapp-stats-button"
            icon={<AntIcons.WhatsAppOutlined />}
            onClick={() => {
              setIdEncabezado(''); // Limpiar input
              setIdEncabezadoVisible(true);
            }}
          >
            WhatsApp Estatus
          </Button>

          {/* Modal para ingresar ID de Encabezado */}
          <Modal
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <AntIcons.SearchOutlined style={{ fontSize: '24px', color: '#25D366' }} />
                <h3 style={{ margin: 0 }}>🔍 Buscar Estadísticas WhatsApp</h3>
              </div>
            }
            open={idEncabezadoVisible}
            onCancel={() => setIdEncabezadoVisible(false)}
            footer={[
              <Button key="cancel" onClick={() => setIdEncabezadoVisible(false)}>
                Cancelar
              </Button>,
              <Button 
                key="search" 
                type="primary"
                icon={<AntIcons.SearchOutlined />}
                onClick={handleBuscarEncabezado}
                style={{ 
                  background: 'linear-gradient(135deg, #25D366 0%, #128C7E 100%)',
                  border: 'none'
                }}
              >
                Buscar
              </Button>
            ]}
          >
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div>
                <Typography.Text strong style={{ display: 'block', marginBottom: '8px' }}>
                  Ingresa el ID del Encabezado:
                </Typography.Text>
                <Input
                  size="large"
                  placeholder="Ejemplo: 44, 45..."
                  value={idEncabezado}
                  onChange={(e) => setIdEncabezado(e.target.value)}
                  onPressEnter={handleBuscarEncabezado}
                  prefix={<AntIcons.NumberOutlined style={{ color: '#25D366' }} />}
                  style={{ borderRadius: '8px' }}
                />
              </div>
              <Typography.Paragraph type="secondary" style={{ textAlign: 'center', margin: 0 }}>
                💡 Ingresa el ID del encabezado de la carga masiva para ver las estadísticas de validación.
              </Typography.Paragraph>
            </Space>
          </Modal>

          {/* Modal de Estadísticas */}
          <Modal
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <AntIcons.WhatsAppOutlined style={{ fontSize: '24px', color: '#25D366' }} />
                <h3 style={{ margin: 0 }}>📊 Estadísticas de Validación WhatsApp (ID: {idEncabezado})</h3>
              </div>
            }
            open={estadisticasVisible}
            onCancel={() => setEstadisticasVisible(false)}
            width={700}
            footer={[
              <Button key="close" onClick={() => setEstadisticasVisible(false)}>
                Cerrar
              </Button>,
              <Button 
                key="change" 
                icon={<AntIcons.SwapOutlined />}
                onClick={() => {
                  setEstadisticasVisible(false);
                  setIdEncabezadoVisible(true);
                }}
              >
                Cambiar Encabezado
              </Button>,
              <Button 
                key="export" 
                type="primary"
                icon={<AntIcons.FileExcelOutlined />}
                onClick={exportarExcel}
                style={{ 
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  border: 'none'
                }}
              >
                Descargar Excel Completo
              </Button>
            ]}
          >
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <div style={{ display: 'flex', justifyContent: 'space-around', marginBottom: '24px' }}>
                <Statistic
                  title="Total de Números"
                  value={estadisticas.total}
                  prefix={<AntIcons.PhoneOutlined />}
                  valueStyle={{ color: '#3b82f6' }}
                />
                <Statistic
                  title="Números Validados"
                  value={estadisticas.procesados}
                  prefix={<AntIcons.CheckCircleOutlined />}
                  valueStyle={{ color: '#10b981' }}
                />
                <Statistic
                  title="Números Pendientes"
                  value={estadisticas.pendientes}
                  prefix={<AntIcons.ClockCircleOutlined />}
                  valueStyle={{ color: '#f59e0b' }}
                />
              </div>
              
              <div style={{ 
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
                padding: '20px', 
                borderRadius: '12px',
                color: 'white',
                textAlign: 'center'
              }}>
                <h3 style={{ color: 'white', marginBottom: '8px' }}>
                  Progreso: {estadisticas.total > 0 
                    ? ((estadisticas.procesados / estadisticas.total) * 100).toFixed(2) 
                    : 0}%
                </h3>
                <p style={{ margin: 0, opacity: 0.9 }}>
                  🤖 20 máquinas trabajando en {estadisticas.total.toLocaleString('es-ES')} números
                </p>
              </div>
              
              <Typography.Paragraph type="secondary" style={{ textAlign: 'center', marginTop: '16px' }}>
                Los datos se actualizan automáticamente cada vez que abres esta ventana.
                Usa el botón de exportar para descargar el detalle completo en Excel.
              </Typography.Paragraph>
            </Space>
          </Modal>
        </>
      )}

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
