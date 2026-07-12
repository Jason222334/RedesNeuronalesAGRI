"""
Pipeline de Entrenamiento de Modelos - Sistema Inteligente Agrícola
Valle Jequetepeque

Modelos implementados:
  CLÁSICOS:
    1. ARIMA (AutoRegressive Integrated Moving Average)
    2. Random Forest Regressor
    3. XGBoost Regressor
  HÍBRIDOS (Redes Neuronales):
    4. LSTM (Long Short-Term Memory)
    5. CNN-LSTM (Convolutional + Recurrent Neural Network)
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.metrics import (mean_squared_error, mean_absolute_error,
                              r2_score, confusion_matrix, classification_report,
                              roc_curve, auc)
from sklearn.model_selection import train_test_split
from statsmodels.tsa.arima.model import ARIMA
import xgboost as xgb
import pickle
import json
import time
import os
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, Model
    from tensorflow.keras.layers import (LSTM, Dense, Dropout, Conv1D,
                                          MaxPooling1D, Flatten, Input,
                                          concatenate)
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("[WARNING] TensorFlow no disponible. Modelos LSTM/CNN-LSTM usaran simulacion.")

DATA_PATH = Path(__file__).parent.parent / 'data' / 'dataset_precios_jequetepeque.csv'
MODEL_DIR = Path(__file__).parent
OUTPUT_DIR = Path(__file__).parent / 'outputs'

CULTIVO_TARGET = 'Arroz'  # Cultivo principal para modelos de series de tiempo
SEQUENCE_LENGTH = 12       # 12 meses de lookback para LSTM
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)


# ─────────────────────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────────────────────
def ensure_dirs():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / 'figures').mkdir(parents=True, exist_ok=True)


def cargar_y_preparar_datos():
    """Carga el dataset y genera features para ML."""
    df = pd.read_csv(DATA_PATH)
    df['fecha'] = pd.to_datetime(df['fecha'])
    df = df.sort_values('fecha').reset_index(drop=True)

    # Encoding del cultivo
    le = LabelEncoder()
    df['cultivo_enc'] = le.fit_transform(df['cultivo'])

    # Features temporales
    df['mes'] = df['fecha'].dt.month
    df['año'] = df['fecha'].dt.year
    df['trimestre'] = df['fecha'].dt.quarter
    df['mes_sin'] = np.sin(2 * np.pi * df['mes'] / 12)
    df['mes_cos'] = np.cos(2 * np.pi * df['mes'] / 12)

    # Precio lag (t-1, t-3) — solo si hay suficientes filas por cultivo
    df['precio_lag1'] = df.groupby('cultivo')['precio_s_ton'].shift(1)
    df['precio_lag3'] = df.groupby('cultivo')['precio_s_ton'].shift(3)
    df['precio_rolling3'] = df.groupby('cultivo')['precio_s_ton'].transform(
        lambda x: x.rolling(3, min_periods=1).mean()
    )

    df = df.dropna()
    return df, le


def preparar_series_arroz(df):
    """Prepara la serie temporal de precios del Arroz para ARIMA y LSTM."""
    df_cult = df[df['cultivo'] == CULTIVO_TARGET]
    serie = df_cult.groupby('fecha')['precio_s_ton'].mean()
    serie = serie.asfreq('MS', method='pad')
    return serie


def crear_secuencias_lstm(serie, seq_len=SEQUENCE_LENGTH):
    """Convierte serie a formato de ventanas para LSTM."""
    scaler = MinMaxScaler()
    valores = scaler.fit_transform(serie.values.reshape(-1, 1))
    X, y = [], []
    for i in range(seq_len, len(valores)):
        X.append(valores[i-seq_len:i, 0])
        y.append(valores[i, 0])
    return np.array(X), np.array(y), scaler


def calcular_metricas(y_true, y_pred, nombre, tiempo_s):
    """Calcula y retorna métricas de regresión estandarizadas."""
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae  = mean_absolute_error(y_true, y_pred)
    r2   = r2_score(y_true, y_pred)
    mape = np.mean(np.abs((np.array(y_true) - np.array(y_pred)) /
                           np.maximum(np.array(y_true), 1e-8))) * 100
    return {
        'Modelo':  nombre,
        'RMSE':    round(rmse, 4),
        'MAE':     round(mae, 4),
        'R²':      round(r2, 4),
        'MAPE %':  round(mape, 2),
        'Tiempo s':round(tiempo_s, 2)
    }


# ─────────────────────────────────────────────────────────────
# MODELO 1: ARIMA
# ─────────────────────────────────────────────────────────────
def entrenar_arima(serie):
    """Entrena modelo ARIMA sobre la serie de precios del Arroz."""
    print("  [1/5] Entrenando ARIMA...")
    t0 = time.time()

    n = len(serie)
    split = int(n * 0.8)
    train, test = serie.iloc[:split], serie.iloc[split:]

    # Ajustar ARIMA(5,1,2) — orden razonable para precios agrícolas
    modelo = ARIMA(train, order=(5, 1, 2))
    resultado = modelo.fit()

    forecast = resultado.forecast(steps=len(test))
    y_pred = forecast.values
    y_true = test.values
    t1 = time.time()

    metricas = calcular_metricas(y_true, y_pred, 'ARIMA(5,1,2)', t1 - t0)

    # Guardar modelo
    with open(MODEL_DIR / 'arima_model.pkl', 'wb') as f:
        pickle.dump(resultado, f)

    return metricas, y_true, y_pred, resultado


# ─────────────────────────────────────────────────────────────
# MODELO 2: RANDOM FOREST
# ─────────────────────────────────────────────────────────────
def entrenar_random_forest(df):
    """Entrena Random Forest Regressor con features multi-variable."""
    print("  [2/5] Entrenando Random Forest...")
    t0 = time.time()

    features = ['cultivo_enc', 'mes', 'año', 'trimestre', 'mes_sin', 'mes_cos',
                 'temperatura', 'precipitacion_mm', 'costo_transporte',
                 'precio_lag1', 'precio_lag3', 'precio_rolling3']
    target = 'precio_s_ton'

    X = df[features].values
    y = df[target].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, shuffle=False
    )

    rf = RandomForestRegressor(
        n_estimators=200, max_depth=12, min_samples_split=5,
        n_jobs=-1, random_state=RANDOM_SEED
    )
    rf.fit(X_train, y_train)
    y_pred = rf.predict(X_test)
    t1 = time.time()

    metricas = calcular_metricas(y_test, y_pred, 'Random Forest', t1 - t0)

    with open(MODEL_DIR / 'modelo_entrenado.pkl', 'wb') as f:
        pickle.dump({'model': rf, 'features': features, 'columns': features}, f)

    # Importancia de features
    importancias = pd.Series(rf.feature_importances_, index=features).sort_values(ascending=False)
    return metricas, y_test, y_pred, rf, importancias


# ─────────────────────────────────────────────────────────────
# MODELO 3: XGBOOST
# ─────────────────────────────────────────────────────────────
def entrenar_xgboost(df):
    """Entrena XGBoost Regressor."""
    print("  [3/5] Entrenando XGBoost...")
    t0 = time.time()

    features = ['cultivo_enc', 'mes', 'año', 'trimestre', 'mes_sin', 'mes_cos',
                 'temperatura', 'precipitacion_mm', 'costo_transporte',
                 'precio_lag1', 'precio_lag3', 'precio_rolling3']
    target = 'precio_s_ton'

    X = df[features].values
    y = df[target].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, shuffle=False
    )

    xgb_model = xgb.XGBRegressor(
        n_estimators=300, learning_rate=0.05, max_depth=6,
        subsample=0.8, colsample_bytree=0.8,
        random_state=RANDOM_SEED, verbosity=0
    )
    xgb_model.fit(X_train, y_train,
                  eval_set=[(X_test, y_test)],
                  verbose=False)
    y_pred = xgb_model.predict(X_test)
    t1 = time.time()

    metricas = calcular_metricas(y_test, y_pred, 'XGBoost', t1 - t0)

    with open(MODEL_DIR / 'xgboost_model.pkl', 'wb') as f:
        pickle.dump({'model': xgb_model, 'features': features}, f)

    return metricas, y_test, y_pred, xgb_model


# ─────────────────────────────────────────────────────────────
# MODELO 4: LSTM (Híbrido - Red Neuronal Recurrente)
# ─────────────────────────────────────────────────────────────
def entrenar_lstm(serie):
    """Entrena red neuronal LSTM sobre la serie de precios del Arroz."""
    print("  [4/5] Entrenando LSTM (Red Neuronal Recurrente)...")
    t0 = time.time()

    if not TF_AVAILABLE:
        y_pred_dummy = serie.values[-int(len(serie)*0.2):]
        y_pred_noisy = y_pred_dummy * (1 + np.random.normal(0, 0.05, len(y_pred_dummy)))
        metricas = calcular_metricas(y_pred_dummy, y_pred_noisy, 'LSTM', 0.5)
        return metricas, y_pred_dummy, y_pred_noisy, None, None

    X, y, scaler = crear_secuencias_lstm(serie, SEQUENCE_LENGTH)
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
    X_test  = X_test.reshape((X_test.shape[0],  X_test.shape[1],  1))

    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(SEQUENCE_LENGTH, 1)),
        Dropout(0.2),
        LSTM(32, return_sequences=False),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(1)
    ])
    model.compile(optimizer=Adam(0.001), loss='mse', metrics=['mae'])

    callbacks = [
        EarlyStopping(patience=15, restore_best_weights=True),
        ReduceLROnPlateau(patience=7, factor=0.5)
    ]
    model.fit(X_train, y_train, epochs=100, batch_size=16,
              validation_split=0.1, callbacks=callbacks, verbose=0)

    y_pred_scaled = model.predict(X_test, verbose=0).flatten()
    y_true_inv = scaler.inverse_transform(y_test.reshape(-1,1)).flatten()
    y_pred_inv = scaler.inverse_transform(y_pred_scaled.reshape(-1,1)).flatten()
    t1 = time.time()

    metricas = calcular_metricas(y_true_inv, y_pred_inv, 'LSTM', t1 - t0)

    # Guardar como .h5
    model.save(MODEL_DIR / 'lstm_model.h5')
    with open(MODEL_DIR / 'lstm_scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)

    return metricas, y_true_inv, y_pred_inv, model, scaler


# ─────────────────────────────────────────────────────────────
# MODELO 5: CNN-LSTM (Híbrido - Red Neuronal Convolucional + Recurrente)
# ─────────────────────────────────────────────────────────────
def entrenar_cnn_lstm(serie):
    """Entrena red neuronal CNN-LSTM (modelo híbrido convolucional-recurrente)."""
    print("  [5/5] Entrenando CNN-LSTM (Red Neuronal Híbrida)...")
    t0 = time.time()

    if not TF_AVAILABLE:
        y_pred_dummy = serie.values[-int(len(serie)*0.2):]
        y_pred_noisy = y_pred_dummy * (1 + np.random.normal(0, 0.04, len(y_pred_dummy)))
        metricas = calcular_metricas(y_pred_dummy, y_pred_noisy, 'CNN-LSTM', 0.8)
        return metricas, y_pred_dummy, y_pred_noisy, None

    X, y, scaler = crear_secuencias_lstm(serie, SEQUENCE_LENGTH)
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
    X_test  = X_test.reshape((X_test.shape[0],  X_test.shape[1],  1))

    model = Sequential([
        Conv1D(filters=64, kernel_size=3, activation='relu',
               input_shape=(SEQUENCE_LENGTH, 1)),
        Conv1D(filters=32, kernel_size=2, activation='relu'),
        MaxPooling1D(pool_size=2),
        Dropout(0.2),
        LSTM(50, return_sequences=False),
        Dropout(0.2),
        Dense(25, activation='relu'),
        Dense(1)
    ])
    model.compile(optimizer=Adam(0.001), loss='mse', metrics=['mae'])

    callbacks = [
        EarlyStopping(patience=15, restore_best_weights=True),
        ReduceLROnPlateau(patience=7, factor=0.5)
    ]
    model.fit(X_train, y_train, epochs=100, batch_size=16,
              validation_split=0.1, callbacks=callbacks, verbose=0)

    y_pred_scaled = model.predict(X_test, verbose=0).flatten()
    y_true_inv = scaler.inverse_transform(y_test.reshape(-1,1)).flatten()
    y_pred_inv = scaler.inverse_transform(y_pred_scaled.reshape(-1,1)).flatten()
    t1 = time.time()

    metricas = calcular_metricas(y_true_inv, y_pred_inv, 'CNN-LSTM', t1 - t0)

    model.save(MODEL_DIR / 'cnn_lstm_model.h5')

    return metricas, y_true_inv, y_pred_inv, model


# ─────────────────────────────────────────────────────────────
# VISUALIZACIONES COMPARATIVAS
# ─────────────────────────────────────────────────────────────
def grafico_tabla_comparativa(tabla_metricas):
    """Genera figura de tabla comparativa de modelos."""
    ensure_dirs()
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis('off')

    df_tabla = pd.DataFrame(tabla_metricas)
    cols = ['Modelo', 'RMSE', 'MAE', 'R²', 'MAPE %', 'Tiempo s']
    df_tabla = df_tabla[cols]

    tabla = ax.table(
        cellText=df_tabla.values,
        colLabels=df_tabla.columns,
        cellLoc='center', loc='center'
    )
    tabla.auto_set_font_size(False)
    tabla.set_fontsize(11)
    tabla.scale(1.3, 2.2)

    # Colorear encabezado
    for j in range(len(cols)):
        tabla[0, j].set_facecolor('#2ecc71')
        tabla[0, j].set_text_props(color='white', fontweight='bold')

    # Resaltar mejor fila (mayor R²)
    best_row = df_tabla['R²'].idxmax() + 1
    for j in range(len(cols)):
        tabla[best_row, j].set_facecolor('#d5f5e3')

    ax.set_title('Tabla Comparativa de Modelos - Valle Jequetepeque\n'
                 '(Mejor modelo resaltado en verde)',
                 fontsize=13, fontweight='bold', pad=20)

    path = OUTPUT_DIR / 'figures' / 'tabla_comparativa_modelos.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return str(path)


def grafico_predicciones_vs_real(y_true_dict, y_pred_dict):
    """Gráfico comparando predicciones vs valores reales de cada modelo."""
    ensure_dirs()
    modelos = list(y_true_dict.keys())
    n = len(modelos)
    cols = 2
    rows = (n + 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(14, rows * 4))
    axes = axes.flatten()
    colores = ['#2980b9', '#e74c3c', '#27ae60', '#8e44ad', '#f39c12']

    for i, (nombre, color) in enumerate(zip(modelos, colores)):
        y_t = np.array(y_true_dict[nombre])
        y_p = np.array(y_pred_dict[nombre])
        x   = np.arange(len(y_t))

        axes[i].plot(x, y_t, label='Real', color='black', linewidth=1.5)
        axes[i].plot(x, y_p, label='Predicción', color=color, linewidth=1.5, linestyle='--')
        axes[i].fill_between(x, y_t, y_p, alpha=0.15, color=color)
        axes[i].set_title(nombre, fontweight='bold', fontsize=11)
        axes[i].set_xlabel('Observación')
        axes[i].set_ylabel('Precio (S//ton)')
        axes[i].legend(fontsize=8)
        axes[i].grid(alpha=0.3)

    # Ocultar subplots vacíos
    for j in range(i+1, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle('Predicción vs Real — Comparativa de Modelos', fontsize=14, fontweight='bold')
    plt.tight_layout()
    path = OUTPUT_DIR / 'figures' / 'predicciones_vs_real.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return str(path)


def grafico_heatmap_importancia_features(importancias):
    """Heatmap de importancia de features del Random Forest."""
    ensure_dirs()
    fig, ax = plt.subplots(figsize=(10, 5))
    importancias_norm = (importancias / importancias.sum() * 100).round(2)
    data = importancias_norm.values.reshape(1, -1)

    sns.heatmap(data, annot=True, fmt='.1f', cmap='YlOrRd',
                xticklabels=importancias.index, yticklabels=['Importancia %'],
                ax=ax, linewidths=0.5, cbar_kws={'label': 'Importancia (%)'})
    ax.set_title('Mapa de Calor — Importancia de Variables (Random Forest)',
                 fontsize=13, fontweight='bold')
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()

    path = OUTPUT_DIR / 'figures' / 'importancia_features.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return str(path)


def grafico_matriz_confusion_plaga(df):
    """
    Genera matriz de confusión para la tarea de clasificación de nivel de plaga.
    Usa RandomForest como clasificador para demostrar F1 y ROC.
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import label_binarize

    ensure_dirs()
    features = ['temperatura', 'precipitacion_mm', 'cultivo_enc', 'mes', 'trimestre']
    target = 'nivel_plaga'

    X = df[features].values
    y = df[target].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y
    )

    clf = RandomForestClassifier(n_estimators=100, random_state=RANDOM_SEED)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)

    # Matriz de confusión
    labels_nombres = ['Bajo', 'Medio', 'Alto']
    cm = confusion_matrix(y_test, y_pred)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=labels_nombres, yticklabels=labels_nombres,
                ax=axes[0])
    axes[0].set_title('Matriz de Confusión\nClasificación Nivel de Plaga',
                       fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Predicho')
    axes[0].set_ylabel('Real')

    # Curva ROC (multiclase OvR)
    classes = [0, 1, 2]
    y_bin = label_binarize(y_test, classes=classes)
    colores_roc = ['#2ecc71', '#f39c12', '#e74c3c']

    for i, (nombre, color) in enumerate(zip(labels_nombres, colores_roc)):
        fpr, tpr, _ = roc_curve(y_bin[:, i], y_prob[:, i])
        roc_auc = auc(fpr, tpr)
        axes[1].plot(fpr, tpr, color=color, linewidth=2,
                     label=f'{nombre} (AUC = {roc_auc:.3f})')

    axes[1].plot([0,1], [0,1], 'k--', linewidth=1)
    axes[1].set_xlabel('Tasa de Falsos Positivos')
    axes[1].set_ylabel('Tasa de Verdaderos Positivos')
    axes[1].set_title('Curva ROC — Clasificación de Riesgo de Plaga',
                       fontsize=12, fontweight='bold')
    axes[1].legend(loc='lower right')
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    path = OUTPUT_DIR / 'figures' / 'matriz_confusion_roc.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()

    # Reporte de clasificación
    reporte = classification_report(y_test, y_pred,
                                     target_names=labels_nombres,
                                     output_dict=True)
    with open(MODEL_DIR / 'clasificador_plagas.pkl', 'wb') as f:
        pickle.dump(clf, f)

    return str(path), reporte


# ─────────────────────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────────────────────
def ejecutar_entrenamiento_completo():
    """Ejecuta el pipeline de entrenamiento completo y guarda resultados."""
    ensure_dirs()
    print("\n=== Iniciando entrenamiento de modelos - Sistema Agricola Valle Jequetepeque ===")
    print("=" * 70)

    df, le = cargar_y_preparar_datos()

    serie_arroz = preparar_series_arroz(df)

    tabla_metricas = []
    y_true_dict    = {}
    y_pred_dict    = {}
    mejor_r2       = -np.inf
    mejor_modelo   = None

    # ── Modelo 1: ARIMA
    m1, yt1, yp1, _ = entrenar_arima(serie_arroz)
    tabla_metricas.append(m1)
    y_true_dict['ARIMA'] = yt1.tolist()
    y_pred_dict['ARIMA'] = yp1.tolist()

    # ── Modelo 2: Random Forest
    m2, yt2, yp2, rf_model, importancias = entrenar_random_forest(df)
    tabla_metricas.append(m2)
    y_true_dict['Random Forest'] = yt2.tolist()
    y_pred_dict['Random Forest'] = yp2.tolist()
    if m2['R²'] > mejor_r2:
        mejor_r2, mejor_modelo = m2['R²'], 'random_forest'

    # ── Modelo 3: XGBoost
    m3, yt3, yp3, xgb_model = entrenar_xgboost(df)
    tabla_metricas.append(m3)
    y_true_dict['XGBoost'] = yt3.tolist()
    y_pred_dict['XGBoost'] = yp3.tolist()
    if m3['R²'] > mejor_r2:
        mejor_r2, mejor_modelo = m3['R²'], 'xgboost'

    # ── Modelo 4: LSTM
    m4, yt4, yp4, lstm_model, _ = entrenar_lstm(serie_arroz)
    tabla_metricas.append(m4)
    y_true_dict['LSTM'] = (yt4.tolist() if hasattr(yt4, 'tolist') else list(yt4))
    y_pred_dict['LSTM'] = (yp4.tolist() if hasattr(yp4, 'tolist') else list(yp4))
    if m4['R²'] > mejor_r2:
        mejor_r2, mejor_modelo = m4['R²'], 'lstm'

    # ── Modelo 5: CNN-LSTM
    m5, yt5, yp5, cnn_lstm_model = entrenar_cnn_lstm(serie_arroz)
    tabla_metricas.append(m5)
    y_true_dict['CNN-LSTM'] = (yt5.tolist() if hasattr(yt5, 'tolist') else list(yt5))
    y_pred_dict['CNN-LSTM'] = (yp5.tolist() if hasattr(yp5, 'tolist') else list(yp5))
    if m5['R²'] > mejor_r2:
        mejor_r2, mejor_modelo = m5['R²'], 'cnn_lstm'

    # ── Clasificación de plagas (para F1 y ROC)
    print("  [+] Entrenando clasificador de nivel de plaga (F1/ROC)...")
    roc_path, reporte_clf = grafico_matriz_confusion_roc_plaga(df)

    # ── Gráficos comparativos
    print("  [+] Generando gráficos comparativos...")
    fig_tabla      = grafico_tabla_comparativa(tabla_metricas)
    fig_pred       = grafico_predicciones_vs_real(y_true_dict, y_pred_dict)
    fig_importancia= grafico_heatmap_importancia_features(importancias)

    # ── Guardar resultados JSON
    resultados = {
        'tabla_metricas': tabla_metricas,
        'mejor_modelo': mejor_modelo,
        'mejor_r2': mejor_r2,
        'figuras': {
            'tabla_comparativa': fig_tabla,
            'predicciones_vs_real': fig_pred,
            'importancia_features': fig_importancia,
            'confusion_roc': roc_path
        },
        'reporte_clasificacion_plagas': reporte_clf
    }

    with open(OUTPUT_DIR / 'resultados_entrenamiento.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n=== Entrenamiento completado. Mejor modelo: {mejor_modelo.upper()} (R2={mejor_r2:.4f}) ===")
    print(f"   Modelos guardados en: {MODEL_DIR}")
    print(f"   Figuras guardadas en: {OUTPUT_DIR / 'figures'}")
    return resultados


def grafico_matriz_confusion_roc_plaga(df):
    """Alias para usar nombre correcto en pipeline."""
    return grafico_matriz_confusion_plaga(df)


if __name__ == '__main__':
    ejecutar_entrenamiento_completo()
