"""
Módulo de Análisis Exploratorio de Datos (EDA)
Sistema Inteligente Agrícola - Valle Jequetepeque
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os
import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / 'data' / 'dataset_precios_jequetepeque.csv'
OUTPUT_PATH = Path(__file__).parent / 'outputs'

def ensure_output_dir():
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    (OUTPUT_PATH / 'figures').mkdir(parents=True, exist_ok=True)

def cargar_datos():
    """Carga y preprocesa el dataset."""
    df = pd.read_csv(DATA_PATH)
    df['fecha'] = pd.to_datetime(df['fecha'])
    df = df.sort_values('fecha').reset_index(drop=True)
    return df

def estadisticos_descriptivos(df):
    """Calcula estadísticos descriptivos completos."""
    numericas = ['precio_s_ton', 'temperatura', 'precipitacion_mm', 'costo_transporte']
    desc = df[numericas].describe().round(3)
    
    extra = pd.DataFrame({
        col: {
            'skewness': round(df[col].skew(), 4),
            'kurtosis': round(df[col].kurtosis(), 4),
            'cv': round(df[col].std() / df[col].mean() * 100, 2),
            'missing': int(df[col].isna().sum()),
            'outliers_iqr': int(detectar_outliers_iqr(df[col]))
        } for col in numericas
    }).T
    
    return desc.to_dict(), extra.to_dict()

def detectar_outliers_iqr(series):
    """Detecta outliers con el método IQR."""
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return ((series < lower) | (series > upper)).sum()

def limpiar_datos(df):
    """Limpieza de datos: imputa nulos y trata outliers."""
    df_clean = df.copy()
    numericas = ['precio_s_ton', 'temperatura', 'precipitacion_mm', 'costo_transporte']
    
    for col in numericas:
        Q1 = df_clean[col].quantile(0.25)
        Q3 = df_clean[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        df_clean[col] = df_clean[col].clip(lower, upper)
        df_clean[col] = df_clean[col].fillna(df_clean[col].median())
    
    return df_clean

def grafico_series_temporales(df):
    """Genera gráfico de series temporales de precios por cultivo."""
    ensure_output_dir()
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Series Temporales de Precios - Valle Jequetepeque', fontsize=16, fontweight='bold')
    
    cultivos = ['Arroz', 'Maiz', 'Cebolla', 'Esparrago']
    colores = ['#2ecc71', '#f39c12', '#e74c3c', '#9b59b6']
    
    for ax, cultivo, color in zip(axes.flatten(), cultivos, colores):
        data_cult = df[df['cultivo'] == cultivo].copy()
        data_cult = data_cult.set_index('fecha')['precio_s_ton']
        ax.plot(data_cult.index, data_cult.values, color=color, linewidth=1.5, alpha=0.8)
        media_movil = data_cult.rolling(window=3).mean()
        ax.plot(media_movil.index, media_movil.values, color='navy', linewidth=2, linestyle='--', label='Media Móvil (3m)')
        ax.set_title(f'{cultivo}', fontweight='bold')
        ax.set_ylabel('Precio (S//ton)')
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    
    plt.tight_layout()
    path = OUTPUT_PATH / 'figures' / 'series_temporales.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return str(path)

def grafico_heatmap_correlacion(df):
    """Genera heatmap de correlación entre variables."""
    ensure_output_dir()
    numericas = ['precio_s_ton', 'temperatura', 'precipitacion_mm', 'costo_transporte', 'nivel_plaga']
    corr_matrix = df[numericas].corr().round(3)
    
    fig, ax = plt.subplots(figsize=(9, 7))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(
        corr_matrix, annot=True, fmt='.3f', cmap='RdYlGn',
        mask=mask, ax=ax, linewidths=0.5,
        cbar_kws={'label': 'Coeficiente de correlación'}
    )
    ax.set_title('Mapa de Calor de Correlaciones\nVariables del Sistema Agrícola', 
                 fontsize=13, fontweight='bold', pad=20)
    
    path = OUTPUT_PATH / 'figures' / 'heatmap_correlacion.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return str(path)

def grafico_distribucion_precios(df):
    """Genera histogramas de distribución de precios por cultivo."""
    ensure_output_dir()
    cultivos = df['cultivo'].unique()
    colores = ['#2ecc71', '#f39c12', '#e74c3c', '#9b59b6']
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle('Distribución de Precios por Cultivo', fontsize=15, fontweight='bold')
    
    for ax, cultivo, color in zip(axes.flatten(), cultivos, colores):
        data = df[df['cultivo'] == cultivo]['precio_s_ton']
        ax.hist(data, bins=25, color=color, edgecolor='white', alpha=0.8)
        ax.axvline(data.mean(), color='navy', linestyle='--', label=f'Media: {data.mean():.0f}')
        ax.axvline(data.median(), color='red', linestyle=':', label=f'Mediana: {data.median():.0f}')
        ax.set_title(cultivo, fontweight='bold')
        ax.set_xlabel('Precio (S//ton)')
        ax.set_ylabel('Frecuencia')
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    
    plt.tight_layout()
    path = OUTPUT_PATH / 'figures' / 'distribucion_precios.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return str(path)

def grafico_boxplot_estacional(df):
    """Boxplot de precios por estación y cultivo."""
    ensure_output_dir()
    df_plot = df.copy()
    df_plot['mes'] = df_plot['fecha'].dt.month
    def get_estacion(m):
        if m in [12, 1, 2]: return 'Verano'
        elif m in [3, 4, 5]: return 'Otoño'
        elif m in [6, 7, 8]: return 'Invierno'
        else: return 'Primavera'
    df_plot['estacion'] = df_plot['mes'].apply(get_estacion)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    cultivos = df['cultivo'].unique()
    colores = ['#2ecc71', '#f39c12', '#e74c3c', '#9b59b6']
    
    df_plot_pivot = df_plot.groupby(['estacion', 'cultivo'])['precio_s_ton'].mean().reset_index()
    pivot = df_plot_pivot.pivot(index='estacion', columns='cultivo', values='precio_s_ton')
    pivot = pivot.loc[['Verano', 'Otoño', 'Invierno', 'Primavera']]
    pivot.plot(kind='bar', ax=ax, color=colores, alpha=0.85, edgecolor='white')
    ax.set_title('Precio Promedio por Estación y Cultivo', fontsize=13, fontweight='bold')
    ax.set_xlabel('Estación')
    ax.set_ylabel('Precio Promedio (S//ton)')
    ax.legend(title='Cultivo')
    ax.grid(axis='y', alpha=0.3)
    plt.xticks(rotation=0)
    plt.tight_layout()
    
    path = OUTPUT_PATH / 'figures' / 'precios_estacionales.png'
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return str(path)

def ejecutar_eda_completo():
    """Ejecuta el pipeline EDA completo y devuelve resultados estructurados."""
    ensure_output_dir()
    df = cargar_datos()
    df_clean = limpiar_datos(df)
    
    desc, extra = estadisticos_descriptivos(df)
    
    figuras = {
        'series_temporales': grafico_series_temporales(df_clean),
        'heatmap': grafico_heatmap_correlacion(df_clean),
        'distribucion': grafico_distribucion_precios(df_clean),
        'estacional': grafico_boxplot_estacional(df_clean)
    }
    
    resumen = {
        'n_registros': len(df),
        'n_registros_limpios': len(df_clean),
        'periodo': f"{df['fecha'].min().strftime('%Y-%m')} a {df['fecha'].max().strftime('%Y-%m')}",
        'cultivos': list(df['cultivo'].unique()),
        'estadisticos': desc,
        'estadisticos_extra': extra,
        'figuras': figuras
    }
    
    # Guardar JSON de resultados
    with open(OUTPUT_PATH / 'eda_resultados.json', 'w', encoding='utf-8') as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2, default=str)
    
    return resumen

if __name__ == '__main__':
    resultado = ejecutar_eda_completo()
    print(f"EDA completado: {resultado['n_registros']} registros analizados")
    print(f"Figuras generadas: {list(resultado['figuras'].keys())}")
