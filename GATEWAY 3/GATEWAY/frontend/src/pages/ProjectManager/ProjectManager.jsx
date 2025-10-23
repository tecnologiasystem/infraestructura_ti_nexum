import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Card,
  Row,
  Col,
  Progress,
  Button,
  Table,
  Typography,
  Space,
  Tag,
  message,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  InputNumber,
} from 'antd';
import {
  PlusOutlined,
  FilePdfOutlined,
  RobotOutlined,
  ArrowLeftOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ProfileOutlined,
} from '@ant-design/icons';
import { Gantt } from 'gantt-task-react';
import 'gantt-task-react/dist/index.css';
import dayjs from 'dayjs';
import 'dayjs/locale/es';
import Holidays from 'date-holidays';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

dayjs.locale('es');
const { Title, Text } = Typography;
const API = process.env.REACT_APP_API_URL_GATEWAY || 'http://localhost:8020/api/project';

const ESTADOS = [
  { value: 'PENDIENTE', label: 'Pendiente' },
  { value: 'EN_EJECUCION', label: 'En ejecución' },
  { value: 'COMPLETADA', label: 'Completada' },
];

const exportPdfEjecutivo = ({
  resumenGeneral,
  modulos,
  tareasCriticas,
  recursos,
  recomendaciones,
  riesgos,
  conclusiones
}) => {
  const doc = new jsPDF();

  doc.setFontSize(18);
  doc.text('INFORME EJECUTIVO DE PROYECTO', 14, 16);
  doc.setFontSize(13);
  doc.text('Implementación de Plataforma de Gestión de Proyectos Nexum', 14, 25);
  doc.text(`Fecha de corte: ${new Date().toLocaleDateString()}`, 14, 32);

  doc.setFontSize(12);
  doc.text('Resumen General', 14, 42);
  doc.autoTable({
    body: resumenGeneral,
    startY: 45,
    theme: 'grid',
    styles: { fontSize: 10 }
  });

  let y = doc.previousAutoTable.finalY + 10;
  doc.setFontSize(12);
  doc.text('Avance por Módulo', 14, y);
  doc.autoTable({
    head: [['Módulo', '% Completado', 'Tareas Críticas', 'Días de Retraso', 'Responsable']],
    body: modulos,
    startY: y + 3,
    theme: 'grid',
    styles: { fontSize: 10 }
  });

  y = doc.previousAutoTable.finalY + 8;
  doc.setFontSize(12);
  doc.text('Tareas Críticas Retrasadas', 14, y);
  doc.autoTable({
    head: [['Tarea', 'Responsable', 'Estado', 'Días de Retraso', 'Horas', 'Comentario']],
    body: tareasCriticas,
    startY: y + 3,
    theme: 'grid',
    styles: { fontSize: 10 }
  });

  y = doc.previousAutoTable.finalY + 8;
  doc.setFontSize(12);
  doc.text('Análisis de Recursos', 14, y);
  doc.autoTable({
    head: [['Recurso', 'Horas Planificadas', 'Horas Consumidas', 'Desviación', 'Comentario']],
    body: recursos,
    startY: y + 3,
    theme: 'grid',
    styles: { fontSize: 10 }
  });

  y = doc.previousAutoTable.finalY + 8;
  doc.setFontSize(12);
  doc.text('Recomendaciones', 14, y);
  doc.setFontSize(10);
  recomendaciones.forEach((rec, idx) => {
    doc.text(`- ${rec}`, 16, y + 7 + idx * 6);
  });

  y += 7 + recomendaciones.length * 6 + 2;
  doc.setFontSize(12);
  doc.text('Riesgos y Alertas', 14, y);
  doc.setFontSize(10);
  riesgos.forEach((r, idx) => {
    doc.text(`- ${r}`, 16, y + 7 + idx * 6);
  });

  y += 7 + riesgos.length * 6 + 2;
  doc.setFontSize(12);
  doc.text('Conclusiones Ejecutivas', 14, y);
  doc.setFontSize(10);
  conclusiones.forEach((c, idx) => {
    doc.text(`- ${c}`, 16, y + 7 + idx * 6);
  });

  doc.setFontSize(9);
  doc.text(
    `Generado automáticamente por Nexum | Fecha y hora: ${new Date().toLocaleString()} | Usuario: Camilo Martínez`,
    105,
    290,
    { align: 'center' }
  );

  doc.save('informe_presidencia_nexum.pdf');
};



export default function ProjectManager() {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(false);

  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  const [totalHours, setTotalHours] = useState(0);
  const [totalDays, setTotalDays] = useState(0);
  const hd = new Holidays('CO');

  // Opciones de recursos para el select <Select>
  const resourceOptions = resources.map(r => ({
    label: r.nombre,
    value: r.idRecurso,
  }));

  const ganttColumns = [
    { header: 'Nombre', width: 250, data: 'name' },
    { header: 'Inicio', width: 120, data: 'start' },
    { header: 'Fin',    width: 120, data: 'end' },
  ];

  // 1) Lista proyectos
  const fetchProjects = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/proyecto/listar`);
      const enriched = await Promise.all(
        data.map(async proj => {
          const { data: tareas } = await axios.get(`${API}/tarea/listar`, { params: { idProyecto: proj.idProyecto } });
          const total = tareas.length;
          const avg = total
            ? Math.round(tareas.reduce((s, t) => s + t.porcentajeCompletado, 0) / total)
            : 0;
          const estado =
            total > 0 ? 'En ejecución' : proj.estado;
          const times = tareas.map(t => ({
            start: dayjs(t.fechaInicio, 'YYYY-MM-DD').toDate().getTime(),
            end:   dayjs(t.fechaFin,    'YYYY-MM-DD').toDate().getTime(),
          }));
          const min = total
            ? new Date(Math.min(...times.map(x => x.start)))
            : dayjs(proj.fechaInicio, 'YYYY-MM-DD').toDate();
          const max = total
            ? new Date(Math.max(...times.map(x => x.end)))
            : dayjs(proj.fechaFin,    'YYYY-MM-DD').toDate();
          return {
            ...proj,
            totalTareas:        total,
            progresoPromedio:   avg,
            estado,
            fechaInicioMostrar: dayjs(min).format('YYYY-MM-DD'),
            fechaFinMostrar:    dayjs(max).format('YYYY-MM-DD'),
          };
        })
      );
      setProjects(enriched);
    } catch {
      message.error('Error al cargar proyectos');
    } finally {
      setLoading(false);
    }
  };

  // 2) Lista detalle (tareas + recursos)
  const fetchDetail = async proj => {
    setLoading(true);
    try {
      const [tRes, rRes] = await Promise.all([
        axios.get(`${API}/tarea/listar`, { params: { idProyecto: proj.idProyecto } }),
        axios.get(`${API}/recurso/listar`),
      ]);
      setTasks(
        tRes.data.map(t => ({
          id:           String(t.idTarea),
          name:         t.titulo,
          start:        dayjs(t.fechaInicio, 'YYYY-MM-DD').toDate(),
          end:          dayjs(t.fechaFin,    'YYYY-MM-DD').toDate(),
          type:         'task',
          progress:     t.porcentajeCompletado,
          dependencies: t.antecesoraId ? [String(t.antecesoraId)] : [],
        }))
      );
      setResources(rRes.data);
      setSelectedProject(proj);
      await fetchProjects();
    } catch {
      message.error('Error al cargar detalles');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const onBack = () => {
    setSelectedProject(null);
    setTasks([]);
  };

  // 3) Crear tarea
  const handleAddTask = async values => {
    const payload = {
      idProyecto:            selectedProject.idProyecto,
      idTarea:               0,
      titulo:                values.name,
      descripcion:           values.descripcion,
      responsable:           values.responsables[0],
      estado:                values.estado,
      porcentajeCompletado:  values.porcentajeCompletado,
      antecesoraId:          values.predecessors?.[0] || null,
      fechaInicio:           values.start.format('YYYY-MM-DD'),
      fechaFin:              values.end.format('YYYY-MM-DD'),
      unidadNegocio:         values.unidadNegocio,
      responsables:          values.responsables,
      predecessors:          values.predecessors,
    };

    try {
      await axios.post(`${API}/tarea/crear`, payload);
      message.success('Tarea creada');
      setModalVisible(false);
      form.resetFields();
      fetchDetail(selectedProject);
    } catch (err) {
      console.error(err);
      message.error('Error al crear la tarea');
    }
  };

  const taskColumns = [
    { title: 'ID',                dataIndex: 'idTarea',            key: 'idTarea' },
    { title: 'Título',            dataIndex: 'titulo',            key: 'titulo' },
    { title: 'Responsable',       dataIndex: 'responsable',       key: 'responsable' },
    { title: 'Inicio',            dataIndex: 'fechaInicio',       key: 'fechaInicio' },
    { title: 'Fin',               dataIndex: 'fechaFin',          key: 'fechaFin' },
    {
      title: '%',
      dataIndex: 'porcentajeCompletado',
      key: 'porcentajeCompletado',
      render: v => <Progress percent={v} size="small" />,
    },
    { title: 'Predecesora',       dataIndex: 'antecesoraId',      key: 'antecesoraId' },
    {
      title: 'Recursos',
      dataIndex: 'recursos',
      key: 'recursos',
      render: rec => rec?.length || 0,
    },
  ];

  const calculateTotals = (start, end) => {
    if (!start || !end) {
      setTotalHours(0);
      setTotalDays(0);
      return;
    }
    const s = start.startOf('day');
    const e = end.startOf('day');
    let curr = s.clone();
    let hours = 0;
    let days = 0;

    while (curr.isBefore(e) || curr.isSame(e)) {
      const dow = curr.day(); // 0 = domingo, 6 = sábado
      const isHoliday = !!hd.isHoliday(curr.toDate());
      if (!isHoliday && dow !== 0) {
        // Lunes–Viernes: 9.5 h; Sábado: 3 h
        if (dow >= 1 && dow <= 5) hours += 9.5;
        else if (dow === 6) hours += 3;
        days += 1;
      }
      curr = curr.add(1, 'day');
    }

    setTotalHours(hours);
    setTotalDays(days);
  };

  // ---- PDF EXPORT ----
  const handleExportPdf = async () => {
    try {
      // Captura Gantt y tabla
      const ganttElement = document.querySelector('.gantt-container') || document.querySelector('.gantt');
      const tableElement = document.querySelector('.ant-table-wrapper');

      if (!ganttElement || !tableElement) {
        message.error('No se encontraron elementos para exportar');
        return;
      }

      // Gantt
      const ganttCanvas = await html2canvas(ganttElement, { backgroundColor: '#fff', useCORS: true, scale: 2 });
      const ganttImg = ganttCanvas.toDataURL('image/png');
      // Tabla
      const tableCanvas = await html2canvas(tableElement, { backgroundColor: '#fff', useCORS: true, scale: 2 });
      const tableImg = tableCanvas.toDataURL('image/png');

      // PDF
      const pdf = new jsPDF('landscape', 'pt', 'a4');
      const pageWidth = pdf.internal.pageSize.getWidth();
      let y = 30;

      pdf.setFontSize(18);
      pdf.text('Informe Ejecutivo Proyecto NEXUM', pageWidth / 2, y, { align: 'center' });
      y += 25;

      // Gantt
      const ganttWidth = pageWidth - 60;
      const ganttHeight = (ganttCanvas.height / ganttCanvas.width) * ganttWidth;
      pdf.addImage(ganttImg, 'PNG', 30, y, ganttWidth, ganttHeight);
      y += ganttHeight + 15;

      // Nueva página si se pasa de largo
      if (y + 200 > pdf.internal.pageSize.getHeight()) {
        pdf.addPage();
        y = 30;
      }

      // Tabla
      const tableWidth = pageWidth - 60;
      const tableHeight = (tableCanvas.height / tableCanvas.width) * tableWidth;
      pdf.addImage(tableImg, 'PNG', 30, y, tableWidth, tableHeight);
      y += tableHeight + 20;

      // Pie de página
      pdf.setFontSize(10);
      pdf.text(
        `Generado por Nexum • ${new Date().toLocaleString()} • Usuario: Camilo Martínez`,
        pageWidth / 2,
        pdf.internal.pageSize.getHeight() - 10,
        { align: 'center' }
      );

      pdf.save('informe_ejecutivo_nexum.pdf');
    } catch (e) {
      message.error('Error al generar PDF');
      console.error(e);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      {!selectedProject ? (
        <>
          <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
            <Title level={2}>Mis Proyectos</Title>
            <Button type="primary" icon={<PlusOutlined />}>
              Nuevo Proyecto
            </Button>
          </Row>
          <Row gutter={[16, 16]}>
            {projects.map(p => {
              const pct = p.progresoPromedio || 0;
              return (
                <Col xs={24} sm={24} md={12} lg={8} xl={6} key={p.idProyecto}>
                  <Card
                    hoverable
                    onClick={() => fetchDetail(p)}
                    bordered={false}
                    bodyStyle={{ padding: 16 }}
                    style={{
                      borderRadius: 8,
                      boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
                      cursor: 'pointer',
                      borderLeft: `4px solid ${
                        p.estado === 'En ejecución' ? '#52c41a' : '#1890ff'
                      }`,
                    }}
                  >
                    <Space direction="vertical" size={4} style={{ width: '100%' }}>
                      <Title level={4} style={{ margin: 0 }}>
                        {p.titulo}
                      </Title>
                      <Space size={8} wrap>
                        <Tag
                          icon={
                            p.estado === 'En ejecución' ? (
                              <CheckCircleOutlined />
                            ) : (
                              <ClockCircleOutlined />
                            )
                          }
                          color={p.estado === 'En ejecución' ? 'success' : 'default'}
                        >
                          {p.estado}
                        </Tag>
                        <Space size={4}>
                          <ProfileOutlined />
                          <Text>{p.totalTareas} tareas</Text>
                        </Space>
                        <Space size={4}>
                          <ProfileOutlined rotate={90} />
                          <Text>{pct}% completado</Text>
                        </Space>
                      </Space>
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {p.fechaInicioMostrar} → {p.fechaFinMostrar}
                      </Text>
                      <Progress percent={pct} size="small" strokeLinecap="round" />
                    </Space>
                  </Card>
                </Col>
              );
            })}
          </Row>
        </>
      ) : (
        <>
          <Row align="middle" justify="space-between" style={{ marginBottom: 16 }}>
            <Space>
              <Button icon={<ArrowLeftOutlined />} onClick={onBack} />
              <Title level={2}>{selectedProject.titulo}</Title>
            </Space>
            <Space>
              <Button icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
                Crear Tarea
              </Button>
              <Button icon={<FilePdfOutlined />} onClick={handleExportPdf}>
                Informe Ejecutivo
              </Button>
              <Button icon={<RobotOutlined />}>Chat IA</Button>
            </Space>
          </Row>

          <Modal
            title="Nueva tarea"
            open={modalVisible}
            onCancel={() => {
              setModalVisible(false);
              form.resetFields();
              setTotalHours(0); setTotalDays(0);
            }}
            onOk={() => form.submit()}
            afterClose={() => {
              form.resetFields();
              setTotalHours(0); setTotalDays(0);
            }}
            okText="Crear"
            cancelText="Cancelar"
            width={900}
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={handleAddTask}
              onValuesChange={(_, vals) => {
                calculateTotals(vals.start, vals.end);
              }}
            >
              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <Form.Item
                    name="name"
                    label="Título"
                    rules={[{ required: true, message: 'Por favor ingresa un título' }]}
                  >
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={24}>
                  <Form.Item
                    name="descripcion"
                    label="Descripción"
                    rules={[{ required: true, message: 'Por favor ingresa una descripción' }]}
                  >
                    <Input.TextArea rows={3} />
                  </Form.Item>
                </Col>

                <Col span={12}>
                  <Form.Item
                    name="estado"
                    label="Estado"
                    rules={[{ required: true, message: 'Selecciona un estado' }]}
                  >
                    <Select placeholder="Selecciona estado">
                      {ESTADOS.map(e => (
                        <Select.Option key={e.value} value={e.value}>
                          {e.label}
                        </Select.Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="porcentajeCompletado"
                    label="% Completado"
                    rules={[{ required: true, message: 'Ingresa un porcentaje' }]}
                  >
                    <InputNumber min={0} max={100} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>

                <Col span={24}>
                  <Form.Item
                    name="unidadNegocio"
                    label="Unidad de Negocio"
                    rules={[{ required: true, message: 'Ingresa unidad de negocio' }]}
                  >
                    <Input />
                  </Form.Item>
                </Col>

                <Col span={12}>
                  <Form.Item
                    name="responsables"
                    label="Responsable(s)"
                    rules={[{ required: true, message: 'Selecciona al menos un responsable' }]}
                  >
                    <Select
                      mode="multiple"
                      showSearch
                      placeholder="Selecciona recurso..."
                      optionFilterProp="label"
                      filterOption={(input, opt) =>
                        opt.label.toLowerCase().includes(input.toLowerCase())
                      }
                      options={resourceOptions}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="predecessors" label="Predecesoras">
                    <Select
                      mode="multiple"
                      placeholder="Selecciona tarea(s) previas"
                      options={tasks.map(t => ({ label: t.name, value: t.id }))}
                    />
                  </Form.Item>
                </Col>

                <Col span={12}>
                  <Form.Item
                    name="start"
                    label="Fecha de inicio"
                    rules={[{ required: true, message: 'Selecciona fecha de inicio' }]}
                  >
                    <DatePicker style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="end"
                    label="Fecha de fin"
                    rules={[{ required: true, message: 'Selecciona fecha de fin' }]}
                  >
                    <DatePicker style={{ width: '100%' }} />
                  </Form.Item>
                </Col>

                <Col span={12}>
                  <Form.Item name="dependencyType" label="Tipo de dependencia">
                    <Select placeholder="Ej: FF">
                      <Select.Option value="FS">Fin–Comienzo (FS)</Select.Option>
                      <Select.Option value="SS">Inicio–Inicio (SS)</Select.Option>
                      <Select.Option value="FF">Fin–Fin (FF)</Select.Option>
                      <Select.Option value="SF">Inicio–Fin (SF)</Select.Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="dependencyLag" label="Retraso (días)">
                    <InputNumber min={0} max={99} style={{ width: '100%' }} placeholder="0-9" />
                  </Form.Item>
                </Col>

                {/* Totales automáticos */}
                <Col span={12}>
                  <Text>
                    Total Horas: <Text strong>{totalHours}</Text>
                  </Text>
                </Col>
                <Col span={12}>
                  <Text>
                    Total Días: <Text strong>{totalDays}</Text>
                  </Text>
                </Col>
              </Row>
            </Form>
          </Modal>

          <Row gutter={24}>
            <Col span={24} style={{ marginBottom: 24 }}>
              <div className="gantt-container">
                <Gantt
                  tasks={tasks}
                  viewMode="Day"
                  fitTasks
                  columns={ganttColumns}
                  onDateChange={() => {}}
                />
              </div>
            </Col>
            <Col span={24}>
              <Table
                dataSource={tasks.map(t => ({
                  ...t,
                  key: t.id,
                  idTarea: t.id,
                  titulo: t.name,
                  fechaInicio: dayjs(t.start).format('YYYY-MM-DD'),
                  fechaFin: dayjs(t.end).format('YYYY-MM-DD'),
                  porcentajeCompletado: t.progress,
                  antecesoraId: t.dependencies[0] || '—',
                  recursos: resources.filter(r => r.idTarea === Number(t.id)),
                }))}
                columns={taskColumns}
                loading={loading}
              />
            </Col>
          </Row>
        </>
      )}
    </div>
  );
}
