from database import SessionLocal
from models_db import Cultivo
from ml_model.predict import entrenar_modelo
from sqlalchemy import text
import random
from datetime import timedelta, date

db = SessionLocal()

def poblar_y_entrenar():
    print("Iniciando inyección de datos y entrenamiento...")

    # 1. Insertar un cultivo de prueba (Ej: Arroz) si no existe
    nuevo_cultivo = Cultivo(nombre_cultivo="Arroz", variedad="Añejo", tiempo_estimado_cosecha_dias=120)
    db.add(nuevo_cultivo)
    db.commit()
    db.refresh(nuevo_cultivo)
    id_cultivo = nuevo_cultivo.id_cultivo
    print(f"Cultivo base registrado con ID: {id_cultivo}")

    # 2. Generar 100 registros históricos ficticios para el Valle Jequetepeque
    datos_entrenamiento = []
    fecha_base = date(2023, 1, 1)

    for i in range(100):
        temp = random.uniform(20.0, 32.0) # Temperatura entre 20 y 32 grados
        prec = random.uniform(0.0, 50.0)  # Lluvia en mm
        trans = random.uniform(100.0, 300.0) # Costo de transporte
        
        # Lógica matemática para dar sentido a los datos: 
        # El precio base es 1500, sube si el transporte es caro, baja si llueve bien.
        precio = 1500 + (trans * 1.5) - (prec * 2) + random.uniform(-50, 50)
        
        # Guardar en la base de datos (Supabase)
        query = text("""
            INSERT INTO datos_historicos_precios 
            (id_cultivo, fecha_registro, precio_venta_tonelada, temperatura_promedio, precipitacion_mm, costo_transporte)
            VALUES (:id_cultivo, :fecha, :precio, :temp, :prec, :trans)
        """)
        db.execute(query, {
            "id_cultivo": id_cultivo,
            "fecha": fecha_base + timedelta(days=i*3), # Datos cada 3 días
            "precio": precio,
            "temp": temp,
            "prec": prec,
            "trans": trans
        })
        
        # Guardar en una lista en memoria para entrenar a Scikit-Learn
        datos_entrenamiento.append({
            "temperatura_promedio": temp,
            "precipitacion_mm": prec,
            "costo_transporte": trans,
            "precio_venta_tonelada": precio
        })

    db.commit()
    print("100 registros históricos insertados en Supabase.")

    # 3. Entrenar el modelo con la lista de datos
    print("Entrenando el modelo ARIMA...")
    score = entrenar_modelo(datos_entrenamiento)
    print(f"¡Éxito! Modelo ARIMA entrenado.")
    print("El archivo 'arima_model.pkl' ya existe en tu carpeta ml_model.")

poblar_y_entrenar()