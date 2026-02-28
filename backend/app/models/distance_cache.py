from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.database import Base


class DistanceMatrixCache(Base):
    __tablename__ = "distance_matrix_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    origin_geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    dest_geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    duration_sec = Column(Integer, nullable=False)
    distance_m = Column(Integer, nullable=True)
    provider = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
