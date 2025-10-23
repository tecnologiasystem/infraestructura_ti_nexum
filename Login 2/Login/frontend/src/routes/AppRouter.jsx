import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LoginForm from '../modules/auth/components/LoginForm';
import AccesoDenegado from '../modules/auth/components/AccesoDenegado';
import ProtectedRoute from '../modules/auth/components/ProtectedRoute';
import CrearUsuario from '../modules/creacion/components/CrearUsuario';

function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Ruta pública: Login */}
        <Route path="/" element={<LoginForm />} />
        <Route path="/c" element={<CrearUsuario />} />
        
        {/* Ruta pública: Acceso Denegado */}
        <Route path="/acceso-denegado" element={<AccesoDenegado />} />
        
        {/* Ruta protegida de ejemplo */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <div>Dashboard Privado</div> {/* Aquí luego pones tu Dashboard real */}
            </ProtectedRoute>
          }
        />
        {/* Ruta comodín para cualquier otra no definida */}
        <Route path="*" element={<Navigate to="/acceso-denegado" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default AppRouter;
