# Sistema Inteligente Agrícola — Valle Jequetepeque
> Predicción de precios y gestión agrícola con IA | Universidad Nacional de Trujillo (UNT)

[![CI](https://github.com/TU_USUARIO/3c_sistema_agricolaa/actions/workflows/ci.yml/badge.svg)](https://github.com/TU_USUARIO/3c_sistema_agricolaa/actions/workflows/ci.yml)

## Descripción

Sistema de inteligencia artificial para la predicción de precios de productos agrícolas en el Valle Jequetepeque, Perú. Implementa 5 modelos predictivos:

| Modelo | Tipo | Descripción |
|--------|------|-------------|
| ARIMA(5,1,2) | Clásico | Serie temporal univariada |
| Random Forest | Clásico | Ensemble con features climáticos |
| XGBoost | Clásico | Gradient Boosting optimizado |
| **LSTM** | **Red Neuronal Híbrida** | Long Short-Term Memory |
| **CNN-LSTM** | **Red Neuronal Híbrida** | Convolucional + Recurrente |

## Arquitectura

```
3c_sistema_agricolaa/
├── backend/               # FastAPI (Python)
│   ├── main.py            # Punto de entrada
│   ├── ml_model/          # Módulo de IA
│   │   ├── eda.py              # Análisis exploratorio
│   │   ├── train_models.py     # 5 modelos (ARIMA, RF, XGB, LSTM, CNN-LSTM)
│   │   ├── cross_validation.py # TimeSeriesSplit k-folds
│   │   ├── hyperparameter_tuning.py  # Optuna + Grid Search
│   │   ├── statistical_tests.py      # Shapiro-Wilk, Ljung-Box, DM, KS, Wilcoxon
│   │   └── report_generator.py       # PDF, Excel, Word
│   ├── routers/           # Endpoints API REST
│   │   └── ia_analysis.py      # Módulo IA endpoints
│   └── data/
│       └── dataset_precios_jequetepeque.csv  # Dataset público 2019-2024
├── frontend/              # React (CRA)
│   └── src/pages/
│       └── ModuloIA.js    # Dashboard de resultados IA
├── streamlit_app/         # Módulo de análisis científico
│   └── app.py             # 6 tabs: EDA, Entrenamiento, CV, HP, Tests, Reportes
├── render.yaml            # Despliegue en Render
├── vercel.json            # Despliegue en Vercel
└── .github/workflows/ci.yml  # GitHub Actions CI
```

## Inicio Rápido

### Backend (FastAPI)
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env   # Completar con tus credenciales
uvicorn main:app --reload
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

### Frontend (React)
```bash
cd frontend
npm install
npm start
# App: http://localhost:3000
```

### Módulo IA — Streamlit
```bash
# Desde la raíz del proyecto
pip install -r streamlit_app/requirements.txt
streamlit run streamlit_app/app.py
# Streamlit: http://localhost:8501
```

## Módulo de Análisis IA (Para el Artículo)

El módulo Streamlit implementa el pipeline completo requerido:

1. **EDA** — Limpieza de datos, estadísticos descriptivos, correlaciones, series temporales
2. **Entrenamiento** — 5 modelos con tabla comparativa (RMSE, MAE, R², MAPE, tiempo)
3. **Validación Cruzada** — TimeSeriesSplit con k=5 folds (configurable 2-10)
4. **Hiperparámetros** — Optuna bayesiano (RF, XGBoost) + Grid Search (ARIMA)
5. **Pruebas Estadísticas** — Shapiro-Wilk, Ljung-Box, KS, Wilcoxon, Diebold-Mariano
6. **Reportes** — PDF (ReportLab), Excel (openpyxl), Word (python-docx)

## Despliegue

### Render (Backend + Streamlit)
1. Conecta tu repositorio GitHub en [render.com](https://render.com)
2. Crea un nuevo "Blueprint" y apunta al `render.yaml`
3. Configura las variables de entorno (`DATABASE_URL`, credenciales de correo)

### Vercel (Frontend React)
1. Importa el repositorio en [vercel.com](https://vercel.com)
2. Configura `Root Directory` → `frontend`
3. Framework: Create React App (detectado automáticamente)

## Dataset

- **Fuente**: Inspirado en datos del MIDAGRI/SIEA — Mercado Mayorista de Productores
- **Período**: Enero 2019 — Diciembre 2024
- **Cultivos**: Arroz, Maíz, Cebolla, Espárrago
- **Variables**: fecha, precio_s_ton, temperatura, precipitacion_mm, costo_transporte, nivel_plaga
- **Registros**: 1,728 observaciones

## Tecnologías

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL (Supabase)
- **ML/IA**: scikit-learn, XGBoost, TensorFlow/Keras (LSTM, CNN-LSTM), statsmodels (ARIMA), Optuna
- **Frontend**: React, Recharts, jsPDF, Axios
- **Análisis**: Streamlit, Plotly, Matplotlib, Seaborn
- **Reportes**: ReportLab (PDF), openpyxl (Excel), python-docx (Word)
- **Despliegue**: Render (backend), Vercel (frontend), GitHub Actions (CI)
