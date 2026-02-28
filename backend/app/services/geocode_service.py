"""
Geocodificación multi-proveedor con cache en DB.
Migra: geocodificarDireccion_(), geocodificadorCascade_(), validateGeoResult_(), 
buscarEnCacheGeo_() del sistema original.
"""
import logging
import hashlib
from dataclasses import dataclass
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.functions import ST_MakePoint, ST_SetSRID, ST_X, ST_Y, ST_DWithin

from app.models.geo_cache import GeoCache
from app.services.address_service import normalize, normalize_key
from app.core.validators import is_in_mendoza, is_known_city_center
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class GeocodeResult:
    lat: float
    lng: float
    formatted_address: str
    has_street_number: bool
    source: str  # 'cache', 'ors', 'mapbox', 'google'
    confidence: float = 1.0
    provider: Optional[str] = None


async def geocode(
    db: AsyncSession,
    address: str,
    provider_override: Optional[str] = None,
) -> Optional[GeocodeResult]:
    """
    Geocodifica una dirección con cascade: cache DB → ORS → Mapbox → Google.
    Equivalente a geocodificarDireccion_() del sistema original.
    """
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

        if result and _validate_result(result, normalized):
            result.source = provider
            await _save_cache(db, cache_key, address, result)
            return result

    logger.warning(f"Geocodificación sin resultado para: {address}")
    return None


async def _lookup_cache(db: AsyncSession, cache_key: str) -> Optional[GeocodeResult]:
    """Busca en la tabla geo_cache."""
    result = await db.execute(
        select(GeoCache).where(GeoCache.key_normalizada == cache_key)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        return None
    # Extraer lat/lng del geom PostGIS
    lat_result = await db.execute(
        select(ST_Y(entry.geom))
    )
    lng_result = await db.execute(
        select(ST_X(entry.geom))
    )
    # Alternativa: usar WKB directamente
    from geoalchemy2.shape import to_shape
    point = to_shape(entry.geom)
    lat, lng = point.y, point.x
    return GeocodeResult(
        lat=lat,
        lng=lng,
        formatted_address=entry.formatted_address or "",
        has_street_number=entry.has_street_number,
        source="cache",
        confidence=entry.score or 1.0,
        provider=entry.provider,
    )


async def _save_cache(
    db: AsyncSession, cache_key: str, original: str, result: GeocodeResult
) -> None:
    """Guarda resultado en geo_cache."""
    from sqlalchemy import func as sqlfunc
    geom_wkt = f"SRID=4326;POINT({result.lng} {result.lat})"
    entry = GeoCache(
        key_normalizada=cache_key,
        query_original=original,
        geom=f"SRID=4326;POINT({result.lng} {result.lat})",
        formatted_address=result.formatted_address,
        has_street_number=result.has_street_number,
        provider=result.provider,
        score=result.confidence,
    )
    db.add(entry)
    try:
        await db.commit()
    except Exception:
        await db.rollback()


async def _geocode_ors(address: str) -> Optional[GeocodeResult]:
    """OpenRouteService geocoding."""
    url = "https://api.openrouteservice.org/geocode/search"
    params = {
        "api_key": settings.ORS_API_KEY,
        "text": f"{address}, Mendoza, Argentina",
        "boundary.rect.min_lng": -69.5,
        "boundary.rect.min_lat": -33.5,
        "boundary.rect.max_lng": -68.0,
        "boundary.rect.max_lat": -32.0,
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
    confidence = props.get("confidence", 0.5)
    has_num = bool(props.get("housenumber"))
    formatted = props.get("label", "")
    return GeocodeResult(
        lat=float(coords[1]),
        lng=float(coords[0]),
        formatted_address=formatted,
        has_street_number=has_num,
        source="ors",
        confidence=confidence,
        provider="ors",
    )


async def _geocode_mapbox(address: str) -> Optional[GeocodeResult]:
    """Mapbox geocoding."""
    import urllib.parse
    encoded = urllib.parse.quote(f"{address}, Mendoza, Argentina")
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded}.json"
    params = {
        "access_token": settings.MAPBOX_TOKEN,
        "country": "ar",
        "bbox": "-69.5,-33.5,-68.0,-32.0",
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
    relevance = feat.get("relevance", 0.5)
    formatted = feat.get("place_name", "")
    context = feat.get("context", [])
    has_num = "address" in feat.get("place_type", [])
    return GeocodeResult(
        lat=float(coords[1]),
        lng=float(coords[0]),
        formatted_address=formatted,
        has_street_number=has_num,
        source="mapbox",
        confidence=relevance,
        provider="mapbox",
    )


async def _geocode_google(address: str) -> Optional[GeocodeResult]:
    """Google Maps Geocoding API."""
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": f"{address}, Mendoza, Argentina",
        "key": settings.GOOGLE_MAPS_API_KEY,
        "components": "country:AR|administrative_area:Mendoza",
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
    address_components = r.get("address_components", [])
    has_num = any(
        "street_number" in c.get("types", []) for c in address_components
    )
    formatted = r.get("formatted_address", "")
    # Google no da confidence — usar location_type como proxy
    lt = r["geometry"].get("location_type", "APPROXIMATE")
    confidence_map = {"ROOFTOP": 0.99, "RANGE_INTERPOLATED": 0.8, "GEOMETRIC_CENTER": 0.6, "APPROXIMATE": 0.3}
    confidence = confidence_map.get(lt, 0.5)
    return GeocodeResult(
        lat=float(loc["lat"]),
        lng=float(loc["lng"]),
        formatted_address=formatted,
        has_street_number=has_num,
        source="google",
        confidence=confidence,
        provider="google",
    )


def _validate_result(result: GeocodeResult, query: str) -> bool:
    """
    Valida un resultado geocodificado.
    Equivalente a validateGeoResult_() del sistema original.
    """
    if not result:
        return False
    if result.lat == 0 and result.lng == 0:
        return False
    if not is_in_mendoza(result.lat, result.lng):
        return False
    if is_known_city_center(result.lat, result.lng):
        return False
    return True
