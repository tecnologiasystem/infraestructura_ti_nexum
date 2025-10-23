import React from 'react';
import { Button, Result } from 'antd';
import { useNavigate } from 'react-router-dom';
import '../styles/login.css'; // Sigue usando tu fuente Montserrat

const AccesoDenegado = () => {
  const navigate = useNavigate();

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #000F9F, #36A2DA)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        flexDirection: 'column',
        fontFamily: 'Montserrat, sans-serif',
        padding: '20px'
      }}
    >
      <Result
        status="403"
        title={
          <div style={{ fontSize: '40px', fontWeight: 'bold', fontFamily: 'Montserrat' }}>
            🚫 Acceso Denegado
          </div>
        }
        subTitle={
          <div style={{ fontSize: '20px', fontWeight: '600', color:'#333333', fontFamily: 'Montserrat' }}>
            No tienes permiso para acceder a esta página.
          </div>
        }
        extra={
          <Button
            type="primary"
            size="large"
            style={{
              backgroundColor: '#662480',
              borderColor: '#662480',
              fontWeight: '700',
              fontFamily: 'Montserrat',
              fontSize: '18px'
            }}
            onClick={() => navigate('/')}
          >
            Volver al Login
          </Button>
        }
      />
    </div>
  );
};

export default AccesoDenegado;
