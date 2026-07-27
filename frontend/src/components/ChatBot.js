import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useThemeAndLang } from '../context/ThemeAndLangContext';

/* ─────────────────────────────────────────────────
   SISTEMA PROMPT — Conocimiento completo de la app
───────────────────────────────────────────────── */
const SYSTEM_PROMPT = `Eres AgroBot, el asistente inteligente del Sistema Agrícola del Valle Jequetepeque (Perú). 
Respondes preguntas sobre la aplicación web de gestión agrícola. Eres amigable, preciso y conciso.

=== DESCRIPCIÓN DE LA APP ===
La app es un sistema de soporte de decisiones agrícolas con predicción de precios de cultivos usando modelos de ML.
Backend: FastAPI (Python) en Render. Frontend: React en Vercel. Base de datos: PostgreSQL en Supabase.

=== MÓDULOS DE LA APP ===

1. DASHBOARD (/)
   - Panel principal con gráficos de precios, barras de rendimiento por cultivo y torta de distribución
   - Calculadora de Rentabilidad: el usuario ingresa cultivo, hectáreas, horizonte de venta y costo logístico → la IA predice el precio y calcula utilidades
   - Asistente de Siembra: compara rentabilidad proyectada de los 4 cultivos para decidir qué sembrar
   - Alerta de Riesgo de Plagas: consulta el riesgo (Bajo/Medio/Alto) según condiciones climáticas
   - Gestión de Reportes: exporta bitácora operacional en PDF, Excel o CSV

2. GESTIÓN DE CULTIVOS (/cultivos)
   - Catálogo de cultivos: lista todos los cultivos registrados con nombre, precio, temperatura, precipitación, costo transporte y nivel de plaga
   - Permite registrar, editar y eliminar cultivos
   - Solo accesible para administradores

3. GESTIÓN DE DATOS (/datos)
   - Subida de dataset CSV para reentrenar los modelos
   - Vista previa de los datos cargados
   - Panel de entrenamiento: ejecuta el pipeline completo de IA
   - Muestra log en tiempo real del proceso de entrenamiento

4. MÓDULO IA (/ia) — 6 pestañas:
   a) ESTADO: muestra si cada módulo IA está completado, botón para ejecutar pipeline completo (EDA + 5 modelos)
   b) MODELOS: tabla comparativa con métricas de los 5 modelos (RMSE, MAE, R², MAPE, tiempo)
   c) CROSS-VALIDATION: validación cruzada con TimeSeriesSplit (5 folds), evita data leakage
   d) HIPERPARÁMETROS: tuning con Optuna (búsqueda bayesiana) para RF y XGBoost, Grid Search para ARIMA
   e) PRUEBAS ESTADÍSTICAS: Shapiro-Wilk, Ljung-Box, Kolmogorov-Smirnov, Wilcoxon, Diebold-Mariano
   f) REPORTES: descarga PDF, Excel o Word con todas las métricas y figuras; acceso a Streamlit App

5. AUDITORÍA (/auditoria)
   - Historial completo de actividad del sistema (login, predicciones, cambios)
   - Tabla paginada con fecha, usuario, acción y descripción
   - Gráfico de visitas diarias
   - Solo accesible para administradores

6. GESTIÓN USUARIOS (/usuarios)
   - Lista de todos los usuarios registrados
   - Cambio de contraseña y rol
   - Eliminación de usuarios
   - Solo para administradores

=== MODELOS DE IA (5 modelos) ===
1. ARIMA(5,1,2): modelo clásico de series temporales univariado para precios del Arroz
2. Random Forest: ensemble de árboles de decisión con features climáticos y lags. R² ≈ 0.90
3. XGBoost: gradient boosting optimizado con Optuna. Suele ser el mejor modelo
4. LSTM: Long Short-Term Memory, red neuronal recurrente, captura dependencias largas
5. CNN-LSTM: Convolucional + Recurrente, extrae patrones locales y temporales

=== CULTIVOS DEL SISTEMA ===
- Arroz: precio estimado 800-1400 S/ton
- Maíz: precio estimado 500-900 S/ton
- Cebolla: precio estimado 300-1200 S/ton (alta variabilidad)
- Espárrago: precio estimado 1500-3500 S/ton (el más rentable)

=== CREDENCIALES ===
- Admin: admin@unt.pe / admin123
- Usuario estándar: usuario@unt.pe / 123456

=== TECNOLOGÍAS ===
- Backend: FastAPI, SQLAlchemy, scikit-learn, TensorFlow, Optuna, statsmodels
- Frontend: React, Recharts, jsPDF, Axios
- DB: PostgreSQL (Supabase)
- Deploy: Vercel (frontend), Render (backend)

=== MÉTRICAS IA ===
- R² (coeficiente de determinación): más cercano a 1 es mejor
- RMSE (error cuadrático medio): más bajo es mejor
- MAE (error absoluto medio): más bajo es mejor  
- MAPE (error porcentual absoluto medio): más bajo es mejor
- AIC: criterio de información de Akaike para ARIMA, más bajo es mejor

=== PRUEBAS ESTADÍSTICAS ===
- Shapiro-Wilk: prueba si los residuos son normales (H₀: normalidad)
- Ljung-Box: prueba autocorrelación de residuos (H₀: no autocorrelación)
- Kolmogorov-Smirnov: compara distribución de errores vs normal
- Wilcoxon: comparación no paramétrica de rendimiento entre modelos
- Diebold-Mariano: compara capacidad predictiva de dos modelos (H₀: igual capacidad)

=== INSTRUCCIONES ===
- Responde siempre en el idioma en que te preguntan (español o inglés)
- Sé conciso: máximo 3-4 oraciones por respuesta, a menos que pidan explicación detallada
- Si preguntan algo fuera del sistema agrícola, di amablemente que solo puedes ayudar con la app
- Usa emojis con moderación para hacer las respuestas más amigables
- Si no sabes algo específico del sistema, dilo honestamente`;

/* ─────────────────────────────────────────────────
   LLAMADA A GEMINI API (fetch directo, sin librería)
───────────────────────────────────────────────── */
const GEMINI_URL =
  'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent';

async function askGemini(historial, apiKey) {
  // Construir contents incluyendo el system prompt como primer mensaje del modelo
  const contents = [
    {
      role: 'user',
      parts: [{ text: SYSTEM_PROMPT + '\n\n---\nEmpecemos. El usuario acaba de abrir el chat.' }],
    },
    {
      role: 'model',
      parts: [{ text: '¡Hola! Soy AgroBot 🌱 Tu asistente del Sistema Agrícola del Valle Jequetepeque. ¿En qué puedo ayudarte hoy?' }],
    },
    ...historial.map((m) => ({
      role: m.role === 'bot' ? 'model' : 'user',
      parts: [{ text: m.text }],
    })),
  ];

  const res = await fetch(`${GEMINI_URL}?key=${apiKey}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contents,
      generationConfig: {
        temperature: 0.7,
        topP: 0.9,
        maxOutputTokens: 512,
      },
    }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err?.error?.message || `HTTP ${res.status}`);
  }

  const data = await res.json();
  return data.candidates?.[0]?.content?.parts?.[0]?.text || 'No obtuve respuesta. Intenta de nuevo.';
}

/* ─────────────────────────────────────────────────
   COMPONENTE PRINCIPAL
───────────────────────────────────────────────── */
export default function ChatBot() {
  const { theme, lang } = useThemeAndLang();
  const isDark = theme === 'dark';

  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'bot', text: lang === 'en'
      ? '👋 Hi! I\'m AgroBot 🌱 Your assistant for the Jequetepeque Valley Agricultural System. How can I help you today?'
      : '👋 ¡Hola! Soy AgroBot 🌱 Tu asistente del Sistema Agrícola del Valle Jequetepeque. ¿En qué puedo ayudarte hoy?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [error, setError] = useState('');

  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const inputRef = useRef(null);

  const apiKey = process.env.REACT_APP_GEMINI_KEY || '';

  // Auto-scroll al último mensaje
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus en input al abrir
  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 300);
  }, [open]);

  // Inicializar SpeechRecognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const rec = new SpeechRecognition();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = lang === 'en' ? 'en-US' : 'es-PE';

    rec.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      setInput(transcript);
      setListening(false);
    };
    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);

    recognitionRef.current = rec;
  }, [lang]);

  // Síntesis de voz
  const speak = useCallback((text) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang === 'en' ? 'en-US' : 'es-PE';
    utterance.rate = 1.0;
    utterance.pitch = 1.05;
    utterance.onstart = () => setSpeaking(true);
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(utterance);
  }, [lang]);

  const stopSpeaking = () => {
    window.speechSynthesis?.cancel();
    setSpeaking(false);
  };

  // Enviar mensaje
  const sendMessage = useCallback(async (text) => {
    const trimmed = (text || input).trim();
    if (!trimmed || loading) return;

    if (!apiKey) {
      setError(lang === 'en'
        ? '⚠️ API key not configured. Add REACT_APP_GEMINI_KEY to your .env.local file.'
        : '⚠️ Clave API no configurada. Agrega REACT_APP_GEMINI_KEY en tu archivo .env.local');
      return;
    }

    setError('');
    const userMsg = { role: 'user', text: trimmed };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setInput('');
    setLoading(true);

    // Filtrar solo los últimos 10 mensajes para no gastar tokens
    const histForApi = newHistory.slice(-10);

    try {
      const botText = await askGemini(histForApi, apiKey);
      const botMsg = { role: 'bot', text: botText };
      setMessages((prev) => [...prev, botMsg]);
      speak(botText);
    } catch (err) {
      const errMsg = err.message?.includes('quota')
        ? (lang === 'en' ? '⚠️ Daily API limit reached. Try again tomorrow.' : '⚠️ Límite diario de API alcanzado. Intenta mañana.')
        : (lang === 'en' ? `❌ Error: ${err.message}` : `❌ Error: ${err.message}`);
      setMessages((prev) => [...prev, { role: 'bot', text: errMsg }]);
    } finally {
      setLoading(false);
    }
  }, [input, messages, loading, apiKey, lang, speak]);

  // Voz: iniciar/detener escucha
  const toggleListen = () => {
    if (!recognitionRef.current) return;
    if (listening) {
      recognitionRef.current.stop();
      setListening(false);
    } else {
      recognitionRef.current.start();
      setListening(true);
    }
  };

  // Enviar con Enter
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  /* ── ESTILOS ── */
  const chatBg = isDark ? '#0f172a' : '#ffffff';
  const headerBg = 'linear-gradient(135deg, #1b5e20 0%, #2e7d32 60%, #43a047 100%)';
  const msgUserBg = 'linear-gradient(135deg, #2e7d32, #43a047)';
  const msgBotBg = isDark ? '#1e293b' : '#f1f5f9';
  const msgBotColor = isDark ? '#f8fafc' : '#1e293b';
  const inputBg = isDark ? '#1e293b' : '#f8fafc';
  const inputBorder = isDark ? '#334155' : '#e2e8f0';
  const borderColor = isDark ? '#334155' : '#e2e8f0';

  return (
    <>
      {/* ── VENTANA DE CHAT ── */}
      <div
        style={{
          position: 'fixed',
          bottom: '94px',
          right: '24px',
          width: open ? '370px' : '0px',
          height: open ? '520px' : '0px',
          opacity: open ? 1 : 0,
          pointerEvents: open ? 'all' : 'none',
          transition: 'all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1)',
          borderRadius: '24px',
          boxShadow: '0 25px 60px rgba(0,0,0,0.35)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          zIndex: 9999,
          background: chatBg,
          border: `1px solid ${borderColor}`,
          transformOrigin: 'bottom right',
          transform: open ? 'scale(1)' : 'scale(0.5)',
        }}
      >
        {/* Header */}
        <div style={{
          background: headerBg,
          padding: '14px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          flexShrink: 0,
        }}>
          <div style={{
            width: '38px', height: '38px', borderRadius: '50%',
            background: 'rgba(255,255,255,0.2)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.2rem', flexShrink: 0,
            animation: speaking ? 'pulse-bot 0.8s ease-in-out infinite' : 'none',
          }}>🌱</div>
          <div style={{ flex: 1 }}>
            <div style={{ color: 'white', fontWeight: '700', fontSize: '0.95rem' }}>AgroBot</div>
            <div style={{ color: 'rgba(255,255,255,0.75)', fontSize: '0.75rem' }}>
              {loading ? (lang === 'en' ? '⏳ Thinking...' : '⏳ Pensando...')
                : speaking ? (lang === 'en' ? '🔊 Speaking...' : '🔊 Hablando...')
                : (lang === 'en' ? '✅ Online' : '✅ En línea')}
            </div>
          </div>
          {speaking && (
            <button onClick={stopSpeaking} title={lang === 'en' ? 'Stop voice' : 'Detener voz'} style={{
              background: 'rgba(255,255,255,0.2)', border: 'none', borderRadius: '8px',
              color: 'white', padding: '5px 10px', cursor: 'pointer', fontSize: '0.8rem',
            }}>🔇</button>
          )}
          <button onClick={() => setOpen(false)} style={{
            background: 'rgba(255,255,255,0.15)', border: 'none', borderRadius: '50%',
            width: '28px', height: '28px', color: 'white', cursor: 'pointer',
            fontSize: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>✕</button>
        </div>

        {/* Mensajes */}
        <div style={{
          flex: 1, overflowY: 'auto', padding: '16px',
          display: 'flex', flexDirection: 'column', gap: '10px',
          scrollbarWidth: 'thin',
          scrollbarColor: isDark ? '#334155 transparent' : '#e2e8f0 transparent',
        }}>
          {messages.map((m, i) => (
            <div key={i} style={{
              display: 'flex',
              justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
              animation: 'fadeInMsg 0.25s ease',
            }}>
              {m.role === 'bot' && (
                <div style={{
                  width: '28px', height: '28px', borderRadius: '50%',
                  background: headerBg, display: 'flex',
                  alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.85rem', flexShrink: 0, marginRight: '8px',
                  alignSelf: 'flex-end',
                }}>🌱</div>
              )}
              <div style={{
                maxWidth: '80%',
                padding: '10px 14px',
                borderRadius: m.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                background: m.role === 'user' ? msgUserBg : msgBotBg,
                color: m.role === 'user' ? 'white' : msgBotColor,
                fontSize: '0.875rem',
                lineHeight: '1.5',
                boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}>
                {m.text}
              </div>
            </div>
          ))}

          {/* Indicador de escritura */}
          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '28px', height: '28px', borderRadius: '50%',
                background: headerBg, display: 'flex',
                alignItems: 'center', justifyContent: 'center', fontSize: '0.85rem',
              }}>🌱</div>
              <div style={{
                background: msgBotBg, padding: '10px 16px',
                borderRadius: '18px 18px 18px 4px',
                display: 'flex', gap: '5px', alignItems: 'center',
              }}>
                {[0, 1, 2].map((d) => (
                  <div key={d} style={{
                    width: '7px', height: '7px', borderRadius: '50%',
                    background: '#4ade80',
                    animation: `typing-dot 1.2s ease-in-out ${d * 0.2}s infinite`,
                  }} />
                ))}
              </div>
            </div>
          )}

          {error && (
            <div style={{
              background: '#ffebee', color: '#c62828', padding: '10px 14px',
              borderRadius: '12px', fontSize: '0.82rem', border: '1px solid #ef9a9a',
            }}>{error}</div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div style={{
          padding: '12px 14px',
          borderTop: `1px solid ${borderColor}`,
          display: 'flex', gap: '8px', alignItems: 'flex-end',
          background: isDark ? '#0f172a' : '#fff',
          flexShrink: 0,
        }}>
          {/* Botón de micrófono */}
          <button
            onClick={toggleListen}
            title={listening
              ? (lang === 'en' ? 'Stop recording' : 'Detener grabación')
              : (lang === 'en' ? 'Voice input' : 'Entrada de voz')}
            style={{
              width: '40px', height: '40px', borderRadius: '50%', border: 'none',
              background: listening
                ? 'linear-gradient(135deg, #e53935, #b71c1c)'
                : (isDark ? '#1e293b' : '#f1f5f9'),
              color: listening ? 'white' : (isDark ? '#94a3b8' : '#64748b'),
              cursor: 'pointer', fontSize: '1.1rem',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0, transition: 'all 0.2s',
              animation: listening ? 'pulse-mic 1s ease-in-out infinite' : 'none',
              boxShadow: listening ? '0 0 12px rgba(229,57,53,0.5)' : 'none',
            }}
          >
            {listening ? '⏹️' : '🎤'}
          </button>

          {/* Campo de texto */}
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={lang === 'en' ? 'Ask me about the app...' : 'Pregúntame sobre la app...'}
            rows={1}
            style={{
              flex: 1, border: `1px solid ${inputBorder}`,
              borderRadius: '20px', padding: '10px 16px',
              fontSize: '0.875rem', resize: 'none', outline: 'none',
              background: inputBg, color: isDark ? '#f8fafc' : '#1e293b',
              lineHeight: '1.4', maxHeight: '100px', overflowY: 'auto',
              fontFamily: "'Segoe UI', sans-serif",
              transition: 'border-color 0.2s',
            }}
            onFocus={(e) => e.target.style.borderColor = '#2e7d32'}
            onBlur={(e) => e.target.style.borderColor = inputBorder}
          />

          {/* Botón enviar */}
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || loading}
            style={{
              width: '40px', height: '40px', borderRadius: '50%', border: 'none',
              background: input.trim() && !loading
                ? 'linear-gradient(135deg, #2e7d32, #43a047)'
                : (isDark ? '#1e293b' : '#e2e8f0'),
              color: input.trim() && !loading ? 'white' : (isDark ? '#475569' : '#94a3b8'),
              cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
              fontSize: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0, transition: 'all 0.2s',
              boxShadow: input.trim() && !loading ? '0 4px 12px rgba(46,125,50,0.4)' : 'none',
            }}
          >
            {loading ? '⏳' : '➤'}
          </button>
        </div>
      </div>

      {/* ── BOTÓN ESFÉRICO ── */}
      <button
        onClick={() => setOpen((p) => !p)}
        aria-label="AgroBot"
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          width: '62px',
          height: '62px',
          borderRadius: '50%',
          border: 'none',
          cursor: 'pointer',
          zIndex: 10000,
          background: open
            ? 'linear-gradient(135deg, #c62828, #e53935)'
            : 'linear-gradient(135deg, #1b5e20 0%, #2e7d32 50%, #43a047 100%)',
          boxShadow: open
            ? '0 8px 25px rgba(198,40,40,0.5)'
            : '0 8px 25px rgba(46,125,50,0.55), 0 0 0 0 rgba(46,125,50,0.4)',
          fontSize: '1.6rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
          animation: open ? 'none' : 'sphere-pulse 2.5s ease-in-out infinite',
          transform: open ? 'rotate(0deg) scale(1)' : 'scale(1)',
        }}
      >
        <span style={{
          transition: 'transform 0.3s ease',
          display: 'block',
          transform: open ? 'rotate(90deg)' : 'rotate(0deg)',
        }}>
          {open ? '✕' : '🌱'}
        </span>
      </button>

      {/* ── ANIMACIONES CSS ── */}
      <style>{`
        @keyframes sphere-pulse {
          0%   { box-shadow: 0 8px 25px rgba(46,125,50,0.55), 0 0 0 0 rgba(46,125,50,0.5); }
          70%  { box-shadow: 0 8px 25px rgba(46,125,50,0.55), 0 0 0 14px rgba(46,125,50,0); }
          100% { box-shadow: 0 8px 25px rgba(46,125,50,0.55), 0 0 0 0 rgba(46,125,50,0); }
        }
        @keyframes typing-dot {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
          30%            { transform: translateY(-6px); opacity: 1; }
        }
        @keyframes fadeInMsg {
          from { opacity: 0; transform: translateY(8px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse-bot {
          0%, 100% { transform: scale(1); }
          50%       { transform: scale(1.15); }
        }
        @keyframes pulse-mic {
          0%, 100% { box-shadow: 0 0 0 0 rgba(229,57,53,0.6); }
          50%       { box-shadow: 0 0 0 10px rgba(229,57,53,0); }
        }
      `}</style>
    </>
  );
}
