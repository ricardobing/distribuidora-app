"""
Router de remitos: ingesta, consulta, clasificación y corrección.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies import get_db, get_current_user, require_operador
from app.models.remito import Remito, RemitoEstadoClasificacion, RemitoEstadoLifecycle
from app.models.carrier import Carrier
from app.models.usuario import Usuario
from app.schemas.remito import (
    RemitoCreate, RemitoSingleCreate, RemitoUpdate,
    DireccionCorreccion, ClasificacionUpdate,
    RemitoResponse, IngestResponse,
)
from app.schemas.common import OkResponse, PaginatedResponse
from app.services import remito_service, geocode_service
from app.core.exceptions import not_found

router = APIRouter(prefix="/remitos", tags=["remitos"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _resolve_carrier_name(db: AsyncSession, carrier_id: Optional[int]) -> Optional[str]:
    if not carrier_id:
        return None
    result = await db.execute(select(Carrier).where(Carrier.id == carrier_id))
    c = result.scalar_one_or_none()
    return c.nombre_canonico if c else None


def _to_response(r: Remito, carrier_nombre: Optional[str] = None) -> dict:
    return {
        "id": r.id,
        "numero": r.numero,
        "cliente": r.cliente,
        "telefono": r.telefono,
        "direccion_raw": r.direccion_raw,
        "direccion_normalizada": r.direccion_normalizada,
        "localidad": r.localidad,
        "observaciones": r.observaciones,
        "estado_clasificacion": r.estado_clasificacion,
        "motivo_clasificacion": r.motivo_clasificacion,
        "estado_lifecycle": r.estado_lifecycle,
        "carrier_id": r.carrier_id,
        "carrier_nombre": carrier_nombre,
        "lat": r.lat,
        "lng": r.lng,
        "geocode_formatted": r.geocode_formatted,
        "geocode_provider": r.geocode_provider,
        "geocode_score": r.geocode_score,
        "ventana_tipo": r.ventana_tipo,
        "ventana_desde_min": r.ventana_desde_min,
        "ventana_hasta_min": r.ventana_hasta_min,
        "es_urgente": r.es_urgente,
        "es_prioridad": r.es_prioridad,
        "llamar_antes": r.llamar_antes,
        "source": r.source,
        "fecha_ingreso": r.fecha_ingreso,
        "fecha_armado": r.fecha_armado,
        "fecha_entregado": r.fecha_entregado,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/ingest", response_model=IngestResponse)
async def ingest_remitos(
    body: RemitoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador),
):
    """Ingesta batch de números de remitos."""
    result = await remito_service.ingest_batch(db, body.remitos, source=body.source)
    return IngestResponse(
        ok=result.ok,
        total=result.total,
        nuevos=result.nuevos,
        duplicados=result.duplicados,
        errores=result.errores,
    )


@router.post("/", response_model=dict)
async def create_remito(
    body: RemitoSingleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador),
):
    """Crea un único remito con todos sus datos."""
    # Verificar duplicado
    existing = await db.execute(select(Remito).where(Remito.numero == body.numero.upper()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Remito {body.numero} ya existe")

    remito = Remito(
        numero=body.numero.upper(),
        cliente=body.cliente,
        telefono=body.telefono,
        direccion_raw=body.domicilio,
        localidad=body.localidad,
        observaciones=body.observaciones,
        es_urgente=body.es_urgente,
        es_prioridad=body.es_prioridad,
        llamar_antes=body.llamar_antes,
        source=body.source,
        estado_clasificacion=RemitoEstadoClasificacion.pendiente.value,
        estado_lifecycle=RemitoEstadoLifecycle.ingresado.value,
    )
    db.add(remito)
    await db.flush()
    await remito_service.process_pipeline(db, remito)
    await db.commit()
    await db.refresh(remito)

    carrier_nombre = await _resolve_carrier_name(db, remito.carrier_id)
    return _to_response(remito, carrier_nombre)


@router.get("/", response_model=PaginatedResponse)
async def list_remitos(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    estado: Optional[str] = Query(None),
    lifecycle: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista remitos con paginación y filtros."""
    stmt = select(Remito)
    if estado:
        stmt = stmt.where(Remito.estado_clasificacion == estado)
    if lifecycle:
        stmt = stmt.where(Remito.estado_lifecycle == lifecycle)
    if q:
        stmt = stmt.where(
            Remito.numero.ilike(f"%{q}%") | Remito.cliente.ilike(f"%{q}%")
        )

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()

    stmt = stmt.order_by(Remito.fecha_ingreso.desc()).offset((page - 1) * size).limit(size)
    rows = (await db.execute(stmt)).scalars().all()

    items = []
    for r in rows:
        cn = await _resolve_carrier_name(db, r.carrier_id)
        items.append(_to_response(r, cn))

    return PaginatedResponse(
        items=items, total=total, page=page, size=size,
        pages=(total + size - 1) // size,
    )


@router.get("/{remito_id}", response_model=dict)
async def get_remito(
    remito_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(Remito).where(Remito.id == remito_id))
    remito = result.scalar_one_or_none()
    if not remito:
        raise not_found("Remito")
    cn = await _resolve_carrier_name(db, remito.carrier_id)
    return _to_response(remito, cn)


@router.get("/numero/{numero}", response_model=dict)
async def get_remito_by_numero(
    numero: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    result = await db.execute(select(Remito).where(Remito.numero == numero.upper()))
    remito = result.scalar_one_or_none()
    if not remito:
        raise not_found("Remito")
    cn = await _resolve_carrier_name(db, remito.carrier_id)
    return _to_response(remito, cn)


@router.put("/{remito_id}", response_model=dict)
async def update_remito(
    remito_id: int = Path(...),
    body: RemitoUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador),
):
    result = await db.execute(select(Remito).where(Remito.id == remito_id))
    remito = result.scalar_one_or_none()
    if not remito:
        raise not_found("Remito")

    if body.direccion_raw is not None:
        remito.direccion_raw = body.direccion_raw
    if body.es_urgente is not None:
        remito.es_urgente = body.es_urgente
    if body.es_prioridad is not None:
        remito.es_prioridad = body.es_prioridad
    if body.observaciones is not None:
        remito.observaciones = body.observaciones
    if body.llamar_antes is not None:
        remito.llamar_antes = body.llamar_antes

    await db.commit()
    await db.refresh(remito)
    cn = await _resolve_carrier_name(db, remito.carrier_id)
    return _to_response(remito, cn)


@router.post("/{remito_id}/corregir-direccion", response_model=dict)
async def corregir_direccion(
    remito_id: int = Path(...),
    body: DireccionCorreccion = ...,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador),
):
    """Corrige la dirección de un remito y re-geocodifica."""
    result = await db.execute(select(Remito).where(Remito.id == remito_id))
    remito = result.scalar_one_or_none()
    if not remito:
        raise not_found("Remito")

    remito.direccion_raw = body.direccion_nueva
    remito.direccion_normalizada = None
    remito.lat = None
    remito.lng = None
    remito.geocode_provider = None
    remito.geocode_score = None
    remito.estado_clasificacion = RemitoEstadoClasificacion.pendiente.value
    remito.motivo_clasificacion = "Dirección corregida manualmente"

    await remito_service.process_pipeline(db, remito)
    await db.commit()
    await db.refresh(remito)
    cn = await _resolve_carrier_name(db, remito.carrier_id)
    return _to_response(remito, cn)


@router.post("/{remito_id}/reclasificar", response_model=dict)
async def reclasificar(
    remito_id: int = Path(...),
    body: ClasificacionUpdate = ...,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador),
):
    """Sobreescribe la clasificación manualmente."""
    result = await db.execute(select(Remito).where(Remito.id == remito_id))
    remito = result.scalar_one_or_none()
    if not remito:
        raise not_found("Remito")

    remito.estado_clasificacion = body.estado
    remito.motivo_clasificacion = body.motivo or "Clasificación manual"
    await db.commit()
    await db.refresh(remito)
    cn = await _resolve_carrier_name(db, remito.carrier_id)
    return _to_response(remito, cn)


@router.post("/procesar-pendientes", response_model=OkResponse)
async def procesar_pendientes(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador),
):
    """Lanza el pipeline en todos los remitos con estado 'pendiente'."""
    count = await remito_service.process_pending(db)
    return OkResponse(message=f"{count} remitos procesados")


@router.post("/{remito_id}/armar", response_model=dict)
async def armar_remito(
    remito_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador),
):
    """Marca el remito como 'armado' (listo para ruta) y clasificación 'enviar'."""
    result = await db.execute(select(Remito).where(Remito.id == remito_id))
    remito = result.scalar_one_or_none()
    if not remito:
        raise not_found("Remito")

    from datetime import datetime, timezone
    remito.estado_lifecycle = RemitoEstadoLifecycle.armado.value
    remito.estado_clasificacion = RemitoEstadoClasificacion.enviar.value
    remito.fecha_armado = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(remito)
    cn = await _resolve_carrier_name(db, remito.carrier_id)
    return _to_response(remito, cn)


@router.delete("/{remito_id}", response_model=OkResponse, dependencies=[Depends(require_operador)])
async def delete_remito(
    remito_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Remito).where(Remito.id == remito_id))
    remito = result.scalar_one_or_none()
    if not remito:
        raise not_found("Remito")
    await db.delete(remito)
    await db.commit()
    return OkResponse(message=f"Remito {remito.numero} eliminado")
