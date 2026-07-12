"""
Ajuste de Hiperparámetros — Sistema Inteligente Agrícola
Usa Optuna (bayesiano) para Random Forest y XGBoost.
Grid Search manual para ARIMA.
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import pickle
import json
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

DATA_PATH   = Path(__file__).parent.parent / 'data' / 'dataset_precios_jequetepeque.csv'
OUTPUT_DIR  = Path(__file__).parent / 'outputs'
MODEL_DIR   = Path(__file__).parent
RANDOM_SEED = 42


def cargar_features():
    df = pd.read_csv(DATA_PATH)
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


FEATURES = ['cultivo_enc', 'mes', 'año', 'trimestre', 'mes_sin', 'mes_cos',
             'temperatura', 'precipitacion_mm', 'costo_transporte',
             'precio_lag1', 'precio_lag3', 'precio_rolling3']


def cv_score(modelo, X, y, n_splits=3):
    """Validación cruzada rápida para Optuna (3 splits para velocidad)."""
    tscv = TimeSeriesSplit(n_splits=n_splits)
    scores = []
    for tr, te in tscv.split(X):
        modelo.fit(X[tr], y[tr])
        pred = modelo.predict(X[te])
        scores.append(np.sqrt(mean_squared_error(y[te], pred)))
    return np.mean(scores)


# ─────────────────────────────────────────────────────────────
# TUNING RANDOM FOREST CON OPTUNA
# ─────────────────────────────────────────────────────────────
def tuning_random_forest(df, n_trials=30):
    """Búsqueda bayesiana de hiperparámetros para Random Forest."""
    X = df[FEATURES].values
    y = df['precio_s_ton'].values

    if not OPTUNA_AVAILABLE:
        print("  [WARNING] Optuna no disponible - usando parametros por defecto mejorados")
        mejores_params = {
            'n_estimators': 200, 'max_depth': 12,
            'min_samples_split': 4, 'min_samples_leaf': 2,
            'max_features': 'sqrt'
        }
        return mejores_params, None

    def objetivo(trial):
        params = {
            'n_estimators':     trial.suggest_int('n_estimators', 50, 400),
            'max_depth':        trial.suggest_int('max_depth', 4, 20),
            'min_samples_split':trial.suggest_int('min_samples_split', 2, 15),
            'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 8),
            'max_features':     trial.suggest_categorical('max_features', ['sqrt', 'log2', None]),
        }
        modelo = RandomForestRegressor(**params, random_state=RANDOM_SEED, n_jobs=-1)
        return cv_score(modelo, X, y)

    study = optuna.create_study(direction='minimize',
                                 sampler=optuna.samplers.TPESampler(seed=RANDOM_SEED))
    study.optimize(objetivo, n_trials=n_trials, show_progress_bar=False)
    best = study.best_params

    # Reentrenar con mejores parámetros
    modelo_final = RandomForestRegressor(**best, random_state=RANDOM_SEED, n_jobs=-1)
    modelo_final.fit(X, y)
    with open(MODEL_DIR / 'rf_tuned.pkl', 'wb') as f:
        pickle.dump({'model': modelo_final, 'features': FEATURES, 'best_params': best}, f)

    history = [{
        'trial': t.number,
        'rmse':  round(t.value, 4),
        'params': t.params
    } for t in study.trials]

    return best, history


# ─────────────────────────────────────────────────────────────
# TUNING XGBOOST CON OPTUNA
# ─────────────────────────────────────────────────────────────
def tuning_xgboost(df, n_trials=30):
    """Búsqueda bayesiana de hiperparámetros para XGBoost."""
    X = df[FEATURES].values
    y = df['precio_s_ton'].values

    if not OPTUNA_AVAILABLE:
        mejores_params = {
            'n_estimators': 300, 'learning_rate': 0.05, 'max_depth': 6,
            'subsample': 0.8, 'colsample_bytree': 0.8, 'reg_alpha': 0.1
        }
        return mejores_params, None

    def objetivo(trial):
        params = {
            'n_estimators':    trial.suggest_int('n_estimators', 50, 500),
            'learning_rate':   trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'max_depth':       trial.suggest_int('max_depth', 3, 10),
            'subsample':       trial.suggest_float('subsample', 0.5, 1.0),
            'colsample_bytree':trial.suggest_float('colsample_bytree', 0.5, 1.0),
            'reg_alpha':       trial.suggest_float('reg_alpha', 1e-4, 10, log=True),
            'reg_lambda':      trial.suggest_float('reg_lambda', 1e-4, 10, log=True),
        }
        modelo = xgb.XGBRegressor(**params, random_state=RANDOM_SEED, verbosity=0)
        return cv_score(modelo, X, y)

    study = optuna.create_study(direction='minimize',
                                 sampler=optuna.samplers.TPESampler(seed=RANDOM_SEED))
    study.optimize(objetivo, n_trials=n_trials, show_progress_bar=False)
    best = study.best_params

    # Reentrenar
    modelo_final = xgb.XGBRegressor(**best, random_state=RANDOM_SEED, verbosity=0)
    modelo_final.fit(X, y)
    with open(MODEL_DIR / 'xgb_tuned.pkl', 'wb') as f:
        pickle.dump({'model': modelo_final, 'features': FEATURES, 'best_params': best}, f)

    history = [{
        'trial': t.number,
        'rmse':  round(t.value, 4),
        'params': t.params
    } for t in study.trials]

    return best, history


# ─────────────────────────────────────────────────────────────
# TUNING ARIMA — Grid Search sobre (p, d, q)
# ─────────────────────────────────────────────────────────────
def tuning_arima(serie):
    """Búsqueda grid de parámetros ARIMA (p, d, q)."""
    from statsmodels.tsa.arima.model import ARIMA
    import itertools

    p_values = [1, 2, 3, 5]
    d_values = [1]
    q_values = [0, 1, 2]

    n = len(serie)
    train = serie.iloc[:int(n * 0.8)]
    test  = serie.iloc[int(n * 0.8):]

    mejores = {'aic': np.inf, 'orden': None, 'rmse': None}
    tabla_grid = []

    for p, d, q in itertools.product(p_values, d_values, q_values):
        try:
            m = ARIMA(train, order=(p, d, q)).fit()
            fc = m.forecast(steps=len(test)).values
            rmse_val = np.sqrt(mean_squared_error(test.values, fc))
            tabla_grid.append({'p': p, 'd': d, 'q': q, 'AIC': round(m.aic, 2), 'RMSE': round(rmse_val, 4)})
            if m.aic < mejores['aic']:
                mejores = {'aic': m.aic, 'orden': (p, d, q), 'rmse': round(rmse_val, 4)}
        except Exception:
            pass

    return mejores, tabla_grid


# ─────────────────────────────────────────────────────────────
# GRÁFICO DE CONVERGENCIA DE OPTUNA
# ─────────────────────────────────────────────────────────────
def grafico_convergencia(history_rf, history_xgb):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / 'figures').mkdir(parents=True, exist_ok=True)

    if history_rf is None or history_xgb is None:
        return None

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle('Convergencia del Ajuste de Hiperparámetros (Optuna — Bayesiano)',
                 fontsize=13, fontweight='bold')

    for ax, history, nombre, color in zip(
        axes,
        [history_rf, history_xgb],
        ['Random Forest', 'XGBoost'],
        ['#2ecc71', '#e74c3c']
    ):
        trials = [h['trial'] for h in history]
        rmses  = [h['rmse']  for h in history]
        best_so_far = [min(rmses[:i+1]) for i in range(len(rmses))]

        ax.scatter(trials, rmses, color=color, alpha=0.4, s=25, label='RMSE por trial')
        ax.plot(trials, best_so_far, color='navy', linewidth=2, label='Mejor RMSE acumulado')
        ax.set_xlabel('Número de Trial')
        ax.set_ylabel('RMSE (Validación)')
        ax.set_title(nombre, fontweight='bold')
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

    plt.tight_layout()
    path = OUTPUT_DIR / 'figures' / 'hiperparametros_convergencia.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return str(path)


# ─────────────────────────────────────────────────────────────
# PIPELINE PRINCIPAL
# ─────────────────────────────────────────────────────────────
def ejecutar_hyperparameter_tuning(n_trials=30):
    """Ejecuta el pipeline completo de ajuste de hiperparámetros."""
    print(f"\n=== Ajuste de Hiperparametros ({n_trials} trials por modelo) ===")
    df = cargar_features()

    # Importar serie de Arroz
    from eda import cargar_datos
    df_full = cargar_datos()
    df_cult = df_full[df_full['cultivo'] == 'Arroz']
    serie_arroz = df_cult.groupby('fecha')['precio_s_ton'].mean()
    serie_arroz = serie_arroz.asfreq('MS', method='pad')

    print("  -> Random Forest...")
    best_rf, hist_rf   = tuning_random_forest(df, n_trials)
    print(f"     Mejores parametros RF: {best_rf}")

    print("  -> XGBoost...")
    best_xgb, hist_xgb = tuning_xgboost(df, n_trials)
    print(f"     Mejores parametros XGB: {best_xgb}")

    print("  -> ARIMA (Grid Search)...")
    best_arima, grid_arima = tuning_arima(serie_arroz)
    print(f"     Mejor orden ARIMA: {best_arima['orden']} (AIC={best_arima['aic']:.2f})")

    fig_path = grafico_convergencia(hist_rf, hist_xgb)

    resultados = {
        'random_forest': {'best_params': best_rf},
        'xgboost':       {'best_params': best_xgb},
        'arima':         {'mejor': best_arima, 'grid': grid_arima},
        'figura_convergencia': fig_path
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / 'hyperparameter_resultados.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)

    print("=== Ajuste de hiperparametros completado ===")
    return resultados


if __name__ == '__main__':
    ejecutar_hyperparameter_tuning(n_trials=20)
