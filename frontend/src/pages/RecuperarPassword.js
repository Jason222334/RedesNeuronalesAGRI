import React, { useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import './Login.css';

function RecuperarPassword() {
  const [correo, setCorreo] = useState('');
  const [mensaje, setMensaje] = useState('');
  const [error, setError] = useState('');
  const [debugLink, setDebugLink] = useState('');

  const manejarSubmit = async (e) => {
    e.preventDefault();
    setMensaje('');
    setError('');
    setDebugLink('');
    
    try {
      const res = await axios.post('http://localhost:8000/api/auth/solicitar-recuperacion', { correo });
      setMensaje(res.data.mensaje);
      if (res.data.link_debug) {
        setDebugLink(res.data.link_debug);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al solicitar recuperación');
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>Recuperar</h1>
          <p>Ingresa tu correo para enviarte un enlace</p>
        </div>

        <form onSubmit={manejarSubmit}>
          {mensaje && <div className="alert alert-success">{mensaje}</div>}
          {error && <div className="alert alert-error">{error}</div>}
          
          <div className="form-group">
            <label>Correo Electrónico</label>
            <input 
              type="email" 
              required 
              placeholder="correo@ejemplo.com"
              value={correo}
              onChange={e => setCorreo(e.target.value)} 
            />
          </div>

          <button type="submit" className="btn-primary">Enviar Instrucciones</button>
        </form>

        {debugLink && (
          <div style={{ marginTop: '20px', padding: '10px', background: '#fff9c4', borderRadius: '8px', fontSize: '0.8rem' }}>
            <strong>DEBUG: Enlace generado (simulación de correo):</strong><br/>
            <a href={debugLink}>{debugLink}</a>
          </div>
        )}

        <div className="login-footer">
          <Link to="/login" style={{color: '#2e7d32', fontWeight: 'bold', textDecoration: 'none'}}>Volver al Inicio</Link>
        </div>
      </div>
    </div>
  );
}

export default RecuperarPassword;
