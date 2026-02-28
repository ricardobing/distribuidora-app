from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.database import Base


class HistoricoEntregado(Base):
    __tablename__ = "historico_entregados"

    id = Column(Integer, primary_key=True, autoincrement=True)
    remito_id = Column(Integer, ForeignKey("remitos.id"), nullable=False)
    numero_remito = Column(String(50), nullable=False)
    cliente = Column(String(255), nullable=True)
    domicilio = Column(Text, nullable=True)
    provincia = Column(String(100), nullable=True)
    observaciones = Column(Text, nullable=True)
    carrier_nombre = Column(String(100), nullable=True)
    estado_al_archivar = Column(String(50), nullable=True)
    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    urgente = Column(Boolean, default=False)
    prioridad = Column(Boolean, default=False)
    obs_entrega = Column(Text, nullable=True)
    transp_json = Column(JSONB, nullable=True)
    fecha_ingreso = Column(DateTime(timezone=True), nullable=True)
    fecha_armado = Column(DateTime(timezone=True), nullable=True)
    fecha_entregado = Column(DateTime(timezone=True), nullable=False)
    fecha_archivado = Column(DateTime(timezone=True), server_default=func.now())
    mes_cierre = Column(String(7), nullable=True)  # '2026-02'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
