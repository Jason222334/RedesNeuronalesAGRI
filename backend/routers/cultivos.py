from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models_db
import schemas
from database import get_db
from sqlalchemy import text

router = APIRouter(
    prefix="/api/cultivos",
    tags=["Gestión de Cultivos"]
)

@router.post("/", response_model=schemas.CultivoRespuesta)
def crear_cultivo(cultivo: schemas.CultivoCrear, db: Session = Depends(get_db)):
    nuevo_cultivo = models_db.Cultivo(**cultivo.model_dump())
    db.add(nuevo_cultivo)
    db.commit()
    db.refresh(nuevo_cultivo)
    
    # Registro en bitácora
    query = text("INSERT INTO bitacora_sucesos (id_usuario, modulo, accion) VALUES (1, 'Cultivos', 'Creación de nuevo cultivo')")
    db.execute(query)
    db.commit()
    
    return nuevo_cultivo

@router.get("/", response_model=List[schemas.CultivoRespuesta])
def obtener_cultivos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cultivos = db.query(models_db.Cultivo).offset(skip).limit(limit).all()
    return cultivos

@router.delete("/{id_cultivo}")
def eliminar_cultivo(id_cultivo: int, db: Session = Depends(get_db)):
    # Buscar si el cultivo existe
    cultivo = db.query(models_db.Cultivo).filter(models_db.Cultivo.id_cultivo == id_cultivo).first()
    
    if not cultivo:
        raise HTTPException(status_code=404, detail="Cultivo no encontrado")
        
    try:
        db.delete(cultivo)
        db.commit()
        
        # Registrar en la bitácora
        query = text("INSERT INTO bitacora_sucesos (id_usuario, modulo, accion) VALUES (1, 'Cultivos', 'Cultivo eliminado: ID ' || :id)")
        db.execute(query, {"id": id_cultivo})
        db.commit()
        
        return {"mensaje": "Cultivo eliminado exitosamente"}
    except Exception as e:
        db.rollback()
        # Si da error, probablemente es porque hay datos (siembras/precios) que dependen de este cultivo
        raise HTTPException(status_code=400, detail="No se puede eliminar el cultivo porque tiene datos históricos asociados.")
    
@router.put("/{id_cultivo}", response_model=schemas.CultivoRespuesta)
def actualizar_cultivo(id_cultivo: int, cultivo_actualizado: schemas.CultivoCrear, db: Session = Depends(get_db)):
    cultivo = db.query(models_db.Cultivo).filter(models_db.Cultivo.id_cultivo == id_cultivo).first()
    
    if not cultivo:
        raise HTTPException(status_code=404, detail="Cultivo no encontrado")
        
    # Actualizar los campos
    cultivo.nombre_cultivo = cultivo_actualizado.nombre_cultivo
    cultivo.tiempo_estimado_cosecha_dias = cultivo_actualizado.tiempo_estimado_cosecha_dias
    db.commit()
    db.refresh(cultivo)
    
    # Registrar en bitácora
    query = text("INSERT INTO bitacora_sucesos (id_usuario, modulo, accion) VALUES (1, 'Cultivos', 'Cultivo actualizado: ID ' || :id)")
    db.execute(query, {"id": id_cultivo})
    db.commit()
    
    return cultivo    