// Configuración dinámica de URLs para Backend FastAPI y Streamlit
export const API_BASE_URL = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/$/, '');
export const STREAMLIT_URL = (process.env.REACT_APP_STREAMLIT_URL || 'http://localhost:8501').replace(/\/$/, '');
