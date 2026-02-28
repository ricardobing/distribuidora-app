"""
Remito service: pipeline completo de ingesta y procesamiento.
Migra: processRowByIndex() (7 pasos), recibirRemitosFraccionados_(), onChangeInstallable()
"""
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.remito import Remito, RemitoEstadoClasificacion, RemitoEstadoLifecycle
from app.models.pedido_listo import PedidoListo
from app.services import carrier_service, geocode_service, address_service, window_service
from app.core.constants import KNOWN_LOCALITIES

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    ok: bool
    total: int
    nuevos: int
    duplicados: int
    errores: list[str]


async def ingest_batch(
    db: AsyncSession,
    numeros: list[str],
    source: str = "manual",
) -> IngestResult:
    """Ingesta batch de remitos."""
    nuevos = 0
    duplicados = 0
    errores = []

    for numero in numeros:
        numero = numero.strip().upper()
        if not numero:
            continue

        exists = await db.execute(select(Remito).where(Remito.numero == numero))
        if exists.scalar_one_or_none():
            duplicados += 1
            continue

        remito = Remito(
            numero=numero,
            source=source,
            estado_clasificacion=RemitoEstadoClasificacion.pendiente.value,
            estado_lifecycle=RemitoEstadoLifecycle.ingresado.value,
        )
        db.add(remito)
        try:
            await db.flush()
            await _lookup_pedidos_listos(db, remito)
            await process_pipeline(db, remito)
            await db.commit()
            nuevos += 1
        except Exception as e:
            await db.rollback()
            errores.append(f"{numero}: {str(e)[:100]}")
            logger.error(f"Error procesando remito {numero}: {e}", exc_info=True)

    return IngestResult(
        ok=True,
        total=len(numeros),
        nuevos=nuevos,
        duplicados=duplicados,
        errores=errores,
    )


async def process_pipeline(db: AsyncSession, remito: Remito) -> Remito:
    """Pipeline de 7 pasos de procesamiento."""
    domicilio = remito.direccion_raw or remito.direccion_normalizada or ""
    observaciones = remito.observaciones or ""

    # PASO 0.5 — Normalizar dirección
    if domicilio:
        normalized = address_service.normalize(domicilio)
        normalized = address_service.fix_ciudad_mendoza(normalized)
        remito.direccion_normalizada = normalized

    # PASO 1 — ¿Es RETIRO?
    if carrier_service.detect_pickup(observaciones) or carrier_service.detect_pickup(domicilio):
        carrier = await _find_carrier_by_name(db, "RETIRO EN GALPON")
        remito.carrier_id = carrier.id if carrier else None
        remito.estado_clasificacion = RemitoEstadoClasificacion.retiro_sospechado.value
        remito.motivo_clasificacion = "Detectado como retiro en galpón"
        remito.updated_at = datetime.now(timezone.utc)
        return remito

    # PASO 2 — ¿Es TRANSPORTE EXTERNO?
    carrier_detection = await carrier_service.detect(
        db, observaciones or remito.direccion_raw or "", remito.localidad
    )
    if carrier_detection.nombre_canonico not in ("ENVIO PROPIO", "DESCONOCIDO", "RETIRO EN GALPON"):
        remito.carrier_id = carrier_detection.carrier_id
        remito.estado_clasificacion = RemitoEstadoClasificacion.transporte_externo.value
        remito.motivo_clasificacion = f"Carrier detectado: {carrier_detection.nombre_canonico}"
        remito.updated_at = datetime.now(timezone.utc)
        return remito

    remito.carrier_id = carrier_detection.carrier_id

    # PASO 3 — Validación básica de dirección
    if not domicilio or len(domicilio.strip()) < 5:
        remito.estado_clasificacion = RemitoEstadoClasificacion.corregir.value
        remito.motivo_clasificacion = "Dirección vacía o muy corta"
        remito.updated_at = datetime.now(timezone.utc)
        return remito

    # PASO 4 — Agregar localidad si no tiene
    normalized_upper = (remito.direccion_normalizada or "").upper()
    has_locality = any(loc in normalized_upper for loc in KNOWN_LOCALITIES)
    if not has_locality and remito.direccion_normalizada:
        remito.direccion_normalizada = f"{remito.direccion_normalizada}, Mendoza"

    # PASO 5 — Geocodificación
    geo_result = await geocode_service.geocode(db, remito.direccion_normalizada or domicilio)
    if geo_result:
        remito.lat = geo_result.lat
        remito.lng = geo_result.lng
        remito.geocode_formatted = geo_result.formatted_address
        remito.geocode_provider = geo_result.source
        remito.geocode_score = geo_result.confidence
        if not geo_result.has_street_number:
            remito.estado_clasificacion = RemitoEstadoClasificacion.corregir.value
            remito.motivo_clasificacion = "Sin número de calle en geocodificación"
            remito.updated_at = datetime.now(timezone.utc)
            return remito
    else:
        remito.estado_clasificacion = RemitoEstadoClasificacion.no_encontrado.value
        remito.motivo_clasificacion = "Geocodificación sin resultado"
        remito.updated_at = datetime.now(timezone.utc)
        return remito

    # PASO 6 — Ventana horaria
    window = window_service.parse_window(observaciones)
    remito.ventana_tipo = window.ventana_tipo
    remito.ventana_desde_min = window.desde_min
    remito.ventana_hasta_min = window.hasta_min
    remito.ventana_raw = window.raw_text
    remito.llamar_antes = window.llamar_antes

    # PASO 7 — Estado final
    remito.estado_clasificacion = RemitoEstadoClasificacion.enviar.value
    remito.motivo_clasificacion = None
    remito.updated_at = datetime.now(timezone.utc)
    return remito


async def process_pending(db: AsyncSession) -> int:
    """Procesa todos los remitos en estado pendiente."""
    result = await db.execute(
        select(Remito).where(
            Remito.estado_clasificacion == RemitoEstadoClasificacion.pendiente.value
        )
    )
    pending = result.scalars().all()
    processed = 0
    for remito in pending:
        try:
            await process_pipeline(db, remito)
            await db.commit()
            processed += 1
        except Exception as e:
            await db.rollback()
            logger.error(f"Error procesando remito pendiente {remito.numero}: {e}")
    return processed


async def get_by_numero(db: AsyncSession, numero: str) -> Optional[Remito]:
    result = await db.execute(select(Remito).where(Remito.numero == numero.upper()))
    return result.scalar_one_or_none()


async def _lookup_pedidos_listos(db: AsyncSession, remito: Remito) -> None:
    """Busca datos en PedidoListo y los copia al remito."""
    result = await db.execute(
        select(PedidoListo).where(PedidoListo.numero_remito == remito.numero)
    )
    pl = result.scalar_one_or_none()
    if not pl or not pl.raw_data:
        return
    data = pl.raw_data
    if not remito.cliente and data.get("cliente"):
        remito.cliente = data["cliente"]
    if not remito.direccion_raw and data.get("domicilio"):
        remito.direccion_raw = data["domicilio"]
    if not remito.observaciones and data.get("observaciones"):
        remito.observaciones = data["observaciones"]
    if not remito.localidad and data.get("localidad"):
        remito.localidad = data["localidad"]
    pl.linked_remito_id = remito.id


async def _find_carrier_by_name(db: AsyncSession, nombre: str):
    from app.models.carrier import Carrier
    result = await db.execute(select(Carrier).where(Carrier.nombre_canonico == nombre))
    return result.scalar_one_or_none()
