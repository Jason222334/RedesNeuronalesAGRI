"""
Pruebas Estadísticas Rigurosas — Sistema Inteligente Agrícola
Valida los modelos con tests estadísticos estándar en econometría y ML:
  - Diebold-Mariano (comparación de modelos de predicción)
  - Shapiro-Wilk (normalidad de residuos)
  - Ljung-Box (autocorrelación de residuos)
  - Kolmogorov-Smirnov (distribución de errores)
  - Wilcoxon (comparación no paramétrica de dos modelos)
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from scipy.stats import shapiro, kstest, wilcoxon
import json
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

OUTPUT_DIR = Path(__file__).parent / 'outputs'


def test_shapiro_wilk(residuos, nombre_modelo):
    """
    Test de Shapiro-Wilk: ¿son normales los errores de predicción?
    H0: Los residuos siguen distribución normal.
    """
    # Shapiro-Wilk funciona mejor con n <= 5000
    sample = residuos[:5000] if len(residuos) > 5000 else residuos
    stat, pvalue = shapiro(sample)
    return {
        'test': 'Shapiro-Wilk',
        'modelo': nombre_modelo,
        'estadistico': round(float(stat), 6),
        'p_valor': round(float(pvalue), 6),
        'H0': 'Residuos siguen distribución normal',
        'resultado': 'No rechazar H0 (normal)' if pvalue > 0.05 else 'Rechazar H0 (no normal)',
        'interpretacion': (
            'Los errores tienen distribución aproximadamente normal. '
            'El modelo no presenta sesgo sistemático significativo.'
            if pvalue > 0.05 else
            'Los errores NO son normales. Puede haber sesgo o valores atípicos en el modelo.'
        )
    }


def test_ljung_box(residuos, nombre_modelo, lags=10):
    """
    Test de Ljung-Box: ¿hay autocorrelación en los residuos?
    H0: No hay autocorrelación en los residuos.
    """
    from statsmodels.stats.diagnostic import acorr_ljungbox
    result = acorr_ljungbox(residuos, lags=[lags], return_df=True)
    stat   = float(result['lb_stat'].iloc[0])
    pvalue = float(result['lb_pvalue'].iloc[0])
    return {
        'test': 'Ljung-Box',
        'modelo': nombre_modelo,
        'lags': lags,
        'estadistico': round(stat, 6),
        'p_valor': round(pvalue, 6),
        'H0': f'No hay autocorrelación en los primeros {lags} lags',
        'resultado': 'No rechazar H0 (sin autocorrelación)' if pvalue > 0.05 else 'Rechazar H0 (autocorrelación presente)',
        'interpretacion': (
            'Los residuos son ruido blanco. El modelo captura adecuadamente la estructura temporal.'
            if pvalue > 0.05 else
            'Existe autocorrelación en los residuos. El modelo no captura toda la estructura temporal.'
        )
    }


def test_kolmogorov_smirnov(residuos, nombre_modelo):
    """
    Test KS: compara la distribución de errores con una normal estándar.
    H0: Los residuos siguen la distribución normal estándar.
    """
    residuos_norm = (residuos - np.mean(residuos)) / np.std(residuos)
    stat, pvalue = kstest(residuos_norm, 'norm')
    return {
        'test': 'Kolmogorov-Smirnov',
        'modelo': nombre_modelo,
        'estadistico': round(float(stat), 6),
        'p_valor': round(float(pvalue), 6),
        'H0': 'Residuos siguen distribución normal estándar',
        'resultado': 'No rechazar H0' if pvalue > 0.05 else 'Rechazar H0',
        'interpretacion': (
            'Los errores estandarizados son consistentes con una distribución normal.'
            if pvalue > 0.05 else
            'Los errores difieren significativamente de la normalidad.'
        )
    }


def test_wilcoxon_comparacion(residuos_a, residuos_b, nombre_a, nombre_b):
    """
    Test de Wilcoxon (rangos con signo): compara pares de errores absolutos.
    H0: No hay diferencia sistemática en los errores de ambos modelos.
    """
    n_min = min(len(residuos_a), len(residuos_b))
    err_a = np.abs(residuos_a[:n_min])
    err_b = np.abs(residuos_b[:n_min])

    if np.all(err_a == err_b):
        return {
            'test': 'Wilcoxon',
            'modelos': f'{nombre_a} vs {nombre_b}',
            'nota': 'Errores idénticos — test no aplicable'
        }

    stat, pvalue = wilcoxon(err_a, err_b)
    return {
        'test': 'Wilcoxon (Rangos con Signo)',
        'modelos': f'{nombre_a} vs {nombre_b}',
        'estadistico': round(float(stat), 6),
        'p_valor': round(float(pvalue), 6),
        'H0': f'No hay diferencia en precisión entre {nombre_a} y {nombre_b}',
        'resultado': 'No rechazar H0 (rendimiento similar)' if pvalue > 0.05 else f'Rechazar H0 — diferencia significativa',
        'mejor': nombre_a if err_a.mean() < err_b.mean() else nombre_b,
        'interpretacion': (
            f'Los modelos {nombre_a} y {nombre_b} tienen rendimiento estadísticamente similar.'
            if pvalue > 0.05 else
            f'Existe diferencia significativa. El modelo con menor MAE es superior.'
        )
    }


def test_diebold_mariano(y_true, pred_a, pred_b, nombre_a, nombre_b, h=1):
    """
    Test de Diebold-Mariano: ¿es un modelo significativamente mejor que el otro?
    Compara las diferencias en errores de predicción cuadráticos.
    H0: Los dos modelos tienen la misma capacidad predictiva.
    """
    e1 = np.array(y_true) - np.array(pred_a)
    e2 = np.array(y_true) - np.array(pred_b)

    n_min = min(len(e1), len(e2))
    e1, e2 = e1[:n_min], e2[:n_min]

    d = e1**2 - e2**2  # diferencia en errores cuadráticos

    mean_d = np.mean(d)
    # Varianza con corrección HAC simple (Newey-West con h lags)
    T = len(d)
    gamma_0 = np.var(d, ddof=1)
    gammas = [np.cov(d[j:], d[:-j])[0, 1] for j in range(1, h+1)] if h > 0 else []
    var_d = gamma_0 + 2 * sum(gammas)
    var_d = max(var_d, 1e-10)

    DM_stat = mean_d / np.sqrt(var_d / T)
    pvalue = 2 * (1 - stats.norm.cdf(abs(DM_stat)))

    return {
        'test': 'Diebold-Mariano',
        'modelos': f'{nombre_a} vs {nombre_b}',
        'estadistico_DM': round(float(DM_stat), 6),
        'p_valor': round(float(pvalue), 6),
        'H0': f'Igual capacidad predictiva entre {nombre_a} y {nombre_b}',
        'resultado': 'No rechazar H0 (igual capacidad)' if pvalue > 0.05 else 'Rechazar H0 — diferencia significativa',
        'mejor': nombre_b if DM_stat > 0 else nombre_a,
        'interpretacion': (
            f'{nombre_a} y {nombre_b} tienen capacidad predictiva estadísticamente equivalente.'
            if pvalue > 0.05 else
            (f'{nombre_b} es significativamente superior.' if DM_stat > 0 else f'{nombre_a} es significativamente superior.')
        )
    }


def grafico_residuos_qq(residuos_dict):
    """Q-Q plots y distribución de residuos para cada modelo."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / 'figures').mkdir(parents=True, exist_ok=True)

    modelos = list(residuos_dict.keys())
    n = len(modelos)
    fig, axes = plt.subplots(n, 2, figsize=(12, n * 3.5))
    if n == 1:
        axes = axes.reshape(1, -1)

    fig.suptitle('Análisis de Residuos — Pruebas Estadísticas',
                 fontsize=14, fontweight='bold')

    colores = ['#2ecc71', '#e74c3c', '#3498db', '#9b59b6', '#f39c12']

    for i, (nombre, color) in enumerate(zip(modelos, colores)):
        res = np.array(residuos_dict[nombre])

        # Q-Q Plot
        stats.probplot(res, dist='norm', plot=axes[i, 0])
        axes[i, 0].set_title(f'{nombre} — Q-Q Plot', fontweight='bold', fontsize=10)
        axes[i, 0].get_lines()[0].set(color=color, markersize=3)
        axes[i, 0].get_lines()[1].set(color='navy')

        # Histograma de residuos
        axes[i, 1].hist(res, bins=30, color=color, edgecolor='white', alpha=0.8)
        xmin, xmax = axes[i, 1].get_xlim()
        x = np.linspace(xmin, xmax, 200)
        p = stats.norm.pdf(x, res.mean(), res.std())
        ax2 = axes[i, 1].twinx()
        ax2.plot(x, p, 'navy', linewidth=2, label='Normal teórica')
        ax2.set_ylabel('Densidad')
        ax2.legend(fontsize=7)
        axes[i, 1].set_title(f'{nombre} — Distribución de Residuos', fontweight='bold', fontsize=10)
        axes[i, 1].set_xlabel('Residuo')
        axes[i, 1].set_ylabel('Frecuencia')

    plt.tight_layout()
    path = OUTPUT_DIR / 'figures' / 'pruebas_estadisticas_residuos.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return str(path)


def ejecutar_pruebas_estadisticas(y_true_dict, y_pred_dict):
    """
    Pipeline completo de pruebas estadísticas.
    
    Args:
        y_true_dict: {'ARIMA': [...], 'Random Forest': [...], ...}
        y_pred_dict: {'ARIMA': [...], 'Random Forest': [...], ...}
    """
    print("\n=== Ejecutando Pruebas Estadisticas ===")
    modelos = list(y_true_dict.keys())

    # Calcular residuos
    residuos_dict = {}
    for m in modelos:
        yt = np.array(y_true_dict[m])
        yp = np.array(y_pred_dict[m])
        n_min = min(len(yt), len(yp))
        residuos_dict[m] = yt[:n_min] - yp[:n_min]

    resultados = {
        'shapiro_wilk': [],
        'ljung_box':    [],
        'ks':           [],
        'wilcoxon':     [],
        'diebold_mariano': []
    }

    # Tests por modelo
    for m in modelos:
        res = residuos_dict[m]
        resultados['shapiro_wilk'].append(test_shapiro_wilk(res, m))
        resultados['ljung_box'].append(test_ljung_box(res, m))
        resultados['ks'].append(test_kolmogorov_smirnov(res, m))

    # Tests comparativos (todos vs todos)
    for i in range(len(modelos)):
        for j in range(i+1, len(modelos)):
            ma, mb = modelos[i], modelos[j]
            ra, rb = residuos_dict[ma], residuos_dict[mb]
            yta, ytb = np.array(y_true_dict[ma]), np.array(y_true_dict[mb])
            ypa, ypb = np.array(y_pred_dict[ma]), np.array(y_pred_dict[mb])

            resultados['wilcoxon'].append(test_wilcoxon_comparacion(ra, rb, ma, mb))

            # DM requiere mismo y_true - usar el que tenga más datos
            n_dm = min(len(yta), len(ytb), len(ypa), len(ypb))
            if n_dm > 5:
                resultados['diebold_mariano'].append(
                    test_diebold_mariano(yta[:n_dm], ypa[:n_dm], ypb[:n_dm], ma, mb)
                )

    # Gráfico Q-Q
    fig_path = grafico_residuos_qq(residuos_dict)
    resultados['figura'] = fig_path

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_DIR / 'pruebas_estadisticas.json', 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2, default=str)

    print(f"  [+] {len(resultados['shapiro_wilk'])} tests Shapiro-Wilk")
    print(f"  [+] {len(resultados['ljung_box'])} tests Ljung-Box")
    print(f"  [+] {len(resultados['ks'])} tests KS")
    print(f"  [+] {len(resultados['wilcoxon'])} tests Wilcoxon")
    print(f"  [+] {len(resultados['diebold_mariano'])} tests Diebold-Mariano")
    return resultados


if __name__ == '__main__':
    # Demo con residuos sintéticos
    np.random.seed(42)
    n = 100
    yt = np.random.normal(1000, 150, n)
    demo_yt   = {'ARIMA': yt, 'Random Forest': yt}
    demo_yp   = {
        'ARIMA':         yt + np.random.normal(0, 80, n),
        'Random Forest': yt + np.random.normal(0, 60, n)
    }
    resultados = ejecutar_pruebas_estadisticas(demo_yt, demo_yp)
    print(json.dumps(resultados['shapiro_wilk'], indent=2, ensure_ascii=False))
