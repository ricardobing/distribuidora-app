from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base


class PedidoListo(Base):
    __tablename__ = "pedidos_listos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    remito_id = Column(Integer, ForeignKey("remitos.id", ondelete="SET NULL"), nullable=True)
    numero_remito = Column(String(50), nullable=False, unique=True)
    cliente = Column(String(255), nullable=True)
    domicilio = Column(Text, nullable=True)
    localidad = Column(String(100), nullable=True)
    provincia = Column(String(100), nullable=True)
    observaciones = Column(Text, nullable=True)
    transporte = Column(String(255), nullable=True)
    fecha_remito = Column(Date, nullable=True)
    source_row = Column(Integer, nullable=True)
    synced_at = Column(DateTime(timezone=True), server_default=func.now())
    raw_data = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
