"""
Geocodificación multi-proveedor con cache en DB.
Migra: geocodificarDireccion_(), geocodificadorCascade_(), validateGeoResult_()
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.geo_cache import GeoCache
from app.services.address_service import normalize, normalize_key
from app.core.validators import is_in_mendoza
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class GeocodeResult:
    lat: float
    lng: float
    formatted_address: str
    has_street_number: bool
    source: str          # 'cache', 'ors', 'mapbox', 'google'
    confidence: float = 1.0
    provider: Optional[str] = None


async def geocode(
    db: AsyncSession,
    address: str,
    provider_override: Optional[str] = None,
) -> Optional[GeocodeResult]:
    """Geocodifica con cascade: cache DB → ORS → Mapbox → Google."""
    if not address:
        return None

    normalized = normalize(address)
    cache_key = normalize_key(address)

    # 1. Cache DB
    cached = await _lookup_cache(db, cache_key)
    if cached:
        return cached

    # 2. Cascade de proveedores
    provider_order = (
        [provider_override]
        if provider_override
        else settings.GEOCODE_PROVIDER_ORDER
    )

    result = None
    for provider in provider_order:
        try:
            if provider == "ors" and settings.ORS_API_KEY:
                result = await _geocode_ors(normalized)
            elif provider == "mapbox" and settings.MAPBOX_TOKEN:
                result = await _geocode_mapbox(normalized)
            elif provider == "google" and settings.GOOGLE_MAPS_API_KEY:
                result = await _geocode_google(normalized)
        except Exception as e:
            logger.warning(f"Geocode {provider} error for '{address}': {e}")
            continue

        if result and _validate_result(result):
            result.source = provider
            result.provider = provider
            await _save_cache(db, cache_key, address, result)
            return result

    logger.warning(f"Geocodificación sin resultado para: {address}")
    return None


async def _lookup_cache(db: AsyncSession, cache_key: str) -> Optional[GeocodeResult]:
    """Busca en la tabla geo_cache por key."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(GeoCache).where(
            GeoCache.key_normalizada == cache_key,
            GeoCache.expires_at > now,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        return None
    return GeocodeResult(
        lat=entry.lat,
        lng=entry.lng,
        formatted_address=entry.formatted_address or "",
        has_street_number=entry.has_street_number or False,
        source="cache",
        confidence=entry.score or 1.0,
        provider=entry.provider,
    )


async def _save_cache(
    db: AsyncSession, cache_key: str, original: str, result: GeocodeResult
) -> None:
    """Guarda resultado en geo_cache."""
    from app.config import settings as cfg
    cache_days = 30
    try:
        # Intentar leer config de DB
        from app.models.config import ConfigRuta
        conf_res = await db.execute(
            select(ConfigRuta).where(ConfigRuta.key == "geocode_cache_days")
        )
        conf = conf_res.scalar_one_or_none()
        if conf:
            cache_days = int(conf.value)
    except Exception:
        pass

    expires_at = datetime.now(timezone.utc) + timedelta(days=cache_days)
    entry = GeoCache(
        key_normalizada=cache_key,
        query_original=original,
        lat=result.lat,
        lng=result.lng,
        formatted_address=result.formatted_address,
        has_street_number=result.has_street_number,
        provider=result.provider or result.source,
        score=result.confidence,
        expires_at=expires_at,
    )
    db.add(entry)
    try:
        await db.flush()
    except Exception:
        await db.rollback()
        logger.warning(f"Cache save failed for key {cache_key}")


def _validate_result(result: GeocodeResult) -> bool:
    """Valida que el resultado esté dentro de Mendoza."""
    return is_in_mendoza(result.lat, result.lng)


async def _geocode_ors(address: str) -> Optional[GeocodeResult]:
    """OpenRouteService geocoding."""
    url = "https://api.openrouteservice.org/geocode/search"
    params = {
        "api_key": settings.ORS_API_KEY,
        "text": f"{address}, Mendoza, Argentina",
        "boundary.rect.min_lng": settings.MENDOZA_LNG_MIN,
        "boundary.rect.min_lat": settings.MENDOZA_LAT_MIN,
        "boundary.rect.max_lng": settings.MENDOZA_LNG_MAX,
        "boundary.rect.max_lat": settings.MENDOZA_LAT_MAX,
        "size": 1,
        "layers": "address",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    features = data.get("features", [])
    if not features:
        return None
    feat = features[0]
    coords = feat["geometry"]["coordinates"]  # [lng, lat]
    props = feat.get("properties", {})
    return GeocodeResult(
        lat=float(coords[1]),
        lng=float(coords[0]),
        formatted_address=props.get("label", ""),
        has_street_number=bool(props.get("housenumber")),
        source="ors",
        confidence=props.get("confidence", 0.5),
        provider="ors",
    )


async def _geocode_mapbox(address: str) -> Optional[GeocodeResult]:
    """Mapbox Geocoding API."""
    import urllib.parse
    encoded = urllib.parse.quote(f"{address}, Mendoza, Argentina")
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded}.json"
    params = {
        "access_token": settings.MAPBOX_TOKEN,
        "country": "ar",
        "bbox": f"{settings.MENDOZA_LNG_MIN},{settings.MENDOZA_LAT_MIN},{settings.MENDOZA_LNG_MAX},{settings.MENDOZA_LAT_MAX}",
        "limit": 1,
        "types": "address",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    features = data.get("features", [])
    if not features:
        return None
    feat = features[0]
    coords = feat["geometry"]["coordinates"]  # [lng, lat]
    has_num = "address" in feat.get("place_type", [])
    return GeocodeResult(
        lat=float(coords[1]),
        lng=float(coords[0]),
        formatted_address=feat.get("place_name", ""),
        has_street_number=has_num,
        source="mapbox",
        confidence=feat.get("relevance", 0.5),
        provider="mapbox",
    )


async def _geocode_google(address: str) -> Optional[GeocodeResult]:
    """Google Maps Geocoding API."""
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": f"{address}, Mendoza, Argentina",
        "key": settings.GOOGLE_MAPS_API_KEY,
        "components": "country:AR",
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    if not results:
        return None
    r = results[0]
    loc = r["geometry"]["location"]
    components = r.get("address_components", [])
    has_num = any("street_number" in c.get("types", []) for c in components)
    return GeocodeResult(
        lat=float(loc["lat"]),
        lng=float(loc["lng"]),
        formatted_address=r.get("formatted_address", ""),
        has_street_number=has_num,
        source="google",
        confidence=0.9,
        provider="google",
    )


async def get_cache_stats(db: AsyncSession) -> dict:
    """Estadísticas del caché de geocodificación."""
    from sqlalchemy import func
    result = await db.execute(
        select(GeoCache.provider, func.count().label("cnt"))
        .group_by(GeoCache.provider)
    )
    by_provider = {row.provider: row.cnt for row in result}
    total = sum(by_provider.values())
    return {"total": total, "by_provider": by_provider}


async def clear_cache(db: AsyncSession) -> int:
    """Limpia el caché completo."""
    from sqlalchemy import delete
    result = await db.execute(delete(GeoCache))
    await db.commit()
    return result.rowcount


async def validate_address(db: AsyncSession, address: str) -> dict:
    """Valida una dirección y retorna resultado."""
    result = await geocode(db, address)
    if not result:
        return {"valid": False, "address": address, "reason": "No geocodificado"}
    return {
        "valid": True,
        "address": address,
        "lat": result.lat,
        "lng": result.lng,
        "formatted": result.formatted_address,
        "has_street_number": result.has_street_number,
        "provider": result.provider,
        "confidence": result.confidence,
    }


async def geocode_batch(
    db: AsyncSession,
    addresses: list[str],
) -> list[dict]:
    """Geocodifica una lista de direcciones."""
    results = []
    for addr in addresses:
        res = await geocode(db, addr)
        results.append({
            "address": addr,
            "ok": res is not None,
            "lat": res.lat if res else None,
            "lng": res.lng if res else None,
            "formatted": res.formatted_address if res else None,
            "provider": res.provider if res else None,
        })
    return results
