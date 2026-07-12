from database import SessionLocal
from sqlalchemy import text
import random
from datetime import timedelta, date

db = SessionLocal()

def poblar_todos_los_cultivos():
    print("Inyectando datos para el resto de cultivos...")
    
    # Buscamos todos los cultivos registrados
    cultivos = db.execute(text("SELECT id_cultivo, nombre_cultivo FROM cultivos")).fetchall()
    
    fecha_base = date(2023, 6, 1)
    calidades = ['Alta', 'Media', 'Baja']

    for id_cultivo, nombre in cultivos:
        # 1. Crear una siembra para cada cultivo
        query_siembra = text("""
            INSERT INTO siembras (id_usuario, id_cultivo, fecha_siembra, area_hectareas, sector_valle, estado)
            VALUES (1, :id, '2023-01-15', 30, 'Sector Jequetepeque', 'Finalizado')
            RETURNING id_siembra
        """)
        id_siembra = db.execute(query_siembra, {"id": id_cultivo}).fetchone()[0]
        
        # 2. Generar 40 cosechas aleatorias para cada cultivo
        for i in range(40):
            rendimiento = random.uniform(3.0, 7.5)
            # Distribuir las fechas a lo largo de los meses
            fecha_cosecha = fecha_base + timedelta(days=i*10 + random.randint(1, 5)) 
            
            query_cosecha = text("""
                INSERT INTO cosechas (id_siembra, fecha_cosecha, rendimiento_toneladas, calidad)
                VALUES (:id_s, :fecha, :rend, :cal)
            """)
            db.execute(query_cosecha, {
                "id_s": id_siembra, "fecha": fecha_cosecha, 
                "rend": round(rendimiento, 2), "cal": random.choice(calidades)
            })

    db.commit()
    print("¡Éxito! Ahora todos tus cultivos tienen datos de producción históricos.")
    db.close()

poblar_todos_los_cultivos()