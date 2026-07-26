import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { API_BASE_URL } from '../config';
import { useThemeAndLang } from '../context/ThemeAndLangContext';

export default function Auditoria() {
  const { t, theme } = useThemeAndLang();
  const isDark = theme === 'dark';
  const navigate = useNavigate();
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState([]);
  const [fechaConsulta, setFechaConsulta] = useState(new Date().toISOString().split('T')[0]);
  const [visitasDia, setVisitasDia] = useState(0);

  useEffect(() => {
    const sesionStr = localStorage.getItem('sesionAgricola');
    const usr = sesionStr ? JSON.parse(sesionStr) : null;
    
    if (!usr || usr.rol !== 'Admin') {
      navigate('/login');
    } else {
      cargarDatos();
    }
  }, [navigate]);

  const cargarDatos = async () => {
    try {
      const resLogs = await axios.get(`${API_BASE_URL}/api/auditoria/`);
      setLogs(resLogs.data);
      const resStats = await axios.get(`${API_BASE_URL}/api/auditoria/visitas/stats`);
      setStats(resStats.data.reverse()); // Orden cronológico para el gráfico
      consultarVisitasDia(fechaConsulta);
    } catch (error) {
      console.error("Error al cargar auditoría", error);
    }
  };

  const consultarVisitasDia = async (fecha) => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/auditoria/visitas/diarias?fecha=${fecha}`);
      setVisitasDia(res.data.total_visitas);
    } catch (error) {
      console.error("Error al consultar visitas", error);
    }
  };

  const manejarCambioFecha = (e) => {
    setFechaConsulta(e.target.value);
    consultarVisitasDia(e.target.value);
  };

  const cardStyle = {
    background: isDark ? '#1e293b' : 'white',
    padding: '25px', borderRadius: '15px',
    boxShadow: isDark ? '0 10px 25px rgba(0,0,0,0.3)' : '0 10px 25px rgba(0,0,0,0.05)',
    border: isDark ? '1px solid #334155' : '1px solid #f0f0f0',
    color: isDark ? '#f8fafc' : '#2c3e50',
    marginBottom: '30px'
  };

  const cardTitleStyle = {
    marginTop: 0, color: isDark ? '#4ade80' : '#2c3e50', borderBottom: '2px solid #4caf50',
    paddingBottom: '10px', display: 'inline-block', marginBottom: '20px'
  };

  return (
    <div style={{ padding: '40px', backgroundColor: isDark ? '#0f172a' : '#f8f9fa', color: isDark ? '#f8fafc' : '#2c3e50', minHeight: '100vh', fontFamily: 'Segoe UI, sans-serif' }}>
      <h1 style={{ color: '#1b5e20', marginBottom: '30px' }}>Centro de Monitoreo y Auditoría</h1>

      <div style={{ display: 'flex', gap: '25px', marginBottom: '30px' }}>
        {/* INDICADOR DE VISITAS DIARIAS */}
        <div style={{ ...cardStyle, flex: 1, textAlign: 'center' }}>
          <h3 style={cardTitleStyle}>Visitas Diarias</h3>
          <div style={{ marginBottom: '15px' }}>
            <input type="date" value={fechaConsulta} onChange={manejarCambioFecha} 
              style={{ padding: '8px', borderRadius: '6px', border: '1px solid #ddd' }} />
          </div>
          <div style={{ fontSize: '3rem', fontWeight: 'bold', color: '#2e7d32' }}>
            {visitasDia}
          </div>
          <p style={{ color: '#666', margin: 0 }}>Visitas registradas el {fechaConsulta}</p>
        </div>

        {/* GRÁFICO DE TENDENCIA */}
        <div style={{ ...cardStyle, flex: 2 }}>
          <h3 style={cardTitleStyle}>Tendencia de Visitas (Últimos 7 días)</h3>
          <div style={{ width: '100%', height: 200 }}>
            <ResponsiveContainer>
              <BarChart data={stats}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="fecha" tick={{fontSize: 10}} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="visitas" fill="#4caf50" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* BITÁCORA DE SUCESOS */}
      <div style={cardStyle}>
        <h3 style={cardTitleStyle}>Historial de Actividad del Sistema</h3>
        <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead style={{ position: 'sticky', top: 0, background: 'white', zIndex: 1 }}>
              <tr style={{ textAlign: 'left', color: '#7f8c8d', borderBottom: '2px solid #f0f2f5' }}>
                <th style={{ padding: '15px' }}>Fecha y Hora</th>
                <th style={{ padding: '15px' }}>Usuario</th>
                <th style={{ padding: '15px' }}>Módulo</th>
                <th style={{ padding: '15px' }}>Acción</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log, index) => (
                <tr key={log.id} style={{ borderBottom: '1px solid #f0f2f5', backgroundColor: index % 2 === 0 ? 'white' : '#fafafa' }}>
                  <td style={{ padding: '15px', color: '#666', fontSize: '0.9rem' }}>
                    {new Date(log.fecha).toLocaleString()}
                  </td>
                  <td style={{ padding: '15px', fontWeight: '600' }}>{log.usuario}</td>
                  <td style={{ padding: '15px' }}>
                    <span style={{ 
                      background: '#f0f2f5', padding: '4px 8px', borderRadius: '4px', fontSize: '0.8rem' 
                    }}>{log.modulo}</span>
                  </td>
                  <td style={{ padding: '15px', color: '#444' }}>{log.accion}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
