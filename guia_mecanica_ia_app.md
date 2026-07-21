# Guía Técnica y Funcional del Módulo IA (Sistema Agrícola Valle Jequetepeque)
> **Destinatario**: Redactor externo del artículo científico para la *Revista Científica de Sistemas e Informática*.

Esta guía detalla el funcionamiento interno de la aplicación web, su arquitectura de inteligencia artificial, la estructura de datos, el flujo metodológico y las métricas estadísticas implementadas. El objetivo es proporcionar al redactor toda la información del software necesaria para completar las secciones de **Materiales y Métodos** y **Resultados y Discusión** del artículo científico, utilizando la plantilla proporcionada.

---

## 1. Arquitectura General y Tecnologías del Sistema

El sistema implementa una arquitectura desacoplada cliente-servidor orientada al análisis predictivo de datos y aprendizaje automático:

* **Backend**: FastAPI (Python 3.12). Proporciona una API REST de alto rendimiento y ejecución asíncrona para servir las predicciones y ejecutar las tareas científicas pesadas en segundo plano.
* **Base de Datos**: PostgreSQL alojado en Supabase, gestionado a través de SQLAlchemy ORM.
* **Frontend**: React (JavaScript/TypeScript). Panel de control administrativo y visualización interactiva.
* **Módulo de Análisis Científico (Streamlit)**: Interfaz paralela desarrollada en Streamlit enfocada en la automatización del flujo econométrico e interpretativo para el artículo científico.
* **Reportes**: ReportLab (PDF), openpyxl (Excel), python-docx (Word).

---

## 2. Estructura y Origen del Dataset
Para la sección de **Materials and Methods** (Variables y Datos):

* **Fuente**: Datos históricos inspirados en los boletines diarios de precios y volúmenes de ingreso en el Mercado Mayorista de Productores (SIEA - MIDAGRI, Perú).
* **Período temporal**: Enero 2019 a Diciembre 2024 (6 años de datos históricos mensuales).
* **Tamaño**: 1,728 registros consolidados.
* **Cultivos analizados**: Arroz, Maíz, Cebolla y Espárrago.
* **Variables del Dataset**:

| Variable | Tipo de Dato | Rol en el Modelo | Descripción |
|----------|--------------|------------------|-------------|
| `fecha` | Temporal (Datetime) | Índice temporal | Fecha del registro consolidado mensual (Formato YYYY-MM-DD). |
| `cultivo` | Categórico (String) | Predictor | Tipo de producto agrícola (Arroz, Maíz, Cebolla, Espárrago). |
| `precio_s_ton` | Numérico continuo | **Target (Objetivo)** | Precio promedio mensual del cultivo en Soles por Tonelada (S/. por Ton). |
| `temperatura` | Numérico continuo | Predictor exógeno | Temperatura promedio mensual (°C) del Valle Jequetepeque. |
| `precipitacion_mm`| Numérico continuo | Predictor exógeno | Precipitación acumulada mensual (mm) en la región. |
| `costo_transporte`| Numérico continuo | Predictor exógeno | Índice de costos de transporte hacia mercados mayoristas (combustible, fletes). |
| `nivel_plaga` | Ordinal categórico | Variable exógena / Target | Nivel de riesgo de plagas registrado en el mes: `0` (Bajo), `1` (Medio), `2` (Alto). |

---

## 3. Metodología: El Pipeline de los 5 Modelos (IA / ML)
Para la sección de **Materials and Methods** (Modelos Predictivos):

La aplicación implementa y compara **tres modelos clásicos y dos modelos híbridos de redes neuronales** sobre la serie temporal del cultivo principal (**Arroz**):

```
                                  ┌── ARIMA (Clásico Univariado)
                                  ├── Random Forest Regressor (Clásico Multivariable)
Predictores ──► [ MÓDULO IA ] ───┼── XGBoost Regressor (Clásico Multivariable)
                                  ├── LSTM (Híbrido - Red Neuronal Recurrente)
                                  └── CNN-LSTM (Híbrido - Convolucional + Recurrente)
```

### A. Modelos Clásicos
1. **ARIMA (5, 1, 2) (AutoRegressive Integrated Moving Average)**:
   * **Tipo**: Clásico univariado lineal.
   * **Uso**: Analiza únicamente el historial del precio del arroz. Su orden es autoconfigurado: 5 términos autorregresivos (p), 1 diferenciación (d) para estacionarizar la serie, y 2 términos de media móvil (q).
2. **Random Forest Regressor**:
   * **Tipo**: Clásico multivariable no lineal.
   * **Uso**: Ensamble de 200 árboles de decisión (`n_estimators=200`, `max_depth=12`). Consume variables exógenas climáticas (temperatura, precipitación) y económicas, además de desfases temporales (`precio_lag1`, `precio_lag3`, `precio_rolling3`).
3. **XGBoost Regressor**:
   * **Tipo**: Clásico multivariable de Boosting de Gradiente Extremo.
   * **Uso**: Algoritmo optimizado sobre árboles de decisión de expansión secuencial. Configurado con `n_estimators=300`, `learning_rate=0.05` y `max_depth=6`.

### B. Modelos Híbridos (Redes Neuronales)
4. **LSTM (Long Short-Term Memory)**:
   * **Tipo**: Híbrido - Red Neuronal Recurrente Profunda (RNN).
   * **Arquitectura**: 
     - Entrada secuencial de tamaño 12 (lookback de 12 meses anteriores).
     - Capa LSTM 1: 64 unidades ocultas con retorno de secuencias activado.
     - Capa de Regularización: Dropout del 20% (para prevenir sobreajuste).
     - Capa LSTM 2: 32 unidades ocultas (retorno desactivado).
     - Capa Dense: 16 neuronas con función de activación ReLU.
     - Capa de Salida: 1 neurona (predicción lineal del precio en $t+1$).
     - Optimizador: Adam con tasa de aprendizaje de $0.001$, entrenado en 100 épocas con parada temprana (Early Stopping) si la pérdida de validación no mejora tras 15 épocas.
5. **CNN-LSTM**:
   * **Tipo**: Híbrido - Red Neuronal Convolucional + LSTM.
   * **Arquitectura**: 
     - Capa Convolucional 1D inicial de 64 filtros (kernel size = 3, activación ReLU) para la extracción automática de patrones espaciales y variaciones locales en la serie de precios.
     - Capa Convolucional 1D secundaria de 32 filtros (kernel size = 2, activación ReLU).
     - Capa Max Pooling 1D (pool size = 2) para reducir dimensionalidad y extraer características dominantes.
     - Capa LSTM de 50 unidades para capturar la secuencialidad a largo plazo de las features convolucionales.
     - Capas Dense (25 neuronas) y Dropout (20%).
     - Salida: 1 neurona lineal.

---

## 4. Las 6 Pestañas del Módulo IA (Estructura de la App)
El redactor debe conocer las 6 partes metodológicas en las que está organizada la aplicación de análisis:

### 1. Pestaña 1: Análisis Exploratorio de Datos (EDA)
* **Función**: Carga y prepara el dataset público. Implementa la limpieza automatizada tratando valores atípicos (outliers) mediante el **método de Rango Intercuartílico (IQR)** con un umbral de $1.5 \times \text{IQR}$, rellenando nulos con la mediana histórica.
* **Gráficos generados**:
  * **Series Temporales**: Gráfico lineal por cultivo con una media móvil (rolling) de 3 meses para identificar tendencias cíclicas y estacionales a mediano plazo.
  * **Heatmap de Correlación**: Matriz de coeficientes de Pearson que cuantifica la fuerza y dirección de la relación lineal entre el precio, el clima, el costo de transporte y las plagas.
  * **Distribución de Precios**: Histogramas de frecuencias comparados con curvas de densidad para verificar la asimetría (skewness) y curtosis de los precios por cultivo.
  * **Precios Estacionales**: Gráfico de barras promedio para las cuatro estaciones del año (Verano, Otoño, Invierno, Primavera) evaluando el impacto estacional en la oferta y demanda.

### 2. Pestaña 2: Entrenamiento y Métricas comparativas
* **Función**: Entrena los 5 modelos usando una división cronológica de datos: **80% para entrenamiento** y **20% para test** (evitando desordenar la línea temporal). Evalúa el desempeño usando 4 métricas estándar:
  $$\text{RMSE} = \sqrt{\frac{1}{N}\sum_{i=1}^N (y_i - \hat{y}_i)^2}$$
  $$\text{MAE} = \frac{1}{N}\sum_{i=1}^N |y_i - \hat{y}_i|$$
  $$R^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y}_i)^2}$$
  $$\text{MAPE (\%)} = \frac{100\%}{N}\sum_{i=1}^N \left| \frac{y_i - \hat{y}_i}{y_i} \right|$$
* **Gráficos generados**:
  * **Predicción vs Real**: Gráfico temporal superpuesto que compara los valores reales con los pronósticos de los 5 modelos para el período de prueba.
  * **Feature Importance**: Gráfico que muestra la relevancia porcentual de cada variable predictora en el modelo de Random Forest (ej. costo de transporte y precio rezagado como las más influyentes).
  * **Matriz de Confusión y Curva ROC/AUC**: Se incluye un clasificador secundario de Random Forest para predecir el riesgo de plagas (`nivel_plaga`), mostrando la curva de capacidad diagnóstica (AUC-ROC) y la tasa de aciertos (F1-Score).

### 3. Pestaña 3: Validación Cruzada (Cross-Validation)
* **Función**: Dado que el método tradicional de $K$-Fold al azar introduce *data leakage* (usar datos del futuro para entrenar modelos que predicen el pasado), la app implementa **TimeSeriesSplit** con $k=5$ folds configurables.
* **Funcionamiento**: El conjunto de entrenamiento crece de forma incremental en cada fold sucesivo, manteniendo siempre el conjunto de validación en una franja de tiempo posterior.
* **Gráficos generados**: Gráfico comparativo de evolución del RMSE, MAE y $R^2$ fold por fold, evaluando la estabilidad predictiva de Random Forest contra XGBoost.

### 4. Pestaña 4: Ajuste de Hiperparámetros (Tuning)
* **Función**: Ajusta y optimiza los hiperparámetros para mejorar la precisión y evitar el sobreajuste.
* **Algoritmos**:
  * **Optuna (Optimización Bayesiana)**: Utilizado para Random Forest y XGBoost. Ejecuta de forma inteligente múltiples ensayos (trials) minimizando el RMSE sobre la validación cruzada.
  * **Grid Search**: Búsqueda en cuadrícula exhaustiva evaluando combinaciones de parámetros $(p, d, q)$ de ARIMA, seleccionando aquella con el menor **Criterio de Información de Akaike (AIC)**.
* **Gráficos generados**: Curva de convergencia de Optuna que ilustra cómo disminuye el error predictivo (RMSE) a lo largo de las iteraciones.

### 5. Pestaña 5: Pruebas Estadísticas Rigurosas
Para la sección de **Results and Discussion** (Validación Estadística del artículo):

El sistema no se limita a evaluar métricas visuales; ejecuta cinco familias de tests de hipótesis econométricas y estadísticas para validar la robustez de los modelos:

1. **Test de Shapiro-Wilk**:
   * *Objetivo*: Evalúa si los residuos (errores del modelo) provienen de una distribución normal.
   * *Hipótesis*: $H_0$: Residuos normales. Si el $p\text{-valor} > 0.05$, no se rechaza $H_0$, lo que indica que el modelo ha extraído toda la información sistemática y los errores son ruido no sesgado.
2. **Test de Ljung-Box**:
   * *Objetivo*: Comprueba la existencia de autocorrelación serial en los residuos (lags=10).
   * *Hipótesis*: $H_0$: No hay autocorrelación (residuos independientes). Un $p\text{-valor} > 0.05$ confirma que los residuos son ruido blanco.
3. **Test de Kolmogorov-Smirnov (KS)**:
   * *Objetivo*: Compara la distribución empírica de los errores estandarizados con la distribución normal estándar teórica.
4. **Test de Rangos con Signo de Wilcoxon**:
   * *Objetivo*: Contraste no paramétrico para determinar si la diferencia entre las distribuciones de errores absolutos de dos modelos en competencia es estadísticamente significativa.
5. **Test de Diebold-Mariano (DM)**:
   * *Objetivo*: Evalúa si la diferencia en la precisión predictiva entre dos modelos (ej. XGBoost vs ARIMA) es estadísticamente significativa o producto del azar.
   * *Hipótesis*: $H_0$: Ambos modelos tienen la misma precisión predictiva. Un $p\text{-valor} < 0.05$ permite rechazar la hipótesis nula, declarando a un modelo estadísticamente superior al otro.
* **Gráficos generados**: Diagrama de dispersión Q-Q (Quantile-Quantile Plot) de residuos e histogramas de frecuencias comparados con curvas de distribución de probabilidad Gaussiana.

### 6. Pestaña 6: Generación de Reportes
* **Función**: Permite descargar los análisis completados en tres formatos listos para usar en la redacción del artículo:
  * **Reporte PDF (Científico)**: Formato formal en una sola columna con el resumen ejecutivo, las 8 figuras incrustadas de forma secuencial y las tablas de métricas/tests estadísticos.
  * **Reporte Word (.docx)**: Documento editable idóneo para copiar y pegar texto, tablas y gráficos directamente a la plantilla final de la revista.
  * **Reporte Excel (.xlsx)**: Hoja de cálculo organizada por pestañas para quienes deseen recrear los gráficos a medida o analizar los números crudos de los folds y trials.

---

## 5. Mapeo de Componentes con la Plantilla de la Revista

Para facilitarle la redacción al escritor del artículo, indícale cómo mapear las secciones del sistema en la plantilla:

1. **Title, Abstract & Keywords**: Puede extraerlos directamente de la sección **Resumen Ejecutivo** del reporte PDF generado.
2. **Introduction (Introducción)**: Usar el contexto del Valle Jequetepeque y el objetivo de predecir precios de cultivos críticos como el Arroz para reducir la incertidumbre financiera en los agricultores.
3. **Materials and methods (Materiales y Métodos)**:
   * *Subsection 2.1 (Data & Variables)*: Describir el dataset de 1,728 registros mensuales (2019-2024), detallando las variables continuas y categóricas.
   * *Subsection 2.2 (Predictive Models)*: Explicar la teoría detrás de los 5 modelos (ARIMA, RF, XGBoost, LSTM y el modelo híbrido CNN-LSTM con su extracción espacial/temporal).
   * *Subsection 2.3 (Validation & Statistics)*: Documentar el uso de TimeSeriesSplit ($k=5$ folds), Optuna para hiperparámetros, y los fundamentos matemáticos de los tests de Shapiro-Wilk, Ljung-Box y Diebold-Mariano.
4. **Results and discussion (Resultados y Discusión)**:
   * *Subsection 3.1 (EDA)*: Insertar las figuras `series_temporales.png` y `heatmap_correlacion.png`, discutiendo cómo influyen las precipitaciones e incremento de plagas en la fluctuación de los precios.
   * *Subsection 3.2 (Model Performance)*: Insertar la tabla comparativa del reporte PDF y la figura `predicciones_vs_real.png`. Resaltar que el modelo de **Random Forest** obtuvo el mejor desempeño general con un $R^2 = 0.9038$.
   * *Subsection 3.3 (Statistical Validation)*: Insertar la tabla del test de Diebold-Mariano y la figura `pruebas_estadisticas_residuos.png` (Q-Q plots) para certificar la validez científica de los residuos de los modelos y la significancia del modelo ganador.
5. **Conclusions (Conclusiones)**: Resumir los beneficios de implementar modelos híbridos y multivariables en comparación con métodos clásicos univariados lineales para la planificación económica agraria.
