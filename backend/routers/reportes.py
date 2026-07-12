from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from sqlalchemy import text
from fastapi.responses import StreamingResponse
import io
import csv
import pandas as pd

router = APIRouter(prefix="/api/reportes", tags=["Reportes"])

@router.get("/cosechas/csv")
def exportar_cosechas_csv(db: Session = Depends(get_db)):
    query = text("SELECT c.fecha_cosecha, c.rendimiento_toneladas, c.calidad FROM cosechas c")
    resultados = db.execute(query).fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerow(["Fecha Cosecha", "Rendimiento (Ton)", "Calidad"])
    
    for row in resultados:
        writer.writerow([row.fecha_cosecha, row.rendimiento_toneladas, row.calidad])
        
    output.seek(0)
    
    # Registro en bitácora
    db.execute(text("INSERT INTO bitacora_sucesos (id_usuario, modulo, accion) VALUES (1, 'Reportes', 'Exportación CSV generada')"))
    db.commit()
    
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=reporte_cosechas.csv"}
    )

@router.get("/cosechas/excel")
def exportar_cosechas_excel(db: Session = Depends(get_db)):
    query = text("SELECT c.fecha_cosecha, c.rendimiento_toneladas, c.calidad FROM cosechas c")
    resultados = db.execute(query).fetchall()
    
    # Convertir a DataFrame de Pandas
    df = pd.DataFrame(resultados, columns=["Fecha Cosecha", "Rendimiento (Ton)", "Calidad"])
    
    # Formatear la fecha a string para evitar serialización incorrecta en Excel
    df["Fecha Cosecha"] = df["Fecha Cosecha"].astype(str)
    
    # Escribir en memoria usando un buffer de bytes
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Cosechas")
    
    output.seek(0)
    
    # Registro en bitácora
    db.execute(text("INSERT INTO bitacora_sucesos (id_usuario, modulo, accion) VALUES (1, 'Reportes', 'Exportación Excel generada')"))
    db.commit()
    
    return StreamingResponse(
        output, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={"Content-Disposition": "attachment; filename=reporte_cosechas.xlsx"}
    )

@router.get("/rendimiento-mensual")
def obtener_rendimiento_mensual(db: Session = Depends(get_db)):
    query = text("""
        SELECT 
            TO_CHAR(c.fecha_cosecha, 'YYYY-MM') AS mes,
            cu.nombre_cultivo,
            SUM(c.rendimiento_toneladas) AS total_toneladas
        FROM cosechas c
        JOIN siembras s ON c.id_siembra = s.id_siembra
        JOIN cultivos cu ON s.id_cultivo = cu.id_cultivo
        GROUP BY TO_CHAR(c.fecha_cosecha, 'YYYY-MM'), cu.nombre_cultivo
        ORDER BY mes
    """)
    resultados = db.execute(query).fetchall()
    
    # Formatear datos para la librería Recharts de React
    datos_formateados = {}
    for fila in resultados:
        mes = fila.mes
        cultivo = fila.nombre_cultivo
        total = float(fila.total_toneladas)
        
        if mes not in datos_formateados:
            datos_formateados[mes] = {"mes": mes}
        datos_formateados[mes][cultivo] = round(total, 2)
        
    return list(datos_formateados.values())

@router.get("/calidad-cosechas")
def obtener_calidad_cosechas(db: Session = Depends(get_db)):
    query = text("""
        SELECT calidad, SUM(rendimiento_toneladas) as total_toneladas
        FROM cosechas
        GROUP BY calidad
    """)
    resultados = db.execute(query).fetchall()
    
    # Formatear para el PieChart de React
    return [{"name": r.calidad, "value": float(r.total_toneladas)} for r in resultados]

@router.get("/cosechas/json")
def exportar_cosechas_json(db: Session = Depends(get_db)):
    query = text("SELECT c.fecha_cosecha, c.rendimiento_toneladas, c.calidad FROM cosechas c ORDER BY c.fecha_cosecha DESC LIMIT 200")
    resultados = db.execute(query).fetchall()
    
    # Registrar auditoría
    db.execute(text("INSERT INTO bitacora_sucesos (id_usuario, modulo, accion) VALUES (1, 'Reportes', 'Generación de reporte PDF')"))
    db.commit()
    
    return [{"fecha": str(r.fecha_cosecha), "rendimiento": float(r.rendimiento_toneladas), "calidad": r.calidad} for r in resultados]