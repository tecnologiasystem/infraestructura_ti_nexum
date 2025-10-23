import React, { useState } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { Layout } from 'antd';
import { AuthProvider } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import AppRouter from './routes/AppRouter';

const { Content } = Layout;

const App = () => {

  return (
    <BrowserRouter>
      <AuthProvider>
        <Layout style={{ minHeight: '100vh', flexDirection: 'row', background: '#e6f0ff' }}>
          <Sidebar />
          <Layout
            style={{
              transition: 'margin-left 0.3s ease',
              background: '#e6f0ff',
              width: '100%',
            }}
          >
              <AppRouter />
          </Layout>
        </Layout>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
