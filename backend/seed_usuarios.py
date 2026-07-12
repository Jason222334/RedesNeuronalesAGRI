from database import SessionLocal
from sqlalchemy import text
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()
try:
    hashed_pass = pwd_context.hash("123456")
    # Creamos un usuario normal
    query = text("""
        INSERT INTO usuarios (id_usuario, nombres, apellidos, correo, contrasena_hash) 
        VALUES (2, 'Agricultor', 'Valle', 'usuario@unt.pe', :h)
    """)
    db.execute(query, {"h": hashed_pass})
    db.commit()
    print("Usuario estándar creado: usuario@unt.pe / 123456 (Hash: OK)")
except Exception as e:
    print(f"Error (quizás ya existe): {e}")
finally:
    db.close()