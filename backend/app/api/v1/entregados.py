from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_operador
from app.models.usuario import Usuario
from app.services.delivery_service import mark_entregado, move_to_historico
from app.schemas.common import OkResponse

router = APIRouter(prefix="/entregados", tags=["entregados"])


@router.post("/marcar", response_model=OkResponse)
async def marcar_entregados(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
):
    """Marca remitos como entregados. body: {remito_ids: [int]}"""
    ids = body.get("remito_ids", [])
    count = await mark_entregado(db, ids)
    return OkResponse(message=f"{count} remitos marcados como entregados")


@router.post("/procesar", response_model=OkResponse)
async def procesar_entregados(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
):
    """Mueve remitos entregados al histórico. body: {remito_ids: [int]}"""
    ids = body.get("remito_ids", [])
    count = await move_to_historico(db, ids)
    return OkResponse(message=f"{count} remitos movidos al histórico")
