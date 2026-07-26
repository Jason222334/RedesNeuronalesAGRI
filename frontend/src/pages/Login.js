import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';
import { API_BASE_URL } from '../config';
import { useThemeAndLang } from '../context/ThemeAndLangContext';
import './Login.css';

function Login() {
  const { lang, setLang, theme, toggleTheme, t } = useThemeAndLang();
  const [esLogin, setEsLogin] = useState(true);
  const [datos, setDatos] = useState({ 
    correo: '', 
    contrasena: '', 
    nombres: '', 
    apellidos: '' 
  });
  const [error, setError] = useState('');
  const [mensaje, setMensaje] = useState('');
  const [cargando, setCargando] = useState(false);
  const navigate = useNavigate();
  const isDark = theme === 'dark';

  const manejarSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMensaje('');
    setCargando(true);
    
    try {
      if (esLogin) {
        const res = await axios.post(`${API_BASE_URL}/api/auth/login`, {
          correo: datos.correo,
          contrasena: datos.contrasena
        });
        localStorage.setItem('sesionAgricola', JSON.stringify(res.data));
        sessionStorage.removeItem('visitaRegistrada');
        navigate('/');
      } else {
        await axios.post(`${API_BASE_URL}/api/auth/registrar`, datos);
        setMensaje('Registro exitoso. Ahora puedes iniciar sesión.');
        setEsLogin(true);
      }
    } catch (err) {
      if (!err.response) {
        setError(`No se pudo conectar al servidor (${API_BASE_URL}). Verifica que el backend en Render esté activo.`);
      } else {
        setError(err.response?.data?.detail || `Error ${err.response.status}: ${err.response.statusText}`);
      }
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="login-container" style={{ position: 'relative' }}>
      {/* CONTROLES SUPERIORES DE TEMA E IDIOMA */}
      <div style={{ position: 'absolute', top: '20px', right: '20px', display: 'flex', gap: '10px', alignItems: 'center' }}>
        <button 
          onClick={() => setLang(lang === 'es' ? 'en' : 'es')} 
          style={{ background: isDark ? '#1e293b' : 'white', color: isDark ? '#f8fafc' : '#333', border: '1px solid #ccc', padding: '6px 12px', borderRadius: '20px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.85rem' }}
        >
          {lang === 'es' ? '🇪🇸 ES' : '🇬🇧 EN'}
        </button>
        <button 
          onClick={toggleTheme} 
          style={{ background: isDark ? '#1e293b' : 'white', color: isDark ? '#f8fafc' : '#333', border: '1px solid #ccc', padding: '6px 12px', borderRadius: '20px', cursor: 'pointer', fontWeight: 'bold', fontSize: '0.85rem' }}
        >
          {isDark ? '☀️ Claro' : '🌙 Oscuro'}
        </button>
      </div>

      <div className="login-card">
        <div className="login-header">
          <h1>{t('loginTitle')}</h1>
          <p>{esLogin ? t('loginSubtitle') : t('registerSubtitle')}</p>
        </div>

        <form onSubmit={manejarSubmit}>
          {mensaje && <div className="alert alert-success">{mensaje}</div>}
          {error && <div className="alert alert-error">{error}</div>}
          
          {!esLogin && (
            <>
              <div className="form-group">
                <label>{t('names')}</label>
                <input type="text" required placeholder="Ej. Juan"
                  onChange={e => setDatos({...datos, nombres: e.target.value})} />
              </div>
              <div className="form-group">
                <label>{t('lastnames')}</label>
                <input type="text" required placeholder="Ej. Pérez"
                  onChange={e => setDatos({...datos, apellidos: e.target.value})} />
              </div>
            </>
          )}

          <div className="form-group">
            <label>{t('email')}</label>
            <input type="email" required placeholder="correo@ejemplo.com"
              onChange={e => setDatos({...datos, correo: e.target.value})} />
          </div>

          <div className="form-group">
            <label>{t('password')}</label>
            <input type="password" required placeholder="••••••••"
              onChange={e => setDatos({...datos, contrasena: e.target.value})} />
          </div>

          {esLogin && (
            <div className="forgot-password">
              <Link to="/recuperar">{t('forgotPassword')}</Link>
            </div>
          )}

          <button type="submit" className="btn-primary" disabled={cargando}>
            {cargando ? t('connecting') : (esLogin ? t('btnLogin') : t('btnRegister'))}
          </button>
        </form>

        <div className="login-footer">
          <p>
            {esLogin ? t('noAccount') : t('haveAccount')}
            <button onClick={() => { setEsLogin(!esLogin); setError(''); setMensaje(''); }}>
              {esLogin ? t('registerNow') : t('loginNow')}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
