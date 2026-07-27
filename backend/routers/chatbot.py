"""
Router del Chatbot IA — AgroBot
Sistema ultra-resiliente con sanitización de claves (limpieza de comillas),
búsqueda en cascada de modelos Groq/Gemini/OpenRouter y motor conversacional inteligente local.
Garantiza 100% de respuestas exitosas en cualquier circunstancia.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import os
import urllib.request
import urllib.error
import json
import logging
import re

logger = logging.getLogger(__name__)
router = APIRouter()

SYSTEM_PROMPT = """Eres AgroBot, el asistente inteligente del Sistema Agrícola del Valle Jequetepeque (Perú).
Respondes preguntas sobre la aplicación web de gestión agrícola. Eres amigable, preciso y conciso.
Responde siempre en el idioma en que te preguntan (español o inglés).
Sé conciso: máximo 3-4 oraciones, salvo que pidan detalle.
Si preguntan algo fuera de la app, di que solo puedes ayudar con el sistema agrícola.
Usa emojis con moderación.

=== DESCRIPCIÓN DE LA APP ===
Sistema de soporte de decisiones agrícolas con predicción de precios usando modelos de ML/DL.
Backend: FastAPI (Python) en Render. Frontend: React en Vercel. BD: PostgreSQL en Supabase.

=== MÓDULOS ===
1. DASHBOARD (/): Panel con gráficos, Calculadora de Rentabilidad (cultivo + hectáreas + horizonte + costo logístico → precio IA + utilidades), Asistente de Siembra (compara los 4 cultivos), Alerta de Plagas (Bajo/Medio/Alto), Reportes (PDF/Excel/CSV).
2. GESTIÓN DE CULTIVOS (/cultivos): Catálogo con precio, temperatura, precipitación, costo transporte, nivel de plaga. CRUD solo para admins.
3. GESTIÓN DE DATOS (/datos): Subida CSV para reentrenar modelos, log en tiempo real del entrenamiento.
4. MÓDULO IA (/ia) — 6 pestañas:
   - ESTADO: módulos completados + botón pipeline EDA+5modelos
   - MODELOS: tabla comparativa RMSE, MAE, R², MAPE, tiempo
   - CROSS-VALIDATION: TimeSeriesSplit 5 folds (evita data leakage)
   - HIPERPARÁMETROS: Optuna (bayesiana) para RF/XGBoost, Grid Search para ARIMA
   - PRUEBAS ESTADÍSTICAS: Shapiro-Wilk, Ljung-Box, KS, Wilcoxon, Diebold-Mariano
   - REPORTES: PDF, Excel, Word; acceso a Streamlit App
5. AUDITORÍA (/auditoria): Historial actividad + gráfico visitas diarias. Solo admins.
6. USUARIOS (/usuarios): Gestión usuarios, roles, contraseñas. Solo admins.

=== 5 MODELOS DE IA ===
1. ARIMA(5,1,2): serie temporal clásica univariada para Arroz
2. Random Forest: ensemble de árboles con features climáticos y lags, R²≈0.90
3. XGBoost: gradient boosting optimizado con Optuna, suele ser el mejor
4. LSTM: red neuronal recurrente, captura dependencias largas
5. CNN-LSTM: Convolucional+Recurrente, extrae patrones locales y temporales

=== CULTIVOS ===
Arroz: 800-1400 S/ton | Maíz: 500-900 S/ton | Cebolla: 300-1200 S/ton | Espárrago: 1500-3500 S/ton (más rentable)

=== MÉTRICAS IA ===
R²: más cercano a 1 es mejor | RMSE, MAE, MAPE: más bajo es mejor | AIC: para ARIMA, más bajo es mejor

=== PRUEBAS ESTADÍSTICAS ===
Shapiro-Wilk: normalidad residuos | Ljung-Box: autocorrelación | KS: distribución errores | Wilcoxon: comparación no paramétrica | Diebold-Mariano: capacidad predictiva entre modelos"""


class ChatMessage(BaseModel):
    role: str
    text: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


def clean_key(val: str) -> str:
    """Limpia comillas dobles, simples, espacios y saltos de línea accidentalmente pegados."""
    if not val:
        return ""
    val = val.strip().strip('"').strip("'").strip()
    return val


def _http_post(url: str, headers: dict, body: dict, timeout: int = 12) -> str:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


# ── GROQ MODELS ──
GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it"
]


def try_groq(messages_for_api: list, api_key: str) -> str:
    cleaned = clean_key(api_key)
    if not cleaned:
        raise ValueError("Sin clave Groq")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cleaned}",
        "User-Agent": "Mozilla/5.0 (FastAPI-AgroBot)"
    }

    for model in GROQ_MODELS:
        body = {
            "model": model,
            "messages": messages_for_api,
            "max_tokens": 512,
            "temperature": 0.7,
        }
        try:
            raw = _http_post("https://api.groq.com/openai/v1/chat/completions", headers, body)
            data = json.loads(raw)
            text = data["choices"][0]["message"]["content"]
            if text and len(text.strip()) > 0:
                return text.strip()
        except Exception as e:
            logger.warning(f"Groq modelo {model} falló: {e}")
            continue
    raise Exception("Todos los modelos Groq fallaron o clave inválida")


# ── GEMINI MODELS ──
GEMINI_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash-latest", "gemini-1.5-flash-8b", "gemini-1.5-flash"]
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def try_gemini(recent_messages: list, api_key: str) -> str:
    cleaned = clean_key(api_key)
    if not cleaned:
        raise ValueError("Sin clave Gemini")

    contents = [
        {"role": "user",  "parts": [{"text": SYSTEM_PROMPT + "\n\nEl usuario acaba de abrir el chat."}]},
        {"role": "model", "parts": [{"text": "¡Hola! Soy AgroBot 🌱 ¿En qué puedo ayudarte hoy?"}]},
        *[
            {"role": "model" if m.role == "bot" else "user", "parts": [{"text": m.text}]}
            for m in recent_messages
        ]
    ]
    body = {"contents": contents, "generationConfig": {"temperature": 0.7, "maxOutputTokens": 512}}

    for model in GEMINI_MODELS:
        url = f"{GEMINI_BASE}/{model}:generateContent?key={cleaned}"
        try:
            raw = _http_post(url, {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}, body)
            data = json.loads(raw)
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            if text and len(text.strip()) > 0:
                return text.strip()
        except Exception as e:
            logger.warning(f"Gemini {model} falló: {e}")
            continue
    raise Exception("Todos los modelos Gemini fallaron")


# ── OPENROUTER FREE MODELS (No Key Needed / Free Fallback) ──
OPENROUTER_FREE_MODELS = [
    "google/gemma-2-9b-it:free",
    "meta-llama/llama-3.2-1b-instruct:free",
    "qwen/qwen-2.5-7b-instruct:free"
]


def try_openrouter_free(messages_for_api: list) -> str:
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (FastAPI-AgroBot)"
    }
    for model in OPENROUTER_FREE_MODELS:
        body = {
            "model": model,
            "messages": messages_for_api,
            "max_tokens": 512,
            "temperature": 0.7,
        }
        try:
            raw = _http_post("https://openrouter.ai/api/v1/chat/completions", headers, body)
            data = json.loads(raw)
            text = data["choices"][0]["message"]["content"]
            if text and len(text.strip()) > 0:
                return text.strip()
        except Exception as e:
            logger.warning(f"OpenRouter {model} falló: {e}")
            continue
    raise Exception("OpenRouter free falló")


# ── SMART CONVERSATIONAL ENGINE (Garantía de respuesta siempre útil) ──
def smart_conversational_response(user_text: str, is_english: bool = False) -> str:
    q = user_text.lower()

    if is_english:
        if any(k in q for k in ["hello", "hi", "hey", "who are you"]):
            return "👋 Hi! I am AgroBot 🌱, your AI assistant for the Jequetepeque Valley Agricultural System. I can answer questions about crop price predictions, profitability calculations, ML models, statistical tests, and report generation."
        if any(k in q for k in ["model", "algorithm", "rf", "random forest", "xgboost", "arima", "lstm"]):
            return "🧠 The app evaluates 5 IA models: ARIMA(5,1,2), Random Forest (R²≈0.90), XGBoost (Optuna tuned), LSTM, and CNN-LSTM. You can compare their RMSE, MAE, R², and MAPE in the AI Module."
        if any(k in q for k in ["crop", "rice", "corn", "onion", "asparagus", "price"]):
            return "🌾 Supported crops: Rice (800-1400 S/ton), Corn (500-900 S/ton), Onion (300-1200 S/ton), and Asparagus (1500-3500 S/ton). Check the Profitability Calculator on the Dashboard for custom forecasts!"
        if any(k in q for k in ["calculator", "profit", "yield", "sow", "plant"]):
            return "💡 The Profitability Calculator lets you select a crop, planted hectares, sales horizon (1-12 months), and logistic costs to predict total revenue and net yield using trained ML models."
        if any(k in q for k in ["report", "pdf", "excel", "download", "word"]):
            return "📊 You can export operational reports (PDF/Excel/CSV) from the Dashboard, or full scientific reports (PDF/Excel/Word) with charts and statistical validation from the AI Module -> Reports tab."
        if any(k in q for k in ["stat", "test", "shapiro", "ljung", "wilcoxon"]):
            return "🔬 Validation includes 5 statistical tests: Shapiro-Wilk (residuals normality), Ljung-Box (autocorrelation), Kolmogorov-Smirnov, Wilcoxon, and Diebold-Mariano (model predictive accuracy)."
        return "🌱 Hi! I'm AgroBot. How can I help you with crop predictions, AI models, profitability estimates, or PDF reports for the Jequetepeque Valley?"

    # Español
    if re.search(r'\b(hola|buenas|buenos dias|buenas tardes|quien eres|quien sos)\b', q):
        return "👋 ¡Hola! Soy AgroBot 🌱, tu asistente virtual del Sistema Agrícola del Valle Jequetepeque. Puedo ayudarte con predicción de precios, la calculadora de rentabilidad, los 5 modelos de IA o la exportación de reportes."
    if any(k in q for k in ["modelo", "algoritmo", "random forest", "xgboost", "arima", "lstm", "cnn"]):
        return "🧠 El sistema utiliza 5 modelos de inteligencia artificial: ARIMA(5,1,2), Random Forest (R²≈0.90), XGBoost (optimizado con Optuna), LSTM y CNN-LSTM. Puedes revisar la tabla comparativa de RMSE, MAE, R² y MAPE en el **Módulo IA -> Modelos**."
    if any(k in q for k in ["cultivo", "arroz", "maiz", "maíz", "cebolla", "esparrago", "espárrago", "precio"]):
        return "🌾 El sistema analiza 4 cultivos principales del Valle Jequetepeque: Arroz (800-1400 S/ton), Maíz (500-900 S/ton), Cebolla (300-1200 S/ton) y Espárrago (1500-3500 S/ton, el más rentable)."
    if any(k in q for k in ["calculadora", "rentabilidad", "calcular", "siembra", "ganancia", "utilidad", "hectárea", "hectarea"]):
        return "💡 En la **Calculadora de Rentabilidad del Dashboard** ingresas tu cultivo, hectáreas sembradas, horizonte de tiempo (1 a 12 meses) y costos logísticos. La IA proyecta el precio estimado y calcula la utilidad neta esperada."
    if any(k in q for k in ["reporte", "pdf", "excel", "descargar", "word", "csv", "exportar"]):
        return "📊 Tienes dos opciones de reportes: Reportes operacionales en el **Dashboard** (PDF, Excel, CSV) y Reportes científicos estructurados en el **Módulo IA -> Reportes** (PDF, Excel, Word)."
    if any(k in q for k in ["prueba", "test", "shapiro", "ljung", "wilcoxon", "diebold", "estadistica", "estadística"]):
        return "🔬 Se realizan 5 pruebas estadísticas en el Módulo IA: Shapiro-Wilk (normalidad de residuos), Ljung-Box (autocorrelación), Kolmogorov-Smirnov, Wilcoxon y Diebold-Mariano (comparación predictiva)."
    if any(k in q for k in ["plaga", "riesgo", "alerta", "clima"]):
        return "🐛 El módulo de Alerta de Riesgo de Plagas clasifica el nivel de riesgo en Bajo, Medio o Alto evaluando temperatura, precipitación acumulada y humedad del Valle Jequetepeque."
    if any(k in q for k in ["usuario", "admin", "clave", "credenciales", "login", "contraseña"]):
        return "🔐 Las credenciales predeterminadas del sistema son:\n- Admin: `admin@unt.pe` / `admin123`\n- Usuario: `usuario@unt.pe` / `123456`"

    return "🌱 Hola, soy AgroBot. ¿En qué puedo ayudarte? Puedes preguntarme sobre la Calculadora de Rentabilidad, los 5 modelos de IA (ARIMA, Random Forest, XGBoost, LSTM, CNN-LSTM), la gestión de cultivos o la generación de reportes."


@router.post("/api/chatbot/message")
async def chatbot_message(req: ChatRequest):
    recent = req.messages[-10:]
    last_user_text = recent[-1].text if recent else ""
    is_english = any(w in last_user_text.lower() for w in ["the", "what", "how", "hello", "is", "crop", "price"])

    groq_key = os.getenv("GROQ_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")

    messages_for_groq = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in recent:
        messages_for_groq.append({"role": "assistant" if m.role == "bot" else "user", "content": m.text})

    # 1. Intentar Groq (con sanitización de clave)
    if groq_key:
        try:
            res_text = try_groq(messages_for_groq, groq_key)
            if res_text:
                return {"response": res_text, "provider": "groq"}
        except Exception as e:
            logger.warning(f"Intento Groq omitido/falló: {e}")

    # 2. Intentar Gemini (con sanitización de clave)
    if gemini_key:
        try:
            res_text = try_gemini(recent, gemini_key)
            if res_text:
                return {"response": res_text, "provider": "gemini"}
        except Exception as e:
            logger.warning(f"Intento Gemini omitido/falló: {e}")

    # 3. Intentar OpenRouter Free Tier
    try:
        res_text = try_openrouter_free(messages_for_groq)
        if res_text:
            return {"response": res_text, "provider": "openrouter-free"}
    except Exception as e:
        logger.warning(f"Intento OpenRouter Free omitido/falló: {e}")

    # 4. Motor de respuesta conversacional inteligente local (Respuesta garantizada al 100%)
    return {
        "response": smart_conversational_response(last_user_text, is_english),
        "provider": "smart-local"
    }
