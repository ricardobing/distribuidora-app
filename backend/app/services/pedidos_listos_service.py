"""
Pedidos Listos service: sync de datos desde fuente externa.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.pedido_listo import PedidoListo
from app.models.remito import Remito

logger = logging.getLogger(__name__)


async def sync_batch(db: AsyncSession, data: list[dict]) -> dict:
    """
    Sincroniza datos de Pedidos Listos a la tabla pedidos_listos.
    Si el remito ya existe en remitos, actualiza sus datos.
    """
    nuevos = 0
    actualizados = 0

    for row in data:
        numero = str(row.get("numero_remito") or row.get("remito") or "").strip().upper()
        if not numero:
            continue

        # Buscar en PL
        result = await db.execute(
            select(PedidoListo).where(PedidoListo.numero_remito == numero)
        )
        pl = result.scalar_one_or_none()

        # Buscar remito asociado
        r_result = await db.execute(
            select(Remito).where(Remito.numero == numero)
        )
        remito = r_result.scalar_one_or_none()

        if pl:
            # Actualizar
            pl.cliente = row.get("cliente") or pl.cliente
            pl.domicilio = row.get("domicilio") or pl.domicilio
            pl.localidad = row.get("localidad") or pl.localidad
            pl.provincia = row.get("provincia") or pl.provincia
            pl.observaciones = row.get("observaciones") or pl.observaciones
            pl.transporte = row.get("transporte") or pl.transporte
            pl.synced_at = datetime.now(timezone.utc)
            pl.raw_data = row
            actualizados += 1
        else:
            pl = PedidoListo(
                numero_remito=numero,
                cliente=row.get("cliente"),
                domicilio=row.get("domicilio"),
                localidad=row.get("localidad"),
                provincia=row.get("provincia"),
                observaciones=row.get("observaciones"),
                transporte=row.get("transporte"),
                raw_data=row,
            )
            db.add(pl)
            nuevos += 1

        if remito and pl:
            pl.remito_id = remito.id

    await db.commit()
    return {"ok": True, "total": len(data), "nuevos": nuevos, "actualizados": actualizados}
