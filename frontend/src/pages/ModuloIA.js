import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { useThemeAndLang } from '../context/ThemeAndLangContext';

const API = API_BASE_URL;

const COLORES = {
  arima:    '#60a5fa',
  rf:       '#34d399',
  xgb:      '#fbbf24',
  lstm:     '#a78bfa',
  cnnlstm:  '#fb923c',
};

function ModuloIA() {
  const { t, theme } = useThemeAndLang();
  const isDark = theme === 'dark';

  const [estado, setEstado]                 = useState(null);
  const [resultadosModelos, setResultadosModelos] = useState(null);
  const [edaData, setEdaData]               = useState(null);
  const [cvData, setCvData]                 = useState(null);
  const [hpData, setHpData]                 = useState(null);
  const [statsData, setStatsData]           = useState(null);
  const [loading, setLoading]               = useState({});
  const [mensaje, setMensaje]               = useState('');
  const [activeTab, setActiveTab]           = useState('estado');

  useEffect(() => {
    cargarEstado();
    cargarResultados();
  }, []);

  const cargarEstado = async () => {
    try {
      const res = await axios.get(`${API}/api/ia/estado-sistema`);
      setEstado(res.data);
    } catch (e) { /* backend puede no estar corriendo */ }
  };

  const cargarResultados = async () => {
    try {
      const res = await axios.get(`${API}/api/ia/resultados-modelos`);
      setResultadosModelos(res.data);
    } catch (e) { /* no entrenado */ }
  };

  const setLoad = (key, val) => setLoading(prev => ({ ...prev, [key]: val }));

  const handleEntrenar = async () => {
    setLoad('entrenar', true);
    setMensaje('⏳ Iniciando entrenamiento de los 5 modelos...');
    try {
      await axios.post(`${API}/api/ia/entrenar`);
      setMensaje('🚀 Entrenamiento iniciado en segundo plano. Puede tardar varios minutos.');
      // Polling cada 10s
      const interval = setInterval(async () => {
        try {
          const r = await axios.get(`${API}/api/ia/entrenar/estado`);
          if (r.data.estado === 'completado') {
            clearInterval(interval);
            setMensaje('✅ Entrenamiento completado.');
            cargarEstado();
            cargarResultados();
            setLoad('entrenar', false);
          } else if (r.data.estado === 'error') {
            clearInterval(interval);
            setMensaje(`❌ Error: ${r.data.mensaje}`);
            setLoad('entrenar', false);
          } else {
            setMensaje(`⏳ ${r.data.mensaje || 'En progreso...'} (${r.data.progreso || 0}%)`);
          }
        } catch (e) { clearInterval(interval); setLoad('entrenar', false); }
      }, 8000);
    } catch (e) {
      setMensaje('❌ Error al contactar el backend. ¿Está corriendo en puerto 8000?');
      setLoad('entrenar', false);
    }
  };

  const handleCV = async () => {
    setLoad('cv', true);
    try {
      const res = await axios.post(`${API}/api/ia/cross-validation?n_folds=5`);
      setCvData(res.data);
      setMensaje('✅ Validación cruzada completada');
    } catch (e) { setMensaje('❌ Error en cross-validation'); }
    setLoad('cv', false);
  };

  const handleHP = async () => {
    setLoad('hp', true);
    setMensaje('⏳ Optimizando hiperparámetros (puede tomar varios minutos)...');
    try {
      const res = await axios.post(`${API}/api/ia/hiperparametros?n_trials=20`);
      setHpData(res.data);
      setMensaje('✅ Ajuste de hiperparámetros completado');
    } catch (e) { setMensaje('❌ Error en tuning'); }
    setLoad('hp', false);
  };

  const handleStats = async () => {
    setLoad('stats', true);
    try {
      const res = await axios.post(`${API}/api/ia/pruebas-estadisticas`);
      setStatsData(res.data);
      setMensaje('✅ Pruebas estadísticas completadas');
    } catch (e) { setMensaje('❌ Error en pruebas estadísticas'); }
    setLoad('stats', false);
  };

  const handleReporte = (tipo) => {
    window.open(`${API}/api/ia/reporte/${tipo}`, '_blank');
  };

  const openStreamlit = () => {
    window.open('http://localhost:8501', '_blank');
  };

  // Styles
  const card = {
    background: isDark ? '#1e293b' : 'white',
    borderRadius: '16px',
    padding: '28px',
    boxShadow: isDark ? '0 10px 30px rgba(0,0,0,0.3)' : '0 10px 30px rgba(0,0,0,0.08)',
    border: isDark ? '1px solid #334155' : '1px solid #f0f0f0',
    color: isDark ? '#f8fafc' : '#2c3e50',
    marginBottom: '24px'
  };
  const btn = (color = '#27ae60') => ({
    background: `linear-gradient(135deg, ${color}, ${color}dd)`,
    color: 'white', border: 'none', borderRadius: '10px',
    padding: '12px 22px', cursor: 'pointer', fontWeight: '600',
    fontSize: '0.9rem', transition: 'all 0.3s ease',
    background: color, color: 'white', border: 'none',
    padding: '10px 20px', borderRadius: '8px', cursor: 'pointer',
    fontWeight: '600', display: 'inline-flex', alignItems: 'center', gap: '8px',
    fontSize: '0.9rem', transition: 'all 0.2s'
  });
  const tabBtn = (active) => ({
    padding: '10px 20px', border: 'none', cursor: 'pointer',
    borderRadius: '8px 8px 0 0',
    background: active ? '#27ae60' : (isDark ? '#334155' : '#e2e8f0'),
    color: active ? 'white' : (isDark ? '#94a3b8' : '#64748b'),
    fontWeight: active ? '600' : '400',
    fontSize: '0.9rem', transition: 'all 0.2s'
  });
  const badge = (color) => ({
    display: 'inline-block', background: color, color: 'white',
    borderRadius: '20px', padding: '3px 12px', fontSize: '0.75rem',
    fontWeight: '600', marginLeft: '8px'
  });
  const metricCard = (color = '#27ae60') => ({
    background: isDark ? '#0f172a' : `linear-gradient(135deg, ${color}15, ${color}05)`,
    border: `1px solid ${color}40`, borderRadius: '12px', padding: '18px',
    textAlign: 'center'
  });

  const tabs = [
    { id: 'estado',   label: t('tabEda') },
    { id: 'modelos',  label: t('tabTrain') },
    { id: 'cv',       label: t('tabCv') },
    { id: 'hp',       label: t('tabHp') },
    { id: 'stats',    label: t('tabStats') },
    { id: 'reportes', label: t('tabReports') },
  ];

  return (
    <div style={{ padding: '36px', fontFamily: "'Segoe UI', Roboto, sans-serif", background: isDark ? '#0f172a' : '#f8f9fa', color: isDark ? '#f8fafc' : '#2c3e50', minHeight: '100vh' }}>
      
      {/* HEADER */}
      <div style={{ ...card, background: 'linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%)', color: 'white' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.8rem', fontWeight: '700' }}>{t('aiModuleTitle')}</h1>
            <p style={{ margin: '6px 0 0', opacity: 0.85, fontSize: '0.95rem' }}>
              {t('aiModuleSub')}
            </p>
          </div>
          <button onClick={openStreamlit} style={btn('#4a90d9')}>
            🌐 Streamlit App
          </button>
        </div>
      </div>

      {/* MENSAJE GLOBAL */}
      {mensaje && (
        <div style={{ 
          background: mensaje.startsWith('✅') ? '#e8f5e9' : mensaje.startsWith('❌') ? '#ffebee' : '#fff8e1',
          border: `1px solid ${mensaje.startsWith('✅') ? '#4caf50' : mensaje.startsWith('❌') ? '#f44336' : '#ffc107'}`,
          borderRadius: '10px', padding: '14px 18px', marginBottom: '20px',
          color: '#333', fontWeight: '500'
        }}>
          {mensaje}
        </div>
      )}

      {/* TABS */}
      <div style={{ borderBottom: '2px solid #e0e0e0', marginBottom: '0', display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={tabBtn(activeTab === t.id)}>
            {t.label}
          </button>
        ))}
      </div>

      <div style={{ ...card, borderRadius: '0 16px 16px 16px', marginTop: 0 }}>

        {/* TAB: ESTADO */}
        {activeTab === 'estado' && (
          <div>
            <h2 style={{ color: '#1b5e20', marginTop: 0 }}>Estado del Sistema IA</h2>
            
            {/* Botón entrenar */}
            <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '28px' }}>
              <button onClick={handleEntrenar} disabled={loading.entrenar} style={btn()}>
                {loading.entrenar ? '⏳ Entrenando...' : '🚀 Ejecutar Pipeline Completo (EDA + 5 Modelos)'}
              </button>
            </div>

            {estado && (
              <>
                <h3 style={{ color: isDark ? '#4ade80' : '#2c3e50', marginBottom: '16px' }}>Módulos Completados</h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '12px' }}>
                  {Object.entries(estado.modulos_completados).map(([key, done]) => (
                    <div key={key} style={{ 
                      padding: '14px', borderRadius: '10px', 
                      background: done ? (isDark ? '#0f291e' : '#e8f5e9') : (isDark ? '#3a2000' : '#fff3e0'),
                      border: `1px solid ${done ? '#4caf50' : '#ff9800'}`
                    }}>
                      <span style={{ fontSize: '1.2rem' }}>{done ? '✅' : '🔴'}</span>
                      <span style={{ marginLeft: '8px', fontWeight: '500', fontSize: '0.9rem', color: isDark ? '#f8fafc' : '#333' }}>
                        {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                    </div>
                  ))}
                </div>
                
                <div style={{ marginTop: '20px', padding: '16px', background: isDark ? '#0f172a' : '#f5f5f5', borderRadius: '10px', border: isDark ? '1px solid #334155' : 'none' }}>
                  <strong>¿Listo para generar reportes?</strong>{' '}
                  <span style={badge(estado.listo_para_reportes ? '#27ae60' : '#e74c3c')}>
                    {estado.listo_para_reportes ? '✅ Sí' : '❌ No — entrena primero'}
                  </span>
                </div>
              </>
            )}

            {!estado && (
              <div style={{ padding: '20px', background: isDark ? '#3a2000' : '#fff3e0', borderRadius: '12px', marginTop: '16px' }}>
                <p style={{ margin: 0, color: isDark ? '#fbc02d' : '#e65100' }}>
                  ⚠️ No se pudo conectar al backend (puerto 8000). Asegúrate de que FastAPI esté corriendo.
                </p>
                <p style={{ margin: '8px 0 0', fontSize: '0.85rem', color: isDark ? '#94a3b8' : '#666' }}>
                  Usa el botón <strong>"🌐 Abrir Streamlit App"</strong> para el módulo de análisis independiente.
                </p>
              </div>
            )}

            {/* Info sobre los 5 modelos */}
            <h3 style={{ color: isDark ? '#4ade80' : '#2c3e50', marginTop: '28px' }}>Los 5 Modelos del Sistema</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '14px' }}>
              {[
                { nombre: 'ARIMA(5,1,2)', tipo: 'Clásico', desc: 'Serie temporal univariada de precios del Arroz', color: '#60a5fa', icono: '📈' },
                { nombre: 'Random Forest', tipo: 'Clásico', desc: 'Ensemble de árboles con features climáticos y de lag', color: '#34d399', icono: '🌲' },
                { nombre: 'XGBoost', tipo: 'Clásico', desc: 'Gradient Boosting optimizado con Optuna', color: '#fbbf24', icono: '⚡' },
                { nombre: 'LSTM', tipo: 'Red Neuronal', desc: 'Long Short-Term Memory — captura dependencias largas', color: '#a78bfa', icono: '🧠' },
                { nombre: 'CNN-LSTM', tipo: 'Red Neuronal', desc: 'Convolucional + Recurrente — extrae patrones locales y temporales', color: '#fb923c', icono: '🔬' },
              ].map(m => (
                <div key={m.nombre} style={{ 
                  padding: '18px', borderRadius: '12px', 
                  background: isDark ? '#0f172a' : `${m.color}12`, border: `1px solid ${m.color}50`
                }}>
                  <div style={{ fontSize: '1.4rem', marginBottom: '8px' }}>{m.icono}</div>
                  <div style={{ fontWeight: '700', color: isDark ? '#f8fafc' : '#333', marginBottom: '4px' }}>{m.nombre}</div>
                  <span style={badge(m.tipo === 'Clásico' ? '#27ae60' : '#8e44ad')}>{m.tipo}</span>
                  <p style={{ margin: '10px 0 0', fontSize: '0.85rem', color: isDark ? '#cbd5e1' : '#666' }}>{m.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB: MODELOS */}
        {activeTab === 'modelos' && (
          <div>
            <h2 style={{ color: '#1b5e20', marginTop: 0 }}>Resultados de Entrenamiento</h2>
            
            {resultadosModelos ? (
              <>
                <div style={{ 
                  padding: '16px 20px', background: isDark ? '#0f291e' : '#e8f5e9', borderRadius: '10px', 
                  marginBottom: '24px', borderLeft: '4px solid #27ae60'
                }}>
                  <strong>🏆 Mejor modelo:</strong>{' '}
                  <span style={{ fontSize: '1.1rem', color: isDark ? '#4ade80' : '#1b5e20', fontWeight: '700' }}>
                    {resultadosModelos.mejor_modelo?.toUpperCase()}
                  </span>
                  <span style={badge('#27ae60')}>R² = {resultadosModelos.mejor_r2?.toFixed(4)}</span>
                </div>

                {/* Tabla comparativa */}
                <h3 style={{ color: isDark ? '#4ade80' : '#2c3e50' }}>Tabla Comparativa de Modelos</h3>
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                    <thead>
                      <tr style={{ background: isDark ? '#0f172a' : '#1b5e20', color: 'white' }}>
                        {['Modelo', 'RMSE ↓', 'MAE ↓', 'R² ↑', 'MAPE % ↓', 'Tiempo (s)'].map(h => (
                          <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontWeight: '600' }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {resultadosModelos.tabla_metricas?.map((m, i) => {
                        const esMejor = m.Modelo?.toLowerCase().replace(' ', '_') === resultadosModelos.mejor_modelo;
                        return (
                          <tr key={i} style={{ 
                            background: esMejor ? (isDark ? '#0f291e' : '#e8f5e9') : i % 2 === 0 ? (isDark ? '#1e293b' : '#fafafa') : (isDark ? '#0f172a' : 'white'),
                            borderBottom: isDark ? '1px solid #334155' : '1px solid #e0e0e0',
                            color: isDark ? '#f8fafc' : '#2c3e50'
                          }}>
                            <td style={{ padding: '12px 16px', fontWeight: esMejor ? '700' : '400', color: isDark ? '#f8fafc' : '#333' }}>
                              {m.Modelo} {esMejor && <span style={badge('#27ae60')}>★ Mejor</span>}
                            </td>
                            <td style={{ padding: '12px 16px', color: isDark ? '#cbd5e1' : '#666' }}>{m.RMSE}</td>
                            <td style={{ padding: '12px 16px', color: isDark ? '#cbd5e1' : '#666' }}>{m.MAE}</td>
                            <td style={{ padding: '12px 16px', color: '#27ae60', fontWeight: '600' }}>{m['R²']}</td>
                            <td style={{ padding: '12px 16px', color: isDark ? '#cbd5e1' : '#666' }}>{m['MAPE %']}%</td>
                            <td style={{ padding: '12px 16px', color: isDark ? '#cbd5e1' : '#666' }}>{m['Tiempo s']}s</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Figuras */}
                {resultadosModelos.figuras && (
                  <>
                    <h3 style={{ color: '#2c3e50', marginTop: '28px' }}>Visualizaciones</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
                      {Object.entries(resultadosModelos.figuras).map(([nombre, url]) => url && (
                        <div key={nombre} style={{ borderRadius: '12px', overflow: 'hidden', border: isDark ? '1px solid #334155' : '1px solid #e0e0e0' }}>
                          <div style={{ padding: '10px 16px', background: isDark ? '#0f172a' : '#f5f5f5', fontWeight: '600', fontSize: '0.85rem', color: isDark ? '#f8fafc' : '#555' }}>
                            {nombre.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </div>
                          <img
                            src={`${API}/api/ia/figura/${url.split(/[\\/]/).pop()}`}
                            alt={nombre}
                            style={{ width: '100%', display: 'block' }}
                            onError={(e) => { e.target.style.display = 'none'; }}
                          />
                        </div>
                      ))}
                    </div>

                    {/* Clasificación de plagas */}
                    {resultadosModelos.reporte_clasificacion_plagas && (
                      <div style={{ marginTop: '24px' }}>
                        <h3 style={{ color: '#2c3e50' }}>Métricas de Clasificación — Riesgo de Plaga (F1-Score)</h3>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                          {[['Bajo', '0'], ['Medio', '1'], ['Alto', '2']].map(([nombre, key]) => {
                            const d = resultadosModelos.reporte_clasificacion_plagas[key];
                            return d ? (
                              <div key={key} style={metricCard(key === '2' ? '#e74c3c' : key === '1' ? '#f39c12' : '#27ae60')}>
                                <div style={{ fontSize: '1rem', fontWeight: '700', color: '#333', marginBottom: '12px' }}>
                                  {nombre}
                                </div>
                                {[['F1-Score', 'f1-score'], ['Precision', 'precision'], ['Recall', 'recall']].map(([label, k]) => (
                                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '6px' }}>
                                    <span style={{ color: '#666' }}>{label}</span>
                                    <span style={{ fontWeight: '700', color: '#333' }}>{d[k]?.toFixed(4)}</span>
                                  </div>
                                ))}
                              </div>
                            ) : null;
                          })}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </>
            ) : (
              <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
                <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🤖</div>
                <p>Los modelos aún no han sido entrenados.</p>
                <p style={{ fontSize: '0.85rem' }}>Ve a la pestaña <strong>📊 Estado</strong> y haz clic en <strong>"🚀 Ejecutar Pipeline Completo"</strong>.</p>
              </div>
            )}
          </div>
        )}

        {/* TAB: CROSS-VALIDATION */}
        {activeTab === 'cv' && (
          <div>
            <h2 style={{ color: '#1b5e20', marginTop: 0 }}>Validación Cruzada</h2>
            <p style={{ color: '#666', marginBottom: '20px' }}>
              Método: <strong>TimeSeriesSplit</strong> — evita data leakage manteniendo el orden cronológico.
              k = 5 folds (configurable en el módulo Streamlit).
            </p>
            <button onClick={handleCV} disabled={loading.cv} style={btn()}>
              {loading.cv ? '⏳ Ejecutando...' : '▶ Ejecutar Cross-Validation (5 folds)'}
            </button>

            {cvData && (
              <div style={{ marginTop: '24px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                  {['random_forest', 'xgboost'].map(m => {
                    const d = cvData[m];
                    return d ? (
                      <div key={m} style={{ ...card, marginBottom: 0 }}>
                        <h3 style={{ color: '#1b5e20', marginTop: 0 }}>{m.replace('_', ' ').toUpperCase()}</h3>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                          {[['R² μ', d.R2_mean, d.R2_std], ['RMSE μ', d.RMSE_mean, d.RMSE_std], ['MAE μ', d.MAE_mean, d.MAE_std]].map(([label, mean, std]) => (
                            <div key={label} style={metricCard()}>
                              <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: '4px' }}>{label}</div>
                              <div style={{ fontSize: '1.2rem', fontWeight: '700', color: '#1b5e20' }}>{mean?.toFixed(4)}</div>
                              <div style={{ fontSize: '0.75rem', color: '#999' }}>± {std?.toFixed(4)}</div>
                            </div>
                          ))}
                        </div>
                        {d.folds && (
                          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                            <thead>
                              <tr style={{ background: isDark ? '#0f172a' : '#f5f5f5' }}>
                                {['Fold', 'RMSE', 'MAE', 'R²', 'Train', 'Test'].map(h => (
                                  <th key={h} style={{ padding: '8px', textAlign: 'center', color: isDark ? '#4ade80' : '#555' }}>{h}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {d.folds.map(f => (
                                <tr key={f.fold} style={{ borderBottom: isDark ? '1px solid #334155' : '1px solid #e0e0e0', background: isDark ? '#1e293b' : 'white', color: isDark ? '#f8fafc' : '#333' }}>
                                  <td style={{ padding: '8px', textAlign: 'center', fontWeight: '600' }}>{f.fold}</td>
                                  <td style={{ padding: '8px', textAlign: 'center' }}>{f.RMSE}</td>
                                  <td style={{ padding: '8px', textAlign: 'center' }}>{f.MAE}</td>
                                  <td style={{ padding: '8px', textAlign: 'center', color: '#27ae60', fontWeight: '600' }}>{f['R²']}</td>
                                  <td style={{ padding: '8px', textAlign: 'center', color: isDark ? '#94a3b8' : '#888', fontSize: '0.8rem' }}>{f.n_train}</td>
                                  <td style={{ padding: '8px', textAlign: 'center', color: isDark ? '#94a3b8' : '#888', fontSize: '0.8rem' }}>{f.n_test}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        )}
                      </div>
                    ) : null;
                  })}
                </div>
                {cvData.figura && (
                  <div style={{ marginTop: '20px', borderRadius: '12px', overflow: 'hidden', border: '1px solid #e0e0e0' }}>
                    <img
                      src={`${API}/api/ia/figura/${cvData.figura.split(/[\\/]/).pop()}`}
                      alt="cross_validation"
                      style={{ width: '100%', display: 'block' }}
                    />
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB: HIPERPARÁMETROS */}
        {activeTab === 'hp' && (
          <div>
            <h2 style={{ color: isDark ? '#4ade80' : '#1b5e20', marginTop: 0 }}>Ajuste de Hiperparámetros</h2>
            <p style={{ color: isDark ? '#94a3b8' : '#666', marginBottom: '20px' }}>
              Usa <strong>Optuna (búsqueda bayesiana)</strong> para RF y XGBoost, y <strong>Grid Search</strong> para ARIMA.
            </p>
            <button onClick={handleHP} disabled={loading.hp} style={btn('#8e44ad')}>
              {loading.hp ? '⏳ Optimizando (puede tardar)...' : '⚙️ Ejecutar Tuning de Hiperparámetros'}
            </button>

            {hpData && (
              <div style={{ marginTop: '24px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
                  {[['Random Forest', 'random_forest'], ['XGBoost', 'xgboost']].map(([label, key]) => {
                    const params = hpData[key]?.best_params;
                    return params ? (
                      <div key={key} style={card}>
                        <h3 style={{ color: isDark ? '#4ade80' : '#1b5e20', marginTop: 0 }}>{label} — Mejores Parámetros</h3>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                          <thead>
                            <tr style={{ background: isDark ? '#0f172a' : '#f5f5f5' }}>
                              <th style={{ padding: '8px', textAlign: 'left', color: isDark ? '#4ade80' : '#333' }}>Hiperparámetro</th>
                              <th style={{ padding: '8px', textAlign: 'right', color: isDark ? '#4ade80' : '#333' }}>Valor Óptimo</th>
                            </tr>
                          </thead>
                          <tbody>
                            {Object.entries(params).map(([k, v]) => (
                              <tr key={k} style={{ borderBottom: isDark ? '1px solid #334155' : '1px solid #e0e0e0', color: isDark ? '#f8fafc' : '#333' }}>
                                <td style={{ padding: '8px', color: isDark ? '#cbd5e1' : '#555' }}>{k}</td>
                                <td style={{ padding: '8px', textAlign: 'right', fontWeight: '600', color: '#27ae60' }}>{v?.toString()}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : null;
                  })}
                </div>

                {hpData.arima?.mejor && (
                  <div style={{ ...card, marginBottom: '20px' }}>
                    <h3 style={{ color: isDark ? '#4ade80' : '#1b5e20', marginTop: 0 }}>ARIMA — Grid Search</h3>
                    <p>
                      Mejor orden: <strong>{JSON.stringify(hpData.arima.mejor.orden)}</strong> |
                      AIC: <strong>{hpData.arima.mejor.aic?.toFixed(2)}</strong> |
                      RMSE: <strong>{hpData.arima.mejor.rmse}</strong>
                    </p>
                  </div>
                )}

                {hpData.figura_convergencia && (
                  <img
                    src={`${API}/api/ia/figura/${hpData.figura_convergencia.split(/[\\/]/).pop()}`}
                    alt="convergencia"
                    style={{ width: '100%', borderRadius: '12px', border: '1px solid #e0e0e0' }}
                  />
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB: PRUEBAS ESTADÍSTICAS */}
        {activeTab === 'stats' && (
          <div>
            <h2 style={{ color: isDark ? '#4ade80' : '#1b5e20', marginTop: 0 }}>Pruebas Estadísticas de Validación</h2>
            <p style={{ color: isDark ? '#94a3b8' : '#666', marginBottom: '12px' }}>
              5 familias de tests: <strong>Shapiro-Wilk</strong>, <strong>Ljung-Box</strong>, <strong>Kolmogorov-Smirnov</strong>,{' '}
              <strong>Wilcoxon</strong>, <strong>Diebold-Mariano</strong>.
            </p>
            <button onClick={handleStats} disabled={loading.stats} style={btn('#c0392b')}>
              {loading.stats ? '⏳ Ejecutando...' : '🔬 Ejecutar Pruebas Estadísticas'}
            </button>

            {statsData && (
              <div style={{ marginTop: '24px' }}>
                {[
                  { label: 'Shapiro-Wilk (Normalidad de Residuos)', key: 'shapiro_wilk', h0: 'H₀: residuos son normales' },
                  { label: 'Ljung-Box (Autocorrelación de Residuos)', key: 'ljung_box', h0: 'H₀: no hay autocorrelación' },
                  { label: 'Kolmogorov-Smirnov', key: 'ks', h0: 'H₀: errores siguen distribución normal' },
                  { label: 'Diebold-Mariano (Comparación de Modelos)', key: 'diebold_mariano', h0: 'H₀: igual capacidad predictiva' },
                  { label: 'Wilcoxon (Comparación No Paramétrica)', key: 'wilcoxon', h0: 'H₀: rendimiento estadísticamente igual' },
                ].map(({ label, key, h0 }) => {
                  const lista = statsData[key];
                  if (!lista || lista.length === 0) return null;
                  return (
                    <div key={key} style={{ ...card, marginBottom: '16px' }}>
                      <h3 style={{ color: isDark ? '#4ade80' : '#2c3e50', marginTop: 0 }}>{label}</h3>
                      <p style={{ color: isDark ? '#94a3b8' : '#888', fontSize: '0.85rem', marginBottom: '12px', fontStyle: 'italic' }}>{h0} (α = 0.05)</p>
                      <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                          <thead>
                            <tr style={{ background: isDark ? '#0f172a' : '#1b5e20', color: 'white' }}>
                              {Object.keys(lista[0]).filter(k => !['H0', 'test'].includes(k)).map(k => (
                                <th key={k} style={{ padding: '10px', textAlign: 'left' }}>
                                  {k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {lista.map((row, i) => (
                              <tr key={i} style={{ borderBottom: isDark ? '1px solid #334155' : '1px solid #e0e0e0', background: i % 2 === 0 ? (isDark ? '#1e293b' : '#fafafa') : (isDark ? '#0f172a' : 'white') }}>
                                {Object.entries(row).filter(([k]) => !['H0', 'test'].includes(k)).map(([k, v]) => (
                                  <td key={k} style={{ 
                                    padding: '10px',
                                    color: k === 'p_valor' && v < 0.05 ? '#c0392b' : k === 'p_valor' ? '#27ae60' : (isDark ? '#f8fafc' : '#333'),
                                    fontWeight: k === 'p_valor' ? '600' : '400'
                                  }}>
                                    {typeof v === 'number' ? v.toFixed(4) : (v?.toString() || '-')}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  );
                })}

                {statsData.figura && (
                  <img
                    src={`${API}/api/ia/figura/${statsData.figura.split(/[\\/]/).pop()}`}
                    alt="residuos_qq"
                    style={{ width: '100%', borderRadius: '12px', border: '1px solid #e0e0e0' }}
                  />
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB: REPORTES */}
        {activeTab === 'reportes' && (
          <div>
            <h2 style={{ color: isDark ? '#4ade80' : '#1b5e20', marginTop: 0 }}>Generación de Reportes</h2>
            <p style={{ color: isDark ? '#94a3b8' : '#666', marginBottom: '24px' }}>
              Descarga reportes completos con tablas comparativas, figuras e interpretaciones.
              Requiere que los modelos estén entrenados.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: '20px', marginBottom: '28px' }}>
              {[
                { tipo: 'pdf',   label: '📕 Reporte PDF',   desc: 'Incluye figuras e interpretaciones. Formato científico.',    color: '#e74c3c' },
                { tipo: 'excel', label: '📗 Reporte Excel',  desc: 'Múltiples hojas: modelos, CV, hiperparámetros, tests.',      color: '#27ae60' },
                { tipo: 'word',  label: '📘 Reporte Word',   desc: 'Formato editable con tablas y figuras incrustadas.',          color: '#3498db' },
              ].map(({ tipo, label, desc, color }) => (
                <div key={tipo} style={{ ...card, textAlign: 'center', marginBottom: 0 }}>
                  <div style={{ fontSize: '3rem', marginBottom: '12px' }}>
                    {tipo === 'pdf' ? '📕' : tipo === 'excel' ? '📗' : '📘'}
                  </div>
                  <h3 style={{ color: isDark ? '#4ade80' : '#2c3e50', marginTop: 0, marginBottom: '8px' }}>{label}</h3>
                  <p style={{ color: isDark ? '#94a3b8' : '#888', fontSize: '0.85rem', marginBottom: '16px' }}>{desc}</p>
                  <button onClick={() => handleReporte(tipo)} style={btn(color)}>
                    ⬇️ Descargar {tipo.toUpperCase()}
                  </button>
                </div>
              ))}
            </div>

            {/* Acceso a Streamlit */}
            <div style={{ 
              padding: '24px', borderRadius: '16px', 
              background: isDark ? '#0f291e' : 'linear-gradient(135deg, #4a90d910, #4a90d920)',
              border: isDark ? '1px solid #2e7d32' : '1px solid #4a90d940', textAlign: 'center'
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '8px' }}>🌐</div>
              <h3 style={{ color: isDark ? '#4ade80' : '#2c3e50', margin: '0 0 8px' }}>Análisis Completo en Streamlit</h3>
              <p style={{ color: isDark ? '#94a3b8' : '#666', marginBottom: '16px', fontSize: '0.9rem' }}>
                Para ejecutar el pipeline completo interactivamente (EDA → Entrenamiento → CV → Hiperparámetros → Tests → Reportes)
              </p>
              <button onClick={openStreamlit} style={btn('#4a90d9')}>
                🚀 Abrir Streamlit App (puerto 8501)
              </button>
              <p style={{ color: isDark ? '#94a3b8' : '#999', fontSize: '0.8rem', marginTop: '10px' }}>
                Ejecuta: <code style={{ background: isDark ? '#0f172a' : '#f5f5f5', color: isDark ? '#4ade80' : '#333', padding: '2px 8px', borderRadius: '4px' }}>
                  streamlit run streamlit_app/app.py
                </code>
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ModuloIA;
