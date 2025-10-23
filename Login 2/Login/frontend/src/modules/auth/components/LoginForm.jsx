import React, { useState } from 'react';
import { Row, Col, Form, Input, Button, Alert, Typography, Card } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';
import '../styles/login.css';
import { Base64 } from 'js-base64';
import logo from '../../../assets/img/logo1.png';
import poweredLogo from '../../../assets/img/powe.png';
import backgroundImage from '../../../assets/img/Fondo-inicio.png';

import {API_URL_GATEWAY} from '../config/config';

const { Title } = Typography;

const LoginForm = () => {   // 👈 Aquí empieza tu componente
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const navigate = useNavigate();   // 👈 También el navigate

  const onFinish = async (values) => {
    setLoading(true);
    setErrorMessage('');
  
    try {
      const response = await authService.login(values.username, values.password);
  
      if (response && response.data.access_token) {
        const token = response.data.access_token;
        const userData = response.data.usuario;
 
        // Construir JSON y codificar en Base64
        const dataToSend = {
          idUsuario: userData.idUsuario,
          nombre: userData.nombre,
          token: token
        };
        const base64Data = Base64.encode(JSON.stringify(dataToSend));
  
        // Redirigir al Gateway
        const url = `${API_URL_GATEWAY}/home?data=${encodeURIComponent(base64Data)}`;
        window.location.href = url;
      } else {
        setErrorMessage('Credenciales inválidas.');
      }
    } catch (error) {
      console.error('Login error:', error);
  
      if (error.response) {
        if (error.response.status === 401) {
          setErrorMessage(error.response.data.detail || 'Usuario o contraseña incorrectos.');
        } else {
          setErrorMessage('Error en el servidor.');
        }
      } else {
        setErrorMessage('No se pudo conectar al servidor.');
      }
    } finally {
      setLoading(false);
    }
  };
  
  
  

  return (
    <div className="login-container">
      <div className="login-background-overlay"></div>
      
      {/* Elementos de fondo animados */}
      <div className="floating-shapes">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
        <div className="shape shape-4"></div>
        <div className="shape shape-5"></div>
      </div>

      {/*formulario */}
      <div className="login-right-section">
        <Card className="login-card">
          
          <div className="login-header">
            <div className="login-title-section">
              <Title level={2} className="login-title">
                {/* <span className="title-gradient">¡Hola!</span> */}
                <strong className="title-gradient">¡Hola!</strong>
              </Title>
              <p className="login-subtitle">
                <span className="subtitle-animated">Nos encanta tenerte por acá</span>
              </p>
            </div>
          </div>

          {errorMessage && (
            <Alert 
              message={errorMessage} 
              type="error" 
              showIcon 
              className="error-alert animated-alert"
            />
          )}

          <Form
            name="login"
            initialValues={{ remember: true }}
            onFinish={onFinish}
            layout="vertical"
            requiredMark={false}
            className="login-form"
          >
            <Form.Item
              name="username"
              label={
                <span className="label-animated">
                  Usuario
                </span>
              }
              rules={[{ required: true, message: 'Por favor ingrese su usuario' }]}
              className="form-item-custom"
            >
              <Input 
                prefix={<UserOutlined className="input-icon" />} 
                placeholder="Ingrese su usuario" 
                size="large"
                className="input-custom input-animated"
              />
            </Form.Item>

            <Form.Item
              name="password"
              label={
                <span className="label-animated">
                  
                  Contraseña
                </span>
              }
              rules={[{ required: true, message: 'Por favor ingrese su contraseña' }]}
              className="form-item-custom"
            >
              <Input.Password 
                prefix={<LockOutlined className="input-icon" />} 
                placeholder="Ingrese su contraseña" 
                size="large"
                className="input-custom input-animated"
              />
            </Form.Item>

            <Form.Item className="submit-section">
              <Button 
                type="primary" 
                htmlType="submit" 
                size="large" 
                loading={loading}
                className="login-button button-animated"
              >
                <span className="button-content">
                  {loading ? (
                    <>
                      <span className="loading-spinner"></span>
                      Ingresando...
                    </>
                  ) : (
                    <>
                      Ingresar 
                    </>
                  )}
                </span>
              </Button>
            </Form.Item>
          </Form>

          <div className="mensajeFinal">
             <p className="benefits-title-left">
               <strong>Nuestra herramienta de</strong><br />
               <strong>Co-creación</strong>
             </p>
             <ul className="benefits-list-right">
               <li className="benefit-item blue">Gestión inteligente</li>
               <li className="benefit-item blue">Resultados efectivos</li>
               <li className="benefit-item blue">Trabajo colaborativo</li>
             </ul>
          </div>


          <div className="powered-by">
            <div className="powered-content">
              <a 
                href="https://www.systemgroupglobal.com/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="powered-logo-link"
              >
                <img src={poweredLogo} alt="Powered by SystemGroup" className="powered-logo" />
              </a>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default LoginForm;
