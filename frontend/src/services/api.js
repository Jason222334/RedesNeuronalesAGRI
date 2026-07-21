import axios from 'axios';
import { API_BASE_URL } from '../config';

// Configuración base dinámica
const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
});

// Exportamos todas las funciones que se comunican con el backend
export const obtenerCultivos = () => api.get('/cultivos/');
export const crearCultivo = (datos) => api.post('/cultivos/', datos);
export const obtenerPrediccion = (temp, prec, trans) => api.post(`/prediccion/precio?temp=${temp}&prec=${prec}&trans=${trans}`);

export default api;