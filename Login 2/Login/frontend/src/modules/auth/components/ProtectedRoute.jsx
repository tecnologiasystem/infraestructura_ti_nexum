import React from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');

  const isAuthenticated = token && token !== 'undefined' && token !== 'null' && token.trim() !== '';

  if (!isAuthenticated) {
    return <Navigate to="/acceso-denegado" replace />;
  }

  return children;
};

export default ProtectedRoute;
