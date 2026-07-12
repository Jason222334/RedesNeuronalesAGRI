import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useParams, useNavigate, Link } from 'react-router-dom';
import './Login.css';

function CambiarPassword() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [nuevaContrasena, setNuevaContrasena] = useState('');
  const [confirmar, setConfirmar] = useState('');
  const [mensaje, setMensaje] = useState('');
  const [error, setError] = useState('');
  const [tokenValido, setTokenValido] = useState(true);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    const validarToken = async () => {
      try {
        await axios.get(`http://localhost:8000/api/auth/validar-token/${token}`);
        setTokenValido(true);
      } catch (err) {
        setTokenValido(false);
      } finally {
        setCargando(false);
      }
    };
    validarToken();
  }, [token]);

  const manejarSubmit = async (e) => {
    e.preventDefault();
    if (nuevaContrasena !== confirmar) {
      setError('Las contraseñas no coinciden');
      return;
    }
    
    try {
      const res = await axios.post('http://localhost:8000/api/auth/restablecer-password', {
        token,
        nueva_contrasena: nuevaContrasena
      });
      setMensaje(res.data.mensaje);
      setTokenValido(false); // Inhabilitar formulario tras éxito
      setTimeout(() => navigate('/login'), 3000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail || 'Error al restablecer contraseña');
      if (detail && detail.includes("token")) {
        setTokenValido(false);
      }
    }
  };

  if (cargando) {
    return (
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <p>Validando enlace...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!tokenValido) {
    return (
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <h1>Enlace No Válido</h1>
            <p>Este enlace ya ha sido utilizado o ha expirado por seguridad.</p>
          </div>
          {mensaje && <div className="alert alert-success">{mensaje}</div>}
          <div className="login-footer">
            <Link to="/recuperar" className="btn-primary" style={{textDecoration: 'none', display: 'block'}}>Solicitar nuevo enlace</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>Nueva Clave</h1>
          <p>Ingresa tu nueva contraseña</p>
        </div>

        <form onSubmit={manejarSubmit}>
          {mensaje && <div className="alert alert-success">{mensaje}</div>}
          {error && <div className="alert alert-error">{error}</div>}
          
          <div className="form-group">
            <label>Nueva Contraseña</label>
            <input 
              type="password" 
              required 
              placeholder="••••••••"
              value={nuevaContrasena}
              onChange={e => setNuevaContrasena(e.target.value)} 
            />
          </div>

          <div className="form-group">
            <label>Confirmar Contraseña</label>
            <input 
              type="password" 
              required 
              placeholder="••••••••"
              value={confirmar}
              onChange={e => setConfirmar(e.target.value)} 
            />
          </div>

          <button type="submit" className="btn-primary">Actualizar Contraseña</button>
        </form>

        <div className="login-footer">
          <Link to="/login" style={{color: '#2e7d32', fontWeight: 'bold', textDecoration: 'none'}}>Cancelar</Link>
        </div>
      </div>
    </div>
  );
}

export default CambiarPassword;
