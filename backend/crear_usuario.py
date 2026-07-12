from database import SessionLocal
from sqlalchemy import text
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

try:
    hashed_pass = pwd_context.hash("admin123")
    query = text("""
        INSERT INTO usuarios (id_usuario, nombres, apellidos, correo, contrasena_hash) 
        VALUES (1, 'Administrador', 'Prueba', 'admin@unt.pe', :h)
    """)
    db.execute(query, {"h": hashed_pass})
    db.commit()
    print("¡Usuario administrador creado exitosamente con hashing!")
except Exception as e:
    print(f"Ocurrió un error: {e}")
finally:
    db.close()