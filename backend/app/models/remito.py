import enum
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
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
    numero = Column(String(100), nullable=False, unique=True)
    cliente = Column(String(500), nullable=True)
    telefono = Column(String(50), nullable=True)
    direccion_raw = Column(Text, nullable=True)
    direccion_normalizada = Column(Text, nullable=True)
    localidad = Column(String(200), nullable=True)
    observaciones = Column(Text, nullable=True)

    # Geo — coordenadas planas (no GeoAlchemy2 para compatibilidad async)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    geocode_provider = Column(String(50), nullable=True)
    geocode_score = Column(Float, nullable=True)
    geocode_formatted = Column(Text, nullable=True)

    # Clasificación
    estado_clasificacion = Column(String(50), nullable=False,
                                  default=RemitoEstadoClasificacion.pendiente.value)
    estado_lifecycle = Column(String(50), nullable=False,
                              default=RemitoEstadoLifecycle.ingresado.value)
    motivo_clasificacion = Column(Text, nullable=True)
    carrier_id = Column(Integer, ForeignKey("carriers.id", ondelete="SET NULL"), nullable=True)

    # Ventana horaria (minutos desde medianoche)
    ventana_raw = Column(Text, nullable=True)
    ventana_tipo = Column(String(50), nullable=True)
    ventana_desde_min = Column(Integer, nullable=True)
    ventana_hasta_min = Column(Integer, nullable=True)
    llamar_antes = Column(Boolean, nullable=False, default=False)

    # Flags
    es_urgente = Column(Boolean, nullable=False, default=False)
    es_prioridad = Column(Boolean, nullable=False, default=False)

    # Meta
    pipeline_error = Column(Text, nullable=True)
    source = Column(String(100), nullable=True, default="manual")

    # Timestamps ciclo de vida
    fecha_ingreso = Column(DateTime(timezone=True), server_default=func.now())
    fecha_armado = Column(DateTime(timezone=True), nullable=True)
    fecha_entregado = Column(DateTime(timezone=True), nullable=True)
    fecha_historico = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
