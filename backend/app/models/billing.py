from sqlalchemy import Column, BigInteger, Integer, String, DateTime, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base


class BillingTrace(Base):
    __tablename__ = "billing_trace"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    run_id = Column(String(100), nullable=True)
    stage = Column(String(50), nullable=True)
    service = Column(String(30), nullable=False)
    sku = Column(String(100), nullable=True)
    units = Column(Integer, nullable=False, default=1)
    response_code = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    url_length = Column(Integer, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
