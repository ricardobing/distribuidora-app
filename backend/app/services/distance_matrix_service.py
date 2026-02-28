"""
Distance Matrix Service.
Calcula matrices NxN de tiempos de viaje.
Cache en BD usando coordenadas Float (sin GeoAlchemy2).
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.distance_cache import DistanceMatrixCache
from app.core.constants import URBAN_SPEED_KMH
from app.core.haversine import haversine_minutes

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 48
CACHE_TOL = 0.0005  # ~55 metros de tolerancia


@dataclass
class MatrixPoint:
    lat: float
    lng: float
    label: str = ""


async def get_matrix_nxn(
    db: AsyncSession,
    points: list[MatrixPoint],
    provider: str = "ors",
) -> list[list[float]]:
    """
    Retorna una matriz NxN de tiempos de viaje en minutos.
    Intenta primero el cache, luego llama a la API externa si no está completo.
    """
    n = len(points)
    matrix: list[list[Optional[float]]] = [[None] * n for _ in range(n)]

    # Llenar diagonal con 0
    for i in range(n):
        matrix[i][i] = 0.0

    # Intentar cache
    now = datetime.now(timezone.utc)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            cached = await _lookup_cache(db, points[i], points[j], now)
            if cached is not None:
                matrix[i][j] = cached

    # Pares faltantes
    missing = [(i, j) for i in range(n) for j in range(n) if matrix[i][j] is None]
    if not missing:
        return _ensure_float(matrix)

    try:
        if provider == "ors":
            api_matrix = await _call_ors(points)
        else:
            api_matrix = await _call_osrm(points)

        for i, row in enumerate(api_matrix):
            for j, val in enumerate(row):
                if matrix[i][j] is None and val is not None:
                    matrix[i][j] = val
                    await _save_cache(db, points[i], points[j], val, now)
        await db.commit()
    except Exception as exc:
        logger.warning(f"DM API error ({provider}): {exc}. Usando Haversine fallback.")

    # Fallback Haversine para los que siguen siendo None
    for i in range(n):
        for j in range(n):
            if matrix[i][j] is None:
                matrix[i][j] = haversine_minutes(
                    points[i].lat, points[i].lng,
                    points[j].lat, points[j].lng,
                    URBAN_SPEED_KMH
                )

    return _ensure_float(matrix)


def _ensure_float(matrix: list[list]) -> list[list[float]]:
    return [[float(v or 0.0) for v in row] for row in matrix]


async def _lookup_cache(
    db: AsyncSession,
    origin: MatrixPoint,
    dest: MatrixPoint,
    now: datetime,
) -> Optional[float]:
    """Busca en cache usando tolerancia Float."""
    tol = CACHE_TOL
    result = await db.execute(
        select(DistanceMatrixCache).where(
            DistanceMatrixCache.origin_lat.between(origin.lat - tol, origin.lat + tol),
            DistanceMatrixCache.origin_lng.between(origin.lng - tol, origin.lng + tol),
            DistanceMatrixCache.dest_lat.between(dest.lat - tol, dest.lat + tol),
            DistanceMatrixCache.dest_lng.between(dest.lng - tol, dest.lng + tol),
            DistanceMatrixCache.expires_at > now,
        ).limit(1)
    )
    row = result.scalar_one_or_none()
    if row:
        return row.duration_sec / 60.0
    return None


async def _save_cache(
    db: AsyncSession,
    origin: MatrixPoint,
    dest: MatrixPoint,
    duracion_min: float,
    now: datetime,
) -> None:
    expires = now + timedelta(hours=CACHE_TTL_HOURS)
    entry = DistanceMatrixCache(
        origin_lat=origin.lat,
        origin_lng=origin.lng,
        dest_lat=dest.lat,
        dest_lng=dest.lng,
        duration_sec=round(duracion_min * 60.0, 2),
        provider="ors",
        expires_at=expires,
    )
    db.add(entry)


# ---------------------------------------------------------------------------
# API Calls
# ---------------------------------------------------------------------------

async def _call_ors(points: list[MatrixPoint]) -> list[list[float]]:
    """Llama a OpenRouteService Matrix API."""
    from app.config import settings

    if not getattr(settings, "ORS_API_KEY", None):
        raise ValueError("ORS_API_KEY no configurada")

    locations = [[p.lng, p.lat] for p in points]
    payload = {
        "locations": locations,
        "metrics": ["duration"],
        "units": "km",
    }
    headers = {
        "Authorization": settings.ORS_API_KEY,
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.openrouteservice.org/v2/matrix/driving-car",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
    durations = data["durations"]  # segundos
    return [[v / 60.0 for v in row] for row in durations]


async def _call_osrm(points: list[MatrixPoint]) -> list[list[float]]:
    """Llama a OSRM Table API (instancia pública o propia)."""
    from app.config import settings
    base_url = getattr(settings, "OSRM_BASE_URL", "http://router.project-osrm.org")

    coords_str = ";".join(f"{p.lng},{p.lat}" for p in points)
    url = f"{base_url}/table/v1/driving/{coords_str}?annotations=duration"

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
    durations = data["durations"]  # segundos
    return [[v / 60.0 for v in row] for row in durations]
