from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RouteConfig(BaseModel):
    tiempo_espera_min: int = 10
    deposito_lat: float = -32.91973
    deposito_lng: float = -68.81829
    deposito_direccion: str = "Elpidio González 2753, Guaymallén, Mendoza"
    hora_desde: str = "09:00"
    hora_hasta: str = "14:00"
    evitar_saltos_min: int = 25
    vuelta_galpon_min: int = 25
    proveedor_matrix: str = "ors"
    utilizar_ventana: bool = True
    distancia_max_km: float = 45.0


class RutaParadaResponse(BaseModel):
    id: int
    orden: int
    remito_id: int
    remito_numero: Optional[str] = None
    cliente: Optional[str] = None
    direccion: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    minutos_desde_anterior: Optional[float] = None
    tiempo_espera_min: Optional[float] = None
    minutos_acumulados: Optional[float] = None
    distancia_desde_anterior_km: Optional[float] = None
    observaciones: Optional[str] = None
    es_urgente: bool = False
    es_prioridad: bool = False
    ventana_tipo: Optional[str] = None
    estado: str = "pendiente"

    model_config = {"from_attributes": True}


class RutaExcluidoResponse(BaseModel):
    id: int
    remito_id: int
    remito_numero: Optional[str] = None
    cliente: Optional[str] = None
    direccion: Optional[str] = None
    motivo: str
    distancia_km: Optional[float] = None
    observaciones: Optional[str] = None

    model_config = {"from_attributes": True}


class RutaResponse(BaseModel):
    id: int
    fecha: str
    estado: str
    total_paradas: int
    total_excluidos: int
    duracion_estimada_min: Optional[int] = None
    distancia_total_km: Optional[float] = None
    gmaps_links: list[str] = []
    paradas: list[RutaParadaResponse] = []
    excluidos: list[RutaExcluidoResponse] = []
    config: dict = {}
    api_cost_estimate: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ParadaEstadoUpdate(BaseModel):
    estado: str


class RutaEstadoUpdate(BaseModel):
    estado: str
