import { useNavigate } from 'react-router-dom';
import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function GestionUsuarios() {
  const navigate = useNavigate();
  const [usuarioLogueado, setUsuarioLogueado] = useState(null);
  const [usuarios, setUsuarios] = useState([]);
  const [nuevoUsuario, setNuevoUsuario] = useState({ 
    nombres: '', apellidos: '', correo: '', rol: 'Usuario', estado: true, contrasena: '' 
  });
  const [idEnEdicion, setIdEnEdicion] = useState(null);

  useEffect(() => {
    const sesionStr = localStorage.getItem('sesionAgricola');
    const usr = sesionStr ? JSON.parse(sesionStr) : null;
    
    if (!usr || usr.rol !== 'Admin') {
      navigate('/login');
    } else {
      setUsuarioLogueado(usr);
      cargarUsuarios();
    }
  }, [navigate]);

  const cargarUsuarios = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/usuarios/');
      setUsuarios(res.data);
    } catch (error) {
      console.error("Error al cargar usuarios", error);
    }
  };

  const guardarUsuario = async (e) => {
    e.preventDefault();
    try {
      if (idEnEdicion) {
        await axios.put(`http://localhost:8000/api/usuarios/${idEnEdicion}`, nuevoUsuario);
        setIdEnEdicion(null);
      } else {
        await axios.post('http://localhost:8000/api/usuarios/', nuevoUsuario);
      }
      setNuevoUsuario({ nombres: '', apellidos: '', correo: '', rol: 'Usuario', estado: true, contrasena: '' });
      cargarUsuarios();
    } catch (error) {
      alert(error.response?.data?.detail || "Error al guardar usuario");
    }
  };

  const prepararEdicion = (usr) => {
    setNuevoUsuario({ 
      nombres: usr.nombres, 
      apellidos: usr.apellidos,
      correo: usr.correo,
      rol: usr.rol,
      estado: usr.estado,
      contrasena: ''
    });
    setIdEnEdicion(usr.id_usuario);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const eliminarUsuario = async (id) => {
    if(window.confirm("¿Estás seguro de eliminar este usuario?")) {
      try {
        await axios.delete(`http://localhost:8000/api/usuarios/${id}`);
        cargarUsuarios();
      } catch (error) {
        alert("Error al eliminar el usuario.");
      }
    }
  };

  // --- ESTILOS ---
  const cardStyle = {
    background: 'white', padding: '30px', borderRadius: '15px',
    boxShadow: '0 10px 25px rgba(0,0,0,0.05)', border: '1px solid #f0f0f0', marginBottom: '30px'
  };

  const cardTitleStyle = {
    marginTop: 0, color: '#2c3e50', borderBottom: '2px solid #4caf50',
    paddingBottom: '10px', display: 'inline-block', marginBottom: '20px'
  };

  const inputStyle = { 
    padding: '12px', borderRadius: '8px', border: '1px solid #ddd', width: '200px', fontSize: '0.95rem'
  };

  const btnPrimary = {
    background: 'linear-gradient(to right, #43a047, #2e7d32)', color: 'white',
    padding: '12px 25px', border: 'none', borderRadius: '8px', cursor: 'pointer',
    fontWeight: '600', textTransform: 'uppercase', fontSize: '0.85rem'
  };

  return (
    <div style={{ padding: '40px', backgroundColor: '#f8f9fa', minHeight: '100vh', fontFamily: 'Segoe UI, sans-serif' }}>
      
      <div style={{...cardStyle, borderTop: idEnEdicion ? '5px solid #fbc02d' : '5px solid #2e7d32' }}>
        <h3 style={cardTitleStyle}>
          {idEnEdicion ? `Editando Usuario ID: ${idEnEdicion}` : "Registrar Nuevo Usuario"}
        </h3>
        <form onSubmit={guardarUsuario} style={{ display: 'flex', flexWrap: 'wrap', gap: '15px', alignItems: 'flex-end' }}>
          <div>
            <label style={{display: 'block', fontSize: '0.85rem', marginBottom: '5px'}}>Nombres</label>
            <input type="text" value={nuevoUsuario.nombres} onChange={e => setNuevoUsuario({...nuevoUsuario, nombres: e.target.value})} required style={inputStyle} />
          </div>
          <div>
            <label style={{display: 'block', fontSize: '0.85rem', marginBottom: '5px'}}>Apellidos</label>
            <input type="text" value={nuevoUsuario.apellidos} onChange={e => setNuevoUsuario({...nuevoUsuario, apellidos: e.target.value})} required style={inputStyle} />
          </div>
          <div>
            <label style={{display: 'block', fontSize: '0.85rem', marginBottom: '5px'}}>Correo</label>
            <input type="email" value={nuevoUsuario.correo} onChange={e => setNuevoUsuario({...nuevoUsuario, correo: e.target.value})} required style={inputStyle} />
          </div>
          <div>
            <label style={{display: 'block', fontSize: '0.85rem', marginBottom: '5px'}}>Rol</label>
            <select value={nuevoUsuario.rol} onChange={e => setNuevoUsuario({...nuevoUsuario, rol: e.target.value})} style={inputStyle}>
              <option value="Usuario">Usuario</option>
              <option value="Admin">Administrador</option>
            </select>
          </div>
          <div>
            <label style={{display: 'block', fontSize: '0.85rem', marginBottom: '5px'}}>{idEnEdicion ? 'Contraseña (dejar vacío para no cambiar)' : 'Contraseña'}</label>
            <input type="password" value={nuevoUsuario.contrasena} onChange={e => setNuevoUsuario({...nuevoUsuario, contrasena: e.target.value})} required={!idEnEdicion} style={inputStyle} />
          </div>
          <button type="submit" style={btnPrimary}>
            {idEnEdicion ? "Guardar" : "Crear"}
          </button>
          {idEnEdicion && (
            <button type="button" onClick={() => {setIdEnEdicion(null); setNuevoUsuario({nombres:'',apellidos:'',correo:'',rol:'Usuario',estado:true,contrasena:''})}} 
              style={{ background: '#9e9e9e', color: 'white', border: 'none', padding: '12px 20px', borderRadius: '8px', cursor: 'pointer' }}>
              Cancelar
            </button>
          )}
        </form>
      </div>

      <div style={cardStyle}>
        <h3 style={cardTitleStyle}>Lista de Usuarios</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ textAlign: 'left', color: '#7f8c8d', borderBottom: '2px solid #f0f2f5' }}>
              <th style={{ padding: '15px' }}>ID</th>
              <th style={{ padding: '15px' }}>Nombre Completo</th>
              <th style={{ padding: '15px' }}>Correo</th>
              <th style={{ padding: '15px' }}>Rol</th>
              <th style={{ padding: '15px' }}>Estado</th>
              <th style={{ padding: '15px', textAlign: 'center' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {usuarios.map((u, index) => (
              <tr key={u.id_usuario} style={{ borderBottom: '1px solid #f0f2f5', backgroundColor: index % 2 === 0 ? 'white' : '#fafafa' }}>
                <td style={{ padding: '15px', fontWeight: 'bold' }}>#{u.id_usuario}</td>
                <td style={{ padding: '15px' }}>{u.nombres} {u.apellidos}</td>
                <td style={{ padding: '15px' }}>{u.correo}</td>
                <td style={{ padding: '15px' }}>
                  <span style={{ 
                    background: u.rol === 'Admin' ? '#e8f5e9' : '#e3f2fd', 
                    color: u.rol === 'Admin' ? '#2e7d32' : '#1976d2',
                    padding: '4px 8px', borderRadius: '4px', fontSize: '0.85rem', fontWeight: 'bold'
                  }}>
                    {u.rol}
                  </span>
                </td>
                <td style={{ padding: '15px' }}>
                  {u.estado ? <span style={{color: 'green'}}>● Activo</span> : <span style={{color: 'red'}}>● Inactivo</span>}
                </td>
                <td style={{ padding: '15px', textAlign: 'center' }}>
                  <button onClick={() => prepararEdicion(u)} style={{ background: '#fbc02d', border: 'none', padding: '8px 12px', borderRadius: '6px', cursor: 'pointer', marginRight: '5px' }}>Editar</button>
                  <button onClick={() => eliminarUsuario(u.id_usuario)} style={{ background: '#d32f2f', color: 'white', border: 'none', padding: '8px 12px', borderRadius: '6px', cursor: 'pointer' }}>Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
