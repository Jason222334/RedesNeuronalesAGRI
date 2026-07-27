"""
Router del Chatbot IA — AgroBot
Usa Groq (primario, 14,400 req/día GRATIS) con Gemini como fallback.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import os
import urllib.request
import urllib.error
import json

router = APIRouter()

# ── Sistema prompt con conocimiento completo de la app ──
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
    role: str   # 'user' o 'bot'
    text: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


def _http_post(url: str, headers: dict, body: dict, timeout: int = 30):
    """Hace POST con urllib (sin dependencias externas)."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ─────────────────────────────────────────────
# PROVEEDOR 1: GROQ (primario, 14,400 req/día)
# ─────────────────────────────────────────────
def call_groq(messages_for_api: list, api_key: str) -> str:
    body = {
        "model": "llama-3.1-8b-instant",
        "messages": messages_for_api,
        "max_tokens": 512,
        "temperature": 0.7,
    }
    data = _http_post(
        "https://api.groq.com/openai/v1/chat/completions",
        {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        body
    )
    return data["choices"][0]["message"]["content"]


# ─────────────────────────────────────────────
# PROVEEDOR 2: GEMINI (fallback)
# ─────────────────────────────────────────────
GEMINI_MODELS = [
    "gemini-1.5-flash-8b",   # 1,500 req/día (más generoso)
    "gemini-1.5-flash-latest",
    "gemini-2.0-flash",
]
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

def call_gemini(recent_messages: list, api_key: str) -> str:
    contents = [
        {"role": "user",  "parts": [{"text": SYSTEM_PROMPT + "\n\nEl usuario acaba de abrir el chat."}]},
        {"role": "model", "parts": [{"text": "¡Hola! Soy AgroBot 🌱 ¿En qué puedo ayudarte hoy?"}]},
        *[
            {"role": "model" if m.role == "bot" else "user", "parts": [{"text": m.text}]}
            for m in recent_messages
        ]
    ]
    body = {"contents": contents, "generationConfig": {"temperature": 0.7, "maxOutputTokens": 512}}

    last_error = "Sin respuesta de Gemini"
    for model in GEMINI_MODELS:
        url = f"{GEMINI_BASE}/{model}:generateContent?key={api_key}"
        try:
            data = _http_post(url, {"Content-Type": "application/json"}, body)
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode())
                last_error = err_body.get("error", {}).get("message", str(e))
            except Exception:
                last_error = str(e)
            if e.code in (404, 429) or "not found" in last_error.lower():
                continue
            raise HTTPException(status_code=e.code, detail=f"Gemini [{model}]: {last_error}")

    raise HTTPException(status_code=429, detail=f"Gemini cuota agotada: {last_error}")


# ─────────────────────────────────────────────
# ENDPOINT PRINCIPAL
# ─────────────────────────────────────────────
@router.post("/api/chatbot/message")
async def chatbot_message(req: ChatRequest):
    groq_key   = os.getenv("GROQ_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not groq_key and not gemini_key:
        raise HTTPException(
            status_code=500,
            detail="No hay clave de IA configurada. Agrega GROQ_API_KEY o GEMINI_API_KEY en las variables de entorno de Render."
        )

    recent = req.messages[-10:]

    # ── Intentar Groq primero ──
    if groq_key:
        messages_for_groq = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in recent:
            messages_for_groq.append({
                "role": "assistant" if m.role == "bot" else "user",
                "content": m.text
            })
        try:
            text = call_groq(messages_for_groq, groq_key)
            return {"response": text, "provider": "groq"}
        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode())
                err_msg = err_body.get("error", {}).get("message", str(e))
            except Exception:
                err_msg = str(e)
            # Si Groq falla por cuota, intentar Gemini
            if e.code == 429 and gemini_key:
                pass  # continuar a Gemini
            else:
                raise HTTPException(status_code=e.code, detail=f"Groq: {err_msg}")
        except Exception as e:
            if gemini_key:
                pass  # continuar a Gemini
            else:
                raise HTTPException(status_code=500, detail=f"Groq: {str(e)}")

    # ── Fallback a Gemini ──
    if gemini_key:
        try:
            text = call_gemini(recent, gemini_key)
            return {"response": text, "provider": "gemini"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gemini: {str(e)}")

    raise HTTPException(status_code=503, detail="Todos los proveedores de IA fallaron.")
