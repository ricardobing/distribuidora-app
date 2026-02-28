"""
Remito service: pipeline completo de ingesta y procesamiento.
Migra: processRowByIndex() (7 pasos), recibirRemitosFraccionados_(), onChangeInstallable()
"""
import logging
import re
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models.remito import Remito, RemitoEstadoClasificacion, RemitoEstadoLifecycle
from app.models.carrier import Carrier
from app.models.pedido_listo import PedidoListo
from app.services import carrier_service, geocode_service, address_service, window_service
from app.core.constants import RE_PICKUP

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
    """
    Ingesta batch de remitos.
    1. Deduplicar contra DB (remitos activos + histórico)
    2. Crear registros pendientes
    3. Ejecutar pipeline para cada nuevo
    4. Retornar resultado
    """
    nuevos = 0
    duplicados = 0
    errores = []

    for numero in numeros:
        numero = numero.strip().upper()
        if not numero:
            continue

        # Verificar duplicado
        exists = await db.execute(
            select(Remito).where(Remito.numero == numero)
        )
        if exists.scalar_one_or_none():
            duplicados += 1
            continue

        # Crear remito en estado pendiente
        remito = Remito(
            numero=numero,
            source=source,
            estado_clasificacion=RemitoEstadoClasificacion.pendiente.value,
            estado_lifecycle=RemitoEstadoLifecycle.ingresado.value,
        )
        db.add(remito)
        try:
            await db.flush()
            # Lookup en Pedidos Listos
            await _lookup_pedidos_listos(db, remito)
            # Pipeline completo
            await process_pipeline(db, remito)
            await db.commit()
            nuevos += 1
        except Exception as e:
            await db.rollback()
            errores.append(f"{numero}: {str(e)[:100]}")
            logger.error(f"Error procesando remito {numero}: {e}")

    return IngestResult(
        ok=True,
        total=len(numeros),
        nuevos=nuevos,
        duplicados=duplicados,
        errores=errores,
    )


async def process_pipeline(db: AsyncSession, remito: Remito) -> Remito:
    """
    Pipeline de 7 pasos de procesamiento.
    Migra: processRowByIndex() del sistema original.
    """
    domicilio = remito.domicilio_raw or remito.domicilio_normalizado or ""
    observaciones = remito.observaciones_pl or ""
    provincia = remito.provincia or "Mendoza"

    # PASO 0.5 — Normalizar dirección
    if domicilio:
        normalized = address_service.normalize(domicilio)
        normalized = address_service.fix_ciudad_mendoza(normalized)
        remito.domicilio_normalizado = normalized

    # PASO 1 — ¿Es RETIRO?
    if carrier_service.detect_pickup(observaciones) or carrier_service.detect_pickup(domicilio):
        carrier = await _find_carrier_by_name(db, "RETIRO EN COMERCIAL")
        remito.carrier_id = carrier.id if carrier else None
        remito.estado_clasificacion = RemitoEstadoClasificacion.retiro_sospechado.value
        remito.motivo_clasificacion = "Detectado como retiro en comercial"
        remito.updated_at = datetime.now(timezone.utc)
        return remito

    # PASO 2 — ¿Es TRANSPORTE EXTERNO?
    carrier_detection = await carrier_service.detect(
        db, observaciones or remito.transporte_raw or "", provincia
    )
    if carrier_detection.nombre_canonico not in (
        "ENVÍO PROPIO (MOLLY MARKET)",
        "DESCONOCIDO",
        "RETIRO EN COMERCIAL",
    ):
        remito.carrier_id = carrier_detection.carrier_id
        remito.estado_clasificacion = RemitoEstadoClasificacion.transporte_externo.value
        remito.motivo_clasificacion = f"Carrier detectado: {carrier_detection.nombre_canonico}"
        remito.updated_at = datetime.now(timezone.utc)
        return remito

    # Asignar carrier
    remito.carrier_id = carrier_detection.carrier_id

    # PASO 3 — Validación básica de dirección
    if not domicilio or len(domicilio.strip()) < 5:
        remito.estado_clasificacion = RemitoEstadoClasificacion.corregir.value
        remito.motivo_clasificacion = "Dirección vacía o muy corta"
        remito.updated_at = datetime.now(timezone.utc)
        return remito

    # PASO 4 — Normalización (ya hecha en 0.5)
    # Si no tiene componente de localidad, marcar para corrección
    normalized_upper = (remito.domicilio_normalizado or "").upper()
    from app.core.constants import KNOWN_LOCALITIES
    has_locality = any(loc in normalized_upper for loc in KNOWN_LOCALITIES)
    if not has_locality:
        # Si no tiene localidad explícita, agregar Mendoza por defecto
        if remito.domicilio_normalizado:
            remito.domicilio_normalizado = f"{remito.domicilio_normalizado}, Mendoza"

    # PASO 5 — Geocodificación
    geo_result = await geocode_service.geocode(db, remito.domicilio_normalizado or domicilio)
    if geo_result:
        remito.geom = f"SRID=4326;POINT({geo_result.lng} {geo_result.lat})"
        remito.geocode_formatted = geo_result.formatted_address
        remito.geocode_has_street_num = geo_result.has_street_number
        remito.geocode_source = geo_result.source
        remito.geocode_confidence = geo_result.confidence
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

    # PASO 7 — Estado final = enviar ✅
    remito.estado_clasificacion = RemitoEstadoClasificacion.enviar.value
    remito.motivo_clasificacion = None
    remito.updated_at = datetime.now(timezone.utc)
    return remito


async def process_pending(db: AsyncSession) -> dict:
    """
    Procesa todos los remitos en estado pendiente.
    Migra: onChangeInstallable() + processPendientes_().
    """
    result = await db.execute(
        select(Remito).where(
            Remito.estado_clasificacion == RemitoEstadoClasificacion.pendiente.value
        )
    )
    pending = result.scalars().all()
    processed = 0
    errors = 0
    for remito in pending:
        try:
            await process_pipeline(db, remito)
            await db.commit()
            processed += 1
        except Exception as e:
            await db.rollback()
            errors += 1
            logger.error(f"Error procesando remito pendiente {remito.numero}: {e}")

    return {"processed": processed, "errors": errors}


async def _lookup_pedidos_listos(db: AsyncSession, remito: Remito) -> None:
    """
    Busca datos del remito en la tabla pedidos_listos.
    Migra: lookupPedidosListos_().
    """
    result = await db.execute(
        select(PedidoListo).where(PedidoListo.numero_remito == remito.numero)
    )
    pl = result.scalar_one_or_none()
    if not pl:
        return
    remito.cliente = pl.cliente or remito.cliente
    remito.domicilio_raw = pl.domicilio or remito.domicilio_raw
    remito.localidad = pl.localidad or remito.localidad
    remito.provincia = pl.provincia or remito.provincia
    remito.observaciones_pl = pl.observaciones or remito.observaciones_pl
    remito.transporte_raw = pl.transporte or remito.transporte_raw
    pl.remito_id = remito.id


async def _find_carrier_by_name(db: AsyncSession, nombre: str) -> Optional[Carrier]:
    result = await db.execute(
        select(Carrier).where(Carrier.nombre_canonico == nombre)
    )
    return result.scalar_one_or_none()


async def get_by_numero(db: AsyncSession, numero: str) -> Optional[Remito]:
    result = await db.execute(
        select(Remito).where(Remito.numero == numero.upper())
    )
    return result.scalar_one_or_none()
