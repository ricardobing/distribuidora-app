from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class HistoricoEntregado(Base):
    __tablename__ = "historico_entregados"

    id = Column(Integer, primary_key=True, autoincrement=True)
    remito_id = Column(Integer, ForeignKey("remitos.id", ondelete="SET NULL"), nullable=True)
    numero = Column(String(100), nullable=False)
    cliente = Column(String(500), nullable=True)
    direccion_snapshot = Column(Text, nullable=True)
    localidad = Column(String(200), nullable=True)
    observaciones = Column(Text, nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    carrier_nombre = Column(String(200), nullable=True)
    es_urgente = Column(Boolean, default=False)
    es_prioridad = Column(Boolean, default=False)
    obs_entrega = Column(Text, nullable=True)
    estado_al_archivar = Column(String(50), nullable=True)
    fecha_ingreso = Column(DateTime(timezone=True), nullable=True)
    fecha_armado = Column(DateTime(timezone=True), nullable=True)
    fecha_entregado = Column(DateTime(timezone=True), nullable=False)
    fecha_archivado = Column(DateTime(timezone=True), server_default=func.now())
    mes_cierre = Column(String(7), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
