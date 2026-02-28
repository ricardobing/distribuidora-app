"""
Distance Matrix multi-provider con cache en DB.
Migra: computeNxNMatrix_(), getMatrix_() del sistema original.
"""
import logging
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from geoalchemy2.functions import ST_DWithin, ST_SetSRID, ST_MakePoint

from app.config import settings
from app.models.distance_cache import DistanceMatrixCache
from app.core.haversine import haversine_minutes

logger = logging.getLogger(__name__)


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
    Construye matriz NxN de duraciones en minutos.
    Usa cache de DB para pares ya calculados.
    Bloques de DM_BLOCK_SIZE x DM_BLOCK_SIZE.
    Diagonal = 0, missing = 9e9.
    """
    n = len(points)
    matrix = [[9e9] * n for _ in range(n)]
    for i in range(n):
        matrix[i][i] = 0.0

    block_size = settings.DM_BLOCK_SIZE

    # Procesar en bloques para respetar límites de API
    for i in range(0, n, block_size):
        origins_idx = list(range(i, min(i + block_size, n)))
        for j in range(0, n, block_size):
            dests_idx = list(range(j, min(j + block_size, n)))
            origins = [points[k] for k in origins_idx]
            dests = [points[k] for k in dests_idx]

            # Intentar cache primero
            durations = await _lookup_matrix_cache(db, origins, dests)

            # Para pares sin cache, llamar API
            uncached_pairs = [
                (oi, di)
                for oi, o in enumerate(origins)
                for di, d in enumerate(dests)
                if durations[oi][di] is None
            ]

            if uncached_pairs:
                try:
                    api_results = await _call_provider(provider, origins, dests)
                    for oi, row in enumerate(api_results):
                        for di, dur_sec in enumerate(row):
                            if dur_sec is not None:
                                durations[oi][di] = dur_sec / 60.0  # seg → min
                                await _save_dm_cache(db, origins[oi], dests[di], int(dur_sec), provider)
                except Exception as e:
                    logger.warning(f"Distance matrix API {provider} error: {e}")
                    # Fallback a Haversine
                    for oi, o in enumerate(origins):
                        for di, d in enumerate(dests):
                            if durations[oi][di] is None:
                                durations[oi][di] = haversine_minutes(
                                    o.lat, o.lng, d.lat, d.lng, settings.URBAN_SPEED_KMH
                                )

            for oi, gi in enumerate(origins_idx):
                for di, gj in enumerate(dests_idx):
                    if durations[oi][di] is not None:
                        matrix[gi][gj] = durations[oi][di]
                    else:
                        matrix[gi][gj] = haversine_minutes(
                            points[gi].lat, points[gi].lng,
                            points[gj].lat, points[gj].lng,
                            settings.URBAN_SPEED_KMH,
                        )

    return matrix


async def get_matrix_1xn(
    db: AsyncSession,
    origin: MatrixPoint,
    destinations: list[MatrixPoint],
    provider: str = "ors",
) -> list[float]:
    """1×N matrix para filtro de vuelta al depósito."""
    matrix = await get_matrix_nxn(db, [origin] + destinations, provider)
    return [matrix[0][i + 1] for i in range(len(destinations))]


async def _lookup_matrix_cache(
    db: AsyncSession,
    origins: list[MatrixPoint],
    dests: list[MatrixPoint],
) -> list[list[Optional[float]]]:
    """Busca duraciones en el cache. Retorna None para cache miss."""
    results = [[None] * len(dests) for _ in range(len(origins))]
    now = datetime.now(timezone.utc)
    tolerance_m = 10  # 10 metros

    for oi, o in enumerate(origins):
        for di, d in enumerate(dests):
            if oi == di and o.lat == d.lat and o.lng == d.lng:
                results[oi][di] = 0.0
                continue
            # Buscar en cache con tolerancia espacial
            o_geom = f"SRID=4326;POINT({o.lng} {o.lat})"
            d_geom = f"SRID=4326;POINT({d.lng} {d.lat})"
            result = await db.execute(
                select(DistanceMatrixCache)
                .where(
                    and_(
                        ST_DWithin(
                            DistanceMatrixCache.origin_geom,
                            ST_SetSRID(ST_MakePoint(o.lng, o.lat), 4326).cast("geography"),
                            tolerance_m,
                        ),
                        ST_DWithin(
                            DistanceMatrixCache.dest_geom,
                            ST_SetSRID(ST_MakePoint(d.lng, d.lat), 4326).cast("geography"),
                            tolerance_m,
                        ),
                        DistanceMatrixCache.expires_at > now,
                    )
                )
                .limit(1)
            )
            entry = result.scalar_one_or_none()
            if entry:
                results[oi][di] = entry.duration_sec / 60.0

    return results


async def _save_dm_cache(
    db: AsyncSession,
    origin: MatrixPoint,
    dest: MatrixPoint,
    duration_sec: int,
    provider: str,
) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.DM_CACHE_TTL_SECONDS)
    entry = DistanceMatrixCache(
        origin_geom=f"SRID=4326;POINT({origin.lng} {origin.lat})",
        dest_geom=f"SRID=4326;POINT({dest.lng} {dest.lat})",
        duration_sec=duration_sec,
        provider=provider,
        expires_at=expires_at,
    )
    db.add(entry)
    try:
        await db.commit()
    except Exception:
        await db.rollback()


async def _call_provider(
    provider: str,
    origins: list[MatrixPoint],
    dests: list[MatrixPoint],
) -> list[list[Optional[int]]]:
    """Llama al proveedor de Distance Matrix. Retorna duraciones en segundos."""
    if provider == "ors":
        return await _call_ors(origins, dests)
    elif provider == "google":
        return await _call_google(origins, dests)
    elif provider == "mapbox":
        return await _call_mapbox(origins, dests)
    raise ValueError(f"Proveedor desconocido: {provider}")


async def _call_ors(
    origins: list[MatrixPoint], dests: list[MatrixPoint]
) -> list[list[Optional[int]]]:
    """ORS: POST /v2/matrix/driving-car"""
    url = "https://api.openrouteservice.org/v2/matrix/driving-car"
    headers = {
        "Authorization": settings.ORS_API_KEY,
        "Content-Type": "application/json",
    }
    all_points = [[p.lng, p.lat] for p in origins] + [[p.lng, p.lat] for p in dests]
    sources = list(range(len(origins)))
    destinations_idx = list(range(len(origins), len(origins) + len(dests)))
    body = {
        "locations": all_points,
        "sources": sources,
        "destinations": destinations_idx,
        "metrics": ["duration"],
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=body, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    durations = data.get("durations", [])
    # durations[i][j] = segundos de origin i a dest j
    result = []
    for row in durations:
        result.append([int(v) if v is not None else None for v in row])
    return result


async def _call_google(
    origins: list[MatrixPoint], dests: list[MatrixPoint]
) -> list[list[Optional[int]]]:
    """Google Distance Matrix API"""
    origins_str = "|".join(f"{p.lat},{p.lng}" for p in origins)
    dests_str = "|".join(f"{p.lat},{p.lng}" for p in dests)
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origins_str,
        "destinations": dests_str,
        "mode": "driving",
        "key": settings.GOOGLE_MAPS_API_KEY,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    result = []
    for row in data.get("rows", []):
        row_result = []
        for elem in row.get("elements", []):
            if elem.get("status") == "OK":
                row_result.append(elem["duration"]["value"])
            else:
                row_result.append(None)
        result.append(row_result)
    return result


async def _call_mapbox(
    origins: list[MatrixPoint], dests: list[MatrixPoint]
) -> list[list[Optional[int]]]:
    """Mapbox Matrix API"""
    all_points = list(dict.fromkeys(origins + dests))
    coords_str = ";".join(f"{p.lng},{p.lat}" for p in (origins + dests))
    sources_idx = ";".join(str(i) for i in range(len(origins)))
    dests_idx = ";".join(str(i) for i in range(len(origins), len(origins) + len(dests)))
    url = f"https://api.mapbox.com/directions-matrix/v1/mapbox/driving/{coords_str}"
    params = {
        "access_token": settings.MAPBOX_TOKEN,
        "sources": sources_idx,
        "destinations": dests_idx,
        "annotations": "duration",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    result = []
    for row in data.get("durations", []):
        result.append([int(v) if v is not None else None for v in row])
    return result
