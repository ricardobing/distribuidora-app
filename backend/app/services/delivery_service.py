"""
Delivery service: ARMADO → ENTREGADO → HISTÓRICO.
Migra: QR handlers, procesarEntregadosDesdeMenu(), movimiento a HISTÓRICO_ENTREGADOS.
"""
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.remito import Remito, RemitoEstadoLifecycle
from app.models.historico import HistoricoEntregado
from app.models.carrier import Carrier
from app.core.constants import CODE_VERSION

logger = logging.getLogger(__name__)


@dataclass
class QRResult:
    ok: bool
    remito: str
    message: str
    version: str = CODE_VERSION


@dataclass
class EntregadoResult:
    ok: bool
    procesados: int
    rechazados: list[dict]


@dataclass
class HistoricoResult:
    ok: bool
    movidos: int
    rechazados: list[dict]


async def scan_qr(db: AsyncSession, numero: str) -> QRResult:
    """
    Procesa un escaneo QR: marca el remito como ARMADO.
    Idempotente: re-escaneo devuelve "Ya estaba ARMADO".
    DESPACHADO no retrocede.
    Migra: _procesarUnRemito_() del sistema original.
    """
    numero = numero.strip().upper()
    result = await db.execute(
        select(Remito).where(Remito.numero == numero)
    )
    remito = result.scalar_one_or_none()

    if not remito:
        return QRResult(ok=False, remito=numero, message=f"Remito {numero} no encontrado")

    lifecycle = remito.estado_lifecycle

    if lifecycle == RemitoEstadoLifecycle.armado.value:
        return QRResult(ok=True, remito=numero, message=f"Remito {numero} ya estaba ARMADO")

    if lifecycle in (
        RemitoEstadoLifecycle.despachado.value,
        RemitoEstadoLifecycle.entregado.value,
        RemitoEstadoLifecycle.historico.value,
    ):
        return QRResult(
            ok=False,
            remito=numero,
            message=f"Remito {numero} en estado {lifecycle.upper()}, no puede retroceder",
        )

    prev_state = lifecycle
    remito.estado_lifecycle = RemitoEstadoLifecycle.armado.value
    remito.fecha_armado = datetime.now(timezone.utc)
    remito.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return QRResult(
        ok=True,
        remito=numero,
        message=f"Remito {numero} marcado como ARMADO (antes: {prev_state.upper()})",
    )


async def mark_entregado(
    db: AsyncSession, remito_ids: list[int]
) -> EntregadoResult:
    """
    Marca remitos como ENTREGADO.
    Requiere que estén en estado ARMADO.
    """
    procesados = 0
    rechazados = []

    for rid in remito_ids:
        result = await db.execute(select(Remito).where(Remito.id == rid))
        remito = result.scalar_one_or_none()
        if not remito:
            rechazados.append({"id": rid, "motivo": "No encontrado"})
            continue
        if remito.estado_lifecycle != RemitoEstadoLifecycle.armado.value:
            rechazados.append({
                "id": rid,
                "numero": remito.numero,
                "motivo": f"Estado actual: {remito.estado_lifecycle} (requiere ARMADO)",
            })
            continue
        remito.estado_lifecycle = RemitoEstadoLifecycle.entregado.value
        remito.fecha_entregado = datetime.now(timezone.utc)
        remito.updated_at = datetime.now(timezone.utc)
        procesados += 1

    await db.commit()
    return EntregadoResult(ok=True, procesados=procesados, rechazados=rechazados)


async def move_to_historico(
    db: AsyncSession, remito_ids: list[int]
) -> HistoricoResult:
    """
    Mueve remitos ENTREGADOS al histórico.
    Crea snapshot en historico_entregados y cambia estado a 'historico'.
    """
    movidos = 0
    rechazados = []
    now = datetime.now(timezone.utc)
    mes_cierre = now.strftime("%Y-%m")

    for rid in remito_ids:
        result = await db.execute(select(Remito).where(Remito.id == rid))
        remito = result.scalar_one_or_none()
        if not remito:
            rechazados.append({"id": rid, "motivo": "No encontrado"})
            continue
        if remito.estado_lifecycle != RemitoEstadoLifecycle.entregado.value:
            rechazados.append({
                "id": rid,
                "numero": remito.numero,
                "motivo": f"Estado actual: {remito.estado_lifecycle} (requiere ENTREGADO)",
            })
            continue

        # Obtener carrier nombre
        carrier_nombre = None
        if remito.carrier_id:
            c_result = await db.execute(select(Carrier).where(Carrier.id == remito.carrier_id))
            carrier = c_result.scalar_one_or_none()
            carrier_nombre = carrier.nombre_canonico if carrier else None

        historico = HistoricoEntregado(
            remito_id=remito.id,
            numero_remito=remito.numero,
            cliente=remito.cliente,
            domicilio=remito.domicilio_normalizado,
            provincia=remito.provincia,
            observaciones=remito.observaciones_pl,
            carrier_nombre=carrier_nombre,
            estado_al_archivar=remito.estado_lifecycle,
            geom=remito.geom,
            urgente=remito.urgente,
            prioridad=remito.prioridad,
            obs_entrega=remito.observaciones_entrega,
            transp_json=remito.transp_json,
            fecha_ingreso=remito.fecha_ingreso,
            fecha_armado=remito.fecha_armado,
            fecha_entregado=remito.fecha_entregado or now,
            fecha_archivado=now,
            mes_cierre=mes_cierre,
        )
        db.add(historico)
        remito.estado_lifecycle = RemitoEstadoLifecycle.historico.value
        remito.fecha_historico = now
        remito.updated_at = now
        movidos += 1

    await db.commit()
    return HistoricoResult(ok=True, movidos=movidos, rechazados=rechazados)


async def restore_from_historico(
    db: AsyncSession, historico_id: int
) -> Optional[Remito]:
    """Restaura un remito del histórico a estado activo (ingresado)."""
    result = await db.execute(
        select(HistoricoEntregado).where(HistoricoEntregado.id == historico_id)
    )
    hist = result.scalar_one_or_none()
    if not hist:
        return None

    result2 = await db.execute(
        select(Remito).where(Remito.id == hist.remito_id)
    )
    remito = result2.scalar_one_or_none()
    if not remito:
        return None

    remito.estado_lifecycle = RemitoEstadoLifecycle.ingresado.value
    remito.fecha_historico = None
    remito.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(remito)
    return remito
