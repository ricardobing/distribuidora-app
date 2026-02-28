from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class ConfigRuta(Base):
    __tablename__ = "config_ruta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(Text, nullable=False)
    tipo = Column(String(20), nullable=False, default="text")
    descripcion = Column(Text, nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
