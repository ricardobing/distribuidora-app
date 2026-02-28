from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from app.database import Base


class DistanceMatrixCache(Base):
    __tablename__ = "distance_matrix_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    origin_lat = Column(Float, nullable=False)
    origin_lng = Column(Float, nullable=False)
    dest_lat = Column(Float, nullable=False)
    dest_lng = Column(Float, nullable=False)
    duration_sec = Column(Float, nullable=False)
    distance_m = Column(Float, nullable=True)
    provider = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
