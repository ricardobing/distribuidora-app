from fastapi import APIRouter, Depends, Query, Path
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies import get_db, get_current_user, require_operador
from app.models.historico import HistoricoEntregado
from app.models.usuario import Usuario
from app.schemas.common import PaginatedResponse, OkResponse
from app.services.delivery_service import restore_from_historico
from app.services.export_service import export_historico_xlsx, monthly_close
from app.core.exceptions import not_found
from typing import Optional

router = APIRouter(prefix="/historico", tags=["historico"])


@router.get("/", response_model=PaginatedResponse)
async def list_historico(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    mes: Optional[str] = Query(None, description="YYYY-MM"),
    q: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    stmt = select(HistoricoEntregado)
    if mes:
        stmt = stmt.where(HistoricoEntregado.mes_cierre == mes)
    if q:
        stmt = stmt.where(
            HistoricoEntregado.numero.ilike(f"%{q}%") |
            HistoricoEntregado.cliente.ilike(f"%{q}%")
        )
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(total_stmt)).scalar_one()
    stmt = stmt.order_by(HistoricoEntregado.fecha_entregado.desc()).offset((page - 1) * size).limit(size)
    items = (await db.execute(stmt)).scalars().all()

    return PaginatedResponse(
        items=[_to_dict(h) for h in items],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size
    )


@router.get("/export/{mes}")
async def export_mes(
    mes: str = Path(..., description="YYYY-MM"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Exporta el histórico de un mes como XLSX."""
    data = await export_historico_xlsx(db, mes)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=historico_{mes}.xlsx"}
    )


@router.post("/restaurar/{historico_id}", response_model=OkResponse)
async def restaurar(
    historico_id: int = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
):
    """Restaura un remito desde el histórico a estado activo."""
    await restore_from_historico(db, historico_id)
    return OkResponse(message="Remito restaurado al estado activo")


@router.post("/cierre-mensual", response_model=OkResponse)
async def cierre_mensual(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_operador)
):
    """Ejecuta el cierre mensual: mueve todos los entregados al histórico."""
    count = await monthly_close(db)
    return OkResponse(message=f"Cierre mensual completado: {count} remitos archivados")


def _to_dict(h: HistoricoEntregado) -> dict:
    return {
        "id": h.id,
        "numero": h.numero,
        "cliente": h.cliente,
        "direccion": h.direccion_snapshot,
        "localidad": h.localidad,
        "fecha_entregado": str(h.fecha_entregado) if h.fecha_entregado else None,
        "mes_cierre": h.mes_cierre,
        "carrier_nombre": h.carrier_nombre,
        "observaciones": h.observaciones,
    }
