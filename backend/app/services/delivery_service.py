"""
Delivery service: marca remitos como entregados / mueve a histórico.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.remito import Remito, RemitoEstadoLifecycle
from app.models.ruta import RutaParada, ParadaEstado
from app.models.historico import HistoricoEntregado
from app.models.carrier import Carrier

logger = logging.getLogger(__name__)


async def scan_qr(db: AsyncSession, numero: str) -> dict:
    """Escanea QR: busca remito por número y retorna estado."""
    result = await db.execute(select(Remito).where(Remito.numero == numero.upper()))
    remito = result.scalar_one_or_none()
    if remito is None:
        return {"encontrado": False, "numero": numero, "mensaje": "Remito no encontrado"}

    carrier_nombre = None
    if remito.carrier_id:
        cres = await db.execute(select(Carrier).where(Carrier.id == remito.carrier_id))
        c = cres.scalar_one_or_none()
        carrier_nombre = c.nombre_canonico if c else None

    return {
        "encontrado": True,
        "id": remito.id,
        "numero": remito.numero,
        "cliente": remito.cliente,
        "direccion": remito.direccion_normalizada or remito.direccion_raw,
        "estado_lifecycle": remito.estado_lifecycle,
        "estado_clasificacion": remito.estado_clasificacion,
        "carrier_nombre": carrier_nombre,
        "es_urgente": remito.es_urgente,
        "es_prioridad": remito.es_prioridad,
        "lat": remito.lat,
        "lng": remito.lng,
    }


async def mark_entregado(db: AsyncSession, ids: list[int]) -> int:
    """
    Marca un lote de remitos como entregados.
    Actualiza estado_lifecycle → 'entregado' y la parada activa → 'entregada'.
    Retorna cantidad procesada.
    """
    count = 0
    now = datetime.now(timezone.utc)

    for remito_id in ids:
        result = await db.execute(select(Remito).where(Remito.id == remito_id))
        remito = result.scalar_one_or_none()
        if not remito:
            continue

        remito.estado_lifecycle = RemitoEstadoLifecycle.entregado.value
        remito.fecha_entregado = now

        # Actualizar parada activa si existe
        parada_res = await db.execute(
            select(RutaParada).where(
                RutaParada.remito_id == remito_id,
                RutaParada.estado == ParadaEstado.pendiente.value,
            ).order_by(RutaParada.id.desc()).limit(1)
        )
        parada = parada_res.scalar_one_or_none()
        if parada:
            parada.estado = ParadaEstado.entregada.value

        count += 1

    await db.commit()
    return count


async def move_to_historico(db: AsyncSession, ids: list[int]) -> int:
    """
    Mueve remitos entregados al histórico.
    Crea HistoricoEntregado y actualiza estado_lifecycle → 'historico'.
    """
    count = 0
    now = datetime.now(timezone.utc)
    mes_cierre = now.strftime("%Y-%m")

    for remito_id in ids:
        result = await db.execute(select(Remito).where(Remito.id == remito_id))
        remito = result.scalar_one_or_none()
        if not remito:
            continue

        carrier_nombre = None
        if remito.carrier_id:
            cres = await db.execute(select(Carrier).where(Carrier.id == remito.carrier_id))
            c = cres.scalar_one_or_none()
            carrier_nombre = c.nombre_canonico if c else None

        fecha_entregado = remito.fecha_entregado or now

        historico = HistoricoEntregado(
            remito_id=remito.id,
            numero=remito.numero,
            cliente=remito.cliente or "",
            direccion_snapshot=remito.direccion_normalizada or remito.direccion_raw or "",
            localidad=remito.localidad,
            observaciones=remito.observaciones or "",
            lat=remito.lat,
            lng=remito.lng,
            carrier_nombre=carrier_nombre,
            es_urgente=remito.es_urgente,
            es_prioridad=remito.es_prioridad,
            obs_entrega="",
            estado_al_archivar=remito.estado_lifecycle,
            fecha_ingreso=remito.fecha_ingreso,
            fecha_armado=remito.fecha_armado,
            fecha_entregado=fecha_entregado,
            mes_cierre=mes_cierre,
        )
        db.add(historico)

        remito.estado_lifecycle = RemitoEstadoLifecycle.historico.value
        remito.fecha_historico = now
        count += 1

    await db.commit()
    return count


async def restore_from_historico(db: AsyncSession, historico_id: int) -> None:
    """Restaura un remito del histórico a estado activo (ingresado)."""
    result = await db.execute(
        select(HistoricoEntregado).where(HistoricoEntregado.id == historico_id)
    )
    historico = result.scalar_one_or_none()
    if not historico:
        raise ValueError(f"Histórico {historico_id} no encontrado")

    if historico.remito_id:
        rres = await db.execute(select(Remito).where(Remito.id == historico.remito_id))
        remito = rres.scalar_one_or_none()
        if remito:
            remito.estado_lifecycle = RemitoEstadoLifecycle.ingresado.value
            remito.fecha_entregado = None
            remito.fecha_historico = None

    await db.delete(historico)
    await db.commit()
