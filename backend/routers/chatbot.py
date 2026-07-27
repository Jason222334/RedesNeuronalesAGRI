"""
Router del Chatbot IA — AgroBot
Llama a Gemini API desde el backend para evitar problemas de CORS y exposición de claves.
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

=== DESCRIPCIÓN DE LA APP ===
La app es un sistema de soporte de decisiones agrícolas con predicción de precios usando modelos de ML.
Backend: FastAPI (Python) en Render. Frontend: React en Vercel. Base de datos: PostgreSQL en Supabase.

=== MÓDULOS DE LA APP ===

1. DASHBOARD (/)
   - Panel principal con gráficos de precios por cultivo (barras y torta)
   - Calculadora de Rentabilidad: el usuario ingresa cultivo, hectáreas, horizonte de venta y costo logístico → la IA predice precio y calcula utilidades
   - Asistente de Siembra: compara rentabilidad proyectada de los 4 cultivos
   - Alerta de Riesgo de Plagas: consulta el riesgo (Bajo/Medio/Alto)
   - Gestión de Reportes: exporta bitácora en PDF, Excel o CSV

2. GESTIÓN DE CULTIVOS (/cultivos)
   - Lista todos los cultivos con nombre, precio, temperatura, precipitación, costo transporte y nivel de plaga
   - Permite registrar, editar y eliminar cultivos
   - Solo para administradores

3. GESTIÓN DE DATOS (/datos)
   - Subida de dataset CSV para reentrenar los modelos
   - Panel de entrenamiento con log en tiempo real
   - Vista previa de los datos cargados

4. MÓDULO IA (/ia) — 6 pestañas:
   a) ESTADO: muestra módulos completados, botón para ejecutar pipeline EDA + 5 modelos
   b) MODELOS: tabla comparativa con RMSE, MAE, R², MAPE, tiempo de los 5 modelos
   c) CROSS-VALIDATION: TimeSeriesSplit (5 folds), evita data leakage
   d) HIPERPARÁMETROS: Optuna (búsqueda bayesiana) para RF y XGBoost, Grid Search para ARIMA
   e) PRUEBAS ESTADÍSTICAS: Shapiro-Wilk, Ljung-Box, Kolmogorov-Smirnov, Wilcoxon, Diebold-Mariano
   f) REPORTES: descarga PDF, Excel, Word; acceso a Streamlit App

5. AUDITORÍA (/auditoria)
   - Historial completo de actividad del sistema
   - Gráfico de visitas diarias. Solo para administradores.

6. GESTIÓN USUARIOS (/usuarios)
   - Lista usuarios, cambia contraseñas y roles, elimina usuarios. Solo para administradores.

=== MODELOS DE IA (5 modelos) ===
1. ARIMA(5,1,2): modelo clásico de series temporales univariado para precios del Arroz
2. Random Forest: ensemble de árboles con features climáticos y lags. R² ≈ 0.90
3. XGBoost: gradient boosting optimizado con Optuna. Suele ser el mejor modelo
4. LSTM: Long Short-Term Memory, red neuronal recurrente
5. CNN-LSTM: Convolucional + Recurrente, extrae patrones locales y temporales

=== CULTIVOS DEL SISTEMA ===
- Arroz: 800-1400 S/ton
- Maíz: 500-900 S/ton
- Cebolla: 300-1200 S/ton (alta variabilidad)
- Espárrago: 1500-3500 S/ton (el más rentable)

=== MÉTRICAS IA ===
- R² (coeficiente de determinación): más cercano a 1 es mejor
- RMSE (error cuadrático medio): más bajo es mejor
- MAE (error absoluto medio): más bajo es mejor
- MAPE (error porcentual absoluto medio): más bajo es mejor

=== PRUEBAS ESTADÍSTICAS ===
- Shapiro-Wilk: normalidad de residuos (H₀: normalidad)
- Ljung-Box: autocorrelación de residuos (H₀: no autocorrelación)
- Kolmogorov-Smirnov: distribución de errores vs normal
- Wilcoxon: comparación no paramétrica de modelos
- Diebold-Mariano: compara capacidad predictiva de dos modelos

=== INSTRUCCIONES ===
- Responde en el idioma en que te preguntan (español o inglés)
- Sé conciso: máximo 3-4 oraciones, salvo que pidan detalle
- Si preguntan algo fuera de la app, di que solo puedes ayudar con el sistema agrícola
- Usa emojis con moderación"""

GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-8b",
    "gemini-1.5-flash",
]
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class ChatMessage(BaseModel):
    role: str   # 'user' o 'bot'
    text: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


@router.post("/api/chatbot/message")
async def chatbot_message(req: ChatRequest):
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY no está configurada en el servidor. Agrégala como variable de entorno en Render."
        )

    # Tomar los últimos 10 mensajes para no gastar tokens
    recent = req.messages[-10:]

    contents = [
        {
            "role": "user",
            "parts": [{"text": SYSTEM_PROMPT + "\n\n---\nEmpecemos. El usuario acaba de abrir el chat."}]
        },
        {
            "role": "model",
            "parts": [{"text": "¡Hola! Soy AgroBot 🌱 Tu asistente del Sistema Agrícola del Valle Jequetepeque. ¿En qué puedo ayudarte hoy?"}]
        },
        *[
            {
                "role": "model" if m.role == "bot" else "user",
                "parts": [{"text": m.text}]
            }
            for m in recent
        ]
    ]

    body = json.dumps({
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.9,
            "maxOutputTokens": 512
        }
    }).encode("utf-8")

    last_error = None
    last_status = None

    for model in GEMINI_MODELS:
        url = f"{GEMINI_BASE}/{model}:generateContent?key={api_key}"
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return {"response": text, "model": model}

        except urllib.error.HTTPError as e:
            last_status = e.code
            try:
                err_data = json.loads(e.read().decode("utf-8"))
                err_msg = err_data.get("error", {}).get("message", str(e))
            except Exception:
                err_msg = str(e)

            last_error = err_msg

            # Si el modelo no existe, probar el siguiente
            if e.code == 404 or "not found" in err_msg.lower() or "not supported" in err_msg.lower():
                continue

            # Cualquier otro error: retornar con detalle
            raise HTTPException(
                status_code=e.code,
                detail=f"Error Gemini API [{model}]: {err_msg}"
            )

        except urllib.error.URLError as e:
            last_error = str(e)
            raise HTTPException(status_code=503, detail=f"No se pudo conectar a Gemini: {last_error}")

    # Si ningún modelo funcionó
    raise HTTPException(
        status_code=502,
        detail=f"Ningún modelo de Gemini respondió correctamente. Último error (HTTP {last_status}): {last_error}"
    )
