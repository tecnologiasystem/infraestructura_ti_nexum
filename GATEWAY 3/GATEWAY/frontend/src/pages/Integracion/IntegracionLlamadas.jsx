import React, { useEffect, useState } from "react";
import {
    Table, Input, Button, DatePicker, Space,
    Spin, message, Divider, Switch
} from "antd";
import axios from "axios";
import dayjs from "dayjs";
import { API_URL_GATEWAY } from "../../config";

const ImportarLlamadas = () => {
    const [modoImportar, setModoImportar] = useState(false);
    const [cargando, setCargando] = useState(false);

    // Datos llamadas
    const [llamadas, setLlamadas] = useState([]);
    const [filtros, setFiltros] = useState({});

    // Datos importación
    const [fechaInicio, setFechaInicio] = useState(null);
    const [fechaFin, setFechaFin] = useState(null);
    const [resultado, setResultado] = useState([]);

    // Columnas
    const columnasLlamadas = [
        { title: "Agente", dataIndex: "agent_name", key: "agent_name" },
        { title: "Fecha", dataIndex: "date_call", key: "date_call" },
        { title: "Teléfono", dataIndex: "telephone", key: "telephone" },
        { title: "Campaña", dataIndex: "campaign_name", key: "campaign_name" },
        { title: "Estado", dataIndex: "status_name", key: "status_name" },
        { title: "Duración", dataIndex: "time_sec", key: "time_sec" },
        { title: "Comentarios", dataIndex: "comments", key: "comments" },
    ];

    const columnasImportacion = [
        { title: "Fecha", dataIndex: "fecha", key: "fecha" },
        { title: "Filas Insertadas", dataIndex: "filas_insertadas", key: "filas_insertadas" },
    ];

    // Obtener llamadas
    const obtenerLlamadas = async () => {
        setCargando(true);
        try {
            const params = {
                ...filtros,
                start_date: filtros.start_date ? dayjs(filtros.start_date).toISOString() : undefined,
                end_date: filtros.end_date ? dayjs(filtros.end_date).toISOString() : undefined,
            };
            const res = await axios.get(`${API_URL_GATEWAY}/gateway/contacto/reporteLlamadas`, { params });
            setLlamadas(res.data);
        } catch (err) {
            console.error(err);
            message.error("Error al consultar llamadas.");
        } finally {
            setCargando(false);
        }
    };

    useEffect(() => {
        if (!modoImportar) obtenerLlamadas();
    }, [modoImportar]);

    const importar = async () => {
        if (!fechaInicio || !fechaFin) {
            return message.warning("Selecciona ambas fechas.");
        }

        setCargando(true);
        try {
            const params = {
                fecha_inicio: dayjs(fechaInicio).toISOString(),
                fecha_fin: dayjs(fechaFin).toISOString(),
            };
            const res = await axios.get(`${API_URL_GATEWAY}/gateway/contacto/importar`, { params });
            setResultado(res.data);
            message.success("Importación completada.");
        } catch (err) {
            console.error(err);
            message.error("Error al importar llamadas.");
        } finally {
            setCargando(false);
        }
    };

    const actualizarFiltro = (clave, valor) => {
        setFiltros({ ...filtros, [clave]: valor });
    };

    return (
        <div style={{ padding: 20 }}>
            <h1> {modoImportar ? "Importar" : "Consultar"}</h1>

            <div style={{ marginBottom: 20 }}>
                <span style={{ marginRight: 8 }}>Modo:</span>
                <Switch
                    checked={modoImportar}
                    onChange={setModoImportar}
                    checkedChildren="Importar"
                    unCheckedChildren="Consultar"
                />
            </div>

            {!modoImportar ? (
                <>
                    <Space wrap style={{ marginBottom: 16 }}>
                        <Input placeholder="Nombre Agente" onChange={(e) => actualizarFiltro("agent_name", e.target.value)} />
                        <Input placeholder="Teléfono" onChange={(e) => actualizarFiltro("telephone", e.target.value)} />
                        <DatePicker showTime placeholder="Desde" onChange={(v) => actualizarFiltro("start_date", v)} />
                        <DatePicker showTime placeholder="Hasta" onChange={(v) => actualizarFiltro("end_date", v)} />
                        <Button type="primary" onClick={obtenerLlamadas}>Buscar</Button>
                    </Space>

                    <Spin spinning={cargando}>
                        <Table
                            columns={columnasLlamadas}
                            dataSource={llamadas.map((item, i) => ({ ...item, key: i }))}
                            scroll={{ x: "max-content" }}
                            pagination={{ pageSize: 10 }}
                        />
                    </Spin>
                </>
            ) : (
                <>
                    <Space style={{ marginBottom: 16 }}>
                        <DatePicker showTime onChange={(v) => setFechaInicio(v)} placeholder="Fecha inicio" />
                        <DatePicker showTime onChange={(v) => setFechaFin(v)} placeholder="Fecha fin" />
                        <Button type="primary" onClick={importar} loading={cargando}>
                            Importar
                        </Button>
                    </Space>

                    <Spin spinning={cargando}>
                        <Table
                            columns={columnasImportacion}
                            dataSource={resultado.map((item, i) => ({ ...item, key: i }))}
                            pagination={false}
                        />
                    </Spin>
                </>
            )}
        </div>
    );
};

export default ImportarLlamadas;
