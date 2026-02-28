from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct

from app.dependencies import get_db, get_current_user, require_admin
from app.models.billing import BillingTrace
from app.models.usuario import Usuario
from app.schemas.common import PaginatedResponse
from typing import Optional

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/", response_model=PaginatedResponse)
async def list_billing(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    service: Optional[str] = Query(None),
    run_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(BillingTrace)
    if service:
        stmt = stmt.where(BillingTrace.service == service)
    if run_id:
        stmt = stmt.where(BillingTrace.run_id == run_id)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()
    stmt = stmt.order_by(BillingTrace.created_at.desc()).offset((page - 1) * size).limit(size)
    items = (await db.execute(stmt)).scalars().all()

    return PaginatedResponse(
        items=[{
            "id": b.id,
            "run_id": b.run_id,
            "stage": b.stage,
            "service": b.service,
            "sku": b.sku,
            "units": b.units,
            "estimated_cost": b.estimated_cost,
            "created_at": str(b.created_at) if b.created_at else None,
        } for b in items],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/summary")
async def billing_summary(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    result = await db.execute(
        select(
            BillingTrace.service,
            BillingTrace.sku,
            func.sum(BillingTrace.estimated_cost).label("total_cost"),
            func.sum(BillingTrace.units).label("total_units"),
            func.count().label("calls"),
        )
        .group_by(BillingTrace.service, BillingTrace.sku)
        .order_by(func.sum(BillingTrace.estimated_cost).desc())
    )
    rows = result.all()
    grand_total = sum(r.total_cost or 0 for r in rows)
    return {
        "grand_total_usd": round(grand_total, 6),
        "by_service_sku": [
            {
                "service": r.service,
                "sku": r.sku,
                "total_cost_usd": round(r.total_cost or 0, 6),
                "total_units": r.total_units,
                "calls": r.calls,
            }
            for r in rows
        ]
    }
