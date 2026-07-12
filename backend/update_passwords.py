from database import SessionLocal
import models_db
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
db = SessionLocal()

def migrate():
    usuarios = db.query(models_db.Usuario).all()
    count = 0
    for u in usuarios:
        # Si la contraseña no parece un hash bcrypt (empieza por $2b$), la hasheamos
        if not u.contrasena_hash.startswith("$2b$"):
            print(f"Hasheando contraseña para: {u.correo}")
            u.contrasena_hash = pwd_context.hash(u.contrasena_hash)
            count += 1
    
    db.commit()
    print(f"Migración completada. {count} usuarios actualizados.")

if __name__ == "__main__":
    migrate()
    db.close()