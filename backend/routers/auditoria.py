from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from sqlalchemy import text, func
import models_db as models
from typing import List
from datetime import date

router = APIRouter(prefix="/api/auditoria", tags=["Auditoría"])

@router.get("/")
def obtener_bitacora(limit: int = 100, db: Session = Depends(get_db)):
    # Unimos con usuarios para tener los nombres
    query = text("""
        SELECT b.id_suceso, b.modulo, b.accion, b.fecha_hora, u.nombres 
        FROM bitacora_sucesos b
        LEFT JOIN usuarios u ON b.id_usuario = u.id_usuario
        ORDER BY b.fecha_hora DESC 
        LIMIT :limit
    """)
    resultados = db.execute(query, {"limit": limit}).fetchall()
    
    return [
        {
            "id": r.id_suceso, 
            "modulo": r.modulo, 
            "accion": r.accion, 
            "fecha": r.fecha_hora,
            "usuario": r.nombres if r.nombres else "Sistema"
        } for r in resultados
    ]

@router.get("/visitas/diarias")
def obtener_visitas_diarias(fecha: date = None, db: Session = Depends(get_db)):
    if not fecha:
        fecha = date.today()
    
    query = text("""
        SELECT COUNT(*) as total 
        FROM bitacora_sucesos 
        WHERE modulo = 'Visita' AND CAST(fecha_hora AS DATE) = :fecha
    """)
    resultado = db.execute(query, {"fecha": fecha}).fetchone()
    return {"fecha": fecha, "total_visitas": resultado.total if resultado else 0}

@router.get("/visitas/stats")
def obtener_stats_visitas(db: Session = Depends(get_db)):
    # Obtener visitas de los últimos 7 días para un gráfico
    query = text("""
        SELECT CAST(fecha_hora AS DATE) as fecha, COUNT(*) as total
        FROM bitacora_sucesos
        WHERE modulo = 'Visita'
        GROUP BY CAST(fecha_hora AS DATE)
        ORDER BY fecha DESC
        LIMIT 7
    """)
    resultados = db.execute(query).fetchall()
    return [{"fecha": str(r.fecha), "visitas": r.total} for r in resultados]
