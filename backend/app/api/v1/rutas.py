from fastapi import APIRouter, Depends, Query, Path, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user, require_operador
from app.models.ruta import Ruta, RutaParada, RutaExcluido, RutaEstado
from app.models.usuario import Usuario
from app.schemas.ruta import (
    RouteConfig, RutaResponse, RutaParadaResponse,
    RutaExcluidoResponse, ParadaEstadoUpdate, RutaEstadoUpdate
)
from app.schemas.common import OkResponse
from app.services.route_service import generate_route
from app.core.exceptions import not_found, bad_request
from typing import Optional
import json

router = APIRouter(prefix="/rutas", tags=["rutas"])


@router.post("/generar", response_model=RutaResponse)
async def generar_ruta(
    config_override: Optional[RouteConfig] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
):
    """Genera la ruta del día con el algoritmo sweep + 2-opt."""
    ruta = await generate_route(db, config_override=config_override)
    return await _load_ruta_response(db, ruta.id)


@router.get("/", response_model=list[dict])
async def list_rutas(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    result = await db.execute(
        select(Ruta).order_by(Ruta.fecha.desc()).limit(limit)
    )
    rutas = result.scalars().all()
    return [
        {
            "id": r.id,
            "fecha": str(r.fecha),
            "estado": r.estado,
            "total_paradas": r.total_paradas,
            "total_excluidos": r.total_excluidos,
            "duracion_estimada_min": r.duracion_estimada_min,
            "distancia_total_km": r.distancia_total_km,
        }
        for r in rutas
    ]


@router.get("/{ruta_id}", response_model=RutaResponse)
async def get_ruta(
    ruta_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return await _load_ruta_response(db, ruta_id)


@router.get("/{ruta_id}/geojson")
async def get_ruta_geojson(
    ruta_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Retorna la ruta en formato GeoJSON para Leaflet."""
    result = await db.execute(select(Ruta).where(Ruta.id == ruta_id))
    ruta = result.scalar_one_or_none()
    if not ruta:
        raise not_found("Ruta")

    paradas_result = await db.execute(
        select(RutaParada).where(RutaParada.ruta_id == ruta_id).order_by(RutaParada.orden)
    )
    paradas = paradas_result.scalars().all()

    features = []
    for p in paradas:
        if p.lat_snapshot and p.lng_snapshot:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [p.lng_snapshot, p.lat_snapshot]},
                "properties": {
                    "orden": p.orden,
                    "remito_id": p.remito_id,
                    "estado": p.estado,
                    "minutos_acumulados": p.minutos_acumulados,
                    "es_urgente": p.es_urgente,
                }
            })

    if ruta.ruta_geom:
        features.append({
            "type": "Feature",
            "geometry": ruta.ruta_geom,
            "properties": {"tipo": "ruta_linea"}
        })

    return {"type": "FeatureCollection", "features": features}


@router.get("/{ruta_id}/gmaps-links")
async def get_gmaps_links(
    ruta_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    result = await db.execute(select(Ruta).where(Ruta.id == ruta_id))
    ruta = result.scalar_one_or_none()
    if not ruta:
        raise not_found("Ruta")
    links = ruta.gmaps_links or []
    return {"links": links, "count": len(links)}


@router.put("/{ruta_id}/estado", response_model=OkResponse)
async def update_ruta_estado(
    ruta_id: int = Path(...),
    body: RutaEstadoUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
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
    body: ParadaEstadoUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
):
    result = await db.execute(
        select(RutaParada).where(RutaParada.id == parada_id, RutaParada.ruta_id == ruta_id)
    )
    parada = result.scalar_one_or_none()
    if not parada:
        raise not_found("Parada")
    parada.estado = body.estado
    await db.commit()
    return OkResponse(message=f"Parada {parada_id} actualizada")


@router.delete("/{ruta_id}", response_model=OkResponse, dependencies=[Depends(require_operador)])
async def delete_ruta(ruta_id: int = Path(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Ruta).where(Ruta.id == ruta_id))
    ruta = result.scalar_one_or_none()
    if not ruta:
        raise not_found("Ruta")
    await db.delete(ruta)
    await db.commit()
    return OkResponse(message=f"Ruta {ruta_id} eliminada")


async def _load_ruta_response(db: AsyncSession, ruta_id: int) -> RutaResponse:
    result = await db.execute(select(Ruta).where(Ruta.id == ruta_id))
    ruta = result.scalar_one_or_none()
    if not ruta:
        raise not_found("Ruta")

    paradas_result = await db.execute(
        select(RutaParada).where(RutaParada.ruta_id == ruta_id).order_by(RutaParada.orden)
    )
    paradas = paradas_result.scalars().all()

    excluidos_result = await db.execute(
        select(RutaExcluido).where(RutaExcluido.ruta_id == ruta_id)
    )
    excluidos = excluidos_result.scalars().all()

    return RutaResponse(
        id=ruta.id,
        fecha=str(ruta.fecha),
        estado=ruta.estado,
        total_paradas=ruta.total_paradas,
        total_excluidos=ruta.total_excluidos,
        duracion_estimada_min=ruta.duracion_estimada_min,
        distancia_total_km=ruta.distancia_total_km,
        gmaps_links=ruta.gmaps_links or [],
        paradas=[
            RutaParadaResponse(
                id=p.id,
                orden=p.orden,
                remito_id=p.remito_id,
                remito_numero=p.remito_numero,
                cliente=p.cliente_snapshot,
                direccion=p.direccion_snapshot,
                lat=p.lat_snapshot,
                lng=p.lng_snapshot,
                minutos_desde_anterior=p.minutos_desde_anterior,
                tiempo_espera_min=p.tiempo_espera_min,
                minutos_acumulados=p.minutos_acumulados,
                distancia_desde_anterior_km=p.distancia_desde_anterior_km,
                observaciones=p.observaciones,
                es_urgente=p.es_urgente,
                es_prioridad=p.es_prioridad,
                ventana_tipo=p.ventana_tipo,
                estado=p.estado,
            )
            for p in paradas
        ],
        excluidos=[
            RutaExcluidoResponse(
                id=e.id,
                remito_id=e.remito_id,
                remito_numero=e.remito_numero,
                cliente=e.cliente_snapshot,
                direccion=e.direccion_snapshot,
                motivo=e.motivo,
                distancia_km=e.distancia_km,
                observaciones=e.observaciones,
            )
            for e in excluidos
        ],
        config=ruta.config_snapshot or {},
        api_cost_estimate=ruta.api_cost_estimate,
        created_at=ruta.created_at,
    )
