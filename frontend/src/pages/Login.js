import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate, Link } from 'react-router-dom';
import './Login.css';

function Login() {
  const [esLogin, setEsLogin] = useState(true);
  const [datos, setDatos] = useState({ 
    correo: '', 
    contrasena: '', 
    nombres: '', 
    apellidos: '' 
  });
  const [error, setError] = useState('');
  const [mensaje, setMensaje] = useState('');
  const navigate = useNavigate();

  const manejarSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMensaje('');
    
    try {
      if (esLogin) {
        const res = await axios.post('http://localhost:8000/api/auth/login', {
          correo: datos.correo,
          contrasena: datos.contrasena
        });
        localStorage.setItem('sesionAgricola', JSON.stringify(res.data));
        sessionStorage.removeItem('visitaRegistrada');
        navigate('/');
      } else {
        await axios.post('http://localhost:8000/api/auth/registrar', datos);
        setMensaje('Registro exitoso. Ahora puedes iniciar sesión.');
        setEsLogin(true);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Ocurrió un error inesperado');
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>AGRO-JEQUETE</h1>
          <p>{esLogin ? 'Gestión Inteligente del Valle' : 'Crea tu cuenta agrícola'}</p>
        </div>

        <form onSubmit={manejarSubmit}>
          {mensaje && <div className="alert alert-success">{mensaje}</div>}
          {error && <div className="alert alert-error">{error}</div>}
          
          {!esLogin && (
            <>
              <div className="form-group">
                <label>Nombres</label>
                <input type="text" required placeholder="Ej. Juan"
                  onChange={e => setDatos({...datos, nombres: e.target.value})} />
              </div>
              <div className="form-group">
                <label>Apellidos</label>
                <input type="text" required placeholder="Ej. Pérez"
                  onChange={e => setDatos({...datos, apellidos: e.target.value})} />
              </div>
            </>
          )}

          <div className="form-group">
            <label>Correo Electrónico</label>
            <input type="email" required placeholder="correo@ejemplo.com"
              onChange={e => setDatos({...datos, correo: e.target.value})} />
          </div>

          <div className="form-group">
            <label>Contraseña</label>
            <input type="password" required placeholder="••••••••"
              onChange={e => setDatos({...datos, contrasena: e.target.value})} />
          </div>

          {esLogin && (
            <div className="forgot-password">
              <Link to="/recuperar">¿Olvidaste tu contraseña?</Link>
            </div>
          )}

          <button type="submit" className="btn-primary">
            {esLogin ? 'Entrar al Dashboard' : 'Registrarme ahora'}
          </button>
        </form>

        <div className="login-footer">
          <p>
            {esLogin ? '¿Aún no tienes cuenta?' : '¿Ya eres miembro?'}
            <button onClick={() => { setEsLogin(!esLogin); setError(''); setMensaje(''); }}>
              {esLogin ? 'Regístrate' : 'Inicia sesión'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
