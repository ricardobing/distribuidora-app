from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from app.dependencies import get_db, get_current_user, require_admin
from app.models.geo_cache import GeoCache
from app.models.usuario import Usuario
from app.schemas.geocode import (
    GeocodeRequest, GeocodeResponse, GeocodeValidateRequest,
    GeocodeValidateResponse, GeocodeStatsResponse, GeocodeBatchRequest
)
from app.schemas.common import OkResponse
from app.services.geocode_service import geocode
from app.core.validators import is_in_mendoza, is_known_city_center
from datetime import datetime, timezone

router = APIRouter(prefix="/geocode", tags=["geocode"])


@router.post("/", response_model=GeocodeResponse)
async def geocode_address(
    body: GeocodeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Geocodifica una dirección usando el proveedor configurado."""
    result = await geocode(db, body.address, provider_override=body.provider)
    if not result:
        from app.core.exceptions import bad_request
        raise bad_request(f"No se pudo geocodificar: '{body.address}'")
    return GeocodeResponse(
        address_input=body.address,
        lat=result.lat,
        lng=result.lng,
        display_name=result.display_name,
        provider=result.provider,
        score=result.score,
        from_cache=result.from_cache,
    )


@router.post("/batch")
async def geocode_batch(
    body: GeocodeBatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Geocodifica múltiples direcciones en secuencia."""
    results = []
    for addr in body.addresses:
        try:
            r = await geocode(db, addr, provider_override=body.provider)
            if r:
                results.append({
                    "address": addr,
                    "lat": r.lat,
                    "lng": r.lng,
                    "provider": r.provider,
                    "from_cache": r.from_cache,
                    "ok": True
                })
            else:
                results.append({"address": addr, "ok": False, "error": "No encontrado"})
        except Exception as e:
            results.append({"address": addr, "ok": False, "error": str(e)})
    return {"results": results, "total": len(results)}


@router.post("/validate", response_model=GeocodeValidateResponse)
async def validate_coords(body: GeocodeValidateRequest, current_user: Usuario = Depends(get_current_user)):
    in_bbox = is_in_mendoza(body.lat, body.lng)
    is_center = is_known_city_center(body.lat, body.lng)
    is_valid = in_bbox and not is_center
    msg = None
    if not in_bbox:
        msg = "Coordenadas fuera del bounding box de Mendoza"
    elif is_center:
        msg = "Coordenadas apuntan al centro de la ciudad (resultado genérico)"
    return GeocodeValidateResponse(in_bbox=in_bbox, is_city_center=is_center, is_valid=is_valid, message=msg)


@router.get("/cache/stats", response_model=GeocodeStatsResponse)
async def cache_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    total = (await db.execute(select(func.count()).select_from(GeoCache))).scalar_one()
    now = datetime.now(timezone.utc)
    expired = (await db.execute(
        select(func.count()).select_from(GeoCache).where(GeoCache.expires_at < now)
    )).scalar_one()

    by_provider_result = await db.execute(
        select(GeoCache.provider, func.count().label("cnt")).group_by(GeoCache.provider)
    )
    by_provider = {row.provider: row.cnt for row in by_provider_result}

    return GeocodeStatsResponse(total_entries=total, by_provider=by_provider, expired=expired)


@router.delete("/cache", response_model=OkResponse, dependencies=[Depends(require_admin)])
async def clear_cache(expired_only: bool = Query(True), db: AsyncSession = Depends(get_db)):
    """Limpia la caché de geocodificación."""
    if expired_only:
        now = datetime.now(timezone.utc)
        await db.execute(delete(GeoCache).where(GeoCache.expires_at < now))
        msg = "Caché expirada eliminada"
    else:
        await db.execute(delete(GeoCache))
        msg = "Caché completa eliminada"
    await db.commit()
    return OkResponse(message=msg)
