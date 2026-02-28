import enum
from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Float, ForeignKey, Boolean, ARRAY
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.database import Base


class RutaEstado(str, enum.Enum):
    generando = "generando"
    generada = "generada"
    en_curso = "en_curso"
    completada = "completada"
    cancelada = "cancelada"


class ParadaEstado(str, enum.Enum):
    pendiente = "pendiente"
    en_camino = "en_camino"
    entregada = "entregada"
    fallida = "fallida"
    saltada = "saltada"


class Ruta(Base):
    __tablename__ = "rutas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha = Column(Date, nullable=False)
    estado = Column(String(20), nullable=False, default=RutaEstado.generando.value)
    config = Column(JSONB, nullable=False)
    deposito_geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    total_paradas = Column(Integer, default=0)
    total_excluidos = Column(Integer, default=0)
    duracion_estimada_min = Column(Integer, nullable=True)
    distancia_total_km = Column(Float, nullable=True)
    gmaps_links = Column(ARRAY(Text), nullable=True)
    ruta_geom = Column(Geometry(geometry_type="LINESTRING", srid=4326), nullable=True)
    api_cost_estimate = Column(Float, default=0.0)
    billing_detail = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class RutaParada(Base):
    __tablename__ = "ruta_paradas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ruta_id = Column(
        Integer,
        ForeignKey("rutas.id", ondelete="CASCADE"),
        nullable=False,
    )
    remito_id = Column(Integer, ForeignKey("remitos.id"), nullable=False)
    orden = Column(Integer, nullable=False)
    minutos_desde_anterior = Column(Float, nullable=True)
    tiempo_espera_min = Column(Float, nullable=True)
    minutos_acumulados = Column(Float, nullable=True)
    distancia_desde_anterior_km = Column(Float, nullable=True)
    # Snapshot inmutable al momento de generar
    cliente_snapshot = Column(String(255), nullable=True)
    direccion_snapshot = Column(Text, nullable=True)
    geom_snapshot = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    observaciones_snapshot = Column(Text, nullable=True)
    estado = Column(String(20), nullable=False, default=ParadaEstado.pendiente.value)
    es_urgente = Column(Boolean, default=False)
    es_prioridad = Column(Boolean, default=False)
    ventana_tipo = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class RutaExcluido(Base):
    __tablename__ = "ruta_excluidos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ruta_id = Column(
        Integer,
        ForeignKey("rutas.id", ondelete="CASCADE"),
        nullable=False,
    )
    remito_id = Column(Integer, ForeignKey("remitos.id"), nullable=False)
    motivo = Column(Text, nullable=False)
    distancia_km = Column(Float, nullable=True)
    observaciones = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
