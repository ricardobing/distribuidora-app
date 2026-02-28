from fastapi import APIRouter, Depends, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_operador
from app.models.usuario import Usuario
from app.services.delivery_service import mark_entregado, move_to_historico, scan_qr
from app.schemas.common import OkResponse

router = APIRouter(prefix="/entregados", tags=["entregados"])


@router.get("/qr/{numero}", response_model=dict)
async def scan_qr_remito(
    numero: str = Path(..., description="Número de remito a escanear"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Escanea QR y retorna el estado actual del remito."""
    return await scan_qr(db, numero)


@router.post("/marcar", response_model=OkResponse)
async def marcar_entregados(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador),
):
    """Marca remitos como entregados. body: {ids: [int]} o {remito_ids: [int]}"""
    ids = body.get("ids") or body.get("remito_ids", [])
    count = await mark_entregado(db, ids)
    return OkResponse(message=f"{count} remitos marcados como entregados")


@router.post("/procesar", response_model=OkResponse)
async def procesar_entregados(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador),
):
    """Mueve remitos entregados al histórico. body: {ids: [int]} o {remito_ids: [int]}"""
    ids = body.get("ids") or body.get("remito_ids", [])
    count = await move_to_historico(db, ids)
    return OkResponse(message=f"{count} remitos movidos al histórico")
