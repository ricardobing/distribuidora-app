from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.dependencies import get_db, get_current_user, require_operador
from app.models.pedido_listo import PedidoListo
from app.models.usuario import Usuario
from app.schemas.common import OkResponse, PaginatedResponse
from app.services.pedidos_listos_service import sync_batch
import csv
import io

router = APIRouter(prefix="/pedidos-listos", tags=["pedidos_listos"])


@router.post("/sync", response_model=OkResponse)
async def sync_pedidos(
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
):
    """Sincroniza datos de Pedidos Listos desde la hoja de cálculo. body: {data: []}"""
    data = body.get("data", [])
    count = await sync_batch(db, data)
    return OkResponse(message=f"{count} pedidos sincronizados")


@router.post("/upload-csv", response_model=OkResponse)
async def upload_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
):
    """Carga datos de pedidos listos desde CSV."""
    content = await file.read()
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    data = [row for row in reader]
    count = await sync_batch(db, data)
    return OkResponse(message=f"{count} pedidos cargados desde CSV")


@router.get("/", response_model=PaginatedResponse)
async def list_pedidos(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    from sqlalchemy import func
    stmt = select(PedidoListo).order_by(PedidoListo.created_at.desc())
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()
    stmt = stmt.offset((page - 1) * size).limit(size)
    items = (await db.execute(stmt)).scalars().all()
    return PaginatedResponse(
        items=[{
            "id": p.id,
            "numero_remito": p.numero_remito,
            "raw_data": p.raw_data,
            "linked_remito_id": p.linked_remito_id,
            "created_at": str(p.created_at) if p.created_at else None,
        } for p in items],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )
