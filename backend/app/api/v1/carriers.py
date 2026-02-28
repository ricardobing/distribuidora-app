from fastapi import APIRouter, Depends, Path, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user, require_admin
from app.models.carrier import Carrier
from app.models.usuario import Usuario
from app.schemas.carrier import (
    CarrierCreate, CarrierUpdate, CarrierResponse,
    CarrierDetectRequest, CarrierDetectResponse
)
from app.schemas.common import OkResponse
from app.services.carrier_service import detect
from app.core.exceptions import not_found, bad_request

router = APIRouter(prefix="/carriers", tags=["carriers"])


@router.get("/", response_model=list[CarrierResponse])
async def list_carriers(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    result = await db.execute(select(Carrier).order_by(Carrier.prioridad_regex, Carrier.nombre_canonico))
    return result.scalars().all()


@router.post("/", response_model=CarrierResponse, dependencies=[Depends(require_admin)])
async def create_carrier(body: CarrierCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(Carrier).where(Carrier.nombre_canonico == body.nombre_canonico)
    )
    if existing.scalar_one_or_none():
        raise bad_request(f"Carrier '{body.nombre_canonico}' ya existe")
    carrier = Carrier(
        nombre_canonico=body.nombre_canonico,
        aliases=body.aliases,
        regex_pattern=body.regex_pattern,
        es_externo=body.es_externo,
        es_pickup=body.es_pickup,
        prioridad_regex=body.prioridad_regex
    )
    db.add(carrier)
    await db.commit()
    await db.refresh(carrier)
    return carrier


@router.get("/{carrier_id}", response_model=CarrierResponse)
async def get_carrier(
    carrier_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    result = await db.execute(select(Carrier).where(Carrier.id == carrier_id))
    carrier = result.scalar_one_or_none()
    if not carrier:
        raise not_found("Carrier")
    return carrier


@router.put("/{carrier_id}", response_model=CarrierResponse, dependencies=[Depends(require_admin)])
async def update_carrier(
    carrier_id: int = Path(...),
    body: CarrierUpdate = Body(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Carrier).where(Carrier.id == carrier_id))
    carrier = result.scalar_one_or_none()
    if not carrier:
        raise not_found("Carrier")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(carrier, field, value)
    await db.commit()
    await db.refresh(carrier)
    return carrier


@router.delete("/{carrier_id}", response_model=OkResponse, dependencies=[Depends(require_admin)])
async def delete_carrier(carrier_id: int = Path(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Carrier).where(Carrier.id == carrier_id))
    carrier = result.scalar_one_or_none()
    if not carrier:
        raise not_found("Carrier")
    await db.delete(carrier)
    await db.commit()
    return OkResponse(message=f"Carrier {carrier_id} eliminado")


@router.post("/detect", response_model=CarrierDetectResponse)
async def detect_carrier(
    body: CarrierDetectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    detection = await detect(db, body.texto, provincia="Mendoza")
    return CarrierDetectResponse(
        carrier=detection.carrier,
        confidence=detection.confidence,
        source=detection.source
    )
