"""
Validación Cruzada — Sistema Inteligente Agrícola
Implementa TimeSeriesSplit con k folds configurables para los 5 modelos.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import TimeSeriesSplit, cross_val_score, KFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import pickle
import json
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')
OUTPUT_DIR = Path(__file__).parent / 'outputs'
DATA_PATH  = Path(__file__).parent.parent / 'data' / 'dataset_precios_jequetepeque.csv'
RANDOM_SEED = 42


def cargar_features(data_path=DATA_PATH):
    df = pd.read_csv(data_path)
    df['fecha'] = pd.to_datetime(df['fecha'])
    df = df.sort_values('fecha').reset_index(drop=True)
    le = LabelEncoder()
    df['cultivo_enc'] = le.fit_transform(df['cultivo'])
    df['mes'] = df['fecha'].dt.month
    df['año'] = df['fecha'].dt.year
    df['trimestre'] = df['fecha'].dt.quarter
    df['mes_sin'] = np.sin(2 * np.pi * df['mes'] / 12)
    df['mes_cos'] = np.cos(2 * np.pi * df['mes'] / 12)
    df['precio_lag1'] = df.groupby('cultivo')['precio_s_ton'].shift(1)
    df['precio_lag3'] = df.groupby('cultivo')['precio_s_ton'].shift(3)
    df['precio_rolling3'] = df.groupby('cultivo')['precio_s_ton'].transform(
        lambda x: x.rolling(3, min_periods=1).mean()
    )
    df = df.dropna()
    return df


def metricas_fold(y_true, y_pred):
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae  = mean_absolute_error(y_true, y_pred)
    r2   = r2_score(y_true, y_pred)
    return {'RMSE': round(rmse, 4), 'MAE': round(mae, 4), 'R²': round(r2, 4)}


def cross_validar_modelo(modelo_nombre, n_folds=5, df=None):
    """
    Ejecuta validación cruzada con TimeSeriesSplit para el modelo dado.
    
    Args:
        modelo_nombre: 'random_forest' | 'xgboost'
        n_folds: número de folds (por defecto 5, configurable)
        df: DataFrame ya cargado (opcional)
    
    Returns:
        dict con métricas promedio y por fold
    """
    if df is None:
        df = cargar_features()

    features = ['cultivo_enc', 'mes', 'año', 'trimestre', 'mes_sin', 'mes_cos',
                 'temperatura', 'precipitacion_mm', 'costo_transporte',
                 'precio_lag1', 'precio_lag3', 'precio_rolling3']

    X = df[features].values
    y = df['precio_s_ton'].values

    tscv = TimeSeriesSplit(n_splits=n_folds)

    resultados_folds = []
    fold_num = 1

    for train_idx, test_idx in tscv.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        if modelo_nombre == 'random_forest':
            modelo = RandomForestRegressor(
                n_estimators=100, max_depth=10, random_state=RANDOM_SEED, n_jobs=-1
            )
        elif modelo_nombre == 'xgboost':
            modelo = xgb.XGBRegressor(
                n_estimators=150, learning_rate=0.07, max_depth=5,
                random_state=RANDOM_SEED, verbosity=0
            )
        else:
            raise ValueError(f"Modelo desconocido: {modelo_nombre}")

        modelo.fit(X_train, y_train)
        y_pred = modelo.predict(X_test)

        m = metricas_fold(y_test, y_pred)
        m['fold'] = fold_num
        m['n_train'] = len(train_idx)
        m['n_test'] = len(test_idx)
        resultados_folds.append(m)
        fold_num += 1

    # Métricas promedio
    rmse_vals = [f['RMSE'] for f in resultados_folds]
    mae_vals  = [f['MAE']  for f in resultados_folds]
    r2_vals   = [f['R²']   for f in resultados_folds]

    resumen = {
        'modelo': modelo_nombre,
        'n_folds': n_folds,
        'RMSE_mean': round(np.mean(rmse_vals), 4),
        'RMSE_std':  round(np.std(rmse_vals), 4),
        'MAE_mean':  round(np.mean(mae_vals), 4),
        'MAE_std':   round(np.std(mae_vals), 4),
        'R2_mean':   round(np.mean(r2_vals), 4),
        'R2_std':    round(np.std(r2_vals), 4),
        'folds':     resultados_folds
    }
    return resumen


def grafico_cv_resultados(resultados_rf, resultados_xgb, n_folds):
    """Genera gráfico comparativo de resultados de CV por fold."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / 'figures').mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(f'Validación Cruzada TimeSeriesSplit ({n_folds} Folds)\nRandom Forest vs XGBoost',
                 fontsize=13, fontweight='bold')

    metricas = ['RMSE', 'MAE', 'R²']
    keys     = ['RMSE', 'MAE', 'R²']
    x = np.arange(1, n_folds + 1)

    for ax, metrica, key in zip(axes, metricas, keys):
        rf_vals  = [f[key] for f in resultados_rf['folds']]
        xgb_vals = [f[key] for f in resultados_xgb['folds']]

        ax.plot(x, rf_vals,  'o-', color='#2ecc71', linewidth=2, label='Random Forest', markersize=7)
        ax.plot(x, xgb_vals, 's-', color='#e74c3c', linewidth=2, label='XGBoost',        markersize=7)

        ax.axhline(resultados_rf[f'{key.replace("²","2")}_mean'],  color='#2ecc71', linestyle='--', alpha=0.5)
        ax.axhline(resultados_xgb[f'{key.replace("²","2")}_mean'], color='#e74c3c', linestyle='--', alpha=0.5)

        ax.set_xlabel('Fold')
        ax.set_ylabel(metrica)
        ax.set_title(metrica)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        ax.set_xticks(x)

    plt.tight_layout()
    path = OUTPUT_DIR / 'figures' / 'cross_validation.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return str(path)


def ejecutar_cross_validation(n_folds=5):
    """Pipeline completo de validación cruzada."""
    print(f"\n=== Ejecutando Cross-Validation con {n_folds} folds ===")
    df = cargar_features()

    resultados_rf  = cross_validar_modelo('random_forest', n_folds, df)
    resultados_xgb = cross_validar_modelo('xgboost', n_folds, df)

    fig_path = grafico_cv_resultados(resultados_rf, resultados_xgb, n_folds)

    resultados_totales = {
        'n_folds': n_folds,
        'metodo': 'TimeSeriesSplit',
        'random_forest': resultados_rf,
        'xgboost': resultados_xgb,
        'figura': fig_path
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / 'cross_validation_resultados.json', 'w', encoding='utf-8') as f:
        json.dump(resultados_totales, f, ensure_ascii=False, indent=2)

    print(f"  RF  - R2: {resultados_rf['R2_mean']:.4f} +/- {resultados_rf['R2_std']:.4f}")
    print(f"  XGB - R2: {resultados_xgb['R2_mean']:.4f} +/- {resultados_xgb['R2_std']:.4f}")
    return resultados_totales


if __name__ == '__main__':
    ejecutar_cross_validation(n_folds=5)
