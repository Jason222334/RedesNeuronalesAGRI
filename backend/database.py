import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Intentar cargar desde variables de entorno, usando la cadena por defecto como fallback
URL_BASE_DATOS = os.getenv("DATABASE_URL")
if not URL_BASE_DATOS:
    URL_BASE_DATOS = "postgresql://postgres.aephgcnbsomypsedvtyk:nosetudime0302@aws-1-us-east-2.pooler.supabase.com:6543/postgres"

# Intentar inicializar el motor con la base de datos especificada
try:
    if "sqlite" in URL_BASE_DATOS:
        engine = create_engine(URL_BASE_DATOS, connect_args={"check_same_thread": False})
    else:
        engine = create_engine(
            URL_BASE_DATOS,
            pool_size=5,
            max_overflow=10,
            pool_timeout=5,        # 5 segundos de espera máximo para failover rápido
            pool_recycle=1800,
            pool_pre_ping=True
        )
    # Probar la conexión física
    with engine.connect() as conn:
        pass
    print("[DATABASE] Conectado exitosamente a la base de datos principal.")
except Exception as e:
    print(f"[DATABASE WARNING] Fallo conexion a PostgreSQL ({e}). Usando base de datos SQLite local de respaldo...")
    # Configurar SQLite local
    URL_BASE_DATOS = "sqlite:///./sql_app.db"
    engine = create_engine(URL_BASE_DATOS, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()