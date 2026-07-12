from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
import models_db
import pandas as pd
import json
import io
import os
from datetime import datetime

router = APIRouter(prefix="/api/archivos", tags=["Archivos"])

UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Validar extensión
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["csv", "xlsx", "xls", "pdf"]:
        raise HTTPException(status_code=400, detail="Formato de archivo no soportado. Use CSV, Excel o PDF.")

    contents = await file.read()
    
    # Procesar archivo para previsualización (JSON)
    preview_json = None
    if ext != "pdf":
        try:
            if ext == "csv":
                df = pd.read_csv(io.BytesIO(contents))
            else:
                df = pd.read_excel(io.BytesIO(contents))
            
            # Tomar los primeros 10 registros para la previsualización de forma segura
            preview_json = df.head(10).to_json(orient="records", date_format="iso")
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error al procesar el archivo: {str(e)}")
    else:
        # Para PDFs, guardamos un json de previsualización básico
        preview_json = json.dumps({"tipo": "PDF", "mensaje": "Este es un documento PDF."})

    # Guardar archivo físicamente
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(UPLOAD_DIR, f"{timestamp}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(contents)

    # Guardar en BD
    nuevo_doc = models_db.Documento(
        nombre_archivo=file.filename,
        tipo_archivo=ext,
        contenido_json=preview_json,
        ruta_archivo=file_path
    )
    db.add(nuevo_doc)
    db.commit()
    db.refresh(nuevo_doc)

    return {"id": nuevo_doc.id_documento, "mensaje": "Archivo subido exitosamente"}

@router.get("/")
def listar_archivos(db: Session = Depends(get_db)):
    return db.query(models_db.Documento).order_by(models_db.Documento.fecha_subida.desc()).all()

@router.get("/{id_documento}")
def obtener_archivo(id_documento: int, db: Session = Depends(get_db)):
    doc = db.query(models_db.Documento).filter(models_db.Documento.id_documento == id_documento).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    # Leer el archivo completo para mostrarlo si es necesario
    try:
        if not os.path.exists(doc.ruta_archivo):
            # Si el archivo físico no existe, usamos la previsualización guardada
            return {
                "nombre": doc.nombre_archivo,
                "data": json.loads(doc.contenido_json) if doc.contenido_json else [],
                "advertencia": "Archivo físico no encontrado, mostrando previsualización guardada."
            }

        if doc.tipo_archivo == "pdf":
            return {
                "nombre": doc.nombre_archivo,
                "tipo_archivo": "pdf",
                "id_documento": doc.id_documento,
                "data": []
            }

        if doc.tipo_archivo == "csv":
            df = pd.read_csv(doc.ruta_archivo)
        else:
            df = pd.read_excel(doc.ruta_archivo)
        
        # Limitar a 100 registros para evitar colapsar el frontend
        data_json = df.head(100).to_json(orient="records", date_format="iso")
        
        return {
            "nombre": doc.nombre_archivo,
            "data": json.loads(data_json)
        }
    except Exception as e:
        # Fallback a la previsualización si falla la lectura completa
        if doc.contenido_json:
            try:
                return {
                    "nombre": doc.nombre_archivo,
                    "data": json.loads(doc.contenido_json),
                    "error_lectura": str(e)
                }
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error al leer el archivo: {str(e)}")

@router.get("/{id_documento}/raw")
def obtener_archivo_crudo(id_documento: int, db: Session = Depends(get_db)):
    doc = db.query(models_db.Documento).filter(models_db.Documento.id_documento == id_documento).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    if not os.path.exists(doc.ruta_archivo):
        raise HTTPException(status_code=404, detail="Archivo físico no encontrado")
        
    media_type = "application/pdf" if doc.tipo_archivo == "pdf" else "application/octet-stream"
    return FileResponse(doc.ruta_archivo, media_type=media_type)
