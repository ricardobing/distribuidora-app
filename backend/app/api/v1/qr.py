from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models.usuario import Usuario
from app.services.delivery_service import scan_qr, mark_entregado, move_to_historico
from app.schemas.common import OkResponse
from app.core.exceptions import not_found, bad_request

router = APIRouter(prefix="/qr", tags=["qr"])


@router.get("/scan")
async def scan_get(
    numero: str = Query(..., description="Número de remito del QR"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Escanea un QR y retorna el resultado."""
    result = await scan_qr(db, numero)
    return result


@router.post("/scan")
async def scan_post(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Escanea un QR por POST (body: {numero: str})."""
    numero = body.get("numero", "").strip()
    if not numero:
        raise bad_request("numero requerido")
    result = await scan_qr(db, numero)
    return result


@router.post("/scan-batch")
async def scan_batch(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Escanea múltiples QRs (body: {numeros: [str]})."""
    numeros = body.get("numeros", [])
    results = []
    for numero in numeros:
        try:
            r = await scan_qr(db, str(numero).strip())
            results.append(r)
        except Exception as e:
            results.append({"numero": numero, "error": str(e)})
    return {"results": results, "total": len(results)}
