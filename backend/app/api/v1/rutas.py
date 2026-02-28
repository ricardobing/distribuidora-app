"""
Router de rutas: generación, consulta y actualización de estado de entregas.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user, require_operador
from app.models.ruta import Ruta, RutaParada, RutaExcluido, ParadaEstado
from app.models.usuario import Usuario
from app.schemas.ruta import (
    RutaResponse, RutaParadaResponse, RutaExcluidoResponse,
    RouteConfig, ParadaEstadoUpdate, RutaEstadoUpdate,
)
from app.schemas.common import OkResponse
from app.services import route_service
from app.core.exceptions import not_found

router = APIRouter(prefix="/rutas", tags=["rutas"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _load_ruta_response(db: AsyncSession, ruta: Ruta) -> dict:
    paradas_res = await db.execute(
        select(RutaParada)
        .where(RutaParada.ruta_id == ruta.id)
        .order_by(RutaParada.orden)
    )
    paradas = paradas_res.scalars().all()

    excluidos_res = await db.execute(
        select(RutaExcluido).where(RutaExcluido.ruta_id == ruta.id)
    )
    excluidos = excluidos_res.scalars().all()

    return {
        "id": ruta.id,
        "fecha": str(ruta.fecha),
        "estado": ruta.estado,
        "total_paradas": ruta.total_paradas,
        "total_excluidos": ruta.total_excluidos,
        "duracion_estimada_min": ruta.duracion_estimada_min,
        "distancia_total_km": ruta.distancia_total_km,
        "gmaps_links": ruta.gmaps_links or [],
        "config": ruta.config_snapshot or {},
        "api_cost_estimate": ruta.api_cost_estimate,
        "created_at": ruta.created_at,
        "paradas": [
            {
                "id": p.id,
                "orden": p.orden,
                "remito_id": p.remito_id,
                "remito_numero": p.remito_numero,
                "cliente": p.cliente_snapshot,
                "direccion": p.direccion_snapshot,
                "lat": p.lat_snapshot,
                "lng": p.lng_snapshot,
                "minutos_desde_anterior": p.minutos_desde_anterior,
                "tiempo_espera_min": p.tiempo_espera_min,
                "minutos_acumulados": p.minutos_acumulados,
                "distancia_desde_anterior_km": p.distancia_desde_anterior_km,
                "observaciones": p.observaciones_snapshot,
                "es_urgente": p.es_urgente,
                "es_prioridad": p.es_prioridad,
                "ventana_tipo": p.ventana_tipo,
                "estado": p.estado,
            }
            for p in paradas
        ],
        "excluidos": [
            {
                "id": e.id,
                "remito_id": e.remito_id,
                "remito_numero": e.remito_numero,
                "cliente": e.cliente_snapshot,
                "direccion": e.direccion_snapshot,
                "motivo": e.motivo,
                "distancia_km": e.distancia_km,
                "observaciones": e.observaciones_snapshot,
            }
            for e in excluidos
        ],
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/generar", response_model=dict)
async def generar_ruta(
    body: Optional[RouteConfig] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador),
):
    """Genera la ruta del día con todos los remitos en estado 'armado'."""
    config_override = body.model_dump(exclude_none=True) if body else None
    ruta = await route_service.generate_route(db, config_override=config_override)
    return await _load_ruta_response(db, ruta)


@router.get("/", response_model=list)
async def list_rutas(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Últimas N rutas generadas."""
    result = await db.execute(
        select(Ruta).order_by(Ruta.created_at.desc()).limit(limit)
    )
    rutas = result.scalars().all()
    out = []
    for ruta in rutas:
        out.append(await _load_ruta_response(db, ruta))
    return out


@router.get("/{ruta_id}", response_model=dict)
async def get_ruta(
    ruta_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(Ruta).where(Ruta.id == ruta_id))
    ruta = result.scalar_one_or_none()
    if not ruta:
        raise not_found("Ruta")
    return await _load_ruta_response(db, ruta)


@router.get("/{ruta_id}/geojson")
async def get_ruta_geojson(
    ruta_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Retorna el GeoJSON LineString de la ruta."""
    result = await db.execute(select(Ruta).where(Ruta.id == ruta_id))
    ruta = result.scalar_one_or_none()
    if not ruta:
        raise not_found("Ruta")

    paradas_res = await db.execute(
        select(RutaParada).where(RutaParada.ruta_id == ruta.id).order_by(RutaParada.orden)
    )
    paradas = paradas_res.scalars().all()

    features = []
    for p in paradas:
        if p.lat_snapshot and p.lng_snapshot:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [p.lng_snapshot, p.lat_snapshot]},
                "properties": {
                    "orden": p.orden,
                    "numero": p.remito_numero,
                    "cliente": p.cliente_snapshot,
                    "estado": p.estado,
                },
            })

    return {
        "type": "FeatureCollection",
        "features": features,
        "ruta_geom": ruta.ruta_geom,
        "deposito": {"lat": ruta.deposito_lat, "lng": ruta.deposito_lng},
    }


@router.put("/{ruta_id}/estado", response_model=OkResponse)
async def update_ruta_estado(
    ruta_id: int = Path(...),
    body: RutaEstadoUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador),
):
    result = await db.execute(select(Ruta).where(Ruta.id == ruta_id))
    ruta = result.scalar_one_or_none()
    if not ruta:
        raise not_found("Ruta")
    ruta.estado = body.estado
    await db.commit()
    return OkResponse(message=f"Estado actualizado a '{body.estado}'")


@router.put("/{ruta_id}/paradas/{parada_id}/estado", response_model=OkResponse)
async def update_parada_estado(
    ruta_id: int = Path(...),
    parada_id: int = Path(...),
    body: ParadaEstadoUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador),
):
    result = await db.execute(
        select(RutaParada).where(
            RutaParada.id == parada_id,
            RutaParada.ruta_id == ruta_id,
        )
    )
    parada = result.scalar_one_or_none()
    if not parada:
        raise not_found("Parada")
    parada.estado = body.estado
    await db.commit()
    return OkResponse(message=f"Parada {parada_id} → '{body.estado}'")
