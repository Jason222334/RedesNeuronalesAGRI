from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

# Esquemas para Cultivos
class CultivoBase(BaseModel):
    nombre_cultivo: str
    variedad: Optional[str] = None
    tiempo_estimado_cosecha_dias: int

class CultivoCrear(CultivoBase):
    pass

class CultivoRespuesta(CultivoBase):
    id_cultivo: int

    class Config:
        from_attributes = True

# Esquemas para Usuarios
class UsuarioBase(BaseModel):
    nombres: str
    apellidos: str
    correo: str
    rol: Optional[str] = "Usuario"
    estado: Optional[bool] = True

class UsuarioCrear(UsuarioBase):
    contrasena: str

class UsuarioUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    correo: Optional[str] = None
    rol: Optional[str] = None
    estado: Optional[bool] = None
    contrasena: Optional[str] = None

class UsuarioRespuesta(UsuarioBase):
    id_usuario: int

    class Config:
        from_attributes = True

# Esquemas para Auditoría
class BitacoraRespuesta(BaseModel):
    id_suceso: int
    modulo: str
    accion: str
    fecha_hora: datetime
    id_usuario: Optional[int]
    nombres_usuario: Optional[str] = None

    class Config:
        from_attributes = True

# Esquemas para Predicción
class PrediccionRequest(BaseModel):
    temperatura_promedio: float
    precipitacion_mm: float
    costo_transporte: float