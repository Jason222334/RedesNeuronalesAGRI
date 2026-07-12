import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
import pickle
import os
from datetime import datetime, timedelta

MODEL_PATH = "ml_model/arima_model.pkl"

def entrenar_modelo(datos_historicos: list):
    """
    Entrena un modelo ARIMA para predicción de precios.
    """
    df = pd.DataFrame(datos_historicos)
    
    if 'fecha_registro' in df.columns:
        df['fecha_registro'] = pd.to_datetime(df['fecha_registro'])
        df = df.sort_values('fecha_registro')
        series = df.set_index('fecha_registro')['precio_venta_tonelada']
    else:
        series = df['precio_venta_tonelada']
    
    # Modelo ARIMA simple (p,d,q) = (5,1,0) como base
    # En un entorno real se buscarían los mejores parámetros
    modelo = ARIMA(series, order=(5, 1, 0))
    modelo_fit = modelo.fit()
    
    # Guardar el objeto de resultados del modelo
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(modelo_fit, f)
        
    return 0.80 # Valor simbólico

def predecir_precio(temperatura, precipitacion, transporte, meses_futuro=1):
    """
    Realiza una predicción usando el modelo ARIMA guardado.
    Nota: ARIMA predice basándose en la serie temporal, los factores externos 
    se usan aquí como ajuste fino sobre la predicción base.
    """
    if not os.path.exists(MODEL_PATH):
        precio_base = 1500 + (transporte * 1.2) - (precipitacion * 0.5)
        return round(precio_base, 2)

    with open(MODEL_PATH, 'rb') as f:
        modelo_fit = pickle.load(f)

    # Predecir n pasos adelante (meses_futuro)
    # Asumiendo datos diarios en el entrenamiento, meses_futuro * 30
    forecast = modelo_fit.forecast(steps=meses_futuro * 10) # 10 pasos si los datos eran cada 3 días
    prediccion_base = forecast.iloc[-1]

    # Ajuste por factores climáticos (Regresión simple sobre la base)
    ajuste_clima = (temperatura - 25) * 2 - (precipitacion - 10) * 0.5
    ajuste_transporte = (transporte - 150) * 0.5
    
    resultado = prediccion_base + ajuste_clima + ajuste_transporte
    
    return round(float(resultado), 2)

def estimar_produccion(id_cultivo, area_hectareas):
    """
    Estima la producción en toneladas basada en el área y el tipo de cultivo.
    En un sistema real, esto usaría un modelo entrenado con suelos y clima.
    """
    # Rendimientos promedio por hectárea en el Valle Jequetepeque (ficticios para el sistema)
    rendimientos = {
        1: 9.5,  # Arroz (Ton/Ha)
        2: 12.0, # Maíz
        3: 25.0, # Cebolla
        4: 5.5,  # Espárrago
    }

    # Si el ID no está, usamos un promedio general de 8.0
    rendimiento_base = rendimientos.get(id_cultivo, 8.0)

    produccion_total = area_hectareas * rendimiento_base
    return round(produccion_total, 2)

def predecir_riesgo_plaga(id_cultivo, temperatura, precipitacion):
    """
    Calcula la probabilidad de plagas específica por cultivo.
    """
    # Riesgos base por cultivo (Sensibilidad)
    riesgos_base = {
        1: 20.0, # Arroz: Sensible a humedad (Hongo)
        2: 15.0, # Maíz: Sensible a calor (Cogollero)
        3: 25.0, # Cebolla: Muy sensible a humedad
        4: 10.0, # Espárrago: Más resistente
    }

    probabilidad = riesgos_base.get(id_cultivo, 15.0)

    # Factores climáticos
    if temperatura > 26 and precipitacion > 15:
        probabilidad += 50.0 
    elif temperatura > 22 and precipitacion > 5:
        probabilidad += 20.0

    return min(round(probabilidad, 1), 100.0)

def calcular_recomendacion_cultivos(cultivos_lista: list, meses_futuro: int = 3, trans_base: float = 150.0):
    """
    Analiza la rentabilidad proyectada para un horizonte de tiempo específico.
    Incluye modelos de costos más realistas para evitar optimismo excesivo.
    """
    from datetime import datetime

    recomendaciones = []
    mes_actual = datetime.now().month
    mes_objetivo = (mes_actual + meses_futuro - 1) % 12 + 1

    # Costos realistas por Ha (Mano de obra, insumos, preparación)
    costos_produccion = {
        1: 6500.0, # Arroz
        2: 5800.0, # Maíz
        3: 7500.0, # Cebolla
        4: 9000.0, # Espárrago
    }

    # Rendimientos promedio realistas
    rendimientos = {1: 9.0, 2: 10.0, 3: 22.0, 4: 5.0}

    for c in cultivos_lista:
        # Predecir clima para el mes objetivo
        if mes_objetivo in [1, 2, 3]: t, p = 28.5, 25.0
        elif mes_objetivo in [4, 5, 6]: t, p = 24.0, 5.0
        elif mes_objetivo in [7, 8, 9]: t, p = 20.0, 1.0
        else: t, p = 23.0, 2.0

        precio_proyectado = predecir_precio(t, p, trans_base)

        # Cálculo de ROI Realista
        costo_fijo = costos_produccion.get(c.id_cultivo, 6000.0)
        rend = rendimientos.get(c.id_cultivo, 8.0)

        ingreso_bruto = rend * precio_proyectado
        costo_total = costo_fijo + (rend * trans_base)
        ganancia = ingreso_bruto - costo_total
        roi = (ganancia / costo_total) * 100

        recomendaciones.append({
            "id_cultivo": c.id_cultivo,
            "nombre": c.nombre_cultivo,
            "viabilidad": round(roi, 1),
            "precio_est": round(precio_proyectado, 2),
            "mes_objetivo": mes_objetivo
        })

    return sorted(recomendaciones, key=lambda x: x['viabilidad'], reverse=True)