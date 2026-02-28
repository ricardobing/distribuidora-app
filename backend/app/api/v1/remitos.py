from fastapi import APIRouter, Depends, Query, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies import get_db, get_current_user, require_operador
from app.models.usuario import Usuario
from app.models.remito import Remito, RemitoEstadoClasificacion, RemitoEstadoLifecycle
from app.schemas.remito import (
    RemitoCreate, RemitoSingleCreate, RemitoUpdate,
    DireccionCorreccion, ClasificacionUpdate, RemitoResponse, IngestResponse
)
from app.schemas.common import PaginatedResponse, OkResponse
from app.services.remito_service import (
    ingest_batch, process_pipeline, get_by_numero, process_pending
)
from app.core.exceptions import not_found, bad_request
from typing import Optional
from datetime import date

router = APIRouter(prefix="/remitos", tags=["remitos"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_remitos(
    body: RemitoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
):
    """Ingesta masiva de remitos por número. El pipeline completo corre para cada uno."""
    result = await ingest_batch(db, body.numeros, source=body.source or "manual")
    return result


@router.post("/", response_model=RemitoResponse)
async def create_remito(
    body: RemitoSingleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
):
    """Crea un remito individual con datos completos."""
    remito = Remito(
        numero=body.numero,
        cliente=body.cliente,
        direccion_raw=body.direccion,
        localidad=body.localidad,
        observaciones=body.observaciones,
        estado_clasificacion=RemitoEstadoClasificacion.pendiente,
        estado_lifecycle=RemitoEstadoLifecycle.ingresado,
    )
    db.add(remito)
    await db.flush()
    remito = await process_pipeline(db, remito)
    await db.commit()
    await db.refresh(remito)
    return _to_response(remito)


@router.get("/", response_model=PaginatedResponse)
async def list_remitos(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    estado_clasificacion: Optional[str] = Query(None),
    estado_lifecycle: Optional[str] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    q: Optional[str] = Query(None, description="Buscar por número o cliente"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(Remito)
    if estado_clasificacion:
        stmt = stmt.where(Remito.estado_clasificacion == estado_clasificacion)
    if estado_lifecycle:
        stmt = stmt.where(Remito.estado_lifecycle == estado_lifecycle)
    if fecha_desde:
        stmt = stmt.where(func.date(Remito.created_at) >= fecha_desde)
    if fecha_hasta:
        stmt = stmt.where(func.date(Remito.created_at) <= fecha_hasta)
    if q:
        stmt = stmt.where(
            Remito.numero.ilike(f"%{q}%") | Remito.cliente.ilike(f"%{q}%")
        )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(Remito.created_at.desc()).offset((page - 1) * size).limit(size)
    items = (await db.execute(stmt)).scalars().all()

    return PaginatedResponse(
        items=[_to_response(r) for r in items],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/pendientes", response_model=list[RemitoResponse])
async def get_pendientes(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Remitos en estado pendiente esperando procesamiento."""
    stmt = select(Remito).where(
        Remito.estado_clasificacion == RemitoEstadoClasificacion.pendiente
    ).order_by(Remito.created_at)
    items = (await db.execute(stmt)).scalars().all()
    return [_to_response(r) for r in items]


@router.get("/{numero}", response_model=RemitoResponse)
async def get_remito(
    numero: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    remito = await get_by_numero(db, numero)
    if not remito:
        raise not_found("Remito")
    return _to_response(remito)


@router.put("/{numero}", response_model=RemitoResponse)
async def update_remito(
    numero: str = Path(...),
    body: RemitoUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
):
    remito = await get_by_numero(db, numero)
    if not remito:
        raise not_found("Remito")
    if body.cliente is not None:
        remito.cliente = body.cliente
    if body.observaciones is not None:
        remito.observaciones = body.observaciones
    if body.es_urgente is not None:
        remito.es_urgente = body.es_urgente
    if body.es_prioridad is not None:
        remito.es_prioridad = body.es_prioridad
    await db.commit()
    await db.refresh(remito)
    return _to_response(remito)


@router.put("/{numero}/direccion", response_model=RemitoResponse)
async def correct_direccion(
    numero: str = Path(...),
    body: DireccionCorreccion = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
):
    """Corrige la dirección y vuelve a geocodificar."""
    remito = await get_by_numero(db, numero)
    if not remito:
        raise not_found("Remito")
    from app.services.geocode_service import geocode
    from app.services.address_service import normalize
    remito.direccion_raw = body.direccion
    remito.direccion_normalizada = normalize(body.direccion)
    result = await geocode(db, body.direccion)
    if result:
        remito.lat = result.lat
        remito.lng = result.lng
        remito.geocode_provider = result.provider
        remito.geocode_score = result.score
        remito.estado_clasificacion = RemitoEstadoClasificacion.enviar
    else:
        remito.estado_clasificacion = RemitoEstadoClasificacion.no_encontrado
    await db.commit()
    await db.refresh(remito)
    return _to_response(remito)


@router.put("/{numero}/clasificacion", response_model=RemitoResponse)
async def update_clasificacion(
    numero: str = Path(...),
    body: ClasificacionUpdate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
):
    remito = await get_by_numero(db, numero)
    if not remito:
        raise not_found("Remito")
    remito.estado_clasificacion = body.clasificacion
    await db.commit()
    await db.refresh(remito)
    return _to_response(remito)


@router.post("/{numero}/reprocess", response_model=RemitoResponse)
async def reprocess_remito(
    numero: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
):
    """Vuelve a ejecutar el pipeline completo para un remito."""
    remito = await get_by_numero(db, numero)
    if not remito:
        raise not_found("Remito")
    remito = await process_pipeline(db, remito)
    await db.commit()
    await db.refresh(remito)
    return _to_response(remito)


@router.post("/reprocess-all")
async def reprocess_pending(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
):
    """Reprocesa todos los remitos en estado pendiente."""
    count = await process_pending(db)
    return {"ok": True, "processed": count}


@router.delete("/{numero}", response_model=OkResponse)
async def delete_remito(
    numero: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
):
    remito = await get_by_numero(db, numero)
    if not remito:
        raise not_found("Remito")
    await db.delete(remito)
    await db.commit()
    return OkResponse(message=f"Remito {numero} eliminado")


def _to_response(r: Remito) -> RemitoResponse:
    return RemitoResponse(
        id=r.id,
        numero=r.numero,
        cliente=r.cliente,
        direccion_raw=r.direccion_raw,
        direccion_normalizada=r.direccion_normalizada,
        localidad=r.localidad,
        observaciones=r.observaciones,
        lat=r.lat,
        lng=r.lng,
        geocode_provider=r.geocode_provider,
        geocode_score=r.geocode_score,
        estado_clasificacion=r.estado_clasificacion,
        estado_lifecycle=r.estado_lifecycle,
        carrier_nombre=r.carrier_nombre,
        carrier_source=r.carrier_source,
        ventana_raw=r.ventana_raw,
        ventana_tipo=r.ventana_tipo,
        ventana_desde=str(r.ventana_desde) if r.ventana_desde else None,
        ventana_hasta=str(r.ventana_hasta) if r.ventana_hasta else None,
        es_urgente=r.es_urgente,
        es_prioridad=r.es_prioridad,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )
