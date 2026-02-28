"""
Billing service: registra costos de llamadas a APIs externas.
"""
import logging
import time
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.billing import BillingTrace

logger = logging.getLogger(__name__)

# Costo estimado por unidad (USD)
COST_PER_UNIT = {
    "google_geocode": 0.005,
    "google_distance_matrix": 0.005,
    "ors_geocode": 0.0,
    "ors_distance_matrix": 0.0,
    "mapbox_geocode": 0.00075,
    "mapbox_distance_matrix": 0.00075,
    "openai_classify": 0.00015 / 1000,  # per token approx
    "openai_normalize": 0.00015 / 1000,
}


async def record(
    db: AsyncSession,
    run_id: str,
    stage: str,
    service: str,
    sku: str,
    units: int = 1,
    response_code: int = 200,
    latency_ms: int = 0,
    metadata: dict = None,
) -> None:
    """Registra una traza de billing."""
    estimated_cost = COST_PER_UNIT.get(f"{service}_{sku}", 0.0) * units
    entry = BillingTrace(
        run_id=run_id,
        stage=stage,
        service=service,
        sku=sku,
        units=units,
        response_code=response_code,
        latency_ms=latency_ms,
        estimated_cost=estimated_cost,
        metadata_=metadata or {},
    )
    db.add(entry)
    try:
        await db.commit()
    except Exception as e:
        logger.warning(f"Error guardando billing trace: {e}")
        await db.rollback()
