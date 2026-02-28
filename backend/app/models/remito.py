import enum
from sqlalchemy import (
    Column, Integer, String, Boolean, Text, DateTime, Float, ForeignKey
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.database import Base


class RemitoEstadoClasificacion(str, enum.Enum):
    pendiente = "pendiente"
    enviar = "enviar"
    corregir = "corregir"
    retiro_sospechado = "retiro_sospechado"
    transporte_externo = "transporte_externo"
    no_encontrado = "no_encontrado"
    excluido = "excluido"


class RemitoEstadoLifecycle(str, enum.Enum):
    ingresado = "ingresado"
    armado = "armado"
    despachado = "despachado"
    entregado = "entregado"
    historico = "historico"


class Remito(Base):
    __tablename__ = "remitos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(String(50), nullable=False, unique=True)

    # Datos del remito
    cliente = Column(String(255), nullable=True)
    domicilio_raw = Column(Text, nullable=True)
    domicilio_normalizado = Column(Text, nullable=True)
    localidad = Column(String(100), nullable=True)
    provincia = Column(String(100), nullable=True)
    observaciones_pl = Column(Text, nullable=True)
    observaciones_entrega = Column(Text, nullable=True)
    transporte_raw = Column(String(255), nullable=True)

    # Clasificación
    carrier_id = Column(Integer, ForeignKey("carriers.id"), nullable=True)
    estado_clasificacion = Column(
        String(30),
        nullable=False,
        default=RemitoEstadoClasificacion.pendiente.value,
    )
    motivo_clasificacion = Column(Text, nullable=True)

    # Ciclo de vida
    estado_lifecycle = Column(
        String(20),
        nullable=False,
        default=RemitoEstadoLifecycle.ingresado.value,
    )

    # Geocodificación — PostGIS POINT(lng lat) SRID 4326
    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    geocode_formatted = Column(Text, nullable=True)
    geocode_has_street_num = Column(Boolean, default=False)
    geocode_source = Column(String(20), nullable=True)  # 'cache','ors','mapbox','google'
    geocode_confidence = Column(Float, nullable=True)

    # Ventana horaria
    ventana_tipo = Column(String(20), nullable=True)  # 'AM', 'PM', 'SIN_HORARIO'
    ventana_desde_min = Column(Integer, nullable=True)  # minutos desde medianoche
    ventana_hasta_min = Column(Integer, nullable=True)
    ventana_raw = Column(Text, nullable=True)
    llamar_antes = Column(Boolean, default=False)

    # Flags de prioridad
    urgente = Column(Boolean, nullable=False, default=False)
    prioridad = Column(Boolean, nullable=False, default=False)

    # Metadata
    seq_id = Column(String(50), nullable=True)
    source = Column(String(20), nullable=False, default="manual")
    motivo_exclusion_ruta = Column(Text, nullable=True)
    transp_json = Column(JSONB, nullable=True)

    # Timestamps
    fecha_ingreso = Column(DateTime(timezone=True), server_default=func.now())
    fecha_armado = Column(DateTime(timezone=True), nullable=True)
    fecha_entregado = Column(DateTime(timezone=True), nullable=True)
    fecha_historico = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
