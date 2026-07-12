import axios from 'axios';

// Configuración base. Aquí pones la URL de tu backend en FastAPI
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

// Exportamos todas las funciones que se comunican con el backend
export const obtenerCultivos = () => api.get('/cultivos/');
export const crearCultivo = (datos) => api.post('/cultivos/', datos);
export const obtenerPrediccion = (temp, prec, trans) => api.post(`/prediccion/precio?temp=${temp}&prec=${prec}&trans=${trans}`);

export default api;