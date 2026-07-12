from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models_db as models
import schemas
from typing import List

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
router = APIRouter(prefix="/api/usuarios", tags=["Usuarios"])

@router.get("/", response_model=List[schemas.UsuarioRespuesta])
def obtener_usuarios(db: Session = Depends(get_db)):
    return db.query(models.Usuario).all()

@router.post("/", response_model=schemas.UsuarioRespuesta)
def crear_usuario(usuario: schemas.UsuarioCrear, db: Session = Depends(get_db)):
    db_usuario = models.Usuario(
        nombres=usuario.nombres,
        apellidos=usuario.apellidos,
        correo=usuario.correo,
        contrasena_hash=pwd_context.hash(usuario.contrasena),
        rol=usuario.rol,
        estado=usuario.estado
    )
    db.add(db_usuario)
    try:
        db.commit()
        db.refresh(db_usuario)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    return db_usuario

@router.put("/{id_usuario}", response_model=schemas.UsuarioRespuesta)
def actualizar_usuario(id_usuario: int, usuario: schemas.UsuarioUpdate, db: Session = Depends(get_db)):
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    update_data = usuario.model_dump(exclude_unset=True)
    if "contrasena" in update_data and update_data["contrasena"]:
        db_usuario.contrasena_hash = pwd_context.hash(update_data.pop("contrasena"))
    elif "contrasena" in update_data:
        update_data.pop("contrasena") # No actualizar si viene vacío
    
    for key, value in update_data.items():
        setattr(db_usuario, key, value)
    
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

@router.delete("/{id_usuario}")
def eliminar_usuario(id_usuario: int, db: Session = Depends(get_db)):
    db_usuario = db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Eliminar registros relacionados para evitar errores de clave foránea
    from sqlalchemy import text
    db.execute(text("DELETE FROM bitacora_sucesos WHERE id_usuario = :id"), {"id": id_usuario})
    db.execute(text("DELETE FROM tokens_recuperacion WHERE id_usuario = :id"), {"id": id_usuario})
    
    db.delete(db_usuario)
    db.commit()
    return {"mensaje": "Usuario eliminado correctamente"}
