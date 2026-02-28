from sqlalchemy import Column, BigInteger, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, INET
from sqlalchemy.sql import func
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    remito_id = Column(
        Integer,
        ForeignKey("remitos.id", ondelete="SET NULL"),
        nullable=True,
    )
    accion = Column(String(100), nullable=False)
    detalle = Column(JSONB, nullable=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    user_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
