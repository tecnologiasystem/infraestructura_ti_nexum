import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, Alert, Modal, Space } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, IdcardOutlined } from '@ant-design/icons';
import { crearNuevoUsuario } from '../services/usuarioService';
import authService from '../../auth/services/authService';
import { useNavigate } from 'react-router-dom';
import '../styles/creaUsuario.css';

const { Title } = Typography;

const CrearUsuario = () => {
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [authModalVisible, setAuthModalVisible] = useState(true);
  const [authLoading, setAuthLoading] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);

  const navigate = useNavigate();
  const [authForm] = Form.useForm();
  const [form] = Form.useForm();

  const onFinishAuth = async (values) => {
    setAuthLoading(true);
    try {
      const response = await authService.login(values.username, values.password);

      if (response && response.data.access_token) {
        const token = response.data.access_token;
        localStorage.setItem('token', token);
        const userData = response.data.usuario;
        localStorage.setItem('userData', JSON.stringify(userData));

        if (userData.idRol === 1) {
          setAuthModalVisible(false);
          setAuthenticated(true);
        } else {
          navigate('/acceso-denegado');
        }
      } else {
        navigate('/acceso-denegado');
      }
    } catch (error) {
      console.error(error);
      navigate('/acceso-denegado');
    } finally {
      setAuthLoading(false);
    }
  };

  const onCancelAuth = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userData');
    setAuthenticated(false);
    setAuthModalVisible(false);
    navigate('/');
  };

  const onLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userData');
    setAuthenticated(false);
    setAuthModalVisible(true);
    form.resetFields();
  };

  const onFinish = async (values) => {
    setLoading(true);
    setErrorMessage('');
    setSuccessMessage('');

    try {
      const payload = {
        nombreCompleto: values.nombreCompleto,
        username: values.username,
        password: values.password,
        correo: values.correo,
        cedula: values.cedula,
        idRol: 3,           // Rol por defecto
        area: "0",          // 🔵 Nuevo: area en "0"
        cargo: "0"          // 🔵 Nuevo: cargo en "0"
      };

      console.log("Payload que mando al backend:", payload);

      await crearNuevoUsuario(payload);
      setSuccessMessage('Usuario creado exitosamente.');
      form.resetFields();
    } catch (error) {
      console.error(error);
      if (error.response && error.response.data && error.response.data.detail) {
        const errorDetail = error.response.data.detail;
        if (Array.isArray(errorDetail)) {
          const firstError = errorDetail[0];
          setErrorMessage(firstError.msg || 'Error de validación.');
        } else if (typeof errorDetail === 'string') {
          setErrorMessage(errorDetail);
        } else {
          setErrorMessage('Error desconocido.');
        }
      } else {
        setErrorMessage('Error al crear usuario.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="crearusuario-container">
      <Modal
        open={authModalVisible}
        title="Autenticación requerida"
        footer={null}
        closable={false}
        centered
      >
        <Form
          form={authForm}
          layout="vertical"
          onFinish={onFinishAuth}
        >
          <Form.Item
            name="username"
            label="Usuario"
            rules={[{ required: true, message: 'Ingrese su usuario' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="Usuario" />
          </Form.Item>

          <Form.Item
            name="password"
            label="Contraseña"
            rules={[{ required: true, message: 'Ingrese su contraseña' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="Contraseña" />
          </Form.Item>

          <Form.Item>
            <Space style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Button type="default" onClick={onCancelAuth} block>
                Cancelar
              </Button>
              <Button type="primary" htmlType="submit" loading={authLoading} block>
                Ingresar
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {!authModalVisible && authenticated && (
        <>
          <div style={{ textAlign: 'right', marginBottom: 16 }}>
            <Button type="link" onClick={onLogout}>
              Cerrar Sesión
            </Button>
          </div>
          <Card className="crearusuario-card">
            <Title level={2} style={{ textAlign: 'center', marginBottom: '20px' }}>
              Crear Usuario
            </Title>

            {errorMessage && <Alert message={errorMessage} type="error" showIcon style={{ marginBottom: 24 }} />}
            {successMessage && <Alert message={successMessage} type="success" showIcon style={{ marginBottom: 24 }} />}

            <Form layout="vertical" form={form} onFinish={onFinish}>
              <Form.Item
                name="nombreCompleto"
                label="Nombre Completo"
                rules={[{ required: true, message: 'Por favor ingrese el nombre completo' }]}
              >
                <Input prefix={<UserOutlined />} placeholder="Nombre Completo" size="large" />
              </Form.Item>

              <Form.Item
                name="username"
                label="Usuario"
                rules={[{ required: true, message: 'Por favor ingrese un usuario' }]}
              >
                <Input prefix={<UserOutlined />} placeholder="Usuario" size="large" />
              </Form.Item>

              <Form.Item
                name="password"
                label="Contraseña"
                rules={[{ required: true, message: 'Por favor ingrese una contraseña' }]}
              >
                <Input.Password prefix={<LockOutlined />} placeholder="Contraseña" size="large" />
              </Form.Item>

              <Form.Item
                name="correo"
                label="Correo"
                rules={[{ required: true, type: 'email', message: 'Ingrese un correo válido' }]}
              >
                <Input prefix={<MailOutlined />} placeholder="Correo" size="large" />
              </Form.Item>

              <Form.Item
                name="cedula"
                label="Cédula"
                rules={[{ required: true, message: 'Ingrese la cédula' }]}
              >
                <Input prefix={<IdcardOutlined />} placeholder="Cédula" size="large" />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" block size="large" loading={loading}>
                  Crear Usuario
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </>
      )}
    </div>
  );
};

export default CrearUsuario;
