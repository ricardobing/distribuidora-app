from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RemitoCreate(BaseModel):
    remitos: list[str]
    source: str = "manual"


class RemitoSingleCreate(BaseModel):
    numero: str
    domicilio: Optional[str] = None   # → direccion_raw en el modelo
    observaciones: Optional[str] = None
    cliente: Optional[str] = None
    telefono: Optional[str] = None
    localidad: Optional[str] = None
    es_urgente: bool = False
    es_prioridad: bool = False
    llamar_antes: bool = False
    source: str = "manual"


class RemitoUpdate(BaseModel):
    direccion_raw: Optional[str] = None
    es_urgente: Optional[bool] = None
    es_prioridad: Optional[bool] = None
    observaciones: Optional[str] = None
    llamar_antes: Optional[bool] = None


class DireccionCorreccion(BaseModel):
    direccion_nueva: str


class ClasificacionUpdate(BaseModel):
    estado: str
    motivo: Optional[str] = None


class RemitoResponse(BaseModel):
    id: int
    numero: str
    cliente: Optional[str] = None
    telefono: Optional[str] = None
    direccion_raw: Optional[str] = None
    direccion_normalizada: Optional[str] = None
    localidad: Optional[str] = None
    observaciones: Optional[str] = None
    estado_clasificacion: str
    motivo_clasificacion: Optional[str] = None
    estado_lifecycle: str
    carrier_id: Optional[int] = None
    carrier_nombre: Optional[str] = None  # Resuelto en router via JOIN
    lat: Optional[float] = None
    lng: Optional[float] = None
    geocode_formatted: Optional[str] = None
    geocode_provider: Optional[str] = None
    geocode_score: Optional[float] = None
    ventana_tipo: Optional[str] = None
    ventana_desde_min: Optional[int] = None
    ventana_hasta_min: Optional[int] = None
    es_urgente: bool = False
    es_prioridad: bool = False
    llamar_antes: bool = False
    source: Optional[str] = "manual"
    fecha_ingreso: Optional[datetime] = None
    fecha_armado: Optional[datetime] = None
    fecha_entregado: Optional[datetime] = None

    model_config = {"from_attributes": True}


class IngestResponse(BaseModel):
    ok: bool
    total: int
    nuevos: int
    duplicados: int
    errores: list[str] = []
    version: str = "1.0.0"
