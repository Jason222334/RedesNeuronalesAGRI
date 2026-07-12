import React, { useState, useEffect } from 'react';
import axios from 'axios';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { useNavigate, Routes, Route, useLocation } from 'react-router-dom';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import GestionCultivos from './pages/GestionCultivos';
import GestionUsuarios from './pages/GestionUsuarios';
import Auditoria from './pages/Auditoria';
import GestionDatos from './pages/GestionDatos';
import Login from './pages/Login';
import RecuperarPassword from './pages/RecuperarPassword';
import CambiarPassword from './pages/CambiarPassword';
import MenuNavegacion from './components/MenuNavegacion';
import ModuloIA from './pages/ModuloIA';

function App() {
  const navigate = useNavigate();
  const location = useLocation();

  const authPaths = ['/login', '/recuperar'];

  useEffect(() => {
    const sesionStr = localStorage.getItem('sesionAgricola');
    if (sesionStr) {
      const usr = JSON.parse(sesionStr);
      
      // BLOQUEO ROBUSTO: Solo registrar si NO hay marca en sessionStorage 
      // y si estamos en una ruta que cuenta como "entrada" (Dashboard)
      const yaRegistrado = sessionStorage.getItem('visitaRegistrada');
      
      if (!yaRegistrado && location.pathname === '/') {
        // Marcamos inmediatamente para evitar que ejecuciones paralelas (StrictMode) pasen el IF
        sessionStorage.setItem('visitaRegistrada', 'pendiente'); 
        
        axios.post(`http://localhost:8000/api/auditoria/track-visit?id_usuario=${usr.id_usuario}`)
          .then(() => {
            sessionStorage.setItem('visitaRegistrada', 'true');
          })
          .catch(e => {
            console.error("Error al registrar visita", e);
            sessionStorage.removeItem('visitaRegistrada'); // Reintentar si falló
          });
      }
    }
  }, [location.pathname]);

  const showSidebar = !authPaths.includes(location.pathname) && !location.pathname.startsWith('/restablecer-password/');

  return (
    <div style={{ display: 'flex', minHeight: '100vh', width: '100%' }}>
      <MenuNavegacion />
      <main style={{ 
        flex: 1, 
        marginLeft: showSidebar ? '260px' : '0', 
        transition: 'margin-left 0.3s ease',
        width: '100%',
        background: '#f8f9fa'
      }}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/recuperar" element={<RecuperarPassword />} />
          <Route path="/restablecer-password/:token" element={<CambiarPassword />} />
          <Route path="/" element={<Dashboard />} />
          <Route path="/cultivos" element={<GestionCultivos />} />
          <Route path="/usuarios" element={<GestionUsuarios />} />
          <Route path="/datos" element={<GestionDatos />} />
          <Route path="/auditoria" element={<Auditoria />} />
          <Route path="/ia" element={<ModuloIA />} />

        </Routes>
      </main>
    </div>
  );
}

function Dashboard() {
  const [prediccion, setPrediccion] = useState(null);
  const [cultivos, setCultivos] = useState([]);
  const [datosGrafico, setDatosGrafico] = useState([]);
  const [datosCalidad, setDatosCalidad] = useState([]);
  const [cultivosOcultos, setCultivosOcultos] = useState([]); 
  const [parametros, setParametros] = useState({ id_cultivo: '', meses_futuro: 3, trans: 150, hectareas: 1.0 });
  const [climaAsumido, setClimaAsumido] = useState(""); 
  const [resultadoAvanzado, setResultadoAvanzado] = useState(null);
  const [riesgoPlaga, setRiesgoPlaga] = useState(null);
  const [recomendaciones, setRecomendaciones] = useState([]);
  const [mostrarBotonDescarga, setMostrarBotonDescarga] = useState(false);
  const [errorModelo, setErrorModelo] = useState("");

  const navigate = useNavigate();
  const [usuario, setUsuario] = useState(null); 

  useEffect(() => {
    const sesionStr = localStorage.getItem('sesionAgricola');
    
    if (!sesionStr) {
      navigate('/login');
    } else {
      const usr = JSON.parse(sesionStr);
      setUsuario(usr); 
      cargarCultivos();
      cargarDatosGrafico();
      cargarRecomendaciones(3); // Por defecto 3 meses
    }
  }, [navigate]); 

  const cargarRecomendaciones = async (meses) => {
    try {
      const res = await axios.get(`http://localhost:8000/api/prediccion/recomendacion-siembra?meses_futuro=${meses}`);
      setRecomendaciones(res.data);
    } catch (error) {
      console.error("Error cargando recomendaciones", error);
    }
  };

  const consultarRiesgoPlaga = async () => {
    try {
      const res = await axios.post(`http://localhost:8000/api/prediccion/riesgo-plaga?id_cultivo=${parametros.id_cultivo}&meses_futuro=${parametros.meses_futuro}`);
      setRiesgoPlaga(res.data);
    } catch (error) {
      console.error("Error consultando riesgo plaga", error);
    }
  };

  const cargarDatosGrafico = async () => {
    try {
      const resRendimiento = await axios.get('http://localhost:8000/api/reportes/rendimiento-mensual');
      setDatosGrafico(resRendimiento.data);
      const resCalidad = await axios.get('http://localhost:8000/api/reportes/calidad-cosechas');
      setDatosCalidad(resCalidad.data);
    } catch (error) {
      console.error("Error al cargar gráficos", error);
    }
  };

  const cargarCultivos = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/cultivos/');
      setCultivos(res.data);
      if (res.data.length > 0) {
        setParametros(prev => ({ ...prev, id_cultivo: res.data[0].id_cultivo }));
      }
    } catch (error) {
      console.error("Error al cargar cultivos", error);
    }
  };

  const manejarCambio = (e) => {
    const { name, value } = e.target;
    setParametros(prev => ({ ...prev, [name]: value }));
  };

  const generarConstanciaPDF = () => {
    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();
    
    doc.setFillColor(46, 125, 50);
    doc.rect(0, 0, pageWidth, 40, 'F');
    
    doc.setFontSize(22);
    doc.setTextColor(255, 255, 255);
    doc.setFont("helvetica", "bold");
    doc.text("CERTIFICADO DE PROYECCIÓN AGRÍCOLA", pageWidth / 2, 22, { align: "center" });
    
    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    doc.text("SISTEMA INTELIGENTE VALLE JEQUETEPEQUE - UNT", pageWidth / 2, 32, { align: "center" });

    doc.setTextColor(60, 60, 60);
    doc.setFontSize(9);
    doc.text(`CÓDIGO DE VERIFICACIÓN: SIGA-${new Date().getTime()}`, 15, 50);
    doc.text(`EMITIDO POR: ${usuario?.nombres?.toUpperCase()}`, 15, 55);
    doc.text(`FECHA DE EMISIÓN: ${new Date().toLocaleString()}`, pageWidth - 15, 50, { align: "right" });

    doc.setDrawColor(200);
    doc.line(15, 60, pageWidth - 15, 60);

    const nombreCultivo = cultivos.find(c => c.id_cultivo.toString() === parametros.id_cultivo.toString())?.nombre_cultivo || "Cultivo Desconocido";
    
    doc.setFontSize(14);
    doc.setTextColor(46, 125, 50);
    doc.setFont("helvetica", "bold");
    doc.text("I. INFORMACIÓN TÉCNICA Y OPERATIVA", 15, 75);
    
    autoTable(doc, {
      startY: 80,
      head: [['Campo', 'Detalle Registrado']],
      body: [
        ['Producto Agrícola', nombreCultivo],
        ['Área de Siembra', `${parametros.hectareas} Hectáreas`],
        ['Horizonte de Tiempo', `Proyección a ${parametros.meses_futuro} meses`],
        ['Ubicación de Referencia', 'Valle Jequetepeque, La Libertad, Perú']
      ],
      theme: 'grid',
      headStyles: { fillColor: [240, 240, 240], textColor: [46, 125, 50], fontStyle: 'bold' }
    });

    let finalY = doc.lastAutoTable.finalY + 15;
    
    doc.setFontSize(14);
    doc.setTextColor(46, 125, 50);
    doc.setFont("helvetica", "bold");
    doc.text("II. RESULTADOS DEL ANÁLISIS PREDICTIVO (AI)", 15, finalY);

    autoTable(doc, {
      startY: finalY + 5,
      head: [['Concepto', 'Estimación AI']],
      body: [
        ['Producción Esperada', `${resultadoAvanzado?.produccion_estimada} Toneladas`],
        ['Precio de Venta (Unidad)', `S/ ${resultadoAvanzado?.precio_unidad}`],
        ['Ingresos Brutos Estimados', `S/ ${resultadoAvanzado?.ingresos_brutos}`],
        ['Costos Operativos Proyectados', `S/ ${resultadoAvanzado?.costos_estimados}`],
        ['GANANCIA NETA ESTIMADA', `S/ ${resultadoAvanzado?.ganancia_neta}`]
      ],
      theme: 'striped',
      headStyles: { fillColor: [46, 125, 50] }
    });

    doc.setFontSize(11);
    doc.setTextColor(0);
    doc.setFont("helvetica", "bold");
    doc.text(`RECOMENDACIÓN DEL SISTEMA: ${resultadoAvanzado?.recomendacion}`, 15, doc.lastAutoTable.finalY + 15);

    doc.setFontSize(9);
    doc.setTextColor(150);
    doc.setFont("helvetica", "normal");
    doc.text("Este documento es una proyección estadística generada por inteligencia artificial.", 20, 270, { align: 'center' });

    doc.save(`Proyeccion_Avanzada_${nombreCultivo}.pdf`);
  };

  const calcularPrediccionAvanzada = async () => {
    try {
      const res = await axios.post(`http://localhost:8000/api/prediccion/avanzada?id_cultivo=${parametros.id_cultivo}&hectareas=${parametros.hectareas}&meses_futuro=${parametros.meses_futuro}&trans=${parametros.trans}&id_usuario=${usuario.id_usuario}`);
      setResultadoAvanzado(res.data);
      setClimaAsumido(res.data.clima_asumido);
      setMostrarBotonDescarga(true);
    } catch (error) {
      console.error("Error conectando al backend predictivo", error);
    }
  };

  const descargarReporte = () => {
    window.open('http://localhost:8000/api/reportes/cosechas/csv', '_blank');
  };

  const descargarExcel = () => {
    window.open('http://localhost:8000/api/reportes/cosechas/excel', '_blank');
  };

  const descargarPDF = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/reportes/cosechas/json');
      const doc = new jsPDF();
      doc.text("Reporte Operacional de Cosechas", 14, 22);
      const tableRows = res.data.map(row => [row.fecha, row.rendimiento, row.calidad]);
      autoTable(doc, {
        head: [["Fecha", "Rendimiento (Ton)", "Calidad"]],
        body: tableRows,
        startY: 45,
        headStyles: { fillColor: [46, 125, 50] } 
      });
      doc.save(`Reporte_Cosechas.pdf`);
    } catch (error) {
      console.error("Error al generar el PDF", error);
    }
  };

  const cultivosConDatos = Array.from(new Set(
    datosGrafico.flatMap(dato => Object.keys(dato).filter(key => key !== 'mes'))
  ));

  const toggleCultivo = (cultivo) => {
    if (cultivosOcultos.includes(cultivo)) {
      setCultivosOcultos(cultivosOcultos.filter(c => c !== cultivo));
    } else {
      setCultivosOcultos([...cultivosOcultos, cultivo]);
    }
  };

  const COLORES_PIE = ['#00C49F', '#FFBB28', '#FF8042'];
  const COLORES_BAR = ['#8884d8', '#82ca9d', '#ffc658', '#d0ed57', '#a4de6c'];

  const cardStyle = {
    background: 'white', padding: '25px', borderRadius: '15px',
    boxShadow: '0 10px 25px rgba(0,0,0,0.05)', border: '1px solid #f0f0f0',
    flex: 1, transition: 'transform 0.3s ease'
  };

  const cardTitleStyle = {
    marginTop: 0, color: '#2c3e50', borderBottom: '2px solid #4caf50',
    paddingBottom: '10px', display: 'inline-block', marginBottom: '20px'
  };

  const inputStyle = { marginLeft: '10px', padding: '8px', borderRadius: '6px', border: '1px solid #ddd', width: '150px' };

  const btnStyle = {
    background: 'linear-gradient(to right, #43a047, #2e7d32)', color: 'white',
    padding: '12px 24px', border: 'none', borderRadius: '8px', cursor: 'pointer',
    fontWeight: '600', boxShadow: '0 4px 6px rgba(46, 125, 50, 0.2)', transition: 'all 0.3s ease'
  };

  if (!usuario) return null;

  return (
    <div style={{ padding: '40px', fontFamily: 'Segoe UI, Roboto, sans-serif', backgroundColor: '#f8f9fa', minHeight: '100vh' }}>
      <h1 style={{ color: '#1b5e20', marginBottom: '30px', fontWeight: 'bold' }}>Dashboard: Sistema Inteligente de Gestión Agrícola</h1>

      <div style={{ display: 'flex', gap: '25px', marginBottom: '40px' }}>
        
        {/* PANEL DE PREDICCIÓN AVANZADA */}
        <div style={{ ...cardStyle, flex: 2 }}>
          <h3 style={cardTitleStyle}>Calculadora de Rentabilidad y Producción (IA)</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
            <label style={{fontWeight: '500'}}>Cultivo Seleccionado:
              <select name="id_cultivo" value={parametros.id_cultivo} onChange={manejarCambio} style={inputStyle}>
                {cultivos.map(c => <option key={c.id_cultivo} value={c.id_cultivo}>{c.nombre_cultivo}</option>)}
              </select>
            </label>
            <label style={{fontWeight: '500'}}>Hectáreas Sembradas:
              <input type="number" name="hectareas" value={parametros.hectareas} onChange={manejarCambio} style={inputStyle} step="0.5" />
            </label>
            <label style={{fontWeight: '500'}}>Horizonte de Venta:
              <select name="meses_futuro" value={parametros.meses_futuro} onChange={manejarCambio} style={inputStyle}>
                <option value={1}>En 1 mes</option>
                <option value={3}>En 3 meses</option>
                <option value={6}>En 6 meses</option>
                <option value={12}>En 1 año</option>
              </select>
            </label>
            <label style={{fontWeight: '500'}}>Costo Logístico (S/): 
              <input type="number" name="trans" value={parametros.trans} onChange={manejarCambio} style={inputStyle} />
            </label>
          </div>
          <button onClick={calcularPrediccionAvanzada} style={btnStyle}>Generar Análisis Completo</button>
          
          {resultadoAvanzado && (
            <div style={{ marginTop: '20px', padding: '20px', backgroundColor: '#e8f5e9', borderRadius: '10px', borderLeft: '5px solid #2e7d32', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
              <div>
                <p style={{margin: 0, fontSize: '0.9rem', color: '#666'}}>Producción Estimada</p>
                <h2 style={{color: '#2e7d32', margin: 0}}>{resultadoAvanzado.produccion_estimada} Ton.</h2>
              </div>
              <div>
                <p style={{margin: 0, fontSize: '0.9rem', color: '#666'}}>Precio Proyectado</p>
                <h2 style={{color: '#2e7d32', margin: 0}}>S/ {resultadoAvanzado.precio_unidad}</h2>
              </div>
              <div>
                <p style={{margin: 0, fontSize: '0.9rem', color: '#666'}}>Ganancia Neta Estimada</p>
                <h2 style={{color: '#1b5e20', margin: 0}}>S/ {resultadoAvanzado.ganancia_neta}</h2>
              </div>
              <div>
                <p style={{margin: 0, fontSize: '0.9rem', color: '#666'}}>Recomendación</p>
                <h3 style={{color: '#1b5e20', margin: 0}}>{resultadoAvanzado.recomendacion}</h3>
              </div>
              <div style={{gridColumn: 'span 2', marginTop: '10px'}}>
                <p style={{fontSize: '0.8rem', color: '#555'}}>Clima Asumido: {climaAsumido}</p>
                <button onClick={generarConstanciaPDF} style={{...btnStyle, width: '100%', marginTop: '10px'}}>Descargar Análisis en PDF</button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '25px', marginBottom: '40px' }}>
        
        {/* PANEL DE RIESGO DE PLAGAS */}
        <div style={{ ...cardStyle, flex: 1 }}>
          <h3 style={cardTitleStyle}>Alerta de Riesgo (Plagas)</h3>
          <p style={{color: '#666', fontSize: '0.9rem', marginBottom: '10px'}}>Analiza el riesgo específico por tipo de cultivo.</p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
            <label style={{fontSize: '0.85rem'}}>Cultivo:
              <select name="id_cultivo" value={parametros.id_cultivo} onChange={manejarCambio} style={{...inputStyle, width: '100%', marginLeft: 0}}>
                {cultivos.map(c => <option key={c.id_cultivo} value={c.id_cultivo}>{c.nombre_cultivo}</option>)}
              </select>
            </label>
            <label style={{fontSize: '0.85rem'}}>Horizonte:
              <select name="meses_futuro" value={parametros.meses_futuro} onChange={manejarCambio} style={{...inputStyle, width: '100%', marginLeft: 0}}>
                <option value={1}>Próximo mes</option>
                <option value={3}>En 3 meses</option>
              </select>
            </label>
          </div>
          
          <div style={{ textAlign: 'center', marginBottom: '15px' }}>
            <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: riesgoPlaga?.probabilidad_plaga > 70 ? '#d32f2f' : riesgoPlaga?.probabilidad_plaga > 40 ? '#f57c00' : '#2e7d32' }}>
              {riesgoPlaga ? `${riesgoPlaga.probabilidad_plaga}%` : '--%'}
            </div>
            <p style={{ fontWeight: '600', textTransform: 'uppercase', margin: 0, fontSize: '0.8rem' }}>Riesgo: {riesgoPlaga?.nivel || '---'}</p>
          </div>
          
          <button onClick={consultarRiesgoPlaga} style={{...btnStyle, width: '100%', background: 'linear-gradient(to right, #616161, #424242)'}}>
            Verificar Alerta
          </button>
          
          {riesgoPlaga && (
            <p style={{marginTop: '10px', fontSize: '0.75rem', color: '#777', fontStyle: 'italic'}}>
              Alerta para Mes {riesgoPlaga.mes_alerta} ({riesgoPlaga.clima_estimado})
            </p>
          )}
        </div>

        {/* ASISTENTE DE SIEMBRA */}
        <div style={{ ...cardStyle, flex: 1.5 }}>
          <h3 style={cardTitleStyle}>Asistente de Siembra (Pre-Campaña)</h3>
          <p style={{color: '#666', fontSize: '0.9rem', marginBottom: '10px'}}>¿Qué será más rentable cosechar en el futuro?</p>
          
          <div style={{ marginBottom: '15px' }}>
            <label style={{fontSize: '0.85rem'}}>Ver rentabilidad para cosecha en:
              <select onChange={(e) => cargarRecomendaciones(e.target.value)} style={{...inputStyle, width: 'auto'}}>
                <option value={1}>1 mes</option>
                <option value={3}>3 meses</option>
                <option value={6}>6 meses</option>
                <option value={12}>1 año</option>
              </select>
            </label>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {recomendaciones.slice(0, 3).map((rec, index) => (
              <div key={rec.id_cultivo} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px', background: index === 0 ? '#f1f8e9' : '#fff', borderRadius: '8px', border: '1px solid #eee' }}>
                <div>
                  <span style={{fontWeight: 'bold', color: '#333', fontSize: '0.9rem'}}>{rec.nombre}</span>
                  <p style={{margin: 0, fontSize: '0.7rem', color: '#777'}}>Precio est: S/ {rec.price_est || rec.precio_est}</p>
                </div>
                <div style={{textAlign: 'right'}}>
                  <span style={{ fontWeight: 'bold', color: rec.viabilidad > 20 ? '#2e7d32' : rec.viabilidad > 0 ? '#f57c00' : '#c62828', fontSize: '0.9rem' }}>
                    {rec.viabilidad > 0 ? '+' : ''}{rec.viabilidad}% ROI
                  </span>
                </div>
              </div>
            ))}
          </div>
          <p style={{marginTop: '10px', fontSize: '0.7rem', color: '#999'}}>*ROI ajustado según costos reales de insumos y preparación de tierra.</p>
        </div>

        {usuario.rol === 'Admin' && (
          <div style={{...cardStyle, flex: 1}}>
            <h3 style={cardTitleStyle}>Gestión de Reportes</h3>
            <p style={{color: '#666', marginBottom: '25px'}}>Descarga la bitácora operacional de cosechas y rendimientos del valle.</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              <button onClick={descargarPDF} style={{...btnStyle, background: 'linear-gradient(to right, #e53935, #c62828)'}}>Exportar PDF</button>
              <button onClick={descargarExcel} style={{...btnStyle, background: 'linear-gradient(to right, #1565c0, #0d47a1)'}}>Exportar Excel</button>
              <button onClick={descargarReporte} style={{...btnStyle, background: 'linear-gradient(to right, #1b5e20, #43a047)'}}>Exportar CSV</button>
            </div>
          </div>
        )}
      </div>

      <h2 style={{ color: '#2c3e50', marginBottom: '25px' }}>Inteligencia de Datos: Rendimientos del Valle</h2>
      
      <div style={{ display: 'flex', gap: '25px', flexWrap: 'wrap' }}>
        <div style={{ ...cardStyle, flex: 2, minWidth: '450px' }}>
          <h3 style={{ margin: 0, color: '#2c3e50', marginBottom: '20px' }}>Tendencia de Cosechas por Mes</h3>
          <div style={{ width: '100%', height: 350 }}>
            <ResponsiveContainer>
              <BarChart data={datosGrafico}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="mes" />
                <YAxis />
                <Tooltip />
                <Legend />
                {cultivosConDatos.map((cultivo, index) => (
                  <Bar key={cultivo} dataKey={cultivo} fill={COLORES_BAR[index % COLORES_BAR.length]} name={cultivo} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div style={{ ...cardStyle, flex: 1, minWidth: '320px' }}>
          <h3 style={{ marginBottom: '25px', color: '#2c3e50', textAlign: 'center' }}>Calidad de Producción Actual</h3>
          <div style={{ width: '100%', height: 350 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={datosCalidad} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={100} label>
                  {datosCalidad.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORES_PIE[index % COLORES_PIE.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;