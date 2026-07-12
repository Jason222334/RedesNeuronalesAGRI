import { useNavigate } from 'react-router-dom';
import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function GestionCultivos() {
  const navigate = useNavigate();
  const [usuario, setUsuario] = useState(null);

  useEffect(() => {
    const sesionStr = localStorage.getItem('sesionAgricola');
    const usr = sesionStr ? JSON.parse(sesionStr) : null;
    
    if (!usr || usr.rol !== 'Admin') {
      navigate('/login');
    } else {
      setUsuario(usr);
      cargarCultivos();
    }
  }, [navigate]);
  const [cultivos, setCultivos] = useState([]);
  const [nuevoCultivo, setNuevoCultivo] = useState({ nombre_cultivo: '', tiempo_estimado_cosecha_dias: '' });
  const [idEnEdicion, setIdEnEdicion] = useState(null);

  const cargarCultivos = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/cultivos/');
      setCultivos(res.data);
    } catch (error) {
      console.error("Error al cargar cultivos", error);
    }
  };

  const guardarCultivo = async (e) => {
    e.preventDefault();
    try {
      if (idEnEdicion) {
        await axios.put(`http://localhost:8000/api/cultivos/${idEnEdicion}`, nuevoCultivo);
        setIdEnEdicion(null);
      } else {
        await axios.post('http://localhost:8000/api/cultivos/', nuevoCultivo);
      }
      setNuevoCultivo({ nombre_cultivo: '', tiempo_estimado_cosecha_dias: '' });
      cargarCultivos();
    } catch (error) {
      console.error("Error al guardar", error);
    }
  };

  const prepararEdicion = (cultivo) => {
    setNuevoCultivo({ 
      nombre_cultivo: cultivo.nombre_cultivo, 
      tiempo_estimado_cosecha_dias: cultivo.tiempo_estimado_cosecha_dias 
    });
    setIdEnEdicion(cultivo.id_cultivo);
    window.scrollTo({ top: 0, behavior: 'smooth' }); // Sube suavemente para editar
  };

  const eliminarCultivo = async (id) => {
    if(window.confirm("¿Estás seguro de eliminar este cultivo?")) {
      try {
        await axios.delete(`http://localhost:8000/api/cultivos/${id}`);
        cargarCultivos();
      } catch (error) {
        alert("No se puede eliminar porque tiene datos históricos asociados.");
      }
    }
  };

  // --- ESTILOS COMPARTIDOS CON EL DASHBOARD ---
  const cardStyle = {
    background: 'white',
    padding: '30px',
    borderRadius: '15px',
    boxShadow: '0 10px 25px rgba(0,0,0,0.05)',
    border: '1px solid #f0f0f0',
    marginBottom: '30px'
  };

  const cardTitleStyle = {
    marginTop: 0,
    color: '#2c3e50',
    borderBottom: '2px solid #4caf50',
    paddingBottom: '10px',
    display: 'inline-block',
    marginBottom: '20px'
  };

  const inputStyle = { 
    padding: '12px', 
    borderRadius: '8px', 
    border: '1px solid #ddd', 
    marginRight: '15px',
    width: '250px',
    fontSize: '0.95rem'
  };

  const btnPrimary = {
    background: 'linear-gradient(to right, #43a047, #2e7d32)',
    color: 'white',
    padding: '12px 25px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: '600',
    textTransform: 'uppercase',
    fontSize: '0.85rem',
    boxShadow: '0 4px 6px rgba(46, 125, 50, 0.2)'
  };

  const btnEdit = {
    background: '#fbc02d',
    color: '#000',
    border: 'none',
    padding: '8px 15px',
    borderRadius: '6px',
    cursor: 'pointer',
    marginRight: '10px',
    fontWeight: '500'
  };

  const btnDelete = {
    background: '#d32f2f',
    color: 'white',
    border: 'none',
    padding: '8px 15px',
    borderRadius: '6px',
    cursor: 'pointer',
    fontWeight: '500'
  };

  return (
    <div style={{ padding: '40px', backgroundColor: '#f8f9fa', minHeight: '100vh', fontFamily: 'Segoe UI, sans-serif' }}>
      
      {/* FORMULARIO DE REGISTRO */}
      <div style={{...cardStyle, borderTop: idEnEdicion ? '5px solid #fbc02d' : '5px solid #2e7d32' }}>
        <h3 style={cardTitleStyle}>
          {idEnEdicion ? `Editando Cultivo: ${idEnEdicion}` : "Registrar Nuevo Cultivo"}
        </h3>
        <form onSubmit={guardarCultivo} style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
          <input 
            type="text" 
            placeholder="Nombre del Cultivo (Arroz, Maíz...)" 
            value={nuevoCultivo.nombre_cultivo} 
            onChange={e => setNuevoCultivo({...nuevoCultivo, nombre_cultivo: e.target.value})} 
            required 
            style={inputStyle} 
          />
          <input 
            type="number" 
            placeholder="Días para cosecha" 
            value={nuevoCultivo.tiempo_estimado_cosecha_dias} 
            onChange={e => setNuevoCultivo({...nuevoCultivo, tiempo_estimado_cosecha_dias: e.target.value})} 
            required 
            style={{...inputStyle, width: '180px'}} 
          />
          <button type="submit" style={btnPrimary}>
            {idEnEdicion ? "Guardar Cambios" : "Añadir Cultivo"}
          </button>
          {idEnEdicion && (
            <button 
              type="button" 
              onClick={() => {setIdEnEdicion(null); setNuevoCultivo({nombre_cultivo: '', tiempo_estimado_cosecha_dias: ''})}}
              style={{ background: '#9e9e9e', color: 'white', border: 'none', padding: '12px 20px', borderRadius: '8px', cursor: 'pointer' }}
            >
              Cancelar
            </button>
          )}
        </form>
      </div>

      {/* TABLA DE CULTIVOS */}
      <div style={cardStyle}>
        <h3 style={cardTitleStyle}>Catálogo de Cultivos Registrados</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
          <thead>
            <tr style={{ textAlign: 'left', color: '#7f8c8d', borderBottom: '2px solid #f0f2f5' }}>
              <th style={{ padding: '15px' }}>ID</th>
              <th style={{ padding: '15px' }}>Nombre del Cultivo</th>
              <th style={{ padding: '15px' }}>Ciclo de Vida (Días)</th>
              <th style={{ padding: '15px', textAlign: 'center' }}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {cultivos.map((c, index) => (
              <tr key={c.id_cultivo} style={{ borderBottom: '1px solid #f0f2f5', backgroundColor: index % 2 === 0 ? 'white' : '#fafafa' }}>
                <td style={{ padding: '15px', fontWeight: 'bold', color: '#2e7d32' }}>#{c.id_cultivo}</td>
                <td style={{ padding: '15px', fontSize: '1.05rem' }}>{c.nombre_cultivo}</td>
                <td style={{ padding: '15px' }}>{c.tiempo_estimado_cosecha_dias} días</td>
                <td style={{ padding: '15px', textAlign: 'center' }}>
                  <button onClick={() => prepararEdicion(c)} style={btnEdit}>Editar</button>
                  <button onClick={() => eliminarCultivo(c.id_cultivo)} style={btnDelete}>Eliminar</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
