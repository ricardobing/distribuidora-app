"""
Router de dashboard: KPIs y estadísticas del día.
"""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies import get_db, get_current_user
from app.models.remito import Remito, RemitoEstadoClasificacion, RemitoEstadoLifecycle
from app.models.ruta import Ruta, RutaParada
from app.models.historico import HistoricoEntregado
from app.models.usuario import Usuario

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/")
async def dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """KPIs principales del sistema."""
    today = date.today()
    mes_actual = today.strftime("%Y-%m")

    # Remitos activos por estado de clasificación
    clasificacion_rows = await db.execute(
        select(Remito.estado_clasificacion, func.count(Remito.id))
        .group_by(Remito.estado_clasificacion)
    )
    clasificacion = {k: v for k, v in clasificacion_rows.all()}

    # Remitos activos por lifecycle
    lifecycle_rows = await db.execute(
        select(Remito.estado_lifecycle, func.count(Remito.id))
        .group_by(Remito.estado_lifecycle)
    )
    lifecycle = {k: v for k, v in lifecycle_rows.all()}

    # Remitos urgentes y prioridad activos
    urgentes = (await db.execute(
        select(func.count(Remito.id)).where(
            Remito.es_urgente == True,
            Remito.estado_lifecycle != RemitoEstadoLifecycle.historico.value,
        )
    )).scalar_one()

    prioridad = (await db.execute(
        select(func.count(Remito.id)).where(
            Remito.es_prioridad == True,
            Remito.estado_lifecycle != RemitoEstadoLifecycle.historico.value,
        )
    )).scalar_one()

    # Ruta del día
    ruta_hoy = (await db.execute(
        select(Ruta).where(Ruta.fecha == today).order_by(Ruta.id.desc()).limit(1)
    )).scalar_one_or_none()

    ruta_info = None
    if ruta_hoy:
        paradas_completadas = (await db.execute(
            select(func.count(RutaParada.id)).where(
                RutaParada.ruta_id == ruta_hoy.id,
                RutaParada.estado == "entregada",
            )
        )).scalar_one()
        ruta_info = {
            "id": ruta_hoy.id,
            "estado": ruta_hoy.estado,
            "total_paradas": ruta_hoy.total_paradas,
            "paradas_completadas": paradas_completadas,
            "total_excluidos": ruta_hoy.total_excluidos,
            "duracion_estimada_min": ruta_hoy.duracion_estimada_min,
            "distancia_total_km": ruta_hoy.distancia_total_km,
        }

    # Histórico del mes actual
    historico_mes = (await db.execute(
        select(func.count(HistoricoEntregado.id)).where(
            HistoricoEntregado.mes_cierre == mes_actual
        )
    )).scalar_one()

    # Entregas hoy (en histórico con fecha_entregado = hoy)
    entregados_hoy = (await db.execute(
        select(func.count(HistoricoEntregado.id)).where(
            func.date(HistoricoEntregado.fecha_entregado) == today
        )
    )).scalar_one()

    return {
        "fecha": str(today),
        "mes": mes_actual,
        "remitos": {
            "por_clasificacion": clasificacion,
            "por_lifecycle": lifecycle,
            "urgentes": urgentes,
            "prioridad": prioridad,
            "total_activos": sum(
                v for k, v in lifecycle.items()
                if k != RemitoEstadoLifecycle.historico.value
            ),
        },
        "ruta_hoy": ruta_info,
        "historico": {
            "entregas_hoy": entregados_hoy,
            "entregas_mes_actual": historico_mes,
        },
    }


@router.get("/stats/geocoding")
async def geocoding_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Estadísticas del geocoding: cobertura, proveedores, score promedio."""
    total = (await db.execute(
        select(func.count(Remito.id)).where(
            Remito.estado_lifecycle != RemitoEstadoLifecycle.historico.value
        )
    )).scalar_one()

    geocodificados = (await db.execute(
        select(func.count(Remito.id)).where(
            Remito.lat.isnot(None),
            Remito.estado_lifecycle != RemitoEstadoLifecycle.historico.value,
        )
    )).scalar_one()

    providers = (await db.execute(
        select(Remito.geocode_provider, func.count(Remito.id))
        .where(Remito.lat.isnot(None))
        .group_by(Remito.geocode_provider)
    )).all()

    avg_score = (await db.execute(
        select(func.avg(Remito.geocode_score)).where(Remito.geocode_score.isnot(None))
    )).scalar_one()

    return {
        "total_remitos": total,
        "geocodificados": geocodificados,
        "sin_geocodificar": total - geocodificados,
        "cobertura_pct": round((geocodificados / total * 100) if total else 0, 1),
        "por_proveedor": {k or "desconocido": v for k, v in providers},
        "score_promedio": round(float(avg_score or 0), 3),
    }
