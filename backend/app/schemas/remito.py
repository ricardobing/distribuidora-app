from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RemitoCreate(BaseModel):
    remitos: list[str]
    source: str = "manual"


class RemitoSingleCreate(BaseModel):
    numero: str
    domicilio: Optional[str] = None
    observaciones: Optional[str] = None
    cliente: Optional[str] = None
    provincia: Optional[str] = None
    source: str = "manual"


class RemitoUpdate(BaseModel):
    domicilio_normalizado: Optional[str] = None
    urgente: Optional[bool] = None
    prioridad: Optional[bool] = None
    observaciones_entrega: Optional[str] = None


class DireccionCorreccion(BaseModel):
    direccion_nueva: str


class ClasificacionUpdate(BaseModel):
    estado: str
    motivo: Optional[str] = None


class RemitoResponse(BaseModel):
    id: int
    numero: str
    cliente: Optional[str] = None
    domicilio_raw: Optional[str] = None
    domicilio_normalizado: Optional[str] = None
    localidad: Optional[str] = None
    provincia: Optional[str] = None
    observaciones_pl: Optional[str] = None
    observaciones_entrega: Optional[str] = None
    transporte_raw: Optional[str] = None
    estado_clasificacion: str
    motivo_clasificacion: Optional[str] = None
    estado_lifecycle: str
    carrier_id: Optional[int] = None
    carrier_nombre: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    geocode_formatted: Optional[str] = None
    geocode_source: Optional[str] = None
    geocode_confidence: Optional[float] = None
    ventana_tipo: Optional[str] = None
    ventana_desde_min: Optional[int] = None
    ventana_hasta_min: Optional[int] = None
    urgente: bool = False
    prioridad: bool = False
    llamar_antes: bool = False
    source: str = "manual"
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
