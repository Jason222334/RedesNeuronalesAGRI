# 🌾 Sistema Inteligente Agricola — Valle Jequetepeque
> **Plataforma Web de Soporte a Decisiones Agrícolas, Predicción de Precios con Inteligencia Artificial (ML/DL) y Asistente Virtual Multimodal**  
> *Desarrollado por: 
GALVEZ LUNA JASON ANDERSON
FLORIAN AREVALO JOEL ANDERSON 
— Universidad Nacional de Trujillo (UNT)*

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/Database-Supabase_PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://supabase.com)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com)
[![License](https://img.shields.io/badge/License-MIT-green.style=for-the-badge)](LICENSE)

---

## 📌 Tabla de Contenidos
- [Visión General](#-visión-general)
- [Características Principales](#-características-principales)
- [Modelos de Inteligencia Artificial](#-modelos-de-inteligencia-artificial)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Chatbot Inteligente — AgroBot 🌱](#-chatbot-inteligente--agrobot-)
- [Guía de Instalación y Ejecución Local](#-guía-de-instalación-y-ejecución-local)
- [Variables de Entorno](#-variables-de-entorno)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Pruebas Estadísticas y Reportes](#-pruebas-estadísticas-y-reportes)
- [Licencia](#-licencia)

---

## 🌾 Visión General

El **Sistema Inteligente Agrícola del Valle Jequetepeque** es una solución integral desacoplada (Client-Server) concebida para apoyar a agricultores, cooperativas y tomadores de decisiones en la predicción del valor de venta de los principales cultivos de la cuenca del Río Jequetepeque (**Arroz, Maíz, Cebolla y Espárrago**).

Integra modelos econométricos tradicionales, algoritmos de Machine Learning en ensambles y arquitecturas de aprendizaje profundo (Deep Learning) combinadas con análisis climático y logístico.

---

## ⚡ Características Principales

- 📊 **Dashboard Ejecutivo Interactivo**: Visualización gráfica en tiempo real (Recharts) de la tendencia histórica y proyectada de los precios por tonelada.
- 💡 **Calculadora de Rentabilidad Financiera (IA)**: Permite ingresar hectáreas sembradas, horizonte temporal de venta (1 a 12 meses) y costos de transporte para estimar el precio futuro, margen bruto y utilidad proyectada.
- 🌱 **Asistente de Recomendación de Siembra**: Evalúa y rankea los 4 cultivos según rentabilidad proyectada en el horizonte seleccionado.
- 🐛 **Alerta y Evaluación de Riesgo de Plagas**: Clasificación multinivel (Bajo, Medio, Alto) en función de variables climáticas (temperatura y precipitación).
- 🌐 **Sistema Bilingüe Nativo (Español 🇪🇸 / Inglés 🇬🇧)**: Cambio dinámico de idioma con persistencia en `localStorage`.
- 🌙 **Motor de Temas (Modo Claro ☀️ / Oscuro 🌙)**: Interfaz adaptativa con paleta de colores personalizada de alto contraste para reducir fatiga visual.
- 🤖 **AgroBot — Chatbot Multimodal con Voz**: Asistente flotante con reconocimiento de voz (Web Speech API), síntesis vocal y backend LLM inteligente (Groq / Gemini / OpenRouter).
- 📄 **Exportación de Reportes**: Generación automática de certificados y reportes operacionales en formato PDF (jsPDF + autoTable), Excel y CSV.
- 🔒 **Módulo de Auditoría y Bitácora del Sistema**: Registro detallado de accesos, predicciones ejecutadas y cambios por usuario para trazabilidad y seguridad.

---

## 🧠 Modelos de Inteligencia Artificial

El sistema compara y evalúa **5 modelos predictivos** sobre el dataset histórico agrícola 2019–2024:

| Modelo | Familia | Tipo de Arquitectura | Propósito / Características |
|---|---|---|---|
| **ARIMA(5,1,2)** | Econométrico | Serie Temporal Univariada | Modelo de referencia para tendencia temporal directa |
| **Random Forest** | ML Ensamble | Bagging de Árboles de Decisión | Captura relaciones no lineales con variables climáticas ($R^2 \approx 0.90$) |
| **XGBoost** | ML Ensamble | Gradient Boosting Optimizado | Optimización bayesiana de hiperparámetros con Optuna |
| **LSTM** | Deep Learning | Recurrent Neural Network | Red de memoria a largo y corto plazo para secuencias temporales |
| **CNN-LSTM** | DL Híbrido | Convolucional 1D + LSTM | Extrae patrones temporales locales y dependencias secuenciales a largo plazo |

### 🔬 Pruebas Estadísticas de Validación
Los residuos y resultados de los modelos son validados con 5 familias de pruebas estadísticas:
1. **Shapiro-Wilk**: Prueba de normalidad de residuos ($H_0$: los residuos son normales).
2. **Ljung-Box**: Evaluación de autocorrelación en los residuos.
3. **Kolmogorov-Smirnov**: Comparación de la distribución de errores frente a la distribución teórica normal.
4. **Prueba de Wilcoxon**: Prueba no paramétrica para rangos con signo entre predicciones.
5. **Diebold-Mariano**: Comparación formal de la capacidad predictiva entre parejas de modelos.

---

## 🏗 Arquitectura del Sistema

El proyecto sigue una arquitectura desacoplada RESTful de tres capas:

```mermaid
graph TD
    Client[Cliente / Navegador Web - React 18] -->|HTTPS / Axios| API[Backend FastAPI - Python 3.12]
    API -->|ORM SQLAlchemy| DB[(Supabase PostgreSQL)]
    API -->|Módulo IA| ML[Engine ML / ML Model]
    API -->|LLM API / Fallback| ChatBot[AgroBot Engine - Groq / Gemini / Local]
    Client -->|Web Speech API| Speech[Voz / Micrófono & Altavoz Nativo]
```

---

## 🤖 Chatbot Inteligente — AgroBot 🌱

Ubicado en un botón esférico flotante animado en la esquina inferior derecha, **AgroBot** ofrece soporte continuo sobre el sistema:

- **Entrada Doble**: Vía teclado o micrófono (vocalización en español e inglés).
- **Lectura Vocal**: Síntesis de voz automática (`SpeechSynthesis`) para escuchar las respuestas del bot.
- **Arquitectura en Cascada Resiliente**:
  1. **Groq API** (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`) — *Ultrarrápido*
  2. **Google Gemini API** (`gemini-2.0-flash`) — *Respaldo*
  3. **OpenRouter Free Tier** — *Respaldo secundario*
  4. **Motor de Conocimiento Conversacional Local** — *Garantía de respuesta 100% libre de errores*

---

## 🚀 Guía de Instalación y Ejecución Local

### Prerrequisitos
- Python 3.10+ (Recomendado Python 3.12)
- Node.js 18+ y npm

### 1. Clonar el Repositorio
```bash
git clone https://github.com/Jason222334/RedesNeuronalesAGRI.git
cd RedesNeuronalesAGRI
```

### 2. Configurar y Ejecutar el Backend (FastAPI)
```bash
cd backend
python -m venv venv

# En Windows:
venv\Scripts\activate
# En Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
- API Backend: `http://localhost:8000`
- Documentación OpenAPI Swagger: `http://localhost:8000/docs`

### 3. Configurar y Ejecutar el Frontend (React)
```bash
cd ../frontend
npm install
npm start
```
- Aplicación Web: `http://localhost:3000`

---

## 🔐 Variables de Entorno

### Frontend (`frontend/.env.local`)
```env
REACT_APP_API_URL=http://localhost:8000
```

### Backend (`backend/.env`)
```env
DATABASE_URL=postgresql://postgres.aephgcnbsomypsedvtyk:PASS@aws-1-us-east-2.pooler.supabase.com:6543/postgres
GROQ_API_KEY=gsk_tu_clave_aqui
GEMINI_API_KEY=tu_clave_gemini_aqui
```

---

## 📁 Estructura del Proyecto

```
RedesNeuronalesAGRI/
├── backend/
│   ├── main.py                  # Entrypoint FastAPI y ruteo principal
│   ├── database.py              # Conexión SQLAlchemy (PostgreSQL / SQLite)
│   ├── models_db.py             # Modelos ORM (Cultivos, Usuarios, Bitácora)
│   ├── requirements.txt         # Dependencias backend optimizadas
│   ├── data/
│   │   └── dataset_precios_jequetepeque.csv # Dataset histórico agrícola 2019-2024
│   ├── ml_model/
│   │   ├── predict.py           # Inferencia de precios y riesgo de plaga
│   │   ├── train_models.py      # Pipeline de entrenamiento de los 5 modelos
│   │   ├── eda.py               # Módulo EDA y generación de gráficos
│   │   ├── cross_validation.py  # Validación cruzada TimeSeriesSplit
│   │   ├── hyperparameter_tuning.py # Optuna + Grid Search
│   │   ├── statistical_tests.py # Pruebas estadísticas formales
│   │   └── report_generator.py  # Exportador PDF, Excel y Word
│   └── routers/
│       ├── cultivos.py          # CRUD de Cultivos
│       ├── usuarios.py          # Gestión de usuarios y credenciales
│       ├── auditoria.py         # Bitácora y métricas de uso
│       ├── reportes.py          # Endpoints de exportación
│       ├── ia_analysis.py       # Endpoints del Módulo IA
│       └── chatbot.py           # Engine proxy resiliente de AgroBot
├── frontend/
│   ├── src/
│   │   ├── App.js               # Dashboard principal y enrutador SPA
│   │   ├── config.js            # Configuración dinámica de URLs de API
│   │   ├── context/
│   │   │   └── ThemeAndLangContext.js # Provider de idioma (ES/EN) y tema (Claro/Oscuro)
│   │   ├── components/
│   │   │   ├── MenuNavegacion.js # Sidebar responsivo con toggles
│   │   │   └── ChatBot.js       # Componente esférico del chatbot multimodal
│   │   └── pages/
│   │       ├── Login.js         # Autenticación de usuarios
│   │       ├── GestionCultivos.js # Administración de catálogo agrícola
│   │       ├── GestionUsuarios.js # Gestión de permisos y roles
│   │       ├── GestionDatos.js   # Carga y reentrenamiento de dataset
│   │       ├── Auditoria.js     # Bitácora operacional
│   │       └── ModuloIA.js      # Dashboard científico de 6 pestañas de IA
│   └── package.json
└── README.md
```

---

## 🔑 Credenciales Predeterminadas (Demostración)

| Rol | Correo Electrónico | Contraseña | Permisos |
|---|---|---|---|
| **Administrador** | `admin@unt.pe` | `admin123` | Acceso total a todos los módulos y gestión |
| **Usuario Agrícola** | `usuario@unt.pe` | `123456` | Acceso al Dashboard, Calculadora e IA |

---

## 📜 Licencia

Este proyecto está bajo la Licencia **MIT**. Consulta el archivo `LICENSE` para más detalles.

---

<div align="center">
  <b>Desarrollado con ❤️ para el Valle Jequetepeque — Universidad Nacional de Trujillo</b>
</div>
