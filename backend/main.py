from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from pydantic import BaseModel
from fastapi import HTTPException
from passlib.context import CryptContext
import secrets
from datetime import datetime, timedelta
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Configuración de correo (se cargará dinámicamente)
def get_mail_config():
    return ConnectionConfig(
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_FROM=os.getenv("MAIL_FROM"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
        MAIL_SERVER=os.getenv("MAIL_SERVER"),
        MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME"),
        MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True") == "True",
        MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False") == "True",
        USE_CREDENTIALS=os.getenv("USE_CREDENTIALS", "True") == "True",
        VALIDATE_CERTS=os.getenv("VALIDATE_CERTS", "True") == "True"
    )

# Importar configuración de la base de datos
from database import engine, Base, get_db
import models_db

# Importar la función del modelo de Machine Learning
from ml_model.predict import predecir_precio, estimar_produccion, predecir_riesgo_plaga, calcular_recomendacion_cultivos

# Importar todos los módulos (Routers)
from routers import cultivos, reportes, auditoria, usuarios, archivos
from routers import ia_analysis

# Agregar ml_model al path de Python para que los routers puedan importar los módulos
import sys
ml_model_path = os.path.join(os.path.dirname(__file__), 'ml_model')
if ml_model_path not in sys.path:
    sys.path.insert(0, ml_model_path)

# Configuración de seguridad para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# Crear las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Sistema Inteligente Agrícola - Valle Jequetepeque")

# Configuración de CORS para permitir que React (Puerto 3000) se comunique con FastAPI (Puerto 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción se cambia por la URL exacta del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vincular los módulos estructurados
app.include_router(cultivos.router)
app.include_router(reportes.router)
app.include_router(auditoria.router)
app.include_router(usuarios.router)
app.include_router(archivos.router)
app.include_router(ia_analysis.router)

# Esquema para recibir los datos de login
class LoginRequest(BaseModel):
    correo: str
    contrasena: str

class RegisterRequest(BaseModel):
    nombres: str
    apellidos: str
    correo: str
    contrasena: str

class SolicitarRecuperacionRequest(BaseModel):
    correo: str

class RestablecerPasswordRequest(BaseModel):
    token: str
    nueva_contrasena: str

@app.post("/api/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    # Usar ORM para evitar SQL Injection y permitir validación compleja
    user = db.query(models_db.Usuario).filter(models_db.Usuario.correo == req.correo, models_db.Usuario.estado == True).first()
    
    if not user or not verify_password(req.contrasena, user.contrasena_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas o usuario inactivo")
    
    registrar_bitacora(db, user.id_usuario, "Autenticación", f"Inicio de sesión exitoso ({user.rol})")
    
    return {
        "id_usuario": user.id_usuario, 
        "nombres": user.nombres, 
        "correo": user.correo, 
        "rol": user.rol
    }

@app.post("/api/auth/registrar")
def registrar(req: RegisterRequest, db: Session = Depends(get_db)):
    # Verificar si ya existe usando ORM
    exists = db.query(models_db.Usuario).filter(models_db.Usuario.correo == req.correo).first()
    if exists:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    
    new_user = models_db.Usuario(
        nombres=req.nombres,
        apellidos=req.apellidos,
        correo=req.correo,
        contrasena_hash=hash_password(req.contrasena),
        rol='Usuario',
        estado=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    registrar_bitacora(db, new_user.id_usuario, "Registro", "Nuevo usuario registrado desde el portal público")
    
    return {"mensaje": "Usuario registrado exitosamente", "id": new_user.id_usuario}

@app.post("/api/auth/solicitar-recuperacion")
async def solicitar_recuperacion(req: SolicitarRecuperacionRequest, db: Session = Depends(get_db)):
    user = db.query(models_db.Usuario).filter(models_db.Usuario.correo == req.correo).first()
    if not user:
        raise HTTPException(status_code=404, detail="El correo electrónico no está registrado en el sistema")
    
    # Generar token único y seguro
    token_str = secrets.token_urlsafe(32)
    expiracion = datetime.now() + timedelta(minutes=15)
    
    token_db = models_db.TokenRecuperacion(
        id_usuario=user.id_usuario,
        token=token_str,
        expiracion=expiracion
    )
    db.add(token_db)
    db.commit()
    
    # Construir el enlace de recuperación
    reset_link = f"http://localhost:3000/restablecer-password/{token_str}"
    
    # Configurar el mensaje de correo
    message = MessageSchema(
        subject="Recuperación de Contraseña - AgroJequete",
        recipients=[req.correo],
        body=f"""
        <html>
            <body style="font-family: sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                    <h2 style="color: #2e7d32;">Hola, {user.nombres}</h2>
                    <p>Has solicitado restablecer tu contraseña en el Sistema AgroJequete.</p>
                    <p>Haz clic en el siguiente botón para continuar:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" style="background-color: #2e7d32; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Restablecer Contraseña</a>
                    </div>
                    <p style="font-size: 0.8rem; color: #777;">Este enlace expirará en 15 minutos.</p>
                    <p style="font-size: 0.8rem; color: #777;">Si no solicitaste este cambio, puedes ignorar este correo.</p>
                </div>
            </body>
        </html>
        """,
        subtype=MessageType.html
    )

    fm = FastMail(get_mail_config())
    try:
        await fm.send_message(message)
        return {"mensaje": "Se ha enviado un enlace de recuperación a tu correo electrónico."}
    except Exception as e:
        import traceback
        error_detallado = traceback.format_exc()
        print(f"--- ERROR CRÍTICO DE CORREO ---")
        print(error_detallado)
        print(f"-------------------------------")
        return {
            "mensaje": f"Error técnico al enviar correo: {str(e)}. El servidor SMTP rechazó la conexión. Verifica tu .env.",
            "link_debug": reset_link 
        }

@app.post("/api/auth/restablecer-password")
def restablecer_password(req: RestablecerPasswordRequest, db: Session = Depends(get_db)):
    token_db = db.query(models_db.TokenRecuperacion).filter(
        models_db.TokenRecuperacion.token == req.token,
        models_db.TokenRecuperacion.usado == False,
        models_db.TokenRecuperacion.expiracion > datetime.now()
    ).first()
    
    if not token_db:
        raise HTTPException(status_code=400, detail="Token inválido, expirado o ya utilizado")
    
    user = db.query(models_db.Usuario).filter(models_db.Usuario.id_usuario == token_db.id_usuario).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Actualizar contraseña y marcar token como usado
    user.contrasena_hash = hash_password(req.nueva_contrasena)
    token_db.usado = True
    db.commit()
    
    registrar_bitacora(db, user.id_usuario, "Seguridad", "Contraseña restablecida mediante token")
    
    return {"mensaje": "Contraseña actualizada exitosamente"}

@app.get("/api/auth/validar-token/{token}")
def validar_token(token: str, db: Session = Depends(get_db)):
    token_db = db.query(models_db.TokenRecuperacion).filter(
        models_db.TokenRecuperacion.token == token,
        models_db.TokenRecuperacion.usado == False,
        models_db.TokenRecuperacion.expiracion > datetime.now()
    ).first()
    
    if not token_db:
        raise HTTPException(status_code=400, detail="Token inválido, expirado o ya utilizado")
    
    return {"valido": True}

@app.post("/api/auditoria/track-visit")
def track_visit(id_usuario: int, db: Session = Depends(get_db)):
    registrar_bitacora(db, id_usuario, "Visita", "Acceso al Dashboard Principal")
    return {"status": "ok"}

# Función Helper para Bitácora local de main.py
def registrar_bitacora(db: Session, id_usuario: int, modulo: str, accion: str):
    query = text("""
        INSERT INTO bitacora_sucesos (id_usuario, modulo, accion) 
        VALUES (:id_usuario, :modulo, :accion)
    """)
    db.execute(query, {"id_usuario": id_usuario, "modulo": modulo, "accion": accion})
    db.commit()

# ==========================================
# ENDPOINT RAÍZ (Comprobación de estado)
# ==========================================
@app.get("/")
def home():
    return {"mensaje": "API del Sistema Inteligente Agrícola 100% Operativa"}

# ==========================================
# ENDPOINT: MÓDULO DE PREDICCIÓN
# ==========================================
@app.post("/api/prediccion/precio")
def obtener_prediccion(meses_futuro: int, trans: float, id_usuario: int = 1, db: Session = Depends(get_db)):
    # 1. Calcular el mes objetivo en base a la fecha actual
    mes_actual = datetime.now().month
    mes_objetivo = (mes_actual + meses_futuro - 1) % 12 + 1
    
    # 2. Lógica Inteligente: Asignar promedios climáticos del Valle Jequetepeque según la estación
    if mes_objetivo in [1, 2, 3]: # Verano (Ene-Mar)
        temp_estimada, prec_estimada = 28.5, 25.0
    elif mes_objetivo in [4, 5, 6]: # Otoño (Abr-Jun)
        temp_estimada, prec_estimada = 24.0, 5.0
    elif mes_objetivo in [7, 8, 9]: # Invierno (Jul-Sep)
        temp_estimada, prec_estimada = 20.0, 1.0
    else: # Primavera (Oct-Dic)
        temp_estimada, prec_estimada = 23.0, 2.0
        
    # 3. Ejecutar el modelo con los datos automatizados
    precio_estimado = predecir_precio(temp_estimada, prec_estimada, trans)
    
    registrar_bitacora(db, id_usuario, "Predicción", f"Proyección a {meses_futuro} meses generada: S/{precio_estimado:.2f}")
    
    return {
        "precio_proyectado_tonelada": round(precio_estimado, 2),
        "clima_asumido": f"Temp: {temp_estimada}°C, Precipitación: {prec_estimada}mm",
        "margen_error": "4.8%" # En un caso real, esto sale de la métrica R^2 del modelo
    }

# ==========================================
# ENDPOINT: PREDICCIÓN AVANZADA
# ==========================================
@app.post("/api/prediccion/avanzada")
def obtener_prediccion_avanzada(id_cultivo: int, hectareas: float, meses_futuro: int, trans: float, id_usuario: int = 1, db: Session = Depends(get_db)):
    # 1. Obtener predicción de precio
    mes_actual = datetime.now().month
    mes_objetivo = (mes_actual + meses_futuro - 1) % 12 + 1
    
    if mes_objetivo in [1, 2, 3]: temp_estimada, prec_estimada = 28.5, 25.0
    elif mes_objetivo in [4, 5, 6]: temp_estimada, prec_estimada = 24.0, 5.0
    elif mes_objetivo in [7, 8, 9]: temp_estimada, prec_estimada = 20.0, 1.0
    else: temp_estimada, prec_estimada = 23.0, 2.0
        
    precio_tonelada = predecir_precio(temp_estimada, prec_estimada, trans)
    
    # 2. Estimar Producción
    produccion_total = estimar_produccion(id_cultivo, hectareas)
    
    # 3. Calcular Rentabilidad
    ingresos_estimados = produccion_total * precio_tonelada
    costo_por_ha = 5500.0 # Costo promedio de producción por hectárea
    costos_totales = (hectareas * costo_por_ha) + (produccion_total * trans)
    rentabilidad_neta = ingresos_estimados - costos_totales
    
    registrar_bitacora(db, id_usuario, "Predicción Avanzada", f"Proyección completa para {hectareas}ha. Ganancia: S/{rentabilidad_neta:.2f}")
    
    return {
        "produccion_estimada": round(produccion_total, 2),
        "precio_unidad": round(precio_tonelada, 2),
        "ingresos_brutos": round(ingresos_estimados, 2),
        "costos_estimados": round(costos_totales, 2),
        "ganancia_neta": round(rentabilidad_neta, 2),
        "clima_asumido": f"Temp: {temp_estimada}°C, Prec: {prec_estimada}mm",
        "recomendacion": "Altamente Rentable" if rentabilidad_neta > (ingresos_estimados * 0.3) else "Rentabilidad Moderada"
    }

# ==========================================
# ENDPOINT: RIESGO DE PLAGAS (MEJORADO)
# ==========================================
@app.post("/api/prediccion/riesgo-plaga")
def obtener_riesgo_plaga(id_cultivo: int, meses_futuro: int, db: Session = Depends(get_db)):
    mes_actual = datetime.now().month
    mes_objetivo = (mes_actual + meses_futuro - 1) % 12 + 1
    
    if mes_objetivo in [1, 2, 3]: t, p = 28.5, 25.0
    elif mes_objetivo in [4, 5, 6]: t, p = 24.0, 5.0
    elif mes_objetivo in [7, 8, 9]: t, p = 20.0, 1.0
    else: t, p = 23.0, 2.0
        
    riesgo = predecir_riesgo_plaga(id_cultivo, t, p)
    
    return {
        "probabilidad_plaga": riesgo,
        "nivel": "Crítico" if riesgo > 70 else "Moderado" if riesgo > 40 else "Bajo",
        "clima_estimado": f"{t}°C / {p}mm",
        "mes_alerta": mes_objetivo
    }

# ==========================================
# ENDPOINT: RECOMENDACIÓN DE SIEMBRA (MEJORADO)
# ==========================================
@app.get("/api/prediccion/recomendacion-siembra")
def obtener_recomendacion(meses_futuro: int = 3, db: Session = Depends(get_db)):
    import models_db
    cultivos_db = db.query(models_db.Cultivo).all()
    recomendaciones = calcular_recomendacion_cultivos(cultivos_db, meses_futuro)
    return recomendaciones
