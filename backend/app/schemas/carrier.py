from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CarrierCreate(BaseModel):
    nombre_canonico: str
    aliases: list[str] = []
    regex_pattern: Optional[str] = None
    es_externo: bool = True
    es_pickup: bool = False
    prioridad_regex: int = 50


class CarrierUpdate(BaseModel):
    nombre_canonico: Optional[str] = None
    aliases: Optional[list[str]] = None
    regex_pattern: Optional[str] = None
    es_externo: Optional[bool] = None
    es_pickup: Optional[bool] = None
    activo: Optional[bool] = None
    prioridad_regex: Optional[int] = None


class CarrierResponse(BaseModel):
    id: int
    nombre_canonico: str
    aliases: list = []
    regex_pattern: Optional[str] = None
    es_externo: bool
    es_pickup: bool
    activo: bool
    prioridad_regex: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CarrierDetectRequest(BaseModel):
    texto: str


class CarrierDetectResponse(BaseModel):
    carrier: str
    confidence: float
    source: str
