import axios from 'axios';
import { API_URL } from '../../../config/config'; // Asegúrate que apunta al backend, no al gateway

export const crearNuevoUsuario = async (usuarioData) => {
  const token = localStorage.getItem('token');

  const response = await axios.post(`${API_URL}/usuarios/crear`, usuarioData, {
    headers: {
      Authorization: `Bearer ${token}`,    
      'Content-Type': 'application/json'
    }
  });

  return response.data;
};
