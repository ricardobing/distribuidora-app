import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class UserRol(str, enum.Enum):
    admin = "admin"
    operador = "operador"
    chofer = "chofer"
    viewer = "viewer"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    nombre = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False, default=UserRol.operador.value)
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
