import axios from 'axios';
import { API_URL } from '../config/config';

const login = async (username, password) => {
  const response = await axios.post(`${API_URL}/auth/login`, { username, password });
  return response;  // No .data aquí, en onFinish se maneja
};

export default { login };
