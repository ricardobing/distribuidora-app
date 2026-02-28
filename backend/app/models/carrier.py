from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base


class Carrier(Base):
    __tablename__ = "carriers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre_canonico = Column(String(100), nullable=False, unique=True)
    aliases = Column(JSONB, nullable=False, default=list)
    regex_pattern = Column(String(500), nullable=True)
    es_externo = Column(Boolean, nullable=False, default=True)
    es_pickup = Column(Boolean, nullable=False, default=False)
    activo = Column(Boolean, nullable=False, default=True)
    prioridad_regex = Column(Integer, nullable=False, default=50)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
