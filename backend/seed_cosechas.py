from database import SessionLocal
from sqlalchemy import text
import random
from datetime import timedelta, date

db = SessionLocal()

def poblar_cosechas():
    print("Iniciando inyección de 200 datos de cosechas...")
    
    try:
        # 1. Necesitamos al menos un usuario y un cultivo en las variables.
        # Asumimos que el usuario 1 ya existe (el administrador que creamos)
        # Vamos a crear una "Siembra" falsa primero, porque la base de datos exige 
        # que una cosecha provenga de una siembra (Integridad Referencial).
        
        query_cultivo = text("SELECT id_cultivo FROM cultivos LIMIT 1")
        resultado = db.execute(query_cultivo).fetchone()
        
        if not resultado:
            print("Error: Necesitas registrar al menos un cultivo en la interfaz antes de correr esto.")
            return
            
        id_cultivo = resultado[0]
        
        # Insertamos una siembra de prueba
        query_siembra = text("""
            INSERT INTO siembras (id_usuario, id_cultivo, fecha_siembra, area_hectareas, sector_valle, estado)
            VALUES (1, :id_cultivo, '2023-01-01', 50.5, 'Sector Pacasmayo', 'Finalizado')
            RETURNING id_siembra
        """)
        resultado_siembra = db.execute(query_siembra, {"id_cultivo": id_cultivo})
        id_siembra = resultado_siembra.fetchone()[0]
        db.commit()

        # 2. Generamos las 200 cosechas ligadas a esa siembra
        fecha_base = date(2023, 5, 1)
        calidades = ['Alta', 'Media', 'Baja']
        
        for i in range(200):
            rendimiento = random.uniform(2.5, 8.5) # Toneladas por hectárea
            calidad = random.choice(calidades)
            fecha_cosecha = fecha_base + timedelta(days=i*2) # Una cosecha cada 2 días
            
            query_cosecha = text("""
                INSERT INTO cosechas (id_siembra, fecha_cosecha, rendimiento_toneladas, calidad)
                VALUES (:id_siembra, :fecha, :rendimiento, :calidad)
            """)
            
            db.execute(query_cosecha, {
                "id_siembra": id_siembra,
                "fecha": fecha_cosecha,
                "rendimiento": round(rendimiento, 2),
                "calidad": calidad
            })

        db.commit()
        print("¡Éxito! 200 cosechas registradas en la base de datos Supabase.")
        
    except Exception as e:
        db.rollback()
        print(f"Ocurrió un error al inyectar datos: {e}")
    finally:
        db.close()

poblar_cosechas()