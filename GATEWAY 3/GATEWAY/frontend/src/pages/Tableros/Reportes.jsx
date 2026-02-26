import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  Form, Input, Button, Table, Space, Card, Select, message,
  Typography, Row, Col, Empty, Divider, Tabs, Checkbox, Tag,
} from "antd";
import {
  DownloadOutlined, SearchOutlined, ClearOutlined, PlusOutlined,
  BarChartOutlined, TableOutlined,
} from "@ant-design/icons";
import * as XLSX from "xlsx";
import ReactECharts from "echarts-for-react";

const { Option } = Select;
const { Title, Text } = Typography;
const { TabPane } = Tabs;

const API_URL = "http://172.18.72.111:8027/api/buscar";
const API_TABLAS = "http://172.18.72.111:8027/api/tablas";
const API_COLUMNAS = "http://172.18.72.111:8027/api/columnas";

const Reportes = () => {
  const chartRef = useRef(null);
  const [tablasDisponibles, setTablasDisponibles] = useState([]);
  const [tabla, setTabla] = useState(null);
  const [columnas, setColumnas] = useState([]);
  const [availableColumns, setAvailableColumns] = useState([]);
  const [columnasInfo, setColumnasInfo] = useState([]); // Info completa de columnas
  const [filters, setFilters] = useState([]);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingColumns, setLoadingColumns] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);

  const [chartType, setChartType] = useState("bar");
  const [xAxisColumn, setXAxisColumn] = useState(null);
  const [yAxisColumns, setYAxisColumns] = useState([]);
  const [chartData, setChartData] = useState({ categories: [], seriesData: [] });
  const [useFullData, setUseFullData] = useState(false);
  const [topN, setTopN] = useState(10);
  const [filteredDataOnClick, setFilteredDataOnClick] = useState([]);

  // Cargar tablas disponibles
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(API_TABLAS);
        const json = await res.json();
        let tablas = [];
        if (Array.isArray(json)) tablas = json;
        else if (Array.isArray(json.tablas)) tablas = json.tablas;
        else if (Array.isArray(json.data)) tablas = json.data;
        setTablasDisponibles(tablas);
      } catch (e) {
        console.error("Error cargando tablas:", e);
        message.error("No se pudieron cargar las tablas desde el servidor");
        setTablasDisponibles([]);
      }
    })();
  }, []);

  // Vuelve a consultar al backend al cambiar de página o tamaño de página
useEffect(() => {
  if (!tabla || useFullData) return;     // si marcaste "Usar toda la tabla", no pegues de nuevo
  fetchData();                            // hace POST con el nuevo offset
}, [page, pageSize]);                     // 👈 dependencias


  // Cargar columnas cuando cambia la tabla
  useEffect(() => {
    if (tabla) {
      (async () => {
        try {
          setLoadingColumns(true);
          const res = await fetch(`${API_COLUMNAS}/${tabla}`);
          const json = await res.json();
          
          if (json.columnas && Array.isArray(json.columnas)) {
            // Guardar info completa de columnas
            setColumnasInfo(json.columnas);
            
            // Extraer solo los nombres para los selects
            const nombresColumnas = json.columnas.map(col => col.nombre);
            setAvailableColumns(nombresColumnas);
            
            message.success(`Se cargaron ${nombresColumnas.length} columnas`);
          }
        } catch (e) {
          console.error("Error cargando columnas:", e);
          message.error("No se pudieron cargar las columnas de la tabla");
          setAvailableColumns([]);
          setColumnasInfo([]);
        } finally {
          setLoadingColumns(false);
        }
      })();
    } else {
      setAvailableColumns([]);
      setColumnasInfo([]);
    }
  }, [tabla]);

  // Reset cuando cambia tabla o useFullData
  useEffect(() => {
    setColumnas([]);
    setFilters([]);
    setData([]);
    setTotal(0);
    setPage(1);
    setPageSize(10);
    setXAxisColumn(null);
    setYAxisColumns([]);
    setFilteredDataOnClick([]);
    // No reseteamos availableColumns aquí porque se maneja en el useEffect anterior
  }, [tabla, useFullData]);

  const buildBody = () => {
    const filtrosObj = Object.fromEntries(
      filters
        .filter(f => f?.key && f.value !== undefined && f.value !== null && String(f.value).trim())
        .map(f => [String(f.key).trim(), String(f.value).trim()])
    );
    const cols = columnas?.map(c => String(c).trim()).filter(c => c.length > 0);
    const body = {
      tabla: String(tabla).trim(),
      filtros: filtrosObj,
      offset: useFullData ? 0 : (page - 1) * pageSize,
      limit: useFullData ? 1000000 : pageSize,
    };
    if (cols && cols.length) body.columnas = cols;
    return body;
  };

  const fetchData = useCallback(async () => {
    if (!tabla) {
      message.warning("Por favor selecciona una tabla primero");
      return;
    }
    try {
      setLoading(true);
      const body = buildBody();
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const txt = await res.text();
      let json;
      try { json = JSON.parse(txt); } catch { json = {}; }

      const resultados = json.resultados ?? json.rows ?? json.data ?? json.result ?? [];
      const totalRegistros = json.total_registros ?? json.total ?? json.count ?? json.totalRows ?? resultados.length;
      const safeResults = Array.isArray(resultados) ? resultados : [];

      setData(safeResults);
      setTotal(typeof totalRegistros === "number" ? totalRegistros : safeResults.length);

      if (safeResults.length > 0) {
        if (!xAxisColumn && availableColumns.length > 0) {
          setXAxisColumn(availableColumns[0]);
        }
        message.success(`Se encontraron ${totalRegistros} registros`);
      } else {
        message.info("No se encontraron resultados");
      }
    } catch (e) {
      console.error("Error en fetch:", e);
      message.error("Error consultando la API");
      setData([]);
      setTotal(0);
    } finally { 
      setLoading(false); 
    }
  }, [tabla, page, pageSize, filters, columnas, useFullData, xAxisColumn, availableColumns]);

  const exportToExcel = () => {
    if (!Array.isArray(data) || !data.length) { 
      message.warning("No hay datos para exportar"); 
      return; 
    }
    const ws = XLSX.utils.json_to_sheet(data);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, tabla || "Datos");
    XLSX.writeFile(wb, `${tabla || "datos"}_${new Date().toISOString().split('T')[0]}.xlsx`);
    message.success("Archivo exportado exitosamente");
  };

  // Construir columnas de la tabla
  const tableColumns = (() => {
    if (!data.length) return [];
    
    // Si el usuario seleccionó columnas específicas, usar esas
    if (columnas && columnas.length > 0) {
      return columnas.map(key => ({
        title: <span style={{ fontWeight: 600 }}>{key}</span>,
        dataIndex: key,
        key,
        render: val => (val == null ? "" : String(val)),
      }));
    }
    
    // Si tenemos availableColumns de la API, usar esas (todas las columnas de la tabla)
    if (availableColumns && availableColumns.length > 0) {
      return availableColumns.map(key => ({
        title: <span style={{ fontWeight: 600 }}>{key}</span>,
        dataIndex: key,
        key,
        render: val => (val == null ? "" : String(val)),
      }));
    }
    
    // Fallback: obtener todas las columnas únicas de todos los registros
    const allKeys = new Set();
    data.forEach(row => {
      Object.keys(row).forEach(k => allKeys.add(k));
    });
    
    return Array.from(allKeys).map(key => ({
      title: <span style={{ fontWeight: 600 }}>{key}</span>,
      dataIndex: key,
      key,
      render: val => (val == null ? "" : String(val)),
    }));
  })();

  // Generar datos del gráfico con topN y "Otros"
  useEffect(() => {
    if (!xAxisColumn || !data.length) return;

    const counts = {};
    data.forEach(row => {
      const val = row[xAxisColumn] ?? "NULO";
      counts[val] = (counts[val] || 0) + 1;
    });

    let sorted = Object.entries(counts).sort((a,b) => b[1]-a[1]);
    const topData = sorted.slice(0, topN);
    const othersData = sorted.slice(topN);

    if (othersData.length) {
      const othersSum = othersData.reduce((sum, [,v]) => sum+v, 0);
      topData.push(["Otros", othersSum]);
    }

    const categories = topData.map(([k]) => k);
    const seriesData = topData.map(([_,v]) => v);
    setChartData({ categories, seriesData });
  }, [data, xAxisColumn, topN, useFullData]);

  const cardStyle = { 
    borderRadius: 12, 
    background: "#ffffff", 
    padding: 20, 
    boxShadow: "0 3px 12px rgba(255, 0, 0, 0.08)" 
  };

  // Click en gráfico -> filtrar datos
  const onChartClick = (params) => {
    const clickedCategory = params.name;
    if (clickedCategory === "Otros") {
      const topKeys = chartData.categories.filter(cat => cat !== "Otros");
      const filtered = data.filter(row => !topKeys.includes(row[xAxisColumn]));
      setFilteredDataOnClick(filtered);
    } else {
      const filtered = data.filter(row => row[xAxisColumn] === clickedCategory);
      setFilteredDataOnClick(filtered);
    }
    setPage(1);
    setPageSize(10);
  };

  // Helper para obtener icono según tipo de dato
  const getColumnIcon = (tipo) => {
    if (!tipo) return '📋';
    const t = tipo.toLowerCase();
    if (t.includes('int') || t.includes('decimal') || t.includes('numeric') || t.includes('float')) return '🔢';
    if (t.includes('varchar') || t.includes('char') || t.includes('text')) return '📝';
    if (t.includes('date') || t.includes('time')) return '📅';
    if (t.includes('bit') || t.includes('bool')) return '☑️';
    return '📋';
  };

  // Helper para obtener info de columna
  const getColumnInfo = (nombreCol) => {
    return columnasInfo.find(c => c.nombre === nombreCol);
  };

  return (
    <div style={{ padding: 24, background: "#f0f2f5", minHeight: "100vh" }}>
      {/* HEADER */}
      <div style={{
        textAlign: "center", 
        marginBottom: 24, 
        padding: 16, 
        borderRadius: 12,
        background: "linear-gradient(90deg, #a600ffff 2%, #28053eff 120%)", 
        color: "#ff0000ff"
      }}>
        <Title level={2} style={{ margin: 5, color: "#ffffff" }}>📊 Buscador Avanzado</Title>
        <Text style={{ color: "#ffffffff" }}>Explora tablas, columnas, filtros y gráficos interactivos</Text>
      </div>

      <Row gutter={[20, 20]}>
        {/* PANEL FILTROS */}
        <Col xs={24} lg={8}>
          <Card title="🔍 Parámetros" style={{ ...cardStyle, minHeight: 520 }}>
            <Form layout="vertical">
              <Form.Item label="Tabla" required>
                <Select
                  showSearch
                  placeholder="Selecciona tabla"
                  value={tabla}
                  onChange={setTabla}
                  allowClear
                  filterOption={(input, option) => 
                    option.children.toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {tablasDisponibles.length
                    ? tablasDisponibles.map((t,i)=>(
                      <Option 
                        key={i} 
                        value={typeof t==="string"?t:t.name??t.tabla??t.nombre??JSON.stringify(t)}
                      >
                        {typeof t==="string"?t:t.name??t.tabla??t.nombre??JSON.stringify(t)}
                      </Option>
                    ))
                    : <Option disabled>No hay tablas</Option>}
                </Select>
              </Form.Item>

              <Form.Item label={
                <Space>
                  <span>Columnas</span>
                  {loadingColumns && <Tag color="blue">Cargando...</Tag>}
                  {availableColumns.length > 0 && (
                    <Tag color="green">{availableColumns.length} disponibles</Tag>
                  )}
                </Space>
              }>
                <Select
                  mode="multiple"
                  style={{ width: "100%" }}
                  placeholder={tabla ? "Selecciona columnas (opcional)" : "Primero selecciona una tabla"}
                  value={columnas}
                  onChange={setColumnas}
                  allowClear
                  disabled={!tabla || loadingColumns}
                  loading={loadingColumns}
                  showSearch
                  filterOption={(input, option) => 
                    option.children.toLowerCase().includes(input.toLowerCase())
                  }
                >
                  {availableColumns.map(col => {
                    const info = getColumnInfo(col);
                    return (
                      <Option key={col} value={col}>
                        {getColumnIcon(info?.tipo)} {col}
                        {info && info.tipo && (
                          <span style={{ color: '#999', fontSize: '0.85em' }}>
                            {' '}({info.tipo})
                          </span>
                        )}
                      </Option>
                    );
                  })}
                </Select>
                {!tabla && (
                  <Text type="secondary" style={{ fontSize: '0.85em' }}>
                    Las columnas se cargarán automáticamente al seleccionar una tabla
                  </Text>
                )}
              </Form.Item>

              <Form.Item label="Filtros">
                {filters.map((f, idx)=>(
                  <Space key={idx} style={{ marginBottom:8, flexWrap:"wrap" }}>
                    <Select
                      showSearch
                      placeholder="Columna"
                      value={f.key}
                      onChange={value => {
                        const nf=[...filters]; 
                        nf[idx].key=value; 
                        setFilters(nf);
                      }}
                      style={{width: 150}}
                      disabled={!tabla || loadingColumns}
                    >
                      {availableColumns.map(col => (
                        <Option key={col} value={col}>
                          {getColumnIcon(getColumnInfo(col)?.tipo)} {col}
                        </Option>
                      ))}
                    </Select>
                    <Input 
                      placeholder="Valor" 
                      value={f.value} 
                      onChange={e=>{
                        const nf=[...filters]; 
                        nf[idx].value=e.target.value; 
                        setFilters(nf);
                      }} 
                      style={{width:130}}
                    />
                    <Button 
                      danger 
                      size="small" 
                      icon={<ClearOutlined />} 
                      onClick={()=>setFilters(filters.filter((_,i)=>i!==idx))}
                    />
                  </Space>
                ))}
                <Button 
                  type="dashed" 
                  block 
                  icon={<PlusOutlined />} 
                  onClick={()=>setFilters([...filters,{key:"",value:""}])}
                  disabled={!tabla || availableColumns.length === 0}
                >
                  Agregar filtro
                </Button>
              </Form.Item>

              <Divider/>

              <Checkbox 
                checked={useFullData} 
                onChange={e=>setUseFullData(e.target.checked)} 
                style={{marginBottom:12}}
              >
                Usar toda la tabla
              </Checkbox>

              <Space style={{ 
                display:"flex", 
                justifyContent:"center", 
                flexWrap:"wrap", 
                gap:12 
              }}>
                <Button 
                  type="primary" 
                  icon={<SearchOutlined />} 
                  onClick={fetchData} 
                  loading={loading}
                  disabled={!tabla}
                >
                  Buscar
                </Button>
                <Button 
                  icon={<DownloadOutlined />} 
                  onClick={exportToExcel}
                  disabled={data.length === 0}
                >
                  Exportar
                </Button>
                <Button 
                  danger 
                  icon={<ClearOutlined />} 
                  onClick={()=>{ 
                    setColumnas([]); 
                    setFilters([]); 
                    setData([]); 
                    setTotal(0); 
                    setTabla(null);
                    setPage(1); 
                    setPageSize(10); 
                    setXAxisColumn(null); 
                    setYAxisColumns([]); 
                    setUseFullData(false); 
                    setFilteredDataOnClick([]);
                  }}
                >
                  Limpiar
                </Button>
              </Space>
            </Form>
          </Card>
        </Col>

        {/* PANEL RESULTADOS Y GRÁFICOS */}
        <Col xs={24} lg={16}>
          <Card style={cardStyle}>
            <Tabs defaultActiveKey="1">
              <TabPane tab={<><TableOutlined /> Resultados ({data.length})</>} key="1">
                <Table
                  dataSource={filteredDataOnClick.length ? filteredDataOnClick : data}
                  columns={tableColumns}
                  loading={loading}
                  scroll={{x:"max-content"}}
                  bordered
                  pagination={{
                    current: page,
                    pageSize,
                    total: filteredDataOnClick.length ? filteredDataOnClick.length : total,
                    showSizeChanger:true,
                    showTotal: (total) => `Total: ${total} registros`,
                    onChange:(p,ps)=>{setPage(p); setPageSize(ps);},
                  }}
                  rowKey={(record,idx)=>idx}
                  locale={{ emptyText: "No hay datos para mostrar" }}
                />
              </TabPane>

              <TabPane tab={<><BarChartOutlined /> Gráficos</>} key="2">
                {(!data.length) ? (
                  <Empty description="No hay datos para graficar. Realiza una búsqueda primero."/>
                ) : (
                  <>
                    <Row gutter={[16,16]} style={{marginBottom:16}}>
                      <Col xs={24} md={8}>
                        <Text strong>Tipo de gráfico:</Text>
                        <Select value={chartType} onChange={setChartType} style={{width:"100%"}}>
                          <Option value="bar">Barras</Option>
                          <Option value="line">Línea</Option>
                          <Option value="pie">Pastel</Option>
                          <Option value="scatter">Dispersión</Option>
                        </Select>
                      </Col>
                      <Col xs={24} md={8}>
                        <Text strong>Eje X:</Text>
                        <Select 
                          value={xAxisColumn} 
                          onChange={setXAxisColumn} 
                          allowClear 
                          style={{width:"100%"}}
                        >
                          {availableColumns.map(col=>(
                            <Option key={col} value={col}>
                              {getColumnIcon(getColumnInfo(col)?.tipo)} {col}
                            </Option>
                          ))}
                        </Select>
                      </Col>
                      <Col xs={24} md={8} style={{display:"flex", alignItems:"flex-end"}}>
                        <Button 
                          type="primary" 
                          block 
                          onClick={()=>{
                            if(chartRef.current){
                              const url=chartRef.current.getEchartsInstance().getDataURL({
                                type:'png',
                                pixelRatio:2,
                                backgroundColor:'#ffffffff'
                              });
                              const link=document.createElement('a');
                              link.href=url;
                              link.download=`${tabla || "grafica"}_${new Date().toISOString().split('T')[0]}.png`;
                              link.click();
                              message.success("Gráfica descargada");
                            } else {
                              message.warning("No hay gráfica para descargar");
                            }
                          }}
                        >
                          Descargar Gráfica 📥
                        </Button>
                      </Col>
                    </Row>

                    {xAxisColumn && chartData.categories.length>0 && (
                      <ReactECharts
                        ref={chartRef}
                        option={{
                          tooltip: {
                            trigger: chartType==="pie"?"item":"axis",
                            formatter: params=>{
                              if(chartType==="pie"){
                                const {name,value,percent}=params;
                                return `${name}: ${value} (${percent}%)`;
                              }else{
                                const p=params[0];
                                return `${p.axisValue}<br/>${p.seriesName}: ${p.data}`;
                              }
                            }
                          },
                          legend:{top:"bottom",type:"scroll"},
                          xAxis: chartType!=="pie"?{type:"category",data:chartData.categories}:undefined,
                          yAxis: chartType!=="pie"?{type:"value"}:undefined,
                          series:[
                            chartType==="pie" ? {
                              type:chartType,
                              radius:"50%",
                              data:chartData.categories.map((c,i)=>({name:c,value:chartData.seriesData[i]})),
                              label:{formatter:"{b}: {d}%"}
                            } : {
                              type:chartType,
                              name:"Conteo",
                              data:chartData.seriesData,
                              smooth:chartType==="line",
                              emphasis:{focus:"series"},
                              itemStyle:{
                                color: (params)=> params.dataIndex<topN ? "#ff4d4f" : "#a0a0a0"
                              }
                            }
                          ]
                        }}
                        style={{height:500,width:"100%"}}
                        onEvents={{ click: onChartClick }}
                      />
                    )}
                  </>
                )}
              </TabPane>
            </Tabs>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Reportes;