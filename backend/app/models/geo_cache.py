from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.database import Base


class GeoCache(Base):
    __tablename__ = "geo_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key_normalizada = Column(String(500), nullable=False, unique=True)
    query_original = Column(Text, nullable=False)
    geom = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
    formatted_address = Column(Text, nullable=True)
    has_street_number = Column(Boolean, default=False)
    provider = Column(String(20), nullable=True)  # 'ors', 'mapbox', 'google'
    raw_response = Column(JSONB, nullable=True)
    score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
