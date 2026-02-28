from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta

from app.dependencies import get_db, get_current_user
from app.models.remito import Remito, RemitoEstadoClasificacion, RemitoEstadoLifecycle
from app.models.historico import HistoricoEntregado
from app.models.ruta import Ruta
from app.models.usuario import Usuario
from app.models.billing import BillingTrace
from typing import Optional

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    today = date.today()

    # Total remitos por estado clasificacion
    remitos_by_clasificacion = await db.execute(
        select(Remito.estado_clasificacion, func.count().label("cnt"))
        .group_by(Remito.estado_clasificacion)
    )
    clasificacion_counts = {row.estado_clasificacion: row.cnt for row in remitos_by_clasificacion}

    # Total remitos por estado lifecycle
    remitos_by_lifecycle = await db.execute(
        select(Remito.estado_lifecycle, func.count().label("cnt"))
        .group_by(Remito.estado_lifecycle)
    )
    lifecycle_counts = {row.estado_lifecycle: row.cnt for row in remitos_by_lifecycle}

    # Histórico del mes actual
    mes_actual = today.strftime("%Y-%m")
    historico_mes = (await db.execute(
        select(func.count()).select_from(HistoricoEntregado)
        .where(HistoricoEntregado.mes_cierre == mes_actual)
    )).scalar_one()

    # Última ruta
    ultima_ruta = (await db.execute(
        select(Ruta).order_by(Ruta.created_at.desc()).limit(1)
    )).scalar_one_or_none()

    # Pendientes urgentes
    urgentes = (await db.execute(
        select(func.count()).select_from(Remito)
        .where(
            Remito.es_urgente == True,
            Remito.estado_lifecycle == RemitoEstadoLifecycle.ingresado
        )
    )).scalar_one()

    return {
        "today": str(today),
        "remitos": {
            "by_clasificacion": clasificacion_counts,
            "by_lifecycle": lifecycle_counts,
            "urgentes_pendientes": urgentes,
        },
        "historico_mes_actual": historico_mes,
        "ultima_ruta": {
            "id": ultima_ruta.id if ultima_ruta else None,
            "fecha": str(ultima_ruta.fecha) if ultima_ruta else None,
            "estado": ultima_ruta.estado if ultima_ruta else None,
            "total_paradas": ultima_ruta.total_paradas if ultima_ruta else None,
        } if ultima_ruta else None,
    }


@router.get("/stats/costos")
async def get_costos(
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Resumen de costos de API de los últimos N días."""
    since = date.today() - timedelta(days=days)
    result = await db.execute(
        select(
            BillingTrace.service,
            func.sum(BillingTrace.estimated_cost).label("total_cost"),
            func.sum(BillingTrace.units).label("total_units"),
            func.count().label("calls")
        )
        .where(func.date(BillingTrace.created_at) >= since)
        .group_by(BillingTrace.service)
        .order_by(func.sum(BillingTrace.estimated_cost).desc())
    )
    rows = result.all()
    total_cost = sum(r.total_cost or 0 for r in rows)
    return {
        "period_days": days,
        "total_cost_usd": round(total_cost, 4),
        "by_service": [
            {
                "service": r.service,
                "total_cost_usd": round(r.total_cost or 0, 4),
                "total_units": r.total_units,
                "calls": r.calls,
            }
            for r in rows
        ]
    }


@router.get("/stats/entregas")
async def get_entregas(
    months: int = Query(3, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Estadísticas de entregas por mes."""
    result = await db.execute(
        select(
            HistoricoEntregado.mes_cierre,
            func.count().label("total"),
        )
        .group_by(HistoricoEntregado.mes_cierre)
        .order_by(HistoricoEntregado.mes_cierre.desc())
        .limit(months)
    )
    rows = result.all()
    return {
        "months": months,
        "data": [{"mes": r.mes_cierre, "total_entregas": r.total} for r in rows]
    }
